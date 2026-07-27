#!/usr/bin/env python3
import requests
import json
import time
import sqlite3
import os
import sys
import argparse
from pathlib import Path
from datetime import datetime

USER_HOME = Path.home()
DEFAULT_GRID_DIR = USER_HOME / "local_grid"
DEFAULT_DB_PATH = DEFAULT_GRID_DIR / "logs" / "grid_telemetry.db"

RAW_OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
OLLAMA_HOST = f"http://{RAW_OLLAMA_HOST}" if not RAW_OLLAMA_HOST.startswith("http") else RAW_OLLAMA_HOST

def parse_arguments():
    parser = argparse.ArgumentParser(description="Grid Benchmark CLI")
    parser.add_argument("-m", "--model", type=str, default=None, help="Target model name.")
    parser.add_argument("-t", "--tokens", type=int, default=150, help="Target output tokens.")
    parser.add_argument("-d", "--db", type=str, default=str(DEFAULT_DB_PATH), help="Custom SQLite DB path.")
    parser.add_argument("--list-models", action="store_true", help="List local models and exit.")
    return parser.parse_args()

def discovery_agent_scan(target_model=None):
    try:
        response = requests.get(f"{OLLAMA_HOST}/api/tags")
        if response.status_code != 200:
            print(f"[ERROR] Could not reach Ollama at {OLLAMA_HOST}.")
            sys.exit(1)
        models = response.json().get("models", [])
        if not models:
            print("[ERROR] No models found on Ollama server!")
            sys.exit(1)
        available_names = [m["name"] for m in models]
        if target_model:
            matches = [m for m in available_names if target_model in m]
            if not matches:
                print(f"[ERROR] Model '{target_model}' not found. Available: {available_names}")
                sys.exit(1)
            return matches[0]
        selected = available_names[0]
        for name in available_names:
            if "qwen" in name or "llama" in name:
                selected = name
                break
        return selected
    except Exception as e:
        print(f"[DISCOVERY AGENT ERROR] {e}")
        sys.exit(1)

def init_db(db_path):
    db_file = Path(db_path)
    db_file.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS hardware_runs (
            run_id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            model_name TEXT,
            target_tokens INTEGER,
            actual_tokens INTEGER,
            tokens_per_sec REAL,
            wall_time_sec REAL,
            load_ms REAL,
            prefill_tps REAL,
            decode_tps REAL
        )
    """)
    conn.commit()
    conn.close()

def main():
    args = parse_arguments()
    if args.list_models:
        resp = requests.get(f"{OLLAMA_HOST}/api/tags")
        if resp.status_code == 200:
            print("📦 Available Local Ollama Models:")
            for m in resp.json().get("models", []):
                print(f" -> {m['name']} (Size: {m.get('size', 0) / 1e9:.2f} GB)")
        return

    init_db(args.db)
    model_name = discovery_agent_scan(args.model)
    target_tokens = args.tokens
    prompt = "Explain hardware bus bottlenecks during localized tensor execution and memory constraints."

    print(f"\n[PORTABLE RUNNER] Executing telemetry suite with [{model_name}]...")
    print("=" * 65)

    payload = {
        "model": model_name,
        "prompt": prompt,
        "stream": True,
        "options": {"temperature": 0.2, "num_predict": target_tokens, "num_gpu": -1}
    }

    start_wall = time.time()
    response = requests.post(f"{OLLAMA_HOST}/api/generate", json=payload, stream=True)
    if response.status_code != 200:
        print(f"Error: {response.text}")
        return

    output_tokens = 0
    accumulated_response = []
    final_telemetry = {}

    print("[STREAMING MODEL RESPONSE]:\n")
    for line in response.iter_lines():
        if line:
            chunk = json.loads(line.decode("utf-8"))
            piece = chunk.get("response", "")
            print(piece, end="", flush=True)
            accumulated_response.append(piece)
            output_tokens += max(len(piece.split()), 1)

            if chunk.get("done", False):
                final_telemetry = chunk
                output_tokens = chunk.get("eval_count", output_tokens)

    print("\n\n" + "=" * 65)
    wall_duration = time.time() - start_wall
    load_ms = final_telemetry.get("load_duration", 0) / 1e6
    prompt_eval_count = final_telemetry.get("prompt_eval_count", 0)
    eval_count = final_telemetry.get("eval_count", output_tokens)
    prefill_tps = prompt_eval_count / (final_telemetry.get("prompt_eval_duration", 1) / 1e9)
    decode_tps = eval_count / (final_telemetry.get("eval_duration", 1) / 1e9)

    print("🔧 LOW-LEVEL SILICON & KERNEL TELEMETRY REPORT:")
    print(f"-> Total Wall Time  : {wall_duration:.2f}s | Model: {model_name}")
    print(f"-> Weight Load Time : {load_ms:.2f} ms")
    print(f"-> Prefill Speed    : {prefill_tps:.2f} tok/sec")
    print(f"-> Pure Decode TPS  : {decode_tps:.2f} tok/sec")
    print("=" * 65)

    conn = sqlite3.connect(args.db)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO hardware_runs (timestamp, model_name, target_tokens, actual_tokens, tokens_per_sec, wall_time_sec, load_ms, prefill_tps, decode_tps)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), model_name, target_tokens, eval_count, round(decode_tps, 2), round(wall_duration, 2), round(load_ms, 2), round(prefill_tps, 2), round(decode_tps, 2)))
    conn.commit()
    conn.close()
    print(f"💾 Saved telemetry run to SQLite -> [{args.db}]")

if __name__ == "__main__":
    main()
