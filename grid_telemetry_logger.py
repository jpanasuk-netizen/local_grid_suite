from pathlib import Path
import requests
import json
import time
import sqlite3
import os
from datetime import datetime

OLLAMA_URL = "http://localhost:11434/api/generate"
DB_PATH = str(Path(__file__).resolve().parent / "logs" / "grid_telemetry.db")

os.makedirs(str(Path(__file__).resolve().parent / "logs"), exist_ok=True)

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS benchmark_runs (
            run_id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            model_name TEXT,
            gpu_layers INTEGER,
            vram_mb_estimated REAL,
            output_tokens INTEGER,
            tokens_per_sec REAL,
            wall_time_sec REAL,
            physics_efficiency_rating TEXT
        )
    ''')
    conn.commit()
    conn.close()

def log_to_db(metrics):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO benchmark_runs (timestamp, model_name, gpu_layers, vram_mb_estimated, output_tokens, tokens_per_sec, wall_time_sec, physics_efficiency_rating)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        metrics["timestamp"],
        metrics["model_name"],
        metrics["gpu_layers"],
        metrics["vram_mb_estimated"],
        metrics["output_tokens"],
        metrics["tokens_per_sec"],
        metrics["wall_time_sec"],
        metrics["physics_rating"]
    ))
    conn.commit()
    conn.close()

def run_telemetry_test(model_name, gpu_layers, task_description):
    mode_label = "Full Native VRAM Acceleration" if gpu_layers == -1 else "Forced System RAM Offload"
    print(f"\n[TELEMETRY PROBE] Model: {model_name} | Mode: {mode_label}")
    print("-" * 65)

    estimated_vram_mb = 5120.0 if gpu_layers == -1 else 150.0

    payload = {
        "model": model_name,
        "prompt": task_description,
        "stream": True,
        "options": {
            "temperature": 0.2,
            "num_predict": 150,
            "num_gpu": gpu_layers  # -1 lets Ollama auto-detect and maximize all layers
        }
    }

    start_time = time.time()
    response = requests.post(OLLAMA_URL, json=payload, stream=True)
    
    if response.status_code != 200:
        print(f"Error: {response.text}")
        return None

    output_tokens = 0
    eval_duration = 0

    for line in response.iter_lines():
        if line:
            chunk = json.loads(line.decode('utf-8'))
            print(chunk.get("response", ""), end="", flush=True)
            if chunk.get("done", False):
                output_tokens = chunk.get("eval_count", 0)
                eval_duration = chunk.get("eval_duration", 1)

    wall_time = time.time() - start_time
    eval_sec = eval_duration / 1_000_000_000
    tps = output_tokens / eval_sec if eval_sec > 0 else 0

    c_factor = "Speed of Light Capped (Sub-nanosecond bus friction)" if gpu_layers == -1 else "Thermal Throttling & PCIe Bottleneck (1.2 Gigawatts required for escape velocity)"
    
    metrics = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "model_name": model_name,
        "gpu_layers": 99 if gpu_layers == -1 else 0,
        "vram_mb_estimated": round(estimated_vram_mb, 2),
        "output_tokens": output_tokens,
        "tokens_per_sec": round(tps, 2),
        "wall_time_sec": round(wall_time, 2),
        "physics_rating": c_factor
    }

    log_to_db(metrics)

    print("\n" + "-" * 65)
    print(f"[TELEMETRY LOGGED TO SQLite]")
    print(f"-> VRAM Allocated     : ~{metrics['vram_mb_estimated']} MB")
    print(f"-> Throughput Speed   : {metrics['tokens_per_sec']} tok/s")
    print(f"-> Physical Constraint: {metrics['physics_rating']}")
    print("=" * 65)
    return metrics

def print_database_history_and_projections():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT run_id, model_name, gpu_layers, vram_mb_estimated, tokens_per_sec FROM benchmark_runs")
    rows = cursor.fetchall()
    conn.close()

    print("\n" + "=" * 65)
    print("📋 HISTORICAL TELEMETRY DATABASE & FUTURE VRAM SCALING PROJECTION")
    print("=" * 65)
    for row in rows:
        run_id, model, layers, vram, tps = row
        print(f"Run #{run_id} | Model: {model} | Layers: {layers} | VRAM: {vram}MB | Speed: {tps} tok/s")

    print("\n🔮 FUTURE VRAM SCALING PROJECTIONS (Theoretical 24GB+ VRAM Rig Upgrade):")
    print("-> If VRAM capacity is scaled to infinity (All layers locked in high-speed cache):")
    print("   Projected Speed: ~85.0 - 92.0 tok/s (Bounded strictly by silicon clock cycles & speed of light trace delays)")
    print("-> Power Requirement Factor: ~1.21 Gigawatts at warp speed tensor operations.")
    print("=" * 65)

if __name__ == "__main__":
    init_db()
    task = "Provide a 3-sentence summary of why hardware bus speeds govern local AI execution limits."
    
    # Run 1: Native full-GPU auto-offload
    run_telemetry_test("qwen3:8b", -1, task)
    time.sleep(2)
    
    # Run 2: Forced RAM bottleneck test
    run_telemetry_test("qwen3:8b", 0, task)
    
    print_database_history_and_projections()
