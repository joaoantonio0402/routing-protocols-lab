#!/bin/bash

PID_FILE="/tmp/routing_algorithm.pid"

if [ ! -f "$PID_FILE" ]; then
    echo "Algoritmo não parece estar rodando."
    exit 0
fi

PID=$(cat "$PID_FILE")

if kill -0 "$PID" 2>/dev/null; then

    echo "Encerrando algoritmo (PID $PID)..."

    kill -TERM "$PID"

    # Aguarda o Python remover suas rotas
    for i in {1..10}; do

        if ! kill -0 "$PID" 2>/dev/null; then
            break
        fi

        sleep 1
    done

else

    echo "Processo $PID não existe."

fi

rm -f "$PID_FILE"

echo "Algoritmo encerrado."