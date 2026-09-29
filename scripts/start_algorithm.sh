#!/bin/bash

set -e

PROJECT_DIR="$(cd "$(dirname "$0")/.." && pwd)"

PID_FILE="/tmp/routing_algorithm.pid"
LOG_FILE="/tmp/routing_algorithm.log"

if [ -f "$PID_FILE" ]; then

    PID=$(cat "$PID_FILE")

    if kill -0 "$PID" 2>/dev/null; then
        echo "O algoritmo já está rodando (PID $PID)."
        exit 1
    fi

    rm -f "$PID_FILE"
fi

echo "Iniciando algoritmo de roteamento..."

python3 -u "$PROJECT_DIR/algorithm/routing.py" \
    > "$LOG_FILE" 2>&1 &

PID=$!

echo "$PID" > "$PID_FILE"

echo "Algoritmo iniciado."
echo "PID: $PID"
echo "Log: $LOG_FILE"