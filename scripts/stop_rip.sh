#!/bin/bash

ROUTERS="r1 r2 r3 r4 r5"

echo "=== Parando RIP/FRR ==="

for R in $ROUTERS; do

    echo "Parando $R..."

    if [ -f /run/frr/$R/ripd.pid ]; then
        sudo kill $(cat /run/frr/$R/ripd.pid) 2>/dev/null || true
    fi

    if [ -f /run/frr/$R/zebra.pid ]; then
        sudo kill $(cat /run/frr/$R/zebra.pid) 2>/dev/null || true
    fi

    if [ -f /run/frr/$R/mgmtd.pid ]; then
        sudo kill $(cat /run/frr/$R/mgmtd.pid) 2>/dev/null || true
    fi

done

echo "=== FRR parado ==="