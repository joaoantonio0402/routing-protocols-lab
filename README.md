# Trabalho GA - Simulação de Roteamento em Redes Linux

Este projeto simula uma topologia de roteadores em namespaces Linux e implementa um algoritmo de roteamento dinâmico baseado em medição ativa de enlaces. A ideia principal é comparar o comportamento de uma solução customizada com protocolos clássicos como RIP e OSPF em uma rede virtual.

## Objetivo

O ambiente foi montado para:

- criar cinco roteadores em namespaces (`r1` a `r5`);
- conectar esses roteadores em uma topologia com múltiplos caminhos;
- medir latência e perda de pacotes em cada enlace;
- calcular rotas usando um algoritmo próprio baseado em Dijkstra;
- instalar essas rotas na tabela de roteamento do Linux;
- permitir a comparação com configuração de RIP e OSPF usando FRR.

## Topologia

A rede é composta por cinco roteadores interconectados com as redes:

- `10.0.12.0/30` — `r1` <-> `r2`
- `10.0.13.0/30` — `r1` <-> `r3`
- `10.0.14.0/30` — `r1` <-> `r4`
- `10.0.24.0/30` — `r2` <-> `r4`
- `10.0.34.0/30` — `r3` <-> `r4`
- `10.0.35.0/30` — `r3` <-> `r5`
- `10.0.45.0/30` — `r4` <-> `r5`

A estrutura está descrita em `algorithm/topology.py`.

## Estrutura do projeto

```text
.
├── README.md
├── algorithm/
│   ├── routing.py
│   └── topology.py
├── configs/
│   └── rip/
│       ├── r1.conf
│       ├── r2.conf
│       ├── r3.conf
│       ├── r4.conf
│       └── r5.conf
├── scripts/
│   ├── setup_topology.sh
│   ├── destroy_topology.sh
│   ├── start_algorithm.sh
│   ├── stop_algorithm.sh
│   ├── start_rip.sh
│   ├── stop_rip.sh
│   ├── start_ospf.sh
│   └── stop_ospf.sh
└── trabalho_ga.pdf
```

## Como o algoritmo funciona

O script `algorithm/routing.py` executa um loop contínuo que:

1. mede cada enlace usando `ping` em ambos os sentidos;
2. calcula uma métrica de custo por enlace:

   custo = latência + 2 × perda + 5

3. monta um grafo ponderado;
4. aplica Dijkstra para descobrir os caminhos mínimos;
5. instala as rotas via `ip route replace` dentro de cada namespace.

Assim, o roteador escolhe o melhor caminho com base em desempenho real da conexão, e não apenas em contagem de saltos.

## Pré-requisitos

Para executar o projeto, o sistema deve ter:

- Linux com suporte a namespaces de rede (`ip netns`);
- privilégios de root ou `sudo`;
- pacote `iproute2`;
- FRR instalado para executar RIP e OSPF;
- Python 3.

## Fluxo de uso

### 1) Criar a topologia

```bash
sudo ./scripts/setup_topology.sh
```

Esse comando cria os namespaces `r1` a `r5`, os links virtuais e atribui os IPs da topologia.

### 2) Iniciar o algoritmo customizado

```bash
./scripts/start_algorithm.sh
```

O script inicia o Python em segundo plano e grava o log em `/tmp/routing_algorithm.log`.

### 3) Iniciar RIP ou OSPF

Para RIP:

```bash
./scripts/start_rip.sh
```

Para OSPF:

```bash
./scripts/start_ospf.sh
```

### 4) Verificar as rotas

Exemplo:

```bash
sudo ip netns exec r1 ip route show
```

Você pode observar as rotas instaladas pelo algoritmo customizado, pelo RIP ou pelo OSPF.

### 5) Encerrar

Para parar o algoritmo customizado:

```bash
./scripts/stop_algorithm.sh
```

Para parar RIP:

```bash
./scripts/stop_rip.sh
```

Para parar OSPF:

```bash
./scripts/stop_ospf.sh
```

Para remover a topologia inteira:

```bash
sudo ./scripts/destroy_topology.sh
```

## Arquivos principais

- `algorithm/topology.py`: descrição da topologia e dos pontos de conexão.
- `algorithm/routing.py`: medição de links, cálculo da métrica, Dijkstra e instalação das rotas.
- `scripts/setup_topology.sh`: criação da rede virtual.
- `scripts/start_algorithm.sh`: inicialização do algoritmo de roteamento.
- `scripts/start_rip.sh`: ativação do daemon RIP via FRR.
- `scripts/start_ospf.sh`: ativação do daemon OSPF via FRR.

## Observações

- O projeto foi pensado para laboratório e simulação em ambiente Linux, não para produção.
- O algoritmo customizado atualiza as rotas automaticamente em intervalos definidos em `routing.py`.
- Os scripts usam `ip netns` e `FRR`, então a execução precisa ocorrer em um ambiente com suporte adequado.

## Licença

Este projeto foi desenvolvido para fins acadêmicos e de estudo em redes de computadores.
