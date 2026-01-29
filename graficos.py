"""
Gerador de Gráficos - Trabalho Final Redes de Computadores (UFJF)

Gera gráficos comparando:
- Vazão da rede com e sem perdas
- Vazão com e sem controle de congestionamento

Uso:
    python3 graficos.py                    # Executa todos os testes e gera gráficos
    python3 graficos.py --no-loss          # Teste sem perda de pacotes
    python3 graficos.py --loss             # Teste com perda de pacotes (5%)
    python3 graficos.py --no-congestion    # Sem controle de congestionamento
    python3 graficos.py --congestion       # Com controle de congestionamento
    python3 graficos.py --simulacao        # Modo simulação (sem servidor real)
"""

import time
import random
import socket
import matplotlib.pyplot as plt
import numpy as np
from dataclasses import dataclass, field
from typing import List, Dict, Tuple
from utils import MSS, BUFFER_SIZE


# ═══════════════════════════════════════════════════════════════════════════
# CONFIGURAÇÕES DE SIMULAÇÃO
# ═══════════════════════════════════════════════════════════════════════════

@dataclass
class SimulationConfig:
    """Configurações para a simulação."""
    num_packets: int = 1000               # Número de pacotes a enviar
    packet_size: int = 500                # Tamanho de cada pacote (bytes)
    loss_probability: float = 0.0         # Probabilidade de perda (0.0 a 1.0)
    use_congestion_control: bool = True   # Se usa controle de congestionamento
    rtt_base: float = 0.0002              # RTT base em segundos (0.2ms - mais rápido)
    rtt_variance: float = 0.0001          # Variância do RTT
    initial_cwnd: int = MSS               # Janela inicial
    ssthresh: int = 64000                 # Slow Start Threshold
    rwnd: int = BUFFER_SIZE               # Janela do receptor


@dataclass
class SimulationResult:
    """Resultados de uma simulação."""
    config_name: str = ""
    total_time: float = 0.0
    total_bytes: int = 0
    packets_sent: int = 0
    packets_lost: int = 0
    retransmissions: int = 0
    throughput_bps: float = 0.0           # bytes/segundo
    throughput_kbps: float = 0.0          # KB/segundo
    cwnd_history: List[float] = field(default_factory=list)
    throughput_history: List[float] = field(default_factory=list)
    time_history: List[float] = field(default_factory=list)
    phase_history: List[str] = field(default_factory=list)


# ═══════════════════════════════════════════════════════════════════════════
# SIMULADOR DE CONTROLE DE CONGESTIONAMENTO
# ═══════════════════════════════════════════════════════════════════════════

class CongestionControlSimulator:
    """Simulador do controle de congestionamento TCP Reno."""
    
    def __init__(self, config: SimulationConfig):
        self.config = config
        self.cwnd = config.initial_cwnd if config.use_congestion_control else float('inf')
        self.ssthresh = config.ssthresh
        self.dup_ack_count = 0
        self.bytes_sent = 0
        self.bytes_acked = 0
        self.packets_lost = 0
        self.retransmissions = 0
        
    def get_phase(self) -> str:
        """Retorna fase atual."""
        if not self.config.use_congestion_control:
            return "no_control"
        return "slow_start" if self.cwnd < self.ssthresh else "congestion_avoidance"
    
    def on_ack(self) -> None:
        """Processa ACK recebido."""
        if not self.config.use_congestion_control:
            return
            
        if self.get_phase() == "slow_start":
            # Slow Start: cwnd += MSS
            self.cwnd += MSS
        else:
            # Congestion Avoidance: cwnd += MSS²/cwnd
            self.cwnd += (MSS * MSS) / self.cwnd
    
    def on_loss(self) -> None:
        """Processa perda de pacote (timeout ou 3 dup ACKs)."""
        if not self.config.use_congestion_control:
            return
            
        # TCP Reno: ssthresh = cwnd/2, cwnd = 1*MSS
        self.ssthresh = max(self.cwnd / 2, 2 * MSS)
        self.cwnd = MSS
        self.packets_lost += 1
        self.retransmissions += 1
    
    def get_effective_window(self) -> float:
        """Retorna janela efetiva: min(cwnd, rwnd)."""
        if not self.config.use_congestion_control:
            return self.config.rwnd
        return min(self.cwnd, self.config.rwnd)


