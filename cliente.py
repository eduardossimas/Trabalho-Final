"""
Trabalho Final - Redes de Computadores (UFJF)
Cliente UDP com Transporte Confiável

Implementa:
- Questão 1: Números de sequência para ordenação
- Questão 2: ACK cumulativo
- Questão 3: Controle de fluxo (rwnd)
- Questão 4: Controle de congestionamento (TCP Reno)
"""

import socket
import time
from utils import *


class CongestionControl:
    """Controle de congestionamento baseado no TCP Reno (AIMD)."""
    
    def __init__(self):
        # Variáveis de estado
        self.cwnd = 1 * MSS          # Janela de congestionamento (1000b)
        self.ssthresh = 64000        # Slow Start Threshold (64KB)
        self.dup_ack_count = 0       # Contador de ACKs duplicados
        self.last_ack_received = 0   # Último ACK para detectar duplicatas
        self.state = "slow_start"
        
        print(f"[CONGESTION] Inicializado: cwnd={self.cwnd}b, ssthresh={self.ssthresh}b")
        print(f"[CONGESTION] Estado inicial: {self.state.upper()}")
    
    def get_phase(self):
        """Retorna fase atual: slow_start ou congestion_avoidance."""
        return "slow_start" if self.cwnd < self.ssthresh else "congestion_avoidance"
    
    def on_new_ack(self, ack_num):
        """Processa novo ACK - atualiza cwnd conforme a fase."""
        if ack_num > self.last_ack_received:
            self.dup_ack_count = 0
            self.last_ack_received = ack_num
            old_cwnd = self.cwnd
            
            if self.get_phase() == "slow_start":
                # Slow Start: cwnd += MSS (crescimento exponencial)
                self.cwnd += MSS
                self.state = "slow_start"
                print(f"[SLOW START] ACK={ack_num}: cwnd {old_cwnd}b → {self.cwnd}b (+{MSS}b)")
            else:
                # Congestion Avoidance: cwnd += MSS²/cwnd (crescimento linear)
                increment = (MSS * MSS) / self.cwnd
                self.cwnd += increment
                self.state = "congestion_avoidance"
                print(f"[CONG AVOID] ACK={ack_num}: cwnd {old_cwnd:.0f}b → {self.cwnd:.0f}b (+{increment:.1f}b)")
            
            # Detecta transição de fase
            if old_cwnd < self.ssthresh <= self.cwnd:
                print(f"[CONGESTION] ⚡ TRANSIÇÃO: Slow Start → Congestion Avoidance")
                print(f"[CONGESTION]    cwnd ({self.cwnd:.0f}b) >= ssthresh ({self.ssthresh}b)")
        else:
            self.on_duplicate_ack(ack_num)
    
    def on_duplicate_ack(self, ack_num):
        """Processa ACK duplicado - detecta necessidade de Fast Retransmit."""
        self.dup_ack_count += 1
        print(f"[DUP ACK] ACK={ack_num} duplicado ({self.dup_ack_count}/3)")
        
        if self.dup_ack_count >= 3:
            print(f"[DUP ACK] ⚠️  3 ACKs duplicados! Iniciando Fast Retransmit...")
            return True
        return False
    
    def on_triple_dup_ack(self):
        """Fast Recovery (TCP Reno): ssthresh = cwnd/2, cwnd = ssthresh."""
        old_cwnd = self.cwnd
        old_ssthresh = self.ssthresh
        
        # Diminuição multiplicativa
        self.ssthresh = max(self.cwnd / 2, 2 * MSS)
        self.cwnd = self.ssthresh
        self.dup_ack_count = 0
        self.state = "congestion_avoidance"
        
        print(f"[FAST RECOVERY] ═══════════════════════════════════════")
        print(f"[FAST RECOVERY] 3 ACKs Duplicados - Perda Leve Detectada")
        print(f"[FAST RECOVERY] ssthresh: {old_ssthresh}b → {self.ssthresh:.0f}b (cwnd/2)")
        print(f"[FAST RECOVERY] cwnd: {old_cwnd:.0f}b → {self.cwnd:.0f}b (= ssthresh)")
        print(f"[FAST RECOVERY] Estado: CONGESTION AVOIDANCE (pula Slow Start)")
        print(f"[FAST RECOVERY] ═══════════════════════════════════════")
    
    def on_timeout(self):
        """Timeout (perda severa): ssthresh = cwnd/2, cwnd = 1*MSS."""
        old_cwnd = self.cwnd
        old_ssthresh = self.ssthresh
        
        # Diminuição multiplicativa + retorno ao Slow Start
        self.ssthresh = max(self.cwnd / 2, 2 * MSS)
        self.cwnd = 1 * MSS
        self.dup_ack_count = 0
        self.state = "slow_start"
        
        print(f"[TIMEOUT] ═════════════════════════════════════════════")
        print(f"[TIMEOUT] ⛔ TIMEOUT - Perda Severa Detectada!")
        print(f"[TIMEOUT] ssthresh: {old_ssthresh}b → {self.ssthresh:.0f}b (cwnd/2)")
        print(f"[TIMEOUT] cwnd: {old_cwnd:.0f}b → {self.cwnd}b (= 1*MSS)")
        print(f"[TIMEOUT] Estado: SLOW START (reinício completo)")
        print(f"[TIMEOUT] ═════════════════════════════════════════════")
    
    def can_send(self, bytes_in_flight, rwnd):
        """Verifica se pode enviar: bytes_in_flight <= min(cwnd, rwnd)."""
        effective_window = min(self.cwnd, rwnd)
        available = effective_window - bytes_in_flight
        return (available > 0, int(available))
    
    def get_status(self):
        """Status atual para log."""
        return f"cwnd={self.cwnd:.0f}b | ssthresh={self.ssthresh:.0f}b | phase={self.get_phase()} | dup_acks={self.dup_ack_count}"


