#!/bin/bash

set -e

ROUTERS="r1 r2 r3 r4 r5"

echo "=== Iniciando FRR + RIP ==="

# Redes RIP de cada roteador
declare -A NETWORKS
NETWORKS[r1]="10.0.12.0/30 10.0.13.0/30 10.0.14.0/30"
NETWORKS[r2]="10.0.12.0/30 10.0.24.0/30"
NETWORKS[r3]="10.0.13.0/30 10.0.34.0/30 10.0.35.0/30"
NETWORKS[r4]="10.0.14.0/30 10.0.24.0/30 10.0.34.0/30 10.0.45.0/30"
NETWORKS[r5]="10.0.35.0/30 10.0.45.0/30"

for R in $ROUTERS; do

    echo "Iniciando FRR em $R..."

    # Cria os diretórios do pathspace
    sudo mkdir -p /etc/frr/$R
    sudo mkdir -p /run/frr/$R

    sudo chown -R frr:frr /etc/frr/$R
    sudo chown -R frr:frr /run/frr/$R

    # Management daemon
    sudo ip netns exec $R /usr/lib/frr/mgmtd \
        -d \
        -N $R \
        -A 127.0.0.1

    sleep 0.3

    # Zebra
    sudo ip netns exec $R /usr/lib/frr/zebra \
        -d \
        -N $R \
        -A 127.0.0.1

    sleep 0.3

    # RIP
    sudo ip netns exec $R /usr/lib/frr/ripd \
        -d \
        -N $R \
        -A 127.0.0.1

    sleep 0.3

done

echo "=== Configurando RIP ==="

for R in $ROUTERS; do

    echo "Configurando RIP em $R..."

    sudo vtysh -N $R \
        -c "configure terminal" \
        -c "hostname $R" \
        -c "router rip" \
        -c "version 2" \
        -c "end"

    for NET in ${NETWORKS[$R]}; do

        sudo vtysh -N $R \
            -c "configure terminal" \
            -c "router rip" \
            -c "network $NET" \
            -c "end"

    done

done

echo ""
echo "=== RIP configurado nos 5 roteadores ==="
echo "Aguarde alguns segundos para a convergência."