# ═══════════════════════════════════════════════════════════════════════════
# FUNÇÃO DE SIMULAÇÃO
# ═══════════════════════════════════════════════════════════════════════════

def run_simulation(config: SimulationConfig, name: str = "") -> SimulationResult:
    """Executa uma simulação com a configuração dada."""
    
    result = SimulationResult(config_name=name)
    cc = CongestionControlSimulator(config)
    
    start_time = time.time()
    packets_acked = 0
    packets_attempted = 0
    
    # Histórico para gráficos
    sample_interval = max(1, config.num_packets // 100)  # 100 pontos no gráfico
    last_progress = -1
    
    print(f"\n{'─'*60}")
    print(f"🔬 Simulação: {name}")
    print(f"{'─'*60}")
    print(f"  • Pacotes: {config.num_packets}")
    print(f"  • Tamanho: {config.packet_size}b cada")
    print(f"  • Perda: {config.loss_probability*100:.1f}%")
    print(f"  • Controle de Congestionamento: {'SIM' if config.use_congestion_control else 'NÃO'}")
    print(f"{'─'*60}")
    
    # Limite de tentativas para evitar loop infinito
    max_attempts = config.num_packets * 3
    
    while packets_acked < config.num_packets and packets_attempted < max_attempts:
        packets_attempted += 1
        
        # Calcula quantos pacotes podem ser enviados (janela)
        effective_window = cc.get_effective_window()
        
        # Envia pacote
        result.packets_sent += 1
        
        # Simula RTT variável (reduzido para não demorar)
        rtt = config.rtt_base + random.uniform(-config.rtt_variance, config.rtt_variance)
        time.sleep(rtt)
        
        # Simula perda de pacote
        if random.random() < config.loss_probability:
            cc.on_loss()
            result.retransmissions += 1
        else:
            # ACK recebido com sucesso
            cc.on_ack()
            cc.bytes_acked += config.packet_size
            packets_acked += 1
            result.total_bytes += config.packet_size
        
        # Registra histórico para gráficos
        if packets_acked % sample_interval == 0 or packets_acked == config.num_packets:
            elapsed = time.time() - start_time
            if elapsed > 0:
                instantaneous_throughput = result.total_bytes / elapsed / 1024  # KB/s
            else:
                instantaneous_throughput = 0
                
            result.cwnd_history.append(cc.cwnd if config.use_congestion_control else config.rwnd)
            result.throughput_history.append(instantaneous_throughput)
            result.time_history.append(elapsed)
            result.phase_history.append(cc.get_phase())
        
        # Progresso (a cada 10%)
        current_progress = int((packets_acked / config.num_packets) * 10)
        if current_progress > last_progress and packets_acked > 0:
            last_progress = current_progress
            progress = (packets_acked / config.num_packets) * 100
            print(f"  Progresso: {progress:.0f}% ({packets_acked}/{config.num_packets}) | "
                  f"cwnd={cc.cwnd:.0f}b | fase={cc.get_phase()}")
    
    # Calcula resultados finais
    result.total_time = time.time() - start_time
    result.packets_lost = cc.packets_lost
    result.throughput_bps = result.total_bytes / result.total_time if result.total_time > 0 else 0
    result.throughput_kbps = result.throughput_bps / 1024
    
    print(f"\n  ✅ Concluído em {result.total_time:.2f}s")
    print(f"  📊 Throughput: {result.throughput_kbps:.2f} KB/s")
    print(f"  🔄 Retransmissões: {result.retransmissions}")
    print(f"{'─'*60}\n")
    
    return result


# ═══════════════════════════════════════════════════════════════════════════
# FUNÇÕES DE GERAÇÃO DE GRÁFICOS
# ═══════════════════════════════════════════════════════════════════════════

def plot_throughput_comparison(results: List[SimulationResult], title: str, filename: str):
    """Gera gráfico de barras comparando throughput."""
    
    plt.figure(figsize=(12, 6))
    
    names = [r.config_name for r in results]
    throughputs = [r.throughput_kbps for r in results]
    colors = ['#2ecc71', '#e74c3c', '#3498db', '#9b59b6']
    
    bars = plt.bar(names, throughputs, color=colors[:len(results)], edgecolor='black', linewidth=1.2)
    
    # Adiciona valores nas barras
    for bar, value in zip(bars, throughputs):
        plt.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.5, 
                 f'{value:.2f}\nKB/s', ha='center', va='bottom', fontsize=10, fontweight='bold')
    
    plt.xlabel('Configuração', fontsize=12)
    plt.ylabel('Throughput (KB/s)', fontsize=12)
    plt.title(title, fontsize=14, fontweight='bold')
    plt.grid(axis='y', alpha=0.3)
    plt.tight_layout()
    plt.savefig(filename, dpi=150, bbox_inches='tight')
    plt.close()
    
    print(f"  📈 Gráfico salvo: {filename}")


