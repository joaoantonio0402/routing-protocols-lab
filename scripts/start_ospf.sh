#!/bin/bash

set -e

ROUTERS="r1 r2 r3 r4 r5"

declare -A ROUTER_ID
ROUTER_ID[r1]="1.1.1.1"
ROUTER_ID[r2]="2.2.2.2"
ROUTER_ID[r3]="3.3.3.3"
ROUTER_ID[r4]="4.4.4.4"
ROUTER_ID[r5]="5.5.5.5"

declare -A NETWORKS
NETWORKS[r1]="10.0.12.0/30 10.0.13.0/30 10.0.14.0/30"
NETWORKS[r2]="10.0.12.0/30 10.0.24.0/30"
NETWORKS[r3]="10.0.13.0/30 10.0.34.0/30 10.0.35.0/30"
NETWORKS[r4]="10.0.14.0/30 10.0.24.0/30 10.0.34.0/30 10.0.45.0/30"
NETWORKS[r5]="10.0.35.0/30 10.0.45.0/30"

echo "=== Iniciando FRR + OSPF ==="

for R in $ROUTERS; do

    echo "Iniciando FRR em $R..."

    sudo mkdir -p /etc/frr/$R
    sudo mkdir -p /run/frr/$R

    sudo chown -R frr:frr /etc/frr/$R
    sudo chown -R frr:frr /run/frr/$R

    sudo ip netns exec $R /usr/lib/frr/mgmtd \
        -d -N $R -A 127.0.0.1

    sleep 0.3

    sudo ip netns exec $R /usr/lib/frr/zebra \
        -d -N $R -A 127.0.0.1

    sleep 0.3

    sudo ip netns exec $R /usr/lib/frr/ospfd \
        -d -N $R -A 127.0.0.1

    sleep 0.3

done

echo "=== Configurando OSPF ==="

for R in $ROUTERS; do

    echo "Configurando OSPF em $R..."

    sudo vtysh -N $R \
        -c "configure terminal" \
        -c "hostname $R" \
        -c "router ospf" \
        -c "ospf router-id ${ROUTER_ID[$R]}" \
        -c "end"

    for NET in ${NETWORKS[$R]}; do

        sudo vtysh -N $R \
            -c "configure terminal" \
            -c "router ospf" \
            -c "network $NET area 0" \
            -c "end"

    done

done

echo ""
echo "=== OSPF configurado nos 5 roteadores ==="
echo "Aguarde alguns segundos para a formação das adjacências."