from pathlib import Path
import requests
import json
import time
import os
from datetime import datetime

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "qwen3:8b"
HISTORY_FILE = str(Path(__file__).resolve().parent / "logs" / "manager_history.json")

os.makedirs(str(Path(__file__).resolve().parent / "logs"), exist_ok=True)

CONFIG_MATRIX = [
    {"run_id": 1, "temperature": 0.2, "num_predict": 300, "top_p": 0.9},
    {"run_id": 2, "temperature": 0.5, "num_predict": 450, "top_p": 0.95},
    {"run_id": 3, "temperature": 0.1, "num_predict": 600, "top_p": 0.85},
]

def manager_agent_configure(step_index):
    config = CONFIG_MATRIX[step_index]
    print(f"\n[MANAGER AGENT] Configuring Run #{config['run_id']} Parameters:")
    print(f" ⚙️  Temperature : {config['temperature']}")
    print(f" ⚙️  Max Tokens  : {config['num_predict']}")
    print(f" ⚙️  Top-P Scope : {config['top_p']}")
    print("-" * 65)
    return config

def worker_agent_run(config, prompt_task):
    payload = {
        "model": MODEL_NAME,
        "prompt": prompt_task,
        "stream": True,
        "options": {
            "temperature": config["temperature"],
            "num_predict": config["num_predict"],
            "top_p": config["top_p"]
        }
    }
    return requests.post(OLLAMA_URL, json=payload, stream=True)

def monitor_agent_track(config, response_stream):
    start_time = time.time()
    output_tokens = 0
    eval_duration = 0

    for line in response_stream.iter_lines():
        if line:
            chunk = json.loads(line.decode("utf-8"))
            print(chunk.get("response", ""), end="", flush=True)

            if chunk.get("done", False):
                output_tokens = chunk.get("eval_count", 0)
                eval_duration = chunk.get("eval_duration", 1)

    total_wall_time = time.time() - start_time
    eval_seconds = eval_duration / 1_000_000_000
    tokens_per_sec = output_tokens / eval_seconds if eval_seconds > 0 else 0

    metrics = {
        **config,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "output_tokens": output_tokens,
        "eval_time_sec": round(eval_seconds, 2),
        "tokens_per_sec": round(tokens_per_sec, 2)
    }
    return metrics

def history_agent_evaluate(metrics):
    history = []
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, "r") as f:
                history = json.load(f)
        except json.JSONDecodeError:
            history = []

    trend_arrow = "---"
    if history:
        prev_run = history[-1]
        speed_delta = metrics["tokens_per_sec"] - prev_run["tokens_per_sec"]
        if speed_delta > 0:
            trend_arrow = f"📈 UP (+{speed_delta:.2f} tok/s)"
        elif speed_delta < 0:
            trend_arrow = f"📉 DOWN ({speed_delta:.2f} tok/s)"
        else:
            trend_arrow = "➡️ EQUAL"

    history.append(metrics)
    with open(HISTORY_FILE, "w") as f:
        json.dump(history, f, indent=4)

    fastest_run = max(history, key=lambda x: x["tokens_per_sec"])

    print("\n" + "-" * 65)
    print(f"[MONITOR & HISTORY REPORT] Run #{metrics['run_id']} Summary:")
    print(f"-> Speed Achieved   : {metrics['tokens_per_sec']} tokens/sec")
    print(f"-> Performance Delta: {trend_arrow}")
    print(f"👑 ALL-TIME FASTEST : Run #{fastest_run['run_id']} ({fastest_run['tokens_per_sec']} tok/s | Temp: {fastest_run['temperature']})")
    print("=" * 65 + "\n")

if __name__ == "__main__":
    benchmark_prompt = "Explain the core architectural bottlenecks of hardware tensor core execution pipelines during localized matrix multiplication operations."
    for idx in range(len(CONFIG_MATRIX)):
        active_config = manager_agent_configure(idx)
        stream_resp = worker_agent_run(active_config, benchmark_prompt)
        if stream_resp.status_code == 200:
            run_metrics = monitor_agent_track(active_config, stream_resp)
            history_agent_evaluate(run_metrics)
        else:
            print(f"Worker Agent failed connection: {stream_resp.text}")
        time.sleep(2)
