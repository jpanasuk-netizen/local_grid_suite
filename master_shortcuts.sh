#!/bin/bash

GRID_DIR="$HOME/local_grid"
PID_FILE="$GRID_DIR/grid_mesh.pid"
LOG_FILE="$GRID_DIR/logs/grid_mesh.log"

show_menu() {
    echo "=================================================="
    echo "          LOCAL GRID MASTER SHORTCUTS             "
    echo "=================================================="
    echo " [Mesh Router Controls]"
    echo "  1) mesh-start    - Start virtual mesh daemon (Port 9099)"
    echo "  2) mesh-stop     - Stop virtual mesh daemon"
    echo "  3) mesh-restart  - Restart virtual mesh daemon"
    echo "  4) mesh-status   - Check virtual mesh daemon status"
    echo "  5) mesh-logs     - Tail live virtual mesh logs"
    echo ""
    echo " [Open WebUI Controls]"
    echo "  6) ui-start      - Spin up Open WebUI container (Port 3000)"
    echo "  7) ui-stop       - Stop and remove Open WebUI container"
    echo ""
    echo " [Multi-Agent Dungeon Crawler Game Pipeline]"
    echo "  8) run-dungeon   - Execute the multi-agent dungeon generation script"
    echo "  9) open-dungeon  - Open the generated HTML dungeon map in browser"
    echo ""
    echo " [Telemetry & Benchmarking]"
    echo " 10) run-benchmark - Execute the grid-benchmark profiling suite"
    echo " 11) run-report    - Generate hardware performance reports"
    echo ""
    echo " [Testing & Diagnostics]"
    echo " 12) test-api      - Send test curl payload to the mesh router"
    echo " 13) list-models   - Query active Ollama model list"
    echo " 14) status-all    - Full health check (Ollama, Mesh, WebUI)"
    echo "=================================================="
}

mesh_start() {
    if [ -f "$PID_FILE" ] && kill -0 $(cat "$PID_FILE") 2>/dev/null; then
        echo "⚠️ Mesh router is already running [PID: $(cat "$PID_FILE")]."
        return
    fi
    mkdir -p "$GRID_DIR/logs"
    python3 "$GRID_DIR/grid_mesh.py" > "$LOG_FILE" 2>&1 &
    echo $! > "$PID_FILE"
    echo "🚀 Virtual Mesh Router started in background! [PID: $(cat "$PID_FILE")]"
}

mesh_stop() {
    if [ ! -f "$PID_FILE" ]; then
        echo "⚠️ No running mesh router found (PID file missing)."
        rm -f "$PID_FILE"
        return
    fi
    PID=$(cat "$PID_FILE")
    kill "$PID" 2>/dev/null && echo "🛑 Stopped Virtual Mesh Router [PID: $PID]" || echo "⚠️ Process not found, cleaning up stale PID file."
    rm -f "$PID_FILE"
}

mesh_restart() {
    echo "🔄 Restarting Virtual Mesh Router..."
    mesh_stop
    sleep 1
    mesh_start
}

mesh_status() {
    if [ -f "$PID_FILE" ] && kill -0 $(cat "$PID_FILE") 2>/dev/null; then
        echo "🟢 Virtual Mesh Router is RUNNING [PID: $(cat "$PID_FILE")] on http://localhost:9099"
    else
        echo "🔴 Virtual Mesh Router is STOPPED."
        rm -f "$PID_FILE"
    fi
}

mesh_logs() {
    if [ -f "$LOG_FILE" ]; then
        echo "📄 Tailing live logs (Press Ctrl+C to exit)..."
        tail -f "$LOG_FILE"
    else
        echo "⚠️ No log file found at $LOG_FILE."
    fi
}

ui_start() {
    echo "🌐 Starting Open WebUI container..."
    docker run -d -p 3000:8080 \
      --add-host=host.docker.internal:host-gateway \
      -v open-webui:/app/backend/data \
      --name open-webui \
      --restart always \
      ghcr.io/open-webui/open-webui:main
    echo "✅ Open WebUI active! Access via browser at: http://localhost:3000"
}