def plot_cwnd_evolution(results: List[SimulationResult], title: str, filename: str):
    """Gera gráfico da evolução da janela de congestionamento."""
    
    plt.figure(figsize=(14, 6))
    
    colors = ['#2ecc71', '#e74c3c', '#3498db', '#9b59b6']
    
    for i, result in enumerate(results):
        if result.cwnd_history:
            # Normaliza o eixo X para porcentagem de progresso
            x = np.linspace(0, 100, len(result.cwnd_history))
            y = [c / 1024 for c in result.cwnd_history]  # Converte para KB
            plt.plot(x, y, label=result.config_name, color=colors[i % len(colors)], 
                     linewidth=2, marker='o', markersize=2)
    
    plt.xlabel('Progresso da Transmissão (%)', fontsize=12)
    plt.ylabel('Janela de Congestionamento (KB)', fontsize=12)
    plt.title(title, fontsize=14, fontweight='bold')
    plt.legend(loc='best', fontsize=10)
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(filename, dpi=150, bbox_inches='tight')
    plt.close()
    
    print(f"  📈 Gráfico salvo: {filename}")


def plot_throughput_over_time(results: List[SimulationResult], title: str, filename: str):
    """Gera gráfico de throughput ao longo do tempo."""
    
    plt.figure(figsize=(14, 6))
    
    colors = ['#2ecc71', '#e74c3c', '#3498db', '#9b59b6']
    
    for i, result in enumerate(results):
        if result.throughput_history:
            x = np.linspace(0, 100, len(result.throughput_history))
            plt.plot(x, result.throughput_history, label=result.config_name, 
                     color=colors[i % len(colors)], linewidth=2)
    
    plt.xlabel('Progresso da Transmissão (%)', fontsize=12)
    plt.ylabel('Throughput Instantâneo (KB/s)', fontsize=12)
    plt.title(title, fontsize=14, fontweight='bold')
    plt.legend(loc='best', fontsize=10)
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(filename, dpi=150, bbox_inches='tight')
    plt.close()
    
    print(f"  📈 Gráfico salvo: {filename}")


def plot_loss_impact(results: List[SimulationResult], filename: str):
    """Gera gráfico mostrando impacto das perdas."""
    
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))
    
    # Gráfico 1: Throughput vs Perda
    names = [r.config_name for r in results]
    throughputs = [r.throughput_kbps for r in results]
    retransmissions = [r.retransmissions for r in results]
    
    colors = ['#2ecc71', '#e74c3c', '#3498db', '#9b59b6']
    
    ax1 = axes[0]
    bars = ax1.bar(names, throughputs, color=colors[:len(results)], edgecolor='black', linewidth=1.2)
    ax1.set_xlabel('Configuração', fontsize=11)
    ax1.set_ylabel('Throughput (KB/s)', fontsize=11)
    ax1.set_title('Throughput por Configuração', fontsize=12, fontweight='bold')
    ax1.grid(axis='y', alpha=0.3)
    
    for bar, value in zip(bars, throughputs):
        ax1.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.2, 
                 f'{value:.1f}', ha='center', va='bottom', fontsize=9)
    
    # Gráfico 2: Retransmissões
    ax2 = axes[1]
    bars2 = ax2.bar(names, retransmissions, color=['#e67e22', '#c0392b', '#2980b9', '#8e44ad'][:len(results)], 
                    edgecolor='black', linewidth=1.2)
    ax2.set_xlabel('Configuração', fontsize=11)
    ax2.set_ylabel('Retransmissões', fontsize=11)
    ax2.set_title('Número de Retransmissões', fontsize=12, fontweight='bold')
    ax2.grid(axis='y', alpha=0.3)
    
    for bar, value in zip(bars2, retransmissions):
        ax2.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.5, 
                 f'{value}', ha='center', va='bottom', fontsize=9)
    
    plt.tight_layout()
    plt.savefig(filename, dpi=150, bbox_inches='tight')
    plt.close()
    
    print(f"  📈 Gráfico salvo: {filename}")


