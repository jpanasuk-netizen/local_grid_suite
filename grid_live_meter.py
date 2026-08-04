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
            target_tokens INTEGER,
            actual_tokens INTEGER,
            tokens_per_sec REAL,
            wall_time_sec REAL
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
        f"│ 🚀 LIVE GRID TELEMETRY DASHBOARD                            │\n"
        f"├─────────────────────────────────────────────────────────────┤\n"
        f"│ Progress : [{bar}] {pct}% ({current_tokens}/{target_tokens} toks) │\n"
        f"│ Speed    : {current_tps:5.2f} TPS (Avg: {avg_tps:5.2f} TPS)               │\n"
        f"│ TPS Graph: [{tps_graph}] (Max: {graph_scale_max} TPS)   │\n"
        f"└─────────────────────────────────────────────────────────────┘"
    )
    return dashboard

def run_live_metered_generation():
    init_db()
    model_name = "qwen3:8b"
    target_tokens = 200
    prompt = "Provide an exhaustive technical breakdown of hardware tensor memory architectures and high-bandwidth bus limits."

    print(f"\n[INITIATING LIVE METERED STREAM] Target Tokens: {target_tokens}")
    print("=" * 65)

    payload = {
        "model": model_name,
        "prompt": prompt,
        "stream": True,
        "options": {"temperature": 0.2, "num_predict": target_tokens, "num_gpu": -1}
    }

    start_time = time.time()
    response = requests.post(OLLAMA_URL, json=payload, stream=True)
    if response.status_code != 200:
        print(f"Error: {response.text}")
        return

    output_tokens = 0
    eval_duration = 0
    last_ui_update = time.time()
    lines_printed = 0

    print("[STREAMING TEXT & TELEMETRY METER]:\n")
    for line in response.iter_lines():
        if line:
            chunk = json.loads(line.decode("utf-8"))
            piece = chunk.get("response", "")
            print(piece, end="", flush=True)
            
            output_tokens += max(len(piece.split()), 1)

            if chunk.get("done", False):
                output_tokens = chunk.get("eval_count", output_tokens)
                eval_duration = chunk.get("eval_duration", 1)

            # Update dashboard in-place every ~0.5 seconds
            if time.time() - last_ui_update >= 0.5:
                elapsed_sub = time.time() - start_time
                sub_tps = output_tokens / elapsed_sub if elapsed_sub > 0 else 0
                dash = get_dashboard_string(output_tokens, target_tokens, sub_tps, start_time)
                
                # If we already printed the dashboard before, move cursor up to overwrite it
                if lines_printed > 0:
                    for _ in range(lines_printed):
                        print("\033[A\033[K", end="")
                
                print(dash)
                lines_printed = len(dash.split("\n"))
                last_ui_update = time.time()

    wall_time = time.time() - start_time
    final_eval_sec = eval_duration / 1_000_000_000 if eval_duration > 1 else wall_time
    final_tps = output_tokens / final_eval_sec if final_eval_sec > 0 else 0

    # Final refresh of dashboard
    if lines_printed > 0:
        for _ in range(lines_printed):
            print("\033[A\033[K", end="")
    print(get_dashboard_string(output_tokens, target_tokens, final_tps, start_time))
    
    print("=" * 65)
    print(f"✅ Generation Complete! Final Speed: {final_tps:.2f} TPS in {wall_time:.2f}s")

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO benchmark_runs (timestamp, model_name, target_tokens, actual_tokens, tokens_per_sec, wall_time_sec)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), model_name, target_tokens, output_tokens, round(final_tps, 2), round(wall_time, 2)))
    conn.commit()
    conn.close()
    print("💾 Telemetry data committed to SQLite successfully.")

if __name__ == "__main__":
    run_live_metered_generation()
