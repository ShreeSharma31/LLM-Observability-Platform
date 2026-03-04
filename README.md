# LLM Observability Platform  
API-Based Usage & Cost Tracking System for LLM Applications
![image alt](https://github.com/ShreeSharma31/LLM-Observability-Platform/blob/main/pic1.jpeg?raw=true)
---

## Overview

LLM Observability Platform is a backend monitoring system designed to track, log, and analyze usage metrics of Large Language Model (LLM) applications.

It acts as an analytics and monitoring layer between LLM-based applications and model providers, enabling structured tracking of token consumption, latency, cost, and custom metadata.

This project focuses on backend system design, analytics computation, and API architecture.

---

## Problem Statement

Modern LLM applications incur variable token usage costs and latency overhead. However, many small-scale deployments lack:

- Structured usage logging  
- Cost visibility by model or user  
- Latency monitoring  
- Aggregated analytics dashboards  

This platform addresses these gaps by providing a lightweight, API-driven observability layer.

---

## Core Features

###  Usage Tracking
- Model name (e.g., gpt-4, gpt-3.5, gemini, etc.)
- Prompt tokens
- Completion tokens
- Latency (in milliseconds)
- Custom metadata (user, feature, environment tags)

### Persistent Logging
- Structured logging using JSONL storage
- Append-only event logging for reliability

### Analytics Engine
- Total cost computation
- Cost breakdown by model
- Cost breakdown by user
- Average latency
- Maximum latency
- Aggregated usage insights

### REST API Endpoints
- GET / → Health check
- POST /track → Ingest usage events
- GET /analytics → Retrieve usage analytics
- /docs → Interactive Swagger UI (OpenAPI 3.1)

---

## System Architecture

The platform follows a modular backend design:

Client Application  
        ↓  
POST /track  
        ↓  
Validation Layer (Pydantic)  
        ↓  
Persistent Logging (JSONL Storage)  
        ↓  
Analytics Engine  
        ↓  
GET /analytics  

Key architectural decisions:
- FastAPI for high-performance async API handling
- Pydantic for strict data validation
- Uvicorn as ASGI server
- OpenAPI-compliant documentation for developer usability

This architecture enables clean separation of ingestion, storage, and analytics computation.

---

## Tech Stack

- *Language:* Python  
- *Framework:* FastAPI  
- *Server:* Uvicorn  
- *Validation:* Pydantic  
- *Storage:* JSONL (Structured Logging)  
- *Documentation:* OpenAPI 3.1 (Swagger UI)

---

##  Example Usage Event

```json
{
  "model": "gpt-4",
  "prompt_tokens": 120,
  "completion_tokens": 80,
  "latency_ms": 450,
  "user": "user_123",
  "feature": "chat",
  "environment": "production"
}