def plot_combined_analysis(results: List[SimulationResult], filename: str):
    """Gera gráfico combinado com múltiplas métricas."""
    
    fig, axes = plt.subplots(2, 2, figsize=(15, 10))
    colors = ['#2ecc71', '#e74c3c', '#3498db', '#9b59b6']
    
    # 1. Throughput Comparison
    ax1 = axes[0, 0]
    names = [r.config_name for r in results]
    throughputs = [r.throughput_kbps for r in results]
    bars = ax1.bar(names, throughputs, color=colors[:len(results)], edgecolor='black')
    ax1.set_ylabel('Throughput (KB/s)', fontsize=10)
    ax1.set_title('Comparação de Throughput', fontsize=11, fontweight='bold')
    ax1.grid(axis='y', alpha=0.3)
    ax1.tick_params(axis='x', rotation=15)
    
    # 2. Evolução do cwnd
    ax2 = axes[0, 1]
    for i, result in enumerate(results):
        if result.cwnd_history:
            x = np.linspace(0, 100, len(result.cwnd_history))
            y = [c / 1024 for c in result.cwnd_history]
            ax2.plot(x, y, label=result.config_name.split('\n')[0], 
                     color=colors[i % len(colors)], linewidth=2)
    ax2.set_xlabel('Progresso (%)', fontsize=10)
    ax2.set_ylabel('cwnd (KB)', fontsize=10)
    ax2.set_title('Evolução da Janela de Congestionamento', fontsize=11, fontweight='bold')
    ax2.legend(fontsize=8)
    ax2.grid(True, alpha=0.3)
    
    # 3. Throughput ao longo do tempo
    ax3 = axes[1, 0]
    for i, result in enumerate(results):
        if result.throughput_history:
            x = np.linspace(0, 100, len(result.throughput_history))
            ax3.plot(x, result.throughput_history, label=result.config_name.split('\n')[0],
                     color=colors[i % len(colors)], linewidth=2)
    ax3.set_xlabel('Progresso (%)', fontsize=10)
    ax3.set_ylabel('Throughput (KB/s)', fontsize=10)
    ax3.set_title('Throughput ao Longo da Transmissão', fontsize=11, fontweight='bold')
    ax3.legend(fontsize=8)
    ax3.grid(True, alpha=0.3)
    
    # 4. Métricas resumidas
    ax4 = axes[1, 1]
    ax4.axis('off')
    
    # Tabela de resumo
    table_data = []
    headers = ['Configuração', 'Throughput\n(KB/s)', 'Retrans.', 'Tempo\n(s)']
    
    for r in results:
        short_name = r.config_name.replace('\n', ' ')[:20]
        table_data.append([
            short_name,
            f'{r.throughput_kbps:.2f}',
            f'{r.retransmissions}',
            f'{r.total_time:.2f}'
        ])
    
    table = ax4.table(cellText=table_data, colLabels=headers,
                       loc='center', cellLoc='center',
                       colColours=['#3498db']*4)
    table.auto_set_font_size(False)
    table.set_fontsize(9)
    table.scale(1.2, 1.5)
    ax4.set_title('Resumo das Simulações', fontsize=11, fontweight='bold', pad=20)
    
    plt.tight_layout()
    plt.savefig(filename, dpi=150, bbox_inches='tight')
    plt.close()
    
    print(f"  📈 Gráfico salvo: {filename}")


# ═══════════════════════════════════════════════════════════════════════════
# CENÁRIOS DE TESTE
# ═══════════════════════════════════════════════════════════════════════════

