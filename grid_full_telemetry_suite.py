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
    ''')
    conn.commit()
    conn.close()

def get_dashboard_string(current_tokens, target_tokens, current_tps, start_time):
    elapsed = max(time.time() - start_time, 0.001)
    avg_tps = current_tokens / elapsed
    
    pct = min(int((current_tokens / target_tokens) * 100), 100)
    bar_length = 30
    filled = int(bar_length * pct // 100)
    bar = "█" * filled + "-" * (bar_length - filled)
    
    graph_scale_max = 90.0
    graph_blocks = int(min(current_tps / graph_scale_max, 1.0) * 20)
    tps_graph = "▓" * graph_blocks + "░" * (20 - graph_blocks)

    dashboard = (
        f"┌─────────────────────────────────────────────────────────────┐\n"
        f"│ 🚀 LIVE HARDWARE TELEMETRY GRID DASHBOARD                   │\n"
        f"├─────────────────────────────────────────────────────────────┤\n"
        f"│ Progress : [{bar}] {pct}% ({current_tokens}/{target_tokens} toks) │\n"
        f"│ Speed    : {current_tps:5.2f} TPS (Avg: {avg_tps:5.2f} TPS)               │\n"
        f"│ TPS Graph: [{tps_graph}] (Max: {graph_scale_max} TPS)   │\n"
        f"└─────────────────────────────────────────────────────────────┘"
    )
    return dashboard

def run_suite():
    init_db()
    model_name = "qwen3:8b"
    target_tokens = 150
    prompt = "Provide a deep technical breakdown of hardware tensor memory architectures and high-bandwidth bus limits."

    print(f"\n[INITIATING FULL HARDWARE TELEMETRY SUITE] Target Tokens: {target_tokens}")
    print("=" * 65)

    payload = {
        "model": model_name,
        "prompt": prompt,
        "stream": True,
        "options": {"temperature": 0.2, "num_predict": target_tokens, "num_gpu": -1}
    }

    start_wall = time.time()
    response = requests.post(OLLAMA_URL, json=payload, stream=True)
    if response.status_code != 200:
        print(f"Error: {response.text}")
        return

    output_tokens = 0
    last_ui_update = time.time()
    lines_printed = 0
    final_telemetry = {}

    print("[STREAMING TEXT & HARDWARE METER]:\n")
    for line in response.iter_lines():
        if line:
            chunk = json.loads(line.decode("utf-8"))
            piece = chunk.get("response", "")
            print(piece, end="", flush=True)
            
            output_tokens += max(len(piece.split()), 1)

            if chunk.get("done", False):
                final_telemetry = chunk
                output_tokens = chunk.get("eval_count", output_tokens)

            # Update dashboard in-place every ~0.5 seconds
            if time.time() - last_ui_update >= 0.5:
                elapsed_sub = time.time() - start_wall
                sub_tps = output_tokens / elapsed_sub if elapsed_sub > 0 else 0
                dash = get_dashboard_string(output_tokens, target_tokens, sub_tps, start_wall)
                
                if lines_printed > 0:
                    for _ in range(lines_printed):
                        print("\033[A\033[K", end="")
                
                print(dash)
                lines_printed = len(dash.split("\n"))
                last_ui_update = time.time()

    wall_duration = time.time() - start_wall

    # Extract precise hardware diagnostics from Ollama closure payload
    load_ms = final_telemetry.get("load_duration", 0) / 1e6
    prompt_eval_count = final_telemetry.get("prompt_eval_count", 0)
    prompt_eval_ns = final_telemetry.get("prompt_eval_duration", 1)
    eval_count = final_telemetry.get("eval_count", output_tokens)
    eval_ns = final_telemetry.get("eval_duration", 1)

    prefill_sec = prompt_eval_ns / 1_000_000_000
    decode_sec = eval_ns / 1_000_000_000

    prefill_tps = prompt_eval_count / prefill_sec if prefill_sec > 0 else 0
    decode_tps = eval_count / decode_sec if decode_sec > 0 else 0

    # Final refresh of dashboard
    if lines_printed > 0:
        for _ in range(lines_printed):
            print("\033[A\033[K", end="")
    print(get_dashboard_string(eval_count, target_tokens, decode_tps, start_wall))
    print("=" * 65)

    # Print Detailed Hardware Engineering Report
    print("🔧 LOW-LEVEL SILICON & KERNEL TELEMETRY REPORT:")
    print(f"┌─────────────────────────────┬──────────────────────────────┐")
    print(f"│ Metric Parameter            │ Hardware Diagnostic Reading  │")
    print(f"├─────────────────────────────┼──────────────────────────────┤")
    print(f"│ Total Wall Time             │ {wall_duration:6.2f} seconds              │")
    print(f"│ Model Weight Load Time (mmap)│ {load_ms:6.2f} ms                     │")
    print(f"│ Prompt Tokens (Prefill)     │ {prompt_eval_count:6.0f} tokens               │")
    print(f"│ Attention Prefill Speed     │ {prefill_tps:6.2f} tok/sec             │")
    print(f"│ Generated Tokens (Decode)   │ {eval_count:6.0f} tokens               │")
    print(f"│ Pure VRAM Decode Speed      │ {decode_tps:6.2f} tok/sec             │")
    print(f"└─────────────────────────────┴──────────────────────────────┘")
    print("=" * 65)

    # Commit to SQLite
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO hardware_runs (timestamp, model_name, target_tokens, actual_tokens, tokens_per_sec, wall_time_sec, load_ms, prefill_tps, decode_tps)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        model_name,
        target_tokens,
        eval_count,
        round(decode_tps, 2),
        round(wall_duration, 2),
        round(load_ms, 2),
        round(prefill_tps, 2),
        round(decode_tps, 2)
    ))
    conn.commit()
    conn.close()
    print("💾 Complete hardware telemetry and metrics logged to SQLite successfully.")

if __name__ == "__main__":
    run_suite()
