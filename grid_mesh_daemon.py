import sys
import subprocess
from pathlib import Path

GRID_DIR = Path.home() / "local_grid"
PID_FILE = GRID_DIR / "grid_mesh.pid"
LOG_FILE = GRID_DIR / "logs" / "grid_mesh.log"
SCRIPT_FILE = GRID_DIR / "grid_mesh.py"

def start():
    if PID_FILE.exists():
        print("⚠️ Mesh router is already running (PID file exists).")
        return
    
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(LOG_FILE, "w") as log:
        process = subprocess.Popen(
            ["python3", str(SCRIPT_FILE)],
            stdout=log,
            stderr=log,
            start_new_session=True
        )
    PID_FILE.write_text(str(process.pid))
    print(f"🚀 Local Grid Mesh started in background! [PID: {process.pid}]")
    print(f"Logs streaming to: {LOG_FILE}")

def stop():
    if not PID_FILE.exists():
        print("⚠️ No running mesh router found (PID file missing).")
        return
    
    pid = int(PID_FILE.read_text().strip())
    try:
        subprocess.run(["kill", str(pid)], check=True)
        print(f"🛑 Stopped Local Grid Mesh [PID: {pid}]")
    except subprocess.CalledProcessError:
        print(f"⚠️ Process {pid} not found, cleaning up stale PID file.")
    finally:
        if PID_FILE.exists():
            PID_FILE.unlink()

def status():
    if not PID_FILE.exists():
        print("🔴 Local Grid Mesh is STOPPED.")
        return
    pid = int(PID_FILE.read_text().strip())
    print(f"🟢 Local Grid Mesh is RUNNING [PID: {pid}] on http://localhost:9099")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 grid_mesh_daemon.py [start|stop|status]")
        sys.exit(1)
        
    cmd = sys.argv[1].lower()
    if cmd == "start":
        start()
    elif cmd == "stop":
        stop()
    elif cmd == "status":
        status()
    else:
        print(f"Unknown command: {cmd}. Use start, stop, or status.")