def run_loss_comparison(num_packets: int = 500) -> List[SimulationResult]:
    """Compara cenários com e sem perda de pacotes."""
    
    print("\n" + "═"*70)
    print("📊 COMPARAÇÃO: COM PERDA vs SEM PERDA")
    print("═"*70)
    
    results = []
    
    # Cenário 1: Sem perda
    config1 = SimulationConfig(
        num_packets=num_packets,
        loss_probability=0.0,
        use_congestion_control=True
    )
    results.append(run_simulation(config1, "Sem Perda\n(0%)"))
    
    # Cenário 2: Com 5% de perda
    config2 = SimulationConfig(
        num_packets=num_packets,
        loss_probability=0.05,
        use_congestion_control=True
    )
    results.append(run_simulation(config2, "Com Perda\n(5%)"))
    
    # Cenário 3: Com 10% de perda
    config3 = SimulationConfig(
        num_packets=num_packets,
        loss_probability=0.10,
        use_congestion_control=True
    )
    results.append(run_simulation(config3, "Com Perda\n(10%)"))
    
    return results


def run_congestion_control_comparison(num_packets: int = 500) -> List[SimulationResult]:
    """Compara cenários com e sem controle de congestionamento."""
    
    print("\n" + "═"*70)
    print("📊 COMPARAÇÃO: COM vs SEM CONTROLE DE CONGESTIONAMENTO")
    print("═"*70)
    
    results = []
    
    # Cenário 1: Com controle de congestionamento, sem perda
    config1 = SimulationConfig(
        num_packets=num_packets,
        loss_probability=0.0,
        use_congestion_control=True
    )
    results.append(run_simulation(config1, "Com Controle\nSem Perda"))
    
    # Cenário 2: Sem controle de congestionamento, sem perda
    config2 = SimulationConfig(
        num_packets=num_packets,
        loss_probability=0.0,
        use_congestion_control=False
    )
    results.append(run_simulation(config2, "Sem Controle\nSem Perda"))
    
    # Cenário 3: Com controle de congestionamento, com perda
    config3 = SimulationConfig(
        num_packets=num_packets,
        loss_probability=0.05,
        use_congestion_control=True
    )
    results.append(run_simulation(config3, "Com Controle\nCom Perda (5%)"))
    
    # Cenário 4: Sem controle de congestionamento, com perda
    config4 = SimulationConfig(
        num_packets=num_packets,
        loss_probability=0.05,
        use_congestion_control=False
    )
    results.append(run_simulation(config4, "Sem Controle\nCom Perda (5%)"))
    
    return results


def run_all_scenarios(num_packets: int = 500):
    """Executa todos os cenários e gera todos os gráficos."""
    
    print("\n" + "═"*70)
    print("🚀 INICIANDO ANÁLISE COMPLETA DO PROTOCOLO")
    print("═"*70)
    print(f"\nParâmetros:")
    print(f"  • Pacotes por cenário: {num_packets}")
    print(f"  • Tamanho do pacote: 500 bytes")
    print(f"  • MSS: {MSS} bytes")
    print(f"  • Buffer: {BUFFER_SIZE} bytes")
    print("═"*70)
    
    all_results = []
    
    # Teste 1: Comparação de perda
    print("\n\n" + "▓"*70)
    print("▓ TESTE 1: IMPACTO DA PERDA DE PACOTES")
    print("▓"*70)
    loss_results = run_loss_comparison(num_packets)
    all_results.extend(loss_results)
    
    print("\n📊 Gerando gráficos de perda...")
    plot_throughput_comparison(loss_results, 
                               'Impacto da Perda de Pacotes no Throughput',
                               'grafico_perda_throughput.png')
    plot_cwnd_evolution(loss_results,
                        'Evolução do cwnd com Diferentes Taxas de Perda',
                        'grafico_perda_cwnd.png')
    plot_throughput_over_time(loss_results,
                              'Throughput ao Longo do Tempo (Diferentes Perdas)',
                              'grafico_perda_tempo.png')
    
    # Teste 2: Comparação de controle de congestionamento
    print("\n\n" + "▓"*70)
    print("▓ TESTE 2: IMPACTO DO CONTROLE DE CONGESTIONAMENTO")
    print("▓"*70)
    cc_results = run_congestion_control_comparison(num_packets)
    
    print("\n📊 Gerando gráficos de controle de congestionamento...")
    plot_throughput_comparison(cc_results,
                               'Comparação: Com vs Sem Controle de Congestionamento',
                               'grafico_congestionamento_throughput.png')
    plot_cwnd_evolution(cc_results,
                        'Evolução do cwnd: Com vs Sem Controle',
                        'grafico_congestionamento_cwnd.png')
    plot_loss_impact(cc_results, 'grafico_congestionamento_impacto.png')
    
    # Gráfico combinado final
    print("\n\n📊 Gerando gráfico de análise combinada...")
    plot_combined_analysis(cc_results, 'grafico_analise_completa.png')
    
    # Resumo final
    print("\n\n" + "═"*70)
    print("✅ ANÁLISE CONCLUÍDA COM SUCESSO!")
    print("═"*70)
    print("\n📁 Arquivos gerados:")
    print("  • grafico_perda_throughput.png")
    print("  • grafico_perda_cwnd.png")
    print("  • grafico_perda_tempo.png")
    print("  • grafico_congestionamento_throughput.png")
    print("  • grafico_congestionamento_cwnd.png")
    print("  • grafico_congestionamento_impacto.png")
    print("  • grafico_analise_completa.png")
    print("\n" + "═"*70)
    
    return loss_results, cc_results


