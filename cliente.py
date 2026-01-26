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


# ═══════════════════════════════════════════════════════════════════════════
# QUESTÃO 4: CONTROLE DE CONGESTIONAMENTO (TCP Reno - AIMD)
# ═══════════════════════════════════════════════════════════════════════════
# Implementa:
#   - Slow Start: crescimento exponencial (cwnd += MSS)
#   - Congestion Avoidance: crescimento linear (cwnd += MSS²/cwnd)
#   - Timeout: perda severa (ssthresh = cwnd/2, cwnd = 1*MSS)
#   - Fast Retransmit: 3 ACKs dup (ssthresh = cwnd/2, cwnd = ssthresh)
# ═══════════════════════════════════════════════════════════════════════════

class CongestionControl:
    """Controle de congestionamento baseado no TCP Reno (AIMD)."""
    
    def __init__(self):
        # Variáveis de estado
        self.cwnd = 1 * MSS          # Janela de congestionamento (1000b)
        self.ssthresh = 64000        # Slow Start Threshold (64KB)
        self.dup_ack_count = 0       # Contador de ACKs duplicados
        self.last_ack_received = 0   # Último ACK para detectar duplicatas
        self.state = "slow_start"
        
        print(f"[Q4-CONGESTION] Inicializado: cwnd={self.cwnd}b, ssthresh={self.ssthresh}b")
        print(f"[Q4-CONGESTION] Estado inicial: {self.state.upper()}")
    
    def get_phase(self):
        """Retorna fase atual: slow_start ou congestion_avoidance."""
        return "slow_start" if self.cwnd < self.ssthresh else "congestion_avoidance"
    
    def on_new_ack(self, ack_num):
        """Processa novo ACK - atualiza cwnd conforme a fase."""
        if ack_num > self.last_ack_received:
            self.dup_ack_count = 0
            self.last_ack_received = ack_num
            old_cwnd = self.cwnd
            old_phase = self.get_phase()
            
            print(f"\n  ┌─ [Q4] Processando ACK #{ack_num} ─────────────────")
            print(f"  │ Estado ANTES:")
            print(f"  │   • cwnd = {old_cwnd:.0f}b")
            print(f"  │   • ssthresh = {self.ssthresh:.0f}b")
            print(f"  │   • Fase = {old_phase.upper()}")
            
            if self.get_phase() == "slow_start":
                # Slow Start: cwnd += MSS (crescimento exponencial)
                self.cwnd += MSS
                self.state = "slow_start"
                print(f"  │")
                print(f"  │ Aplicando SLOW START:")
                print(f"  │   Equação: cwnd = cwnd + MSS")
                print(f"  │   Cálculo: {old_cwnd} + {MSS} = {self.cwnd}b")
            else:
                # Congestion Avoidance: cwnd += MSS²/cwnd (crescimento linear)
                increment = (MSS * MSS) / self.cwnd
                self.cwnd += increment
                self.state = "congestion_avoidance"
                print(f"  │")
                print(f"  │ Aplicando CONGESTION AVOIDANCE:")
                print(f"  │   Equação: cwnd = cwnd + (MSS² / cwnd)")
                print(f"  │   Cálculo: {old_cwnd:.0f} + ({MSS}² / {old_cwnd:.0f}) = {self.cwnd:.0f}b")
                print(f"  │   Incremento: +{increment:.1f}b")
            
            print(f"  │")
            print(f"  │ Estado DEPOIS:")
            print(f"  │   • cwnd = {self.cwnd:.0f}b")
            print(f"  │   • ssthresh = {self.ssthresh:.0f}b")
            print(f"  │   • Fase = {self.get_phase().upper()}")
            
            # Detecta transição de fase
            if old_phase == "slow_start" and self.get_phase() == "congestion_avoidance":
                print(f"  │")
                print(f"  │ ⚡ TRANSIÇÃO DE FASE DETECTADA!")
                print(f"  │    Slow Start → Congestion Avoidance")
                print(f"  │    Motivo: cwnd ({self.cwnd:.0f}b) >= ssthresh ({self.ssthresh}b)")
            
            print(f"  └────────────────────────────────────────────────")
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


# ═══════════════════════════════════════════════════════════════════════════
# CLASSE SENDER - INTEGRAÇÃO DE TODAS AS QUESTÕES
# ═══════════════════════════════════════════════════════════════════════════