ui_stop() {
    echo "🛑 Stopping Open WebUI container..."
    docker stop open-webui 2>/dev/null && docker rm open-webui 2>/dev/null && echo "✅ Open WebUI stopped." || echo "⚠️ Open WebUI container was not running."
}

run_dungeon() {
    if [ -f "$GRID_DIR/dungeon_pipeline.py" ]; then
        echo "🗺️ Running multi-agent dungeon crawler generation pipeline..."
        python3 "$GRID_DIR/dungeon_pipeline.py"
    elif [ -f "$GRID_DIR/dungeon.py" ]; then
        echo "🗺️ Running dungeon script..."
        python3 "$GRID_DIR/dungeon.py"
    else
        echo "⚠️ Dungeon script not found in $GRID_DIR (Check file name if custom)."
    fi
}

open_dungeon() {
    if [ -f "$GRID_DIR/dungeon.html" ]; then
        echo "🌐 Opening dungeon runtime interface in browser..."
        xdg-open "$GRID_DIR/dungeon.html" 2>/dev/null || open "$GRID_DIR/dungeon.html" 2>/dev/null
    else
        echo "⚠️ dungeon.html runtime file not found. Run dungeon generation first."
    fi
}

run_benchmark() {
    if [ -f "$GRID_DIR/grid_benchmark.py" ]; then
        echo "📊 Running grid-benchmark telemetry suite..."
        python3 "$GRID_DIR/grid_benchmark.py"
    else
        echo "⚠️ grid_benchmark.py not found in $GRID_DIR."
    fi
}

run_report() {
    if [ -f "$GRID_DIR/grid_report.py" ]; then
        echo "📈 Generating hardware telemetry report..."
        python3 "$GRID_DIR/grid_report.py"
    else
        echo "⚠️ grid_report.py not found in $GRID_DIR."
    fi
}

test_api() {
    echo "🧪 Testing virtual mesh routing endpoint (grid-coder -> Ollama)..."
    curl -s -X POST "http://localhost:9099/v1/chat/completions" \
      -H "Content-Type: application/json" \
      -d '{
        "model": "grid-coder",
        "messages": [{"role": "user", "content": "Hello mesh, confirm your status."}],
        "stream": false
      }' | jq .
}

list_models() {
    echo "📋 Fetching models currently registered in local Ollama backend:"
    curl -s http://localhost:11434/api/tags | jq .
}

status_all() {
    echo "=================================================="
    echo "             LOCAL GRID HEALTH CHECK              "
    echo "=================================================="
    if curl -s http://localhost:11434/api/tags > /dev/null; then
        echo "🟢 Ollama Daemon (Port 11434)  : ONLINE"
    else
        echo "🔴 Ollama Daemon (Port 11434)  : OFFLINE"
    fi
    
    if [ -f "$PID_FILE" ] && kill -0 $(cat "$PID_FILE") 2>/dev/null; then
        echo "🟢 Virtual Mesh (Port 9099)    : RUNNING [PID: $(cat "$PID_FILE")]"
    else
        echo "🔴 Virtual Mesh (Port 9099)    : STOPPED"
    fi
    
    if [ "$(docker inspect -f '{{.State.Running}}' open-webui 2>/dev/null)" == "true" ]; then
        echo "🟢 Open WebUI (Port 3000)      : RUNNING"
    else
        echo "🔴 Open WebUI (Port 3000)      : STOPPED"
    fi
    echo "=================================================="
}

case "$1" in
    mesh-start) mesh_start ;;
    mesh-stop) mesh_stop ;;
    mesh-restart) mesh_restart ;;
    mesh-status) mesh_status ;;
    mesh-logs) mesh_logs ;;
    ui-start) ui_start ;;
    ui-stop) ui_stop ;;
    run-dungeon) run_dungeon ;;
    open-dungeon) open_dungeon ;;
    run-benchmark) run_benchmark ;;
    run-report) run_report ;;
    test-api) test_api ;;
    list-models) list_models ;;
    status-all) status_all ;;
    *) show_menu ;;
esac
