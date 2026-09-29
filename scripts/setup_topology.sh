#!/bin/bash

set -e

echo "=== Criando roteadores ==="

for router in r1 r2 r3 r4 r5; do
    ip netns add $router
    ip netns exec $router ip link set lo up
done


echo "=== Criando links ==="

# R1 <-> R2
ip link add r1-r2 type veth peer name r2-r1
ip link set r1-r2 netns r1
ip link set r2-r1 netns r2

# R1 <-> R3
ip link add r1-r3 type veth peer name r3-r1
ip link set r1-r3 netns r1
ip link set r3-r1 netns r3

# R1 <-> R4
ip link add r1-r4 type veth peer name r4-r1
ip link set r1-r4 netns r1
ip link set r4-r1 netns r4

# R2 <-> R4
ip link add r2-r4 type veth peer name r4-r2
ip link set r2-r4 netns r2
ip link set r4-r2 netns r4

# R3 <-> R4
ip link add r3-r4 type veth peer name r4-r3
ip link set r3-r4 netns r3
ip link set r4-r3 netns r4

# R3 <-> R5
ip link add r3-r5 type veth peer name r5-r3
ip link set r3-r5 netns r3
ip link set r5-r3 netns r5

# R4 <-> R5
ip link add r4-r5 type veth peer name r5-r4
ip link set r4-r5 netns r4
ip link set r5-r4 netns r5


echo "=== Configurando IPs ==="

# R1 - R2
ip netns exec r1 ip addr add 10.0.12.1/30 dev r1-r2
ip netns exec r2 ip addr add 10.0.12.2/30 dev r2-r1

# R1 - R3
ip netns exec r1 ip addr add 10.0.13.1/30 dev r1-r3
ip netns exec r3 ip addr add 10.0.13.2/30 dev r3-r1

# R1 - R4
ip netns exec r1 ip addr add 10.0.14.1/30 dev r1-r4
ip netns exec r4 ip addr add 10.0.14.2/30 dev r4-r1

# R2 - R4
ip netns exec r2 ip addr add 10.0.24.1/30 dev r2-r4
ip netns exec r4 ip addr add 10.0.24.2/30 dev r4-r2

# R3 - R4
ip netns exec r3 ip addr add 10.0.34.1/30 dev r3-r4
ip netns exec r4 ip addr add 10.0.34.2/30 dev r4-r3

# R3 - R5
ip netns exec r3 ip addr add 10.0.35.1/30 dev r3-r5
ip netns exec r5 ip addr add 10.0.35.2/30 dev r5-r3

# R4 - R5
ip netns exec r4 ip addr add 10.0.45.1/30 dev r4-r5
ip netns exec r5 ip addr add 10.0.45.2/30 dev r5-r4


echo "=== Ativando interfaces ==="

for router in r1 r2 r3 r4 r5; do
    ip netns exec $router ip link set up dev lo
done

ip netns exec r1 ip link set r1-r2 up
ip netns exec r2 ip link set r2-r1 up

ip netns exec r1 ip link set r1-r3 up
ip netns exec r3 ip link set r3-r1 up

ip netns exec r1 ip link set r1-r4 up
ip netns exec r4 ip link set r4-r1 up

ip netns exec r2 ip link set r2-r4 up
ip netns exec r4 ip link set r4-r2 up

ip netns exec r3 ip link set r3-r4 up
ip netns exec r4 ip link set r4-r3 up

ip netns exec r3 ip link set r3-r5 up
ip netns exec r5 ip link set r5-r3 up

ip netns exec r4 ip link set r4-r5 up
ip netns exec r5 ip link set r5-r4 up


echo "=== Habilitando encaminhamento IPv4 ==="

for router in r1 r2 r3 r4 r5; do
    ip netns exec $router sysctl -w net.ipv4.ip_forward=1 > /dev/null
done


echo "=== Topologia criada ==="

ip netns list