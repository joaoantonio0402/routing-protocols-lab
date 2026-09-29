#!/bin/bash

echo "=== Removendo topologia ==="

for router in r1 r2 r3 r4 r5; do
    ip netns delete $router 2>/dev/null || true
done

echo "=== Topologia removida ==="