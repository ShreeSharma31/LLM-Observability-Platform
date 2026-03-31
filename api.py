from fastapi import FastAPI, Depends, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from database import SessionLocal, engine, ensure_sqlite_schema
from models import Base, LLMLog
from collections import defaultdict
from pydantic import BaseModel, ConfigDict, Field
from datetime import datetime, timezone
from pathlib import Path
from settings import settings
from typing import Dict

app = FastAPI(title="LLM Observability Platform")

# Mock per-call pricing in USD; unknown models use DEFAULT_MODEL_PRICE.
MODEL_PRICING: Dict[str, float] = {
    "gpt-4": 0.03,
    "gpt-3.5": 0.002,
    "gemini": 0.001,
    "claude": 0.008,
}
DEFAULT_MODEL_PRICE = 0.004

allow_origins = [x.strip() for x in settings.cors_origins.split(",")] if settings.cors_origins != "*" else ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=allow_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ✅ Create tables
Base.metadata.create_all(bind=engine)
ensure_sqlite_schema()

# ✅ DB Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def validate_api_key(x_api_key: str | None = Header(default=None)):
    if not settings.api_key_enabled:
        return
    if not settings.api_key:
        raise HTTPException(status_code=500, detail="API key is enabled but not configured")
    if x_api_key != settings.api_key:
        raise HTTPException(status_code=401, detail="Invalid API key")


def _create_token(username: str, role: str):
    now = datetime.now(timezone.utc)
    payload = {
        "sub": username,
        "role": role,
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(minutes=settings.jwt_expire_minutes)).timestamp()),
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def get_current_user(token: str | None = Depends(oauth2_scheme)):
    if not settings.jwt_auth_enabled:
        return {"username": "anonymous", "role": "admin"}
    if not token:
        raise HTTPException(status_code=401, detail="Missing bearer token")
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
    except JWTError as exc:
        raise HTTPException(status_code=401, detail="Invalid or expired token") from exc

    username = payload.get("sub")
    role = payload.get("role")
    if not username or not role:
        raise HTTPException(status_code=401, detail="Invalid token claims")
    return {"username": username, "role": role}


def require_admin(user=Depends(get_current_user)):
    if user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Admin role required")
    return user


@app.middleware("http")
async def observability_middleware(request: Request, call_next):
    start = time.perf_counter()
    path = request.url.path
    method = request.method

    # Lightweight in-memory IP rate limiting.
    if settings.rate_limit_enabled and path not in {"/health", "/metrics"}:
        ip = request.client.host if request.client else "unknown"
        now = time.time()
        bucket = request_buckets.setdefault(ip, [])
        cutoff = now - RATE_LIMIT_WINDOW_SECONDS
        bucket[:] = [t for t in bucket if t >= cutoff]
        if len(bucket) >= settings.rate_limit_per_minute:
            REQUEST_COUNT.labels(method=method, path=path, status="429").inc()
            return Response(content="Rate limit exceeded", status_code=429)
        bucket.append(now)

    response = await call_next(request)
    elapsed = max(0.0, time.perf_counter() - start)
    REQUEST_COUNT.labels(method=method, path=path, status=str(response.status_code)).inc()
    REQUEST_LATENCY.labels(method=method, path=path).observe(elapsed)
    return response


@app.post("/auth/token")
def issue_token(form_data: OAuth2PasswordRequestForm = Depends()):
    user = USERS.get(form_data.username)
    if not user or form_data.password != user["password"]:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    token = _create_token(form_data.username, user["role"])
    return {"access_token": token, "token_type": "bearer", "role": user["role"]}


# ✅ Home
@app.get("/")
def home():
    index_path = Path(__file__).with_name("index.html")
    if index_path.exists():
        return FileResponse(str(index_path))
    return {"status": "LLM Observability API running", "hint": "index.html not found"}


@app.get("/health")
def health():
    return {"status": "ok", "ts": datetime.now(timezone.utc).isoformat()}


@app.get("/metrics")
def metrics():
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)


@app.get("/me")
def me(user=Depends(get_current_user)):
    return user


