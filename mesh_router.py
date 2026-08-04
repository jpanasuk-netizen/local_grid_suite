import time
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import uvicorn

app = FastAPI(title="Grid Mesh Router")

# 1. Healthcheck / Root Endpoint
@app.get("/")
async def root():
    return {"status": "online", "service": "Grid-Nexus Mesh Router"}

# 2. Model Discovery Endpoints (Fixes {"detail":"Not Found"} when Open WebUI scans port 9099)
@app.get("/v1/models")
@app.get("/models")
async def list_models():
    """Returns available virtual routed models for Open WebUI discovery."""
    return {
        "object": "list",
        "data": [
            {
                "id": "grid-auto-router",
                "object": "model",
                "created": int(time.time()),
                "owned_by": "grid-nexus"
            },
            {
                "id": "grid-coder",
                "object": "model",
                "created": int(time.time()),
                "owned_by": "grid-nexus"
            }
        ]
    }

# 3. Chat Completions Router Endpoint
@app.post("/v1/chat/completions")
@app.post("/chat/completions")
async def chat_completions(request: Request):
    """Intercepts prompts and routes them based on model ID / context."""
    body = await request.json()
    requested_model = body.get("model", "grid-auto-router")
    messages = body.get("messages", [])

    # Mock dynamic routing response (Replace with your actual proxy logic to Ollama)
    return {
        "id": f"chatcmpl-grid-{int(time.time())}",
        "object": "chat.completion",
        "created": int(time.time()),
        "model": requested_model,
        "choices": [
            {
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": f"[Routed through {requested_model}]: Processing request via local grid execution."
                },
                "finish_reason": "stop"
            }
        ],
        "usage": {
            "prompt_tokens": 10,
            "completion_tokens": 20,
            "total_tokens": 30
        }
    }

if __name__ == "__main__":
    print("⚡ Starting Grid Mesh Router on http://127.0.0.1:9099 ...")
    uvicorn.run(app, host="0.0.0.0", port=9099)
