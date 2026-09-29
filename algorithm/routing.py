import heapq
import re
import signal
import subprocess
import time

from topology import ROUTERS, LINKS


# ==========================================================
# Configuração do algoritmo
# ==========================================================

# Fórmula:
#
# custo = latência_ms + LOSS_WEIGHT * perda_% + HOP_PENALTY
#
LOSS_WEIGHT = 2
HOP_PENALTY = 5

# Quantidade de pings utilizados para medir cada direção
PING_COUNT = 5

# Timeout de cada ping
PING_TIMEOUT = 1

# Intervalo entre uma rodada de cálculo e outra
UPDATE_INTERVAL = 5

# Controla o loop principal
RUNNING = True


# ==========================================================
# Execução de comandos
# ==========================================================

def run_command(command):
    """
    Executa um comando do sistema e retorna
    o resultado do subprocess.
    """

    return subprocess.run(
        command,
        capture_output=True,
        text=True,
    )


# ==========================================================
# Medição dos enlaces
# ==========================================================

def ping(namespace, destination_ip):
    """
    Executa ping de dentro de um namespace.

    Retorna:
        (latencia_media_ms, perda_percentual)

    Se o destino estiver inacessível:
        (None, 100.0)
    """

    command = [
        "ip",
        "netns",
        "exec",
        namespace,
        "ping",
        "-c",
        str(PING_COUNT),
        "-i",
        "0.2",
        "-W",
        str(PING_TIMEOUT),
        destination_ip,
    ]

    result = run_command(command)

    output = result.stdout + result.stderr

    # ------------------------------------------------------
    # Extrair perda de pacotes
    # ------------------------------------------------------

    loss_match = re.search(
        r"([\d.]+)% packet loss",
        output
    )

    if loss_match:
        packet_loss = float(
            loss_match.group(1)
        )
    else:
        packet_loss = 100.0

    # 100% de perda = enlace indisponível
    if packet_loss >= 100:
        return None, 100.0

    # ------------------------------------------------------
    # Extrair RTT médio
    #
    # Exemplo:
    #
    # rtt min/avg/max/mdev =
    # 0.030/0.040/0.050/0.005 ms
    # ------------------------------------------------------

    latency_match = re.search(
        r"=\s*"
        r"([\d.]+)/"
        r"([\d.]+)/"
        r"([\d.]+)/"
        r"([\d.]+)\s*ms",
        output,
    )

    if not latency_match:
        return None, packet_loss

    average_latency = float(
        latency_match.group(2)
    )

    return average_latency, packet_loss


def measure_link(link):
    """
    Mede um enlace nas duas direções.

    Exemplo:

        R1 -> R4
        R4 -> R1

    Como decisão conservadora, utilizamos o pior
    resultado encontrado nas duas direções.
    """

    router_a, router_b = link["routers"]

    ip_a = link[router_a]["ip"]
    ip_b = link[router_b]["ip"]

    # A -> B
    latency_ab, loss_ab = ping(
        router_a,
        ip_b
    )

    # B -> A
    latency_ba, loss_ba = ping(
        router_b,
        ip_a
    )

    # Se qualquer direção estiver completamente
    # indisponível, consideramos o enlace indisponível.
    if latency_ab is None or latency_ba is None:

        return {
            "available": False,
            "latency": None,
            "loss": 100.0,
        }

    # Utilizamos o pior caso entre as duas direções.
    latency = max(
        latency_ab,
        latency_ba
    )

    loss = max(
        loss_ab,
        loss_ba
    )

    return {
        "available": True,
        "latency": latency,
        "loss": loss,
    }


# ==========================================================
# Métrica própria
# ==========================================================

def calculate_cost(latency, loss):
    """
    Calcula o custo de um enlace.

    Fórmula:

        custo =
            latência
            + 2 * perda
            + 5

    O valor 5 funciona como uma penalidade por enlace,
    fazendo com que caminhos com muitos saltos também
    sejam penalizados.
    """

    return (
        latency
        + LOSS_WEIGHT * loss
        + HOP_PENALTY
    )


# ==========================================================
# Construção do grafo
# ==========================================================

def build_graph():
    """
    Mede todos os enlaces e constrói um grafo
    ponderado utilizado pelo Dijkstra.
    """

    graph = {
        router: {}
        for router in ROUTERS
    }

    print("\n=== Medição dos enlaces ===\n")

    for link in LINKS:

        router_a, router_b = link["routers"]

        measurement = measure_link(link)

        if not measurement["available"]:

            print(
                f"{router_a} <-> {router_b}: "
                f"INDISPONÍVEL"
            )

            continue

        latency = measurement["latency"]
        loss = measurement["loss"]

        cost = calculate_cost(
            latency,
            loss
        )

        # Grafo bidirecional
        graph[router_a][router_b] = cost
        graph[router_b][router_a] = cost

        print(
            f"{router_a} <-> {router_b}: "
            f"latência={latency:.3f} ms | "
            f"perda={loss:.1f}% | "
            f"custo={cost:.3f}"
        )

    return graph


