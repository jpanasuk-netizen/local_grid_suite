from pathlib import Path
import requests
import json
import time
import os
from datetime import datetime

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "qwen3:8b"
HISTORY_FILE = "/home/jpanasusuk/local_grid/logs/benchmark_history.json"

# Ensure log directory exists
os.makedirs(str(Path(__file__).resolve().parent / "logs"), exist_ok=True)
ACTUAL_HISTORY_FILE = str(Path(__file__).resolve().parent / "logs" / "benchmark_history.json")

def worker_agent_run(prompt_task):
    """Worker Agent: Executes the raw generation request against local hardware."""
    payload = {
        "model": MODEL_NAME,
        "prompt": prompt_task,
        "stream": True,
        "options": {"temperature": 0.2, "num_predict": 400}
    }
    return requests.post(OLLAMA_URL, json=payload, stream=True)

def monitor_agent_track(run_id, response_stream):
    """Monitor Agent: Tracks streaming chunks, prints live updates, and calculates telemetry."""
    print(f"\n[MONITOR AGENT] Tracking Run #{run_id} on model [{MODEL_NAME}]...")
    print("-" * 65)

    start_time = time.time()
    output_tokens = 0
    eval_duration = 0
    full_response_text = ""

    for line in response_stream.iter_lines():
        if line:
            chunk = json.loads(line.decode('utf-8'))
            token_piece = chunk.get("response", "")
            print(token_piece, end="", flush=True)
            full_response_text += token_piece

            if chunk.get("done", False):
                output_tokens = chunk.get("eval_count", 0)
                eval_duration = chunk.get("eval_duration", 1) # nanoseconds

    total_wall_time = time.time() - start_time
    eval_seconds = eval_duration / 1_000_000_000
    tokens_per_sec = output_tokens / eval_seconds if eval_seconds > 0 else 0

    metrics = {
        "run_id": run_id,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "model": MODEL_NAME,
        "output_tokens": output_tokens,
        "total_wall_time_sec": round(total_wall_time, 2),
        "eval_time_sec": round(eval_seconds, 2),
        "tokens_per_sec": round(tokens_per_sec, 2)
    }

    print("\n" + "-" * 65)
    print(f"[MONITOR AGENT REPORT] Run #{run_id} Complete.")
    print(f"-> Speed : {metrics['tokens_per_sec']} tokens/sec | Tokens: {output_tokens} | Time: {metrics['eval_time_sec']}s")
    print("=" * 65)
    
    return metrics

def history_agent_record(metrics):
    """History Agent: Keeps ledger history, appends telemetry, and prints the leaderboard champion."""
    history = []
    if os.path.exists(ACTUAL_HISTORY_FILE):
        try:
            with open(ACTUAL_HISTORY_FILE, "r") as f:
                history = json.load(f)
        except json.JSONDecodeError:
            history = []

    history.append(metrics)

    with open(ACTUAL_HISTORY_FILE, "w") as f:
        json.dump(history, f, indent=4)

    # Find the fastest run by tokens_per_sec
    fastest_run = max(history, key=lambda x: x["tokens_per_sec"])

    print(f"\n[HISTORY AGENT LEADERBOARD] Total Runs Logged: {len(history)}")
    print(f"👑 CURRENT FASTEST RUN: Run #{fastest_run['run_id']} at **{fastest_run['tokens_per_sec']} tokens/sec** ({fastest_run['model']})")
    print("=" * 65 + "\n")

if __name__ == "__main__":
    benchmark_prompt = (
        "Write a highly detailed technical breakdown of how memory bandwidth "
        "affects local LLM inference speeds, explaining KV caching and token generation bottlenecks."
    )

    # Let's execute 3 consecutive benchmark iterations to test performance consistency
    for i in range(1, 4):
        print(f"\n>>> INITIALIZING BENCHMARK ITERATION {i} OF 3")
        stream_response = worker_agent_run(benchmark_prompt)
        if stream_response.status_code == 200:
            run_metrics = monitor_agent_track(i, stream_response)
            history_agent_record(run_metrics)
        else:
            print(f"Worker Agent failed to connect: {stream_response.text}")
        
        time.sleep(2) # Cool-down buffer between runs
