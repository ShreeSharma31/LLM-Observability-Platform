# LLM Observability Platform

Real-time dashboard for LLM usage analytics: cost, latency, users, models, features, and environments.

## Features

- `POST /track` to ingest LLM usage logs
- `GET /analytics` for aggregate metrics and time-series
- Dashboard at `/` with Chart.js visualizations
- Threshold-based alerts (`high_cost`, `high_latency`)
- Optional API key protection using `X-API-Key`
- Optional JWT auth with role claims (admin/viewer)
- Built-in per-IP rate limiting
- Prometheus metrics endpoint at `/metrics`
- SQLite default, Postgres-ready via `DATABASE_URL`

## Local Run (Windows PowerShell)

```powershell
cd "c:\Users\Dell\OneDrive\Documents\llm-observability-platform"
python -m pip install -r requirements.txt
python -m uvicorn api:app --reload --port 8000
```

Open [http://localhost:8000/](http://localhost:8000/).

## API Example

```powershell
Invoke-RestMethod -Method Post -Uri "http://localhost:8000/track" `
  -ContentType "application/json" `
  -Body (@{
    user="demo"
    model="gpt-4"
    cost=0.002
    latency=240
    feature="chat"
    environment="prod"
  } | ConvertTo-Json)
```

## Environment Variables

Copy `.env.example` values into your environment:

- `DATABASE_URL` (`sqlite:///./llm_data.db` by default)
- `CORS_ORIGINS` (comma-separated origins or `*`)
- `API_KEY_ENABLED` (`true/false`)
- `API_KEY` (required when API key is enabled)
- `JWT_AUTH_ENABLED`
- `JWT_SECRET`
- `JWT_ALGORITHM`
- `JWT_EXPIRE_MINUTES`
- `RATE_LIMIT_ENABLED`
- `RATE_LIMIT_PER_MINUTE`
- `HIGH_COST_THRESHOLD`
- `HIGH_LATENCY_THRESHOLD_MS`

## JWT Login Flow (optional)

If `JWT_AUTH_ENABLED=true`, get a bearer token first:

```powershell
Invoke-RestMethod -Method Post -Uri "http://localhost:8000/auth/token" `
  -ContentType "application/x-www-form-urlencoded" `
  -Body "username=admin&password=admin123"
```

Use returned `access_token` in:

```powershell
Invoke-RestMethod -Method Get -Uri "http://localhost:8000/me" `
  -Headers @{ Authorization = "Bearer <TOKEN>" }
```

For the dashboard UI, paste the same token into the "Optional JWT bearer token" input and click "Save Token".

## Migrations (Alembic)

```powershell
python -m alembic upgrade head
```

## Docker

```powershell
docker compose up --build
```

Then open [http://localhost:8000/](http://localhost:8000/).

## Tests

```powershell
python -m pytest -q
```
