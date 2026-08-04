#!/bin/bash

GRID_DIR="$HOME/local_grid"
PID_FILE="$GRID_DIR/grid_mesh.pid"
LOG_FILE="$GRID_DIR/logs/grid_mesh.log"

show_help() {
    echo "=========================================="
    echo "       LOCAL GRID MESH MANAGER            "
    echo "=========================================="
    echo "Usage: ./grid_manager.sh [command]"
    echo ""
    echo "Commands:"
    echo "  mesh-start   - Start the virtual mesh router daemon"
    echo "  mesh-stop    - Stop the virtual mesh router daemon"
    echo "  mesh-status  - Check if the mesh router is running"
    echo "  mesh-logs    - Tail the live mesh router logs"
    echo "  ui-start     - Spin up Open WebUI via Docker connected to mesh"
    echo "  ui-stop      - Stop the Open WebUI container"
    echo "  status-all   - Show status of Ollama, Mesh, and WebUI"
    echo "=========================================="
}

mesh_start() {
    if [ -f "$PID_FILE" ]; then
        echo "⚠️ Mesh router is already running (PID file exists)."
        return
    fi
    mkdir -p "$GRID_DIR/logs"
    python3 "$GRID_DIR/grid_mesh.py" > "$LOG_FILE" 2>&1 &
    echo $! > "$PID_FILE"
    echo "🚀 Local Grid Mesh started in background! [PID: $(cat "$PID_FILE")]"
    echo "Logs streaming to: $LOG_FILE"
}

mesh_stop() {
    if [ ! -f "$PID_FILE" ]; then
        echo "⚠️ No running mesh router found (PID file missing)."
        return
    fi
    PID=$(cat "$PID_FILE")
    kill "$PID" 2>/dev/null && echo "🛑 Stopped Local Grid Mesh [PID: $PID]" || echo "⚠️ Process not found, cleaning up stale PID file."
    rm -f "$PID_FILE"
}

mesh_status() {
    if [ -f "$PID_FILE" ] && kill -0 $(cat "$PID_FILE") 2>/dev/null; then
        echo "🟢 Local Grid Mesh is RUNNING [PID: $(cat "$PID_FILE")] on http://localhost:9099"
    else
        echo "🔴 Local Grid Mesh is STOPPED."
        rm -f "$PID_FILE"
    fi
}

mesh_logs() {
    if [ -f "$LOG_FILE" ]; then
        tail -f "$LOG_FILE"
    else
        echo "⚠️ No log file found yet."
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
    echo "✅ Open WebUI started! Access it at: http://localhost:3000"
}

ui_stop() {
    echo "🛑 Stopping Open WebUI container..."
    docker stop open-webui && docker rm open-webui
    echo "✅ Open WebUI stopped."
}

status_all() {
    echo "--- System Status Check ---"
    # Check Ollama
    if curl -s http://localhost:11434/api/tags > /dev/null; then
        echo "🟢 Ollama Service: ONLINE (Port 11434)"
    else
        echo "🔴 Ollama Service: OFFLINE"
    fi
    
    # Check Mesh
    mesh_status
    
    # Check WebUI Docker container
    if [ "$(docker inspect -f '{{.State.Running}}' open-webui 2>/dev/null)" == "true" ]; then
        echo "🟢 Open WebUI Docker: RUNNING (Port 3000)"
    else
        echo "🔴 Open WebUI Docker: STOPPED"
    fi
    echo "--------------------------"
}

case "$1" in
    mesh-start) mesh_start ;;
    mesh-stop) mesh_stop ;;
    mesh-status) mesh_status ;;
    mesh-logs) mesh_logs ;;
    ui-start) ui_start ;;
    ui-stop) ui_stop ;;
    status-all) status_all ;;
    *) show_help ;;
esac