def run_single_test(loss: bool = False, congestion_control: bool = True, num_packets: int = 500):
    """Executa um único teste com configurações específicas."""
    
    loss_prob = 0.05 if loss else 0.0
    
    print("\n" + "═"*70)
    print("🔬 TESTE INDIVIDUAL")
    print("═"*70)
    
    config = SimulationConfig(
        num_packets=num_packets,
        loss_probability=loss_prob,
        use_congestion_control=congestion_control
    )
    
    name = f"{'Com' if congestion_control else 'Sem'} Controle\n{'Com' if loss else 'Sem'} Perda"
    result = run_simulation(config, name)
    
    # Gera gráfico individual
    print("\n📊 Gerando gráfico...")
    suffix = f"{'loss' if loss else 'noloss'}_{'cc' if congestion_control else 'nocc'}"
    
    plt.figure(figsize=(12, 5))
    
    # Subplot 1: cwnd
    plt.subplot(1, 2, 1)
    if result.cwnd_history:
        x = np.linspace(0, 100, len(result.cwnd_history))
        y = [c / 1024 for c in result.cwnd_history]
        plt.plot(x, y, color='#3498db', linewidth=2)
    plt.xlabel('Progresso (%)')
    plt.ylabel('cwnd (KB)')
    plt.title('Evolução da Janela de Congestionamento')
    plt.grid(True, alpha=0.3)
    
    # Subplot 2: Throughput
    plt.subplot(1, 2, 2)
    if result.throughput_history:
        x = np.linspace(0, 100, len(result.throughput_history))
        plt.plot(x, result.throughput_history, color='#2ecc71', linewidth=2)
    plt.xlabel('Progresso (%)')
    plt.ylabel('Throughput (KB/s)')
    plt.title('Throughput ao Longo do Tempo')
    plt.grid(True, alpha=0.3)
    
    plt.suptitle(f"Teste: {name.replace(chr(10), ' ')}", fontsize=12, fontweight='bold')
    plt.tight_layout()
    plt.savefig(f'grafico_teste_{suffix}.png', dpi=150, bbox_inches='tight')
    plt.close()
    
    print(f"  📈 Gráfico salvo: grafico_teste_{suffix}.png")
    
    return result


# ═══════════════════════════════════════════════════════════════════════════
# MENU INTERATIVO
# ═══════════════════════════════════════════════════════════════════════════