# ✅ Analytics
@app.get("/analytics")
def get_analytics(
    db: Session = Depends(get_db),
    _auth: None = Depends(validate_api_key),
    _user=Depends(get_current_user),
    limit: int = Query(default=5000, ge=1, le=10000),
):
    logs = db.query(LLMLog).order_by(LLMLog.id.desc()).limit(limit).all()

    total_cost = 0.0
    cost_by_model = defaultdict(float)
    cost_by_user = defaultdict(float)
    cost_by_feature = defaultdict(float)
    cost_by_env = defaultdict(float)
    latencies = []
    points = []

    for record in logs:
        cost = float(record.cost_usd or 0.0)
        total_cost += cost

        cost_by_model[record.model] += cost
        cost_by_user[record.user] += cost
        cost_by_feature[record.feature] += cost
        cost_by_env[record.environment] += cost
        latency = float(record.latency_ms or 0.0)
        latencies.append(latency)

        created = record.created_at
        if created is None:
            # Back-compat for older rows (or rows inserted before created_at existed)
            created = datetime.now(timezone.utc)
        elif created.tzinfo is None:
            created = created.replace(tzinfo=timezone.utc)

        points.append({"ts": created.isoformat(), "cost_usd": cost, "latency_ms": latency})

    points.sort(key=lambda p: p["ts"])

    alerts = []
    if total_cost >= settings.high_cost_threshold:
        alerts.append(
            {
                "type": "high_cost",
                "message": f"Total cost crossed threshold (${settings.high_cost_threshold:.4f})",
                "value": round(total_cost, 6),
                "threshold": settings.high_cost_threshold,
            }
        )
    if latencies and max(latencies) >= settings.high_latency_threshold_ms:
        alerts.append(
            {
                "type": "high_latency",
                "message": f"Latency crossed threshold ({settings.high_latency_threshold_ms:.1f} ms)",
                "value": max(latencies),
                "threshold": settings.high_latency_threshold_ms,
            }
        )

    return {
        "total_cost": round(total_cost, 6),
        "avg_latency_ms": round(sum(latencies)/len(latencies), 2) if latencies else 0,
        "max_latency_ms": max(latencies) if latencies else 0,
        "cost_by_model": dict(cost_by_model),
        "cost_by_user": dict(cost_by_user),
        "cost_by_feature": dict(cost_by_feature),
        "cost_by_environment": dict(cost_by_env),
        "top_users": sorted(
            [{"user": user, "cost_usd": round(cost, 6)} for user, cost in cost_by_user.items()],
            key=lambda x: x["cost_usd"],
            reverse=True,
        )[:5],
        "timeseries": points,
        "alerts": alerts,
    }


# ✅ Request Model
class LogRequest(BaseModel):
    user: str
    model: str
    cost_usd: float = Field(..., alias="cost")
    latency_ms: float = Field(..., alias="latency")
    feature: str
    environment: str

    model_config = ConfigDict(populate_by_name=True)


# ✅ Track API (ONLY ONE)
@app.post("/track")
def track_log(
    data: LogRequest,
    db: Session = Depends(get_db),
    _auth: None = Depends(validate_api_key),
    _user=Depends(get_current_user),
):
    if data.cost_usd < 0:
        raise HTTPException(status_code=400, detail="cost must be >= 0")
    if data.latency_ms < 0:
        raise HTTPException(status_code=400, detail="latency must be >= 0")

    new_log = LLMLog(
        user=data.user,
        model=data.model,
        cost_usd=data.cost_usd,
        latency_ms=data.latency_ms,
        feature=data.feature,
        environment=data.environment,
        created_at=datetime.now(timezone.utc),
    )

    db.add(new_log)
    db.commit()
    db.refresh(new_log)
    TRACK_LOG_COUNT.inc()

    return {"message": "Log stored successfully", "id": new_log.id}


@app.get("/admin/config")
def admin_config(_user=Depends(require_admin)):
    return {
        "rate_limit_enabled": settings.rate_limit_enabled,
        "rate_limit_per_minute": settings.rate_limit_per_minute,
        "high_cost_threshold": settings.high_cost_threshold,
        "high_latency_threshold_ms": settings.high_latency_threshold_ms,
    }