class Sender:
    """
    Remetente com transporte confiável sobre UDP.
    
    Integra:
    - Números de sequência (Questão 1)
    - ACK cumulativo (Questão 2)  
    - Controle de fluxo via rwnd (Questão 3)
    - Controle de congestionamento TCP Reno (Questão 4)
    """
    
    def __init__(self, timeout=2.0):
        # Socket UDP
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.settimeout(timeout)
        
        # Controle de congestionamento (Questão 4)
        self.cc = CongestionControl()
        
        # Números de sequência (Questão 1)
        self.base_seq = 100
        self.next_seq = 100
        
        # Buffer de retransmissão
        self.unacked_packets = {}
        
        # Janela do receptor (Questão 3)
        self.rwnd = BUFFER_SIZE
        
        print(f"[SENDER] Inicializado com base_seq={self.base_seq}")
    
    def bytes_in_flight(self):
        """Bytes enviados mas não confirmados."""
        return self.next_seq - self.base_seq
    
    def send_packet(self, payload):
        """Envia pacote se a janela permitir."""
        can_send, available = self.cc.can_send(self.bytes_in_flight(), self.rwnd)
        
        if not can_send:
            print(f"[SENDER] ⏸️  Janela cheia! in_flight={self.bytes_in_flight()}, cwnd={self.cc.cwnd:.0f}b, rwnd={self.rwnd}b")
            return False
        
        if len(payload) > available:
            print(f"[SENDER] ⏸️  Payload ({len(payload)}b) > disponível ({available}b)")
            return False
        
        # Cria pacote com número de sequência
        pkt = Packet(seq_num=self.next_seq, ack_num=0, flags=0, window=0, payload=payload)
        
        # Armazena para retransmissão
        self.unacked_packets[self.next_seq] = {
            'packet': pkt,
            'timestamp': time.time(),
            'payload': payload
        }
        
        print(f"[SENDER] → Enviando seq={self.next_seq}, {len(payload)}b")
        print(f"[SENDER]   {self.cc.get_status()}")
        print(f"[SENDER]   bytes_in_flight={self.bytes_in_flight()}, rwnd={self.rwnd}")
        
        self.sock.sendto(pkt.to_bytes(), (SERVER_IP, SERVER_PORT))
        self.next_seq += len(payload)
        
        return True
    
    def receive_ack(self):
        """Recebe e processa ACK do servidor."""
        try:
            data, addr = self.sock.recvfrom(BUFFER_SIZE)
            ack_pkt = Packet.from_bytes(data)
            
            # Atualiza janela do receptor (Questão 3)
            self.rwnd = ack_pkt.window
            
            print(f"[SENDER] ← Recebido ACK: ack_num={ack_pkt.ack_num}, window={ack_pkt.window}")
            
            if ack_pkt.ack_num > self.cc.last_ack_received:
                # Novo ACK - atualiza cwnd (Questão 4)
                self.cc.on_new_ack(ack_pkt.ack_num)
                
                # Remove pacotes confirmados (ACK cumulativo - Questão 2)
                self._remove_acked_packets(ack_pkt.ack_num)
                self.base_seq = ack_pkt.ack_num
            else:
                # ACK duplicado - possível Fast Retransmit
                if self.cc.on_duplicate_ack(ack_pkt.ack_num):
                    self._fast_retransmit(ack_pkt.ack_num)
            
            return {'ack_num': ack_pkt.ack_num, 'window': ack_pkt.window}
            
        except socket.timeout:
            print(f"[SENDER] ⏱️  TIMEOUT detectado!")
            self._handle_timeout()
            return None
    
    def _remove_acked_packets(self, ack_num):
        """Remove pacotes confirmados pelo ACK cumulativo."""
        to_remove = [seq for seq in self.unacked_packets if seq < ack_num]
        for seq in to_remove:
            del self.unacked_packets[seq]
        if to_remove:
            print(f"[SENDER] ✓ Removidos {len(to_remove)} pacotes confirmados")
    
    def _fast_retransmit(self, ack_num):
        """Fast Retransmit após 3 ACKs duplicados."""
        self.cc.on_triple_dup_ack()
        
        if ack_num in self.unacked_packets:
            pkt_info = self.unacked_packets[ack_num]
            print(f"[FAST RETRANSMIT] 🔄 Retransmitindo seq={ack_num}")
            self.sock.sendto(pkt_info['packet'].to_bytes(), (SERVER_IP, SERVER_PORT))
            pkt_info['timestamp'] = time.time()
        else:
            print(f"[FAST RETRANSMIT] ⚠️  Pacote seq={ack_num} não encontrado")
    
    def _handle_timeout(self):
        """Trata timeout com retransmissão."""
        self.cc.on_timeout()
        
        if self.unacked_packets:
            oldest_seq = min(self.unacked_packets.keys())
            pkt_info = self.unacked_packets[oldest_seq]
            print(f"[TIMEOUT RETRANSMIT] 🔄 Retransmitindo seq={oldest_seq}")
            self.sock.sendto(pkt_info['packet'].to_bytes(), (SERVER_IP, SERVER_PORT))
            pkt_info['timestamp'] = time.time()
    
    def send_data(self, data_list):
        """Envia lista de dados com transporte confiável."""
        print("\n" + "="*70)
        print("INICIANDO TRANSMISSÃO COM TRANSPORTE CONFIÁVEL")
        print("="*70)
        print(f"Total de mensagens: {len(data_list)}")
        print(f"Estado inicial: {self.cc.get_status()}")
        print("="*70 + "\n")
        
        idx = 0
        while idx < len(data_list):
            payload = data_list[idx].encode() if isinstance(data_list[idx], str) else data_list[idx]
            
            print(f"\n--- Mensagem {idx + 1}/{len(data_list)} ---")
            
            if self.send_packet(payload):
                result = self.receive_ack()
                if result:
                    idx += 1
            else:
                print("[SENDER] Aguardando ACKs...")
                self.receive_ack()
            
            time.sleep(0.5)
        
        print("\n" + "="*70)
        print("TRANSMISSÃO CONCLUÍDA")
        print(f"Estado final: {self.cc.get_status()}")
        print("="*70)
    
    def close(self):
        """Fecha socket."""
        self.sock.close()


def run_client():
    """Função principal do cliente."""
    print("""
    ╔══════════════════════════════════════════════════════════════════╗
    ║          TRABALHO FINAL - REDES DE COMPUTADORES (UFJF)          ║
    ║                   Cliente UDP Confiável                          ║
    ╠══════════════════════════════════════════════════════════════════╣
    ║  Questão 1: Números de sequência (ordenação)                     ║
    ║  Questão 2: ACK cumulativo                                       ║
    ║  Questão 3: Controle de fluxo (rwnd)                             ║
    ║  Questão 4: Controle de congestionamento (TCP Reno)              ║
    ╚══════════════════════════════════════════════════════════════════╝
    """)
    
    sender = Sender()
    
    mensagens = [f"Pacote {i} - Dados de teste" for i in range(10)]
    
    try:
        sender.send_data(mensagens)
    except KeyboardInterrupt:
        print("\n[SENDER] Transmissão interrompida")
    finally:
        sender.close()


if __name__ == "__main__":
    run_client()