def menu_interativo():
    """Menu interativo para escolher o tipo de teste."""
    
    print("""
    ╔══════════════════════════════════════════════════════════════════╗
    ║     GERADOR DE GRÁFICOS - TRABALHO FINAL REDES (UFJF)           ║
    ╠══════════════════════════════════════════════════════════════════╣
    ║  Compara vazão da rede em diferentes cenários:                  ║
    ║  • Com e sem perda de pacotes                                    ║
    ║  • Com e sem controle de congestionamento                        ║
    ╚══════════════════════════════════════════════════════════════════╝
    """)
    
    while True:
        print("\n" + "─"*50)
        print("MENU DE OPÇÕES")
        print("─"*50)
        print("1. Executar análise completa (todos os cenários)")
        print("2. Comparar: Com perda vs Sem perda")
        print("3. Comparar: Com controle vs Sem controle de congestionamento")
        print("4. Teste individual customizado")
        print("5. Configurar número de pacotes")
        print("0. Sair")
        print("─"*50)
        
        try:
            num_packets = 500  # Padrão
            
            escolha = input("\nEscolha uma opção: ").strip()
            
            if escolha == "1":
                n = input("Número de pacotes por cenário (padrão 500): ").strip()
                num_packets = int(n) if n else 500
                run_all_scenarios(num_packets)
                
            elif escolha == "2":
                n = input("Número de pacotes por cenário (padrão 500): ").strip()
                num_packets = int(n) if n else 500
                results = run_loss_comparison(num_packets)
                print("\n📊 Gerando gráficos...")
                plot_throughput_comparison(results, 
                                           'Impacto da Perda de Pacotes',
                                           'grafico_perda_throughput.png')
                plot_cwnd_evolution(results,
                                    'Evolução do cwnd',
                                    'grafico_perda_cwnd.png')
                
            elif escolha == "3":
                n = input("Número de pacotes por cenário (padrão 500): ").strip()
                num_packets = int(n) if n else 500
                results = run_congestion_control_comparison(num_packets)
                print("\n📊 Gerando gráficos...")
                plot_throughput_comparison(results,
                                           'Com vs Sem Controle de Congestionamento',
                                           'grafico_congestionamento.png')
                plot_loss_impact(results, 'grafico_impacto.png')
                
            elif escolha == "4":
                print("\n🔧 CONFIGURAÇÃO DO TESTE INDIVIDUAL")
                
                loss_input = input("Simular perda de pacotes? (s/n, padrão: n): ").strip().lower()
                loss = loss_input == 's'
                
                cc_input = input("Usar controle de congestionamento? (s/n, padrão: s): ").strip().lower()
                cc = cc_input != 'n'
                
                n = input("Número de pacotes (padrão 500): ").strip()
                num_packets = int(n) if n else 500
                
                run_single_test(loss=loss, congestion_control=cc, num_packets=num_packets)
                
            elif escolha == "5":
                n = input("Digite o número de pacotes para os testes: ").strip()
                num_packets = int(n) if n else 500
                print(f"✓ Número de pacotes definido: {num_packets}")
                
            elif escolha == "0":
                print("\n👋 Encerrando...")
                break
                
            else:
                print("❌ Opção inválida!")
                
        except ValueError as e:
            print(f"❌ Erro de entrada: {e}")
        except KeyboardInterrupt:
            print("\n\n👋 Interrompido pelo usuário.")
            break
        
        input("\n[Pressione ENTER para continuar]")


# ═══════════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    import sys
    
    # Verifica argumentos de linha de comando
    args = sys.argv[1:]
    
    if not args:
        # Menu interativo
        menu_interativo()
    else:
        # Modo linha de comando
        num_packets = 500
        loss = False
        congestion = True
        all_tests = False
        
        for arg in args:
            if arg in ['--all', '-a']:
                all_tests = True
            elif arg in ['--loss', '-l']:
                loss = True
            elif arg in ['--no-loss', '-nl']:
                loss = False
            elif arg in ['--congestion', '-c']:
                congestion = True
            elif arg in ['--no-congestion', '-nc']:
                congestion = False
            elif arg.startswith('--packets='):
                num_packets = int(arg.split('=')[1])
            elif arg.startswith('-n'):
                num_packets = int(arg[2:])
            elif arg in ['--help', '-h']:
                print(__doc__)
                sys.exit(0)
        
        if all_tests:
            run_all_scenarios(num_packets)
        else:
            run_single_test(loss=loss, congestion_control=congestion, num_packets=num_packets)