# ==========================================================
# Dijkstra
# ==========================================================

def dijkstra(graph, source):
    """
    Executa Dijkstra a partir de um roteador de origem.
    """

    distances = {
        router: float("inf")
        for router in graph
    }

    previous = {
        router: None
        for router in graph
    }

    distances[source] = 0

    queue = [
        (0, source)
    ]

    while queue:

        current_distance, current_router = (
            heapq.heappop(queue)
        )

        # Entrada antiga da fila
        if current_distance > distances[current_router]:
            continue

        for neighbor, link_cost in graph[current_router].items():

            new_distance = (
                current_distance
                + link_cost
            )

            if new_distance < distances[neighbor]:

                distances[neighbor] = new_distance

                previous[neighbor] = current_router

                heapq.heappush(
                    queue,
                    (
                        new_distance,
                        neighbor
                    )
                )

    return distances, previous


def get_path(previous, source, destination):
    """
    Reconstrói o caminho encontrado pelo Dijkstra.

    Exemplo:

        r1 -> r3 -> r5
    """

    path = []

    current = destination

    while current is not None:

        path.append(current)

        if current == source:
            break

        current = previous[current]

    path.reverse()

    # Não existe caminho
    if not path or path[0] != source:
        return None

    return path


# ==========================================================
# Informações da topologia
# ==========================================================

def get_direct_networks(router):
    """
    Retorna as redes diretamente conectadas
    ao roteador.

    Exemplo para R1:

        10.0.12.0/30
        10.0.13.0/30
        10.0.14.0/30
    """

    networks = set()

    for link in LINKS:

        if router in link["routers"]:
            networks.add(
                link["network"]
            )

    return networks


def get_next_hop_ip(source, next_hop):
    """
    Descobre o endereço IP do próximo roteador
    no enlace entre source e next_hop.

    Exemplo:

        source   = r1
        next_hop = r3

    Resultado:

        10.0.13.2
    """

    for link in LINKS:

        routers = link["routers"]

        if (
            source in routers
            and next_hop in routers
        ):
            return link[next_hop]["ip"]

    return None


# ==========================================================
# Cálculo das rotas
# ==========================================================

def calculate_network_routes(graph):
    """
    Calcula as rotas que precisam ser instaladas
    em cada namespace.

    Redes diretamente conectadas não precisam
    receber uma rota estática.
    """

    routes = {
        router: {}
        for router in ROUTERS
    }

    for source in ROUTERS:

        # Calcula todos os menores caminhos
        # partindo deste roteador.
        distances, previous = dijkstra(
            graph,
            source
        )

        direct_networks = get_direct_networks(
            source
        )

        # Cada link representa uma rede /30.
        for link in LINKS:

            network = link["network"]

            # Já existe uma rota proto kernel
            # para redes diretamente conectadas.
            if network in direct_networks:
                continue

            router_a, router_b = link["routers"]

            # Uma rede de trânsito possui dois
            # roteadores conectados diretamente a ela.
            #
            # Portanto podemos chegar à rede através
            # de qualquer uma das extremidades.
            candidates = []

            for destination in (
                router_a,
                router_b,
            ):

                if (
                    distances[destination]
                    == float("inf")
                ):
                    continue

                path = get_path(
                    previous,
                    source,
                    destination
                )

                if path is None:
                    continue

                candidates.append(
                    (
                        distances[destination],
                        destination,
                        path,
                    )
                )

            # Nenhuma extremidade alcançável.
            if not candidates:
                continue

            # Escolhe a extremidade da rede
            # que possui menor custo.
            cost, destination, path = min(
                candidates,
                key=lambda item: item[0]
            )

            if len(path) < 2:
                continue

            # Segundo elemento do caminho =
            # próximo roteador.
            next_hop = path[1]

            next_hop_ip = get_next_hop_ip(
                source,
                next_hop
            )

            if next_hop_ip is None:
                continue

            routes[source][network] = {
                "destination_router": destination,
                "path": path,
                "next_hop": next_hop,
                "next_hop_ip": next_hop_ip,
                "cost": cost,
            }

    return routes


# ==========================================================
# Exibição das rotas
# ==========================================================

