from fastapi import FastAPI
import json
from collections import defaultdict

LOG_FILE = "logs/llm_usage.jsonl"

app = FastAPI(title="LLM Observability Platform")

@app.get("/")
def home():
    return {"status": "LLM Observability API running"}

@app.get("/analytics")
def get_analytics():
    total_cost = 0.0
    cost_by_model = defaultdict(float)
    cost_by_user = defaultdict(float)
    cost_by_feature = defaultdict(float)
    cost_by_env = defaultdict(float)
    latencies = []

    with open(LOG_FILE, "r") as f:
        for line in f:
            record = json.loads(line)

            cost = record["cost_usd"]
            model = record["model"]
            latency = record.get("latency_ms", 0)

            tags = record.get("tags", {})
            user = tags.get("user", "unknown")
            feature = tags.get("feature", "unknown")
            env = tags.get("environment", "unknown")

            total_cost += cost
            cost_by_model[model] += cost
            cost_by_user[user] += cost
            cost_by_feature[feature] += cost
            cost_by_env[env] += cost
            latencies.append(latency)

    return {
        "total_cost": round(total_cost, 6),
        "avg_latency_ms": round(sum(latencies)/len(latencies), 2) if latencies else 0,
        "max_latency_ms": max(latencies) if latencies else 0,
        "cost_by_model": cost_by_model,
        "cost_by_user": cost_by_user,
        "cost_by_feature": cost_by_feature,
        "cost_by_environment": cost_by_env
    }