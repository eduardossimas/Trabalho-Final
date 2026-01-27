# Trabalho Final - Redes de Computadores (UFJF)

## Descrição

Implementação de **Transporte Confiável sobre UDP** com controle de congestionamento TCP Reno.

### Funcionalidades Implementadas

#### ✅ Questão 1: Números de Sequência
- Ordenação correta de pacotes recebidos
- Buffer de reordenação no servidor
- Entrega em ordem para a aplicação

#### ✅ Questão 2: ACK Cumulativo
- Confirmação acumulativa de bytes recebidos
- Buffer de retransmissão no cliente
- Detecção e descarte de duplicatas

#### ✅ Questão 3: Controle de Fluxo (rwnd)
- Janela do receptor anunciada nos ACKs
- Cliente respeita janela disponível do servidor
- Previne overflow do buffer

#### ✅ Questão 4: Controle de Congestionamento (TCP Reno - AIMD)
- **Slow Start**: crescimento exponencial (cwnd += MSS)
- **Congestion Avoidance**: crescimento linear (cwnd += MSS²/cwnd)
- **Timeout**: perda severa → ssthresh = cwnd/2, cwnd = 1×MSS
- **Fast Retransmit**: 3 ACKs duplicados → ssthresh = cwnd/2, cwnd = ssthresh

#### ✅ Questão 5: Criptografia (XOR)
- Handshake para negociação de chave
- Criptografia simétrica do payload
- Suporte opcional via flag `--crypto`

#### ✅ Questão 6: Avaliação com 10.000+ Pacotes
- Modo benchmark otimizado
- Estatísticas completas de desempenho
- Logs resumidos para análise

---

## Como Executar

#### 1️⃣ Iniciar o Servidor

Em um terminal:

```bash
python3 servidor.py
```

**Servidor em modo benchmark** (logs resumidos):
```bash
python3 servidor.py --benchmark
# ou
python3 servidor.py -b
```

#### 2️⃣ Executar o Cliente

Em outro terminal, escolha uma das opções abaixo:

---

### 🎯 Modos de Execução do Cliente

#### **Modo Normal** (8 mensagens - demonstração)
```bash
python3 cliente.py
```
- Envia 8 pacotes de teste
- Logs detalhados de cada operação
- Ideal para visualizar o funcionamento

---

#### **Modo Benchmark** (10.000 pacotes - avaliação)
```bash
python3 cliente.py --benchmark
# ou
python3 cliente.py -b
```
- Envia 10.000 pacotes (~500 bytes cada)
- Logs resumidos (a cada 500 pacotes)
- Estatísticas completas ao final
- **Tempo**: ~1-3 minutos
- **Timeout otimizado**: 0.2s

---

#### **Com Criptografia** (XOR simétrico)
```bash
python3 cliente.py --crypto
# ou
python3 cliente.py -c
```
- Negocia chave de criptografia com servidor
- Payload criptografado com XOR
- Flag `ENC` ativada nos pacotes

---

#### **Benchmark + Criptografia**
```bash
python3 cliente.py --benchmark --crypto
# ou
python3 cliente.py -b -c
```
- Combina avaliação de desempenho com criptografia
- 10.000 pacotes criptografados

---

## 📊 Exemplo de Estatísticas

Ao final da transmissão, o cliente exibe:

```
⏱️  TEMPO TOTAL DECORRIDO: 120.45s (2.0 minutos)
══════════════════════════════════════════════════════════════════════

📊 ESTATÍSTICAS FINAIS:

  📦 Pacotes enviados: 10530
  ✅ ACKs recebidos: 10000
  🔄 Pacotes retransmitidos: 530
  📊 Taxa de retransmissão: 5.03%
  ⏱️  Timeouts: 530
  📈 Total de bytes: 4,658,560b (4549.4 KB)
  🚀 Throughput médio: 38,690 bytes/s (37.8 KB/s)
  📦 Taxa de envio: 83.0 pacotes/s

  [Q4] Controle de Congestionamento:
      • cwnd final = 7443b
      • ssthresh final = 4185b
      • Fase final = CONGESTION_AVOIDANCE
      • ACKs em Slow Start: 821
      • ACKs em Congestion Avoidance: 8940
```

---

## 📁 Estrutura do Projeto

```
.
├── cliente.py          # Cliente UDP com controle de congestionamento
├── servidor.py         # Servidor UDP com ordenação e controle de fluxo
├── utils.py            # Classes auxiliares (Packet, Security)
├── testes.py           # Testes unitários das questões
└── README.md           # Este arquivo
```

---

## 🔧 Parâmetros de Configuração

### Em `utils.py`:

```python
SERVER_IP = '127.0.0.1'
SERVER_PORT = 5005
BUFFER_SIZE = 1024       # Tamanho do buffer do servidor
MSS = 1000               # Maximum Segment Size
```

### Simulação de Perda (servidor.py):

```python
LOSS_PROBABILITY = 0.05  # 5% de perda de pacotes
```

---

## 🧪 Executar Testes Unitários

```bash
python3 testes.py
```

Menu interativo com testes para cada questão:
1. Questão 1 - Entrega ordenada de pacotes
2. Questão 2 - Confirmação acumulativa (ACK)
3. Questão 3 - Controle de fluxo
4. Questão 4 - Controle de congestionamento (TCP Reno)

---

## 📝 Observações Importantes

1. **Ordem de Execução**: Sempre inicie o **servidor antes** do cliente
2. **Portas**: Certifique-se de que a porta 5005 esteja disponível
3. **Localhost**: Cliente e servidor rodam na mesma máquina (127.0.0.1)
4. **Perda de Pacotes**: Servidor simula 5% de perda aleatória para testar retransmissões
5. **Timeout no Benchmark**: Reduzido para 0.2s para acelerar execução
6. **Envio em Rajadas**: Cliente envia até 5 pacotes por vez para melhor desempenho

---

## 🎓 Autores

Trabalho Final da disciplina de Redes de Computadores - UFJF

---

## 📄 Licença

Este projeto é para fins educacionais.
