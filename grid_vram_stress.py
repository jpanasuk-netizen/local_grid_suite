import requests
import json
import time

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "qwen3:8b"

def run_offload_test(mode_name, num_gpu_setting):
    print(f"\n[TEST SUITE] Running Mode: {mode_name} (num_gpu={num_gpu_setting})")
    print("-" * 65)

    prompt = "Explain how memory bus bandwidth bottlenecks inference speeds when local model weights spill over from VRAM into standard system RAM."
    
    payload = {
        "model": MODEL_NAME,
        "prompt": prompt,
        "stream": True,
        "options": {
            "temperature": 0.2,
            "num_predict": 300,
            "num_gpu": num_gpu_setting  # Controls hardware offloading level
        }
    }

    start_time = time.time()
    response = requests.post(OLLAMA_URL, json=payload, stream=True)
    
    if response.status_code != 200:
        print(f"Error: {response.text}")
        return

    output_tokens = 0
    eval_duration = 0

    for line in response.iter_lines():
        if line:
            chunk = json.loads(line.decode('utf-8'))
            print(chunk.get("response", ""), end="", flush=True)
            if chunk.get("done", False):
                output_tokens = chunk.get("eval_count", 0)
                eval_duration = chunk.get("eval_duration", 1)

    eval_seconds = eval_duration / 1_000_000_000
    tokens_per_sec = output_tokens / eval_seconds if eval_seconds > 0 else 0
    total_time = time.time() - start_time

    print("\n" + "-" * 65)
    print(f"[{mode_name} RESULTS]")
    print(f"-> Speed Achieved   : {tokens_per_sec:.2f} tokens/sec")
    print(f"-> Total Time Taken : {total_time:.2f}s for {output_tokens} tokens")
    print("=" * 65)
    return tokens_per_sec

if __name__ == "__main__":
    print("=== VRAM VS. SYSTEM RAM OFFLOAD BENCHMARK ===")
    
    # Phase 1: Full VRAM Offload (Maximum GPU acceleration)
    vram_speed = run_offload_test("Phase 1: Full VRAM (GPU Accelerated)", num_gpu=99)
    
    time.sleep(3) # Cool-down buffer
    
    # Phase 2: Forced System RAM Offload (No GPU acceleration)
    ram_speed = run_offload_test("Phase 2: Forced RAM/CPU Offload", num_gpu=0)
    
    if vram_speed and ram_speed:
        slowdown_factor = vram_speed / ram_speed
        print(f"\n📊 EXECUTIVE SUMMARY FOR LEADERSHIP:")
        print(f"-> Full VRAM speed: {vram_speed:.2f} tok/s")
        print(f"-> System RAM speed: {ram_speed:.2f} tok/s")
        print(f"-> COST OF LOW VRAM: Running on system RAM is **{slowdown_factor:.1f}x slower**!")