def print_routes(routes):
    """
    Mostra as decisões tomadas pelo algoritmo.
    """

    print("\n=== Rotas escolhidas ===\n")

    for router, router_routes in routes.items():

        print(
            f"--- {router.upper()} ---"
        )

        if not router_routes:
            print("Nenhuma rota remota disponível.")

        for network, route in router_routes.items():

            path = " -> ".join(
                route["path"]
            )

            print(
                f"{network}: "
                f"{path} | "
                f"next-hop={route['next_hop']} "
                f"({route['next_hop_ip']}) | "
                f"custo={route['cost']:.3f}"
            )

        print()


# ==========================================================
# Instalação das rotas
# ==========================================================

def install_routes(routes):
    """
    Instala/atualiza as rotas calculadas
    na tabela de roteamento do Linux.

    Utilizamos:

        ip route replace

    para que uma rota existente possa ser atualizada
    quando o algoritmo escolher outro caminho.
    """

    print("\n=== Instalando rotas ===\n")

    for router, router_routes in routes.items():

        print(
            f"--- {router.upper()} ---"
        )

        for network, route in router_routes.items():

            next_hop_ip = route["next_hop_ip"]

            command = [
                "ip",
                "netns",
                "exec",
                router,
                "ip",
                "route",
                "replace",
                network,
                "via",
                next_hop_ip,
                "proto",
                "static",
            ]

            result = run_command(
                command
            )

            if result.returncode == 0:

                print(
                    f"{network} "
                    f"via {next_hop_ip} "
                    f"({route['next_hop']})"
                )

            else:

                print(
                    f"ERRO instalando "
                    f"{network} em {router}: "
                    f"{result.stderr.strip()}"
                )

        print()


# ==========================================================
# Limpeza das rotas
# ==========================================================

def remove_routes():
    """
    Remove as rotas proto static.

    As rotas diretamente conectadas são proto kernel
    e, portanto, permanecem intactas.
    """

    print(
        "\n=== Removendo rotas do algoritmo ===\n"
    )

    for router in ROUTERS:

        result = run_command([
            "ip",
            "netns",
            "exec",
            router,
            "ip",
            "-o",
            "route",
            "show",
            "proto",
            "static",
        ])

        for line in result.stdout.splitlines():

            parts = line.split()

            if not parts:
                continue

            network = parts[0]

            delete_result = run_command([
                "ip",
                "netns",
                "exec",
                router,
                "ip",
                "route",
                "del",
                network,
            ])

            if delete_result.returncode == 0:

                print(
                    f"{router}: "
                    f"{network} removida"
                )

        print(
            f"{router}: limpeza concluída"
        )


# ==========================================================
# Tratamento de encerramento
# ==========================================================

def signal_handler(sig, frame):
    """
    Chamado quando recebemos:

        Ctrl+C  -> SIGINT
        kill    -> SIGTERM
    """

    global RUNNING

    print(
        "\nEncerramento solicitado..."
    )

    RUNNING = False


# ==========================================================
# Programa principal
# ==========================================================

def main():

    global RUNNING

    # Captura Ctrl+C
    signal.signal(
        signal.SIGINT,
        signal_handler
    )

    # Captura kill -TERM
    signal.signal(
        signal.SIGTERM,
        signal_handler
    )

    print(
        "======================================="
    )

    print(
        " Algoritmo de Roteamento Multi-Métrica"
    )

    print(
        "======================================="
    )

    print(
        f"\nMétrica: "
        f"latência + "
        f"{LOSS_WEIGHT} * perda + "
        f"{HOP_PENALTY}"
    )

    print(
        f"Atualização automática: "
        f"{UPDATE_INTERVAL} segundos"
    )

    try:

        while RUNNING:

            print(
                "\n"
                "=======================================\n"
                " Nova rodada de cálculo\n"
                "======================================="
            )

            # ----------------------------------------------
            # 1. Mede os enlaces
            # ----------------------------------------------

            graph = build_graph()

            # ----------------------------------------------
            # 2. Executa Dijkstra e calcula as rotas
            # ----------------------------------------------

            routes = calculate_network_routes(
                graph
            )

            # ----------------------------------------------
            # 3. Mostra as decisões
            # ----------------------------------------------

            print_routes(
                routes
            )

            # ----------------------------------------------
            # 4. Instala/atualiza as rotas
            # ----------------------------------------------

            install_routes(
                routes
            )

            # ----------------------------------------------
            # 5. Aguarda próxima rodada
            # ----------------------------------------------

            if RUNNING:

                print(
                    f"\nPróxima atualização em "
                    f"{UPDATE_INTERVAL} segundos..."
                )

                time.sleep(
                    UPDATE_INTERVAL
                )

    finally:

        # Mesmo se houver Ctrl+C ou SIGTERM,
        # tentamos limpar as rotas.
        remove_routes()

        print(
            "\nAlgoritmo encerrado."
        )


# ==========================================================
# Entrada
# ==========================================================

if __name__ == "__main__":
    main()