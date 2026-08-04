from pathlib import Path
import subprocess
import requests
import json
import os

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "qwen3:8b"
WORKSPACE_DIR = str(Path(__file__).resolve().parent / "workspace")

os.makedirs(WORKSPACE_DIR, exist_ok=True)

def ask_local_ai(prompt):
    payload = {
        "model": MODEL_NAME,
        "prompt": prompt,
        "stream": False,
        "options": {"num_predict": 2048, "temperature": 0.2}
    }
    response = requests.post(OLLAMA_URL, json=payload)
    if response.status_code == 200:
        return response.json().get("response", "")
    else:
        raise Exception(f"Ollama error: {response.text}")

def clean_code_block(text):
    """Extracts raw Python code if the model wrapped it in markdown code blocks."""
    if "```python" in text:
        parts = text.split("```python")
        if len(parts) > 1:
            code = parts[1].split("```")[0]
            return code.strip()
    elif "```" in text:
        parts = text.split("```")
        if len(parts) > 1:
            code = parts[1].split("```")[0]
            return code.strip()
    return text.strip()

def run_autonomous_loop(objective, max_retries=3):
    current_prompt = f"""
    You are an elite autonomous coding agent. Your objective is: {objective}
    Write a complete, executable Python script that fulfills this objective. 
    Return ONLY valid Python code enclosed in standard markdown code blocks. No introductory chat or explanation.
    """
    
    target_file = os.path.join(WORKSPACE_DIR, "generated_task.py")

    for attempt in range(1, max_retries + 1):
        print(f"\n[Attempt {attempt}/{max_retries}] Asking local AI for code...")
        raw_response = ask_local_ai(current_prompt)
        python_code = clean_code_block(raw_response)

        with open(target_file, "w") as f:
            f.write(python_code)

        print(f"Executing code from {target_file}...")
        result = subprocess.run(["python3", target_file], capture_output=True, text=True)

        if result.returncode == 0:
            print("SUCCESS! Code executed with zero errors.")
            print("--- Output ---")
            print(result.stdout)
            return True
        else:
            print(f"Execution failed with exit code {result.returncode}.")
            print("--- Error Stack Trace ---")
            print(result.stderr)
            
            current_prompt = f"""
            The previous Python code you wrote failed with this error:
            {result.stderr}
            
            Here was the code that failed:
            {python_code}
            
            Fix the bug and return ONLY the corrected, complete Python code in markdown code blocks.
            """

    print("Max retries reached. Agent failed to self-heal.")
    return False

if __name__ == "__main__":
    test_objective = "Write a script that calculates the first 20 numbers of the Fibonacci sequence, prints them, and writes them to a file named fibonacci.txt"
    run_autonomous_loop(test_objective)
