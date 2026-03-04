import json #json string to python dictionary and python dict to json string
from collections import defaultdict

LOG_FILE = "logs/llm_usage.jsonl" #every LLM call appends one JSON object per line to this file (JSONL)

def analyze_logs(): #reads all past LLM usage,aggregates cost,prints analytics
    total_cost = 0.0 #INITIALIZE ACCUMULATORS - store overall money spent on LLMs
    cost_by_model = defaultdict(float)# tracks which model costs the most
    cost_by_user = defaultdict(float)#tracks who is burning money 
    latencies = []
    cost_by_feature = defaultdict(float)
    cost_by_env = defaultdict(float)

    with open(LOG_FILE, "r") as f: # opens file in read mode , also closes it safely 
        for line in f: # read 1 LLM call at a time
            record = json.loads(line)#convert JSON sting to dictionary

            cost = record["cost_usd"] # extract values , money spent for single LLM model
            model = record["model"]# LLM that was used 
            user = record["tags"].get("user", "unknown")# prevents crashes 
            latency = record.get("latency_ms", 0)  # get latency (ms), default 0

            # Feature and environment tracking
            feature = record["tags"].get("feature", "unknown")
            env = record["tags"].get("environment", "unknown")
            cost_by_feature[feature] += cost
            cost_by_env[env] += cost

            total_cost += cost
            cost_by_model[model] += cost#adds cost to that model's bucket
            cost_by_user[user] += cost
            latencies.append(latency)

    if latencies:
        print(f"Average latency: {sum(latencies)/len(latencies):.2f} ms")
        print(f"Max latency: {max(latencies):.2f} ms")

    print("\n📊 LLM COST ANALYTICS")# just formatting 
    print(f"Total cost: ${total_cost:.6f}\n")#.6f = print 6 digits after decimal

    print("Cost by model:")
    for model, cost in cost_by_model.items():
        print(f"  {model}: ${cost:.6f}")#prints cost per model 

    print("\nCost by user:")
    for user, cost in cost_by_user.items():
        print(f"  {user}: ${cost:.6f}")#prints cost per user

    print("\nCost by feature:")
    for feature, cost in cost_by_feature.items():
        print(f"  {feature}: ${cost:.6f}")

    print("\nCost by environment:")
    for env, cost in cost_by_env.items():
        print(f"  {env}: ${cost:.6f}") 