class Sender:
    """
    Remetente com transporte confiável sobre UDP.
    
    Integra:
    - Questão 1: Números de sequência para ordenação
    - Questão 2: ACK cumulativo
    - Questão 3: Controle de fluxo via rwnd
    - Questão 4: Controle de congestionamento TCP Reno
    - Questão 5: Criptografia (XOR)
    """
    
    def __init__(self, timeout=2.0, use_encryption=False):
        # Socket UDP
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.settimeout(timeout)
        
        # ─────────── QUESTÃO 1: Números de Sequência ───────────
        self.base_seq = 100          # Primeiro byte esperado
        self.next_seq = 100          # Próximo byte a enviar
        
        # ─────────── QUESTÃO 2: ACK Cumulativo ───────────
        self.unacked_packets = {}    # Buffer de retransmissão
        
        # ─────────── QUESTÃO 3: Controle de Fluxo ───────────
        self.rwnd = BUFFER_SIZE      # Janela do receptor
        
        # ─────────── QUESTÃO 4: Controle de Congestionamento ───────────
        self.cc = CongestionControl()
        
        # ─────────── QUESTÃO 5: Criptografia ───────────
        self.security = Security()
        self.use_encryption = use_encryption
        
        print(f"\n[SENDER] ═══════════════════════════════════════════")
        print(f"[SENDER] INICIALIZAÇÃO DO CLIENTE")
        print(f"[SENDER] ═══════════════════════════════════════════")
        print(f"[SENDER] [Q1] base_seq = {self.base_seq}")
        print(f"[SENDER] [Q3] rwnd = {self.rwnd}b")
        print(f"[SENDER] [Q5] Criptografia = {'HABILITADA' if use_encryption else 'DESABILITADA'}")
        print(f"[SENDER] ═══════════════════════════════════════════\n")
    
    def bytes_in_flight(self):
        """Bytes enviados mas não confirmados."""
        return self.next_seq - self.base_seq
    
    def send_packet(self, payload, msg_num=None):
        """Envia pacote se a janela permitir."""
        
        print(f"\n{'='*70}")
        if msg_num:
            print(f"📤 ENVIANDO MENSAGEM #{msg_num}")
        else:
            print(f"📤 ENVIANDO PACOTE")
        print(f"{'='*70}")
        
        # ────── QUESTÃO 1: Número de Sequência ──────
        print(f"\n[Q1 - NUMERAÇÃO]")
        print(f"  • seq_num = {self.next_seq}")
        print(f"  • Tamanho payload = {len(payload)}b")
        print(f"  • Próximo seq será = {self.next_seq + len(payload)}")
        
        # ────── QUESTÃO 3 e 4: Controle de Fluxo + Congestionamento ──────
        bytes_in_flight = self.bytes_in_flight()
        can_send, available = self.cc.can_send(bytes_in_flight, self.rwnd)
        
        print(f"\n[Q3 - CONTROLE DE FLUXO]")
        print(f"  • rwnd (janela do servidor) = {self.rwnd}b")
        print(f"  • bytes_in_flight (não confirmados) = {bytes_in_flight}b")
        
        print(f"\n[Q4 - CONTROLE DE CONGESTIONAMENTO]")
        print(f"  • cwnd = {self.cc.cwnd:.0f}b")
        print(f"  • ssthresh = {self.cc.ssthresh:.0f}b")
        print(f"  • Fase = {self.cc.get_phase().upper()}")
        print(f"  • Janela efetiva = min(cwnd, rwnd) = min({self.cc.cwnd:.0f}, {self.rwnd}) = {min(self.cc.cwnd, self.rwnd):.0f}b")
        print(f"  • Espaço disponível = {available}b")
        
        # Verifica se pode enviar
        if not can_send:
            print(f"\n❌ BLOQUEADO: Janela cheia!")
            print(f"   Aguarde ACKs para liberar espaço...")
            return False
        
        if len(payload) > available:
            print(f"\n❌ BLOQUEADO: Payload muito grande!")
            print(f"   Necessário: {len(payload)}b, Disponível: {available}b")
            return False
        
        # ────── QUESTÃO 5: Criptografia ──────
        flags = 0
        original_payload = payload
        if self.use_encryption:
            payload = self.security.encrypt(payload)
            flags |= ENC
            print(f"\n[Q5 - CRIPTOGRAFIA]")
            print(f"  • Original: {original_payload[:30]}...")
            print(f"  • Criptografado: {payload[:30]}...")
            print(f"  • Flag ENC definida")
        
        # ────── QUESTÃO 2: Buffer de Retransmissão ──────
        pkt = Packet(seq_num=self.next_seq, ack_num=0, flags=flags, window=0, payload=payload)
        
        self.unacked_packets[self.next_seq] = {
            'packet': pkt,
            'timestamp': time.time(),
            'payload': original_payload
        }
        
        print(f"\n[Q2 - RETRANSMISSÃO]")
        print(f"  • Pacote armazenado no buffer para possível retransmissão")
        print(f"  • Total de pacotes não confirmados = {len(self.unacked_packets)}")
        
        # Envia pacote
        print(f"\n✅ ENVIANDO PARA {SERVER_IP}:{SERVER_PORT}")
        print(f"   seq={self.next_seq}, tamanho={len(original_payload)}b")
        
        self.sock.sendto(pkt.to_bytes(), (SERVER_IP, SERVER_PORT))
        self.next_seq += len(original_payload)
        
        print(f"{'='*70}\n")
        
        return True
    
    def receive_ack(self):
        """Recebe e processa ACK do servidor."""
        try:
            print(f"\n{'─'*70}")
            print(f"📥 AGUARDANDO ACK DO SERVIDOR...")
            print(f"{'─'*70}")
            
            data, addr = self.sock.recvfrom(BUFFER_SIZE)
            ack_pkt = Packet.from_bytes(data)
            
            print(f"\n✅ ACK RECEBIDO")
            print(f"  • ack_num = {ack_pkt.ack_num} (próximo byte esperado pelo servidor)")
            print(f"  • window = {ack_pkt.window}b (espaço disponível no servidor)")
            
            # ────── QUESTÃO 3: Atualiza Janela do Receptor ──────
            old_rwnd = self.rwnd
            self.rwnd = ack_pkt.window
            
            print(f"\n[Q3 - CONTROLE DE FLUXO]")
            print(f"  • rwnd atualizada: {old_rwnd}b → {self.rwnd}b")
            if self.rwnd < old_rwnd:
                print(f"  ⚠️  Buffer do servidor enchendo!")
            elif self.rwnd > old_rwnd:
                print(f"  ✓ Buffer do servidor liberando espaço")
            
            # ────── QUESTÃO 2: ACK Cumulativo ──────
            print(f"\n[Q2 - ACK CUMULATIVO]")
            if ack_pkt.ack_num > self.cc.last_ack_received:
                bytes_confirmados = ack_pkt.ack_num - self.base_seq
                print(f"  • NOVO ACK!")
                print(f"  • Confirma todos os bytes até {ack_pkt.ack_num}")
                print(f"  • Total confirmado neste ACK: {bytes_confirmados}b")
                
                # ────── QUESTÃO 4: Atualiza cwnd ──────
                self.cc.on_new_ack(ack_pkt.ack_num)
                
                # Remove pacotes confirmados
                self._remove_acked_packets(ack_pkt.ack_num)
                self.base_seq = ack_pkt.ack_num
            else:
                print(f"  • ACK DUPLICADO (já recebido)")
                print(f"  • ack_num={ack_pkt.ack_num}, last_ack={self.cc.last_ack_received}")
                
                # ACK duplicado - possível Fast Retransmit
                if self.cc.on_duplicate_ack(ack_pkt.ack_num):
                    self._fast_retransmit(ack_pkt.ack_num)
            
            print(f"{'─'*70}\n")
            
            return {'ack_num': ack_pkt.ack_num, 'window': ack_pkt.window}
            
        except socket.timeout:
            print(f"\n{'═'*70}")
            print(f"⏱️  TIMEOUT DETECTADO!")
            print(f"{'═'*70}")
            print(f"Nenhum ACK recebido no tempo esperado ({self.sock.gettimeout()}s)")
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
    
    def negotiate_encryption(self):
        """Negocia criptografia com o servidor (Questão 5)."""
        if not self.use_encryption:
            return True
        
        print(f"\n{'═'*70}")
        print(f"🔐 [Q5] NEGOCIANDO CRIPTOGRAFIA COM SERVIDOR")
        print(f"{'═'*70}")
        
        # Gera chave aleatória
        key = self.security.generate_key()
        print(f"  • Chave gerada: {key.hex()}")
        print(f"  • Tamanho: {len(key)} bytes")
        print(f"  • Algoritmo: XOR (simétrico)")
        
        # Envia handshake com a chave
        handshake_pkt = Packet(seq_num=0, ack_num=0, flags=SYN|ENC, window=0, payload=key)
        print(f"\n  → Enviando handshake (SYN|ENC)...")
        self.sock.sendto(handshake_pkt.to_bytes(), (SERVER_IP, SERVER_PORT))
        
        try:
            data, addr = self.sock.recvfrom(BUFFER_SIZE)
            ack_pkt = Packet.from_bytes(data)
            
            if ack_pkt.flags & ACK and ack_pkt.flags & ENC:
                print(f"  ← ACK recebido! Servidor aceitou criptografia")
                self.security.encryption_enabled = True
                print(f"\n✅ CRIPTOGRAFIA ESTABELECIDA")
                print(f"{'═'*70}\n")
                return True
            else:
                print(f"  ✗ Servidor rejeitou criptografia")
                return False
        except socket.timeout:
            print(f"  ✗ Timeout ao aguardar confirmação")
            return False
    
    def send_data(self, data_list):
        """Envia lista de dados com transporte confiável."""
        print("\n" + "═"*70)
        print("🚀 INICIANDO TRANSMISSÃO COM TRANSPORTE CONFIÁVEL")
        print("═"*70)
        print(f"Total de mensagens: {len(data_list)}")
        print(f"Servidor: {SERVER_IP}:{SERVER_PORT}")
        print(f"Criptografia: {'HABILITADA' if self.use_encryption else 'DESABILITADA'}")
        print("═"*70)
        
        # Negocia criptografia se habilitada
        if self.use_encryption:
            if not self.negotiate_encryption():
                print("\n❌ Falha na negociação de criptografia!")
                return
        
        idx = 0
        while idx < len(data_list):
            payload = data_list[idx].encode() if isinstance(data_list[idx], str) else data_list[idx]
            
            # Salva next_seq antes de tentar enviar
            seq_antes_envio = self.next_seq
            
            if self.send_packet(payload, msg_num=idx+1):
                result = self.receive_ack()
                if result:
                    idx += 1
                    print(f"\n✅ Mensagem {idx}/{len(data_list)} confirmada!\n")
                else:
                    # Timeout: restaura next_seq para reenviar com mesmo seq_num
                    self.next_seq = seq_antes_envio
                    print(f"\n🔄 Preparando para reenviar mensagem {idx+1} com seq={seq_antes_envio}...\n")
            else:
                print("\n⏸️  Aguardando ACKs para liberar janela...")
                result = self.receive_ack()
                if result:
                    idx += 1
                    print(f"\n✅ Mensagem {idx}/{len(data_list)} confirmada!\n")
            
            time.sleep(0.3)
        
        print("\n" + "═"*70)
        print("🎉 TRANSMISSÃO CONCLUÍDA COM SUCESSO")
        print("═"*70)
        print(f"\n📊 ESTATÍSTICAS FINAIS:")
        print(f"  [Q4] cwnd final = {self.cc.cwnd:.0f}b")
        print(f"  [Q4] ssthresh final = {self.cc.ssthresh:.0f}b")
        print(f"  [Q4] Fase final = {self.cc.get_phase().upper()}")
        print(f"  Total de mensagens enviadas = {len(data_list)}")
        print("═"*70)
    
    def close(self):
        """Fecha socket."""
        self.sock.close()


def run_client(use_encryption=False):
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
    ║  Questão 5: Criptografia (XOR)                                   ║
    ╚══════════════════════════════════════════════════════════════════╝
    """)
    
    sender = Sender(use_encryption=use_encryption)
    
    mensagens = [f"Mensagem {i+1}: Dados de teste para transmissão" for i in range(8)]
    
    try:
        sender.send_data(mensagens)
    except KeyboardInterrupt:
        print("\n[SENDER] Transmissão interrompida")
    finally:
        sender.close()


if __name__ == "__main__":
    import sys
    
    # Opção de usar criptografia via linha de comando
    use_crypto = "--crypto" in sys.argv or "-c" in sys.argv
    
    if use_crypto:
        print("\n🔐 Modo: COM CRIPTOGRAFIA\n")
    else:
        print("\n📝 Modo: SEM CRIPTOGRAFIA (use --crypto ou -c para habilitar)\n")
    
    run_client(use_encryption=use_crypto)
