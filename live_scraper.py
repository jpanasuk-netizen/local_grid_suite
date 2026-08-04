import requests
import json
import time

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "qwen3:8b"

def run_monitored_task(task_name, prompt):
    print(f"\n[GRID TASK ACTIVE] Starting: {task_name}")
    print(f"[TARGET MODEL] {MODEL_NAME}")
    print("-" * 60)

    payload = {
        "model": MODEL_NAME,
        "prompt": prompt,
        "stream": True,
        "options": {"temperature": 0.3, "num_predict": 512}
    }

    start_time = time.time()
    response = requests.post(OLLAMA_URL, json=payload, stream=True)
    
    if response.status_code != 200:
        print(f"Error connecting to local grid: {response.text}")
        return

    output_tokens = 0
    eval_duration = 0

    print("[STREAMING OUTPUT & LOGGING]")
    for line in response.iter_lines():
        if line:
            chunk = json.loads(line.decode('utf-8'))
            
            # Print the text chunk live as it's generated
            chunk_text = chunk.get("response", "")
            print(chunk_text, end="", flush=True)

            # Check if the stream has finished and collect final metrics
            if chunk.get("done", False):
                output_tokens = chunk.get("eval_count", 0)
                eval_duration = chunk.get("eval_duration", 1) # in nanoseconds

    total_time = time.time() - start_time
    
    # Calculate tokens per second using Ollama's nanosecond duration metric
    # 1 second = 1,000,000,000 nanoseconds
    actual_eval_seconds = eval_duration / 1_000_000_000
    tokens_per_sec = output_tokens / actual_eval_seconds if actual_eval_seconds > 0 else 0

    print("\n" + "-" * 60)
    print(f"[METRICS REPORT] Task: {task_name}")
    print(f"-> Total Generation Time : {total_time:.2f}s")
    print(f"-> Output Tokens Generated: {output_tokens} tokens")
    print(f"-> Throughput Speed     : {tokens_per_sec:.2f} tokens/sec")
    print("=" * 60)

if __name__ == "__main__":
    fake_long_task = (
        "Write a comprehensive technical blueprint for a distributed multi-agent "
        "local intelligence grid. Detail the subprocess sandboxing mechanism, "
        "the local SQLite telemetry log store, and the fallback error-handling loop."
    )
    run_monitored_task("Distributed Grid Architectural Blueprint Generation", fake_long_task)
