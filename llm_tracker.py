# ====== LLM TRACKER ======
import pprint
import json
import time
from analytics import analyze_logs  # import your analytics function

# Load model pricing
with open("model_pricing.json") as f:
    MODEL_PRICING = json.load(f)

# COST CALCULATION FUNCTION
def calculate_cost(model, prompt_tokens, completion_tokens):
    default_pricing = {"prompt": 0.01, "completion": 0.02}  # fallback
    pricing = MODEL_PRICING.get(model, default_pricing)

    if model not in MODEL_PRICING:
        print(f"Pricing not found for model '{model}'. Using default pricing.")

    prompt_cost = (prompt_tokens / 1000) * pricing["prompt"]
    completion_cost = (completion_tokens / 1000) * pricing["completion"]
    return round(prompt_cost + completion_cost, 6)

# LOG USAGE FUNCTION
def log_usage(usage_data):
    with open("logs/llm_usage.jsonl", "a") as f:
        f.write(json.dumps(usage_data) + "\n")

# TRACK ONE LLM CALL
def track_llm_call(prompt, model, tags):
    start_time = time.time()

    # MOCK RESPONSE (replace with real API call later)
    response_text = "This is a mock LLM response"
    prompt_tokens = len(prompt.split())
    completion_tokens = 20
    end_time = time.time()

    cost = calculate_cost(model, prompt_tokens, completion_tokens)

    usage = {
        "model": model,
        "prompt_tokens": prompt_tokens,
        "completion_tokens": completion_tokens,
        "cost_usd": cost,
        "latency_ms": round((end_time - start_time) * 1000, 2),
        "tags": tags
    }

    log_usage(usage)

    # Print summary per call
    print(f"[{tags.get('user','unknown')}] Model: {model} | Cost: ${cost:.6f} | Latency: {usage['latency_ms']} ms")
    return response_text, usage

# ====== RUN MULTIPLE TEST CALLS ======
test_calls = [
    {"prompt": "Explain LLM observability", "model": "gemini", "tags": {"user": "demo", "feature": "education", "environment": "dev"}},
    {"prompt": "Explain transformers in AI", "model": "gemini", "tags": {"user": "alice", "feature": "research", "environment": "dev"}},
    {"prompt": "Summarize this article", "model": "gemini", "tags": {"user": "bob", "feature": "summary", "environment": "prod"}},
    {"prompt": "Explain transformers in AI", "model": "gpt-3.5", "tags": {"user": "alice", "feature": "research", "environment": "dev"}},
    {"prompt": "Summarize climate change article", "model": "gpt-4", "tags": {"user": "bob", "feature": "summary", "environment": "prod"}},
    {"prompt": "List Python data structures", "model": "gpt-3.5", "tags": {"user": "carol", "feature": "education", "environment": "dev"}},
    {"prompt": "Explain quantum computing simply", "model": "gpt-4", "tags": {"user": "dave", "feature": "research", "environment": "prod"}},
    {"prompt": "Generate a short poem about AI", "model": "gemini", "tags": {"user": "eve", "feature": "creative", "environment": "dev"}},
]

# Run all test calls
for call in test_calls:
    track_llm_call(call["prompt"], call["model"], call["tags"])

# Run analytics at the end
print("\n===== LLM USAGE ANALYTICS =====")
analyze_logs()