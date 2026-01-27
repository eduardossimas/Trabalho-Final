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
    
    def on_new_ack(self, ack_num, verbose=True):
        """Processa novo ACK - atualiza cwnd conforme a fase."""
        if ack_num > self.last_ack_received:
            self.dup_ack_count = 0
            self.last_ack_received = ack_num
            old_cwnd = self.cwnd
            old_phase = self.get_phase()
            
            if verbose:
                print(f"\n  ┌─ [Q4] Processando ACK #{ack_num} ─────────────────")
                print(f"  │ Estado ANTES:")
                print(f"  │   • cwnd = {old_cwnd:.0f}b")
                print(f"  │   • ssthresh = {self.ssthresh:.0f}b")
                print(f"  │   • Fase = {old_phase.upper()}")
            
            if self.get_phase() == "slow_start":
                # Slow Start: cwnd += MSS (crescimento exponencial)
                self.cwnd += MSS
                self.state = "slow_start"
                if verbose:
                    print(f"  │")
                    print(f"  │ Aplicando SLOW START:")
                    print(f"  │   Equação: cwnd = cwnd + MSS")
                    print(f"  │   Cálculo: {old_cwnd} + {MSS} = {self.cwnd}b")
            else:
                # Congestion Avoidance: cwnd += MSS²/cwnd (crescimento linear)
                increment = (MSS * MSS) / self.cwnd
                self.cwnd += increment
                self.state = "congestion_avoidance"
                if verbose:
                    print(f"  │")
                    print(f"  │ Aplicando CONGESTION AVOIDANCE:")
                    print(f"  │   Equação: cwnd = cwnd + (MSS² / cwnd)")
                    print(f"  │   Cálculo: {old_cwnd:.0f} + ({MSS}² / {old_cwnd:.0f}) = {self.cwnd:.0f}b")
                    print(f"  │   Incremento: +{increment:.1f}b")
            
            if verbose:
                print(f"  │")
                print(f"  │ Estado DEPOIS:")
                print(f"  │   • cwnd = {self.cwnd:.0f}b")
                print(f"  │   • ssthresh = {self.ssthresh:.0f}b")
                print(f"  │   • Fase = {self.get_phase().upper()}")
            
            # Detecta transição de fase
            if old_phase == "slow_start" and self.get_phase() == "congestion_avoidance":
                if verbose:
                    print(f"  │")
                    print(f"  │ ⚡ TRANSIÇÃO DE FASE DETECTADA!")
                    print(f"  │    Slow Start → Congestion Avoidance")
                    print(f"  │    Motivo: cwnd ({self.cwnd:.0f}b) >= ssthresh ({self.ssthresh}b)")
            
            if verbose:
                print(f"  └────────────────────────────────────────────────")
        else:
            self.on_duplicate_ack(ack_num, verbose)
    
    def on_duplicate_ack(self, ack_num, verbose=True):
        """Processa ACK duplicado - detecta necessidade de Fast Retransmit."""
        self.dup_ack_count += 1
        if verbose:
            print(f"[DUP ACK] ACK={ack_num} duplicado ({self.dup_ack_count}/3)")
        
        if self.dup_ack_count >= 3:
            if verbose:
                print(f"[DUP ACK] ⚠️  3 ACKs duplicados! Iniciando Fast Retransmit...")
            return True
        return False
    
    def on_triple_dup_ack(self, verbose=True):
        """Fast Recovery (TCP Reno): ssthresh = cwnd/2, cwnd = ssthresh."""
        old_cwnd = self.cwnd
        old_ssthresh = self.ssthresh
        
        # Diminuição multiplicativa
        self.ssthresh = max(self.cwnd / 2, 2 * MSS)
        self.cwnd = self.ssthresh
        self.dup_ack_count = 0
        self.state = "congestion_avoidance"
        
        if verbose:
            print(f"[FAST RECOVERY] ════════════════════════════════")
            print(f"[FAST RECOVERY] 3 ACKs Duplicados - Perda Leve Detectada")
            print(f"[FAST RECOVERY] ssthresh: {old_ssthresh}b → {self.ssthresh:.0f}b (cwnd/2)")
            print(f"[FAST RECOVERY] cwnd: {old_cwnd:.0f}b → {self.cwnd:.0f}b (= ssthresh)")
            print(f"[FAST RECOVERY] Estado: CONGESTION AVOIDANCE (pula Slow Start)")
            print(f"[FAST RECOVERY] ════════════════════════════════")
    
    def on_timeout(self, verbose=True):
        """Timeout (perda severa): ssthresh = cwnd/2, cwnd = 1*MSS."""
        old_cwnd = self.cwnd
        old_ssthresh = self.ssthresh
        
        # Diminuição multiplicativa + retorno ao Slow Start
        self.ssthresh = max(self.cwnd / 2, 2 * MSS)
        self.cwnd = 1 * MSS
        self.dup_ack_count = 0
        self.state = "slow_start"
        
        if verbose:
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
    
    def __init__(self, timeout=2.0, use_encryption=False, verbose=True):
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
        
        # ─────────── QUESTÃO 6: Modo de Execução ───────────
        self.verbose = verbose
        
        # Estatísticas para modo benchmark
        self.stats = {
            'packets_sent': 0,
            'packets_retransmitted': 0,
            'timeouts': 0,
            'fast_retransmits': 0,
            'total_bytes': 0,
            'acks_received': 0,
            'slow_start_count': 0,
            'cong_avoid_count': 0
        }
        
        if self.verbose:
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
        
        self.stats['packets_sent'] += 1
        
        if self.verbose:
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
        
        if self.verbose:
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
            if self.verbose:
                print(f"\n❌ BLOQUEADO: Janela cheia!")
                print(f"   Aguarde ACKs para liberar espaço...")
            return False
        
        if len(payload) > available:
            if self.verbose:
                print(f"\n❌ BLOQUEADO: Payload muito grande!")
                print(f"   Necessário: {len(payload)}b, Disponível: {available}b")
            return False
        
        # ────── QUESTÃO 5: Criptografia ──────
        flags = 0
        original_payload = payload
        if self.use_encryption:
            payload = self.security.encrypt(payload)
            flags |= ENC
            if self.verbose:
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
        
        if self.verbose:
            print(f"\n[Q2 - RETRANSMISSÃO]")
            print(f"  • Pacote armazenado no buffer para possível retransmissão")
            print(f"  • Total de pacotes não confirmados = {len(self.unacked_packets)}")
            
            # Envia pacote
            print(f"\n✅ ENVIANDO PARA {SERVER_IP}:{SERVER_PORT}")
            print(f"   seq={self.next_seq}, tamanho={len(original_payload)}b")
            
            print(f"{'='*70}\n")
        
        self.stats['total_bytes'] += len(original_payload)
        self.sock.sendto(pkt.to_bytes(), (SERVER_IP, SERVER_PORT))
        self.next_seq += len(original_payload)
        
        return True
    
    def receive_ack(self):
        """Recebe e processa ACK do servidor."""
        try:
            if self.verbose:
                print(f"\n{'-'*70}")
                print(f"📥 AGUARDANDO ACK DO SERVIDOR...")
                print(f"{'-'*70}")
            
            data, addr = self.sock.recvfrom(BUFFER_SIZE)
            ack_pkt = Packet.from_bytes(data)
            
            self.stats['acks_received'] += 1
            
            if self.verbose:
                print(f"\n✅ ACK RECEBIDO")
                print(f"  • ack_num = {ack_pkt.ack_num} (próximo byte esperado pelo servidor)")
                print(f"  • window = {ack_pkt.window}b (espaço disponível no servidor)")
            
            # ────── QUESTÃO 3: Atualiza Janela do Receptor ──────
            old_rwnd = self.rwnd
            self.rwnd = ack_pkt.window
            
            if self.verbose:
                print(f"\n[Q3 - CONTROLE DE FLUXO]")
                print(f"  • rwnd atualizada: {old_rwnd}b → {self.rwnd}b")
                if self.rwnd < old_rwnd:
                    print(f"  ⚠️  Buffer do servidor enchendo!")
                elif self.rwnd > old_rwnd:
                    print(f"  ✓ Buffer do servidor liberando espaço")
            
            # ────── QUESTÃO 2: ACK Cumulativo ──────
            if self.verbose:
                print(f"\n[Q2 - ACK CUMULATIVO]")
            if ack_pkt.ack_num > self.cc.last_ack_received:
                bytes_confirmados = ack_pkt.ack_num - self.base_seq
                if self.verbose:
                    print(f"  • NOVO ACK!")
                    print(f"  • Confirma todos os bytes até {ack_pkt.ack_num}")
                    print(f"  • Total confirmado neste ACK: {bytes_confirmados}b")
                
                # ────── QUESTÃO 4: Atualiza cwnd ──────
                self.cc.on_new_ack(ack_pkt.ack_num, verbose=self.verbose)
                
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
        if to_remove and self.verbose:
            print(f"[SENDER] ✓ Removidos {len(to_remove)} pacotes confirmados")
    
    def _fast_retransmit(self, ack_num):
        """Fast Retransmit após 3 ACKs duplicados."""
        self.stats['fast_retransmits'] += 1
        self.stats['packets_retransmitted'] += 1
        self.cc.on_triple_dup_ack(verbose=self.verbose)
        
        if ack_num in self.unacked_packets:
            pkt_info = self.unacked_packets[ack_num]
            if self.verbose:
                print(f"[FAST RETRANSMIT] 🔄 Retransmitindo seq={ack_num}")
            self.sock.sendto(pkt_info['packet'].to_bytes(), (SERVER_IP, SERVER_PORT))
            pkt_info['timestamp'] = time.time()
        else:
            if self.verbose:
                print(f"[FAST RETRANSMIT] ⚠️  Pacote seq={ack_num} não encontrado")
    
    def _handle_timeout(self):
        """Trata timeout com retransmissão."""
        self.stats['timeouts'] += 1
        self.stats['packets_retransmitted'] += 1
        self.cc.on_timeout(verbose=self.verbose)
        
        if self.unacked_packets:
            oldest_seq = min(self.unacked_packets.keys())
            pkt_info = self.unacked_packets[oldest_seq]
            if self.verbose:
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
        start_time = time.time()
        
        print("\n" + "═"*70)
        print("🚀 INICIANDO TRANSMISSÃO COM TRANSPORTE CONFIÁVEL")
        print("═"*70)
        print(f"Total de mensagens: {len(data_list)}")
        print(f"Servidor: {SERVER_IP}:{SERVER_PORT}")
        print(f"Criptografia: {'HABILITADA' if self.use_encryption else 'DESABILITADA'}")
        print(f"Modo: {'VERBOSE (detalhado)' if self.verbose else 'BENCHMARK (resumido)'}")
        print("═"*70)
        
        # Negocia criptografia se habilitada
        if self.use_encryption:
            if not self.negotiate_encryption():
                print("\n❌ Falha na negociação de criptografia!")
                return
        
        idx = 0
        last_progress = 0
        progress_interval = 500 if not self.verbose else 1
        
        # Stats para agregação em benchmark
        batch_start_seq = self.next_seq
        batch_losses = 0
        batch_start_idx = 0
        
        while idx < len(data_list):
            # Fase 1: Envia múltiplos pacotes (burst) respeitando a janela
            packets_sent_in_burst = 0
            while idx < len(data_list) and packets_sent_in_burst < 5:  # Máximo 5 pacotes por burst
                payload = data_list[idx].encode() if isinstance(data_list[idx], str) else data_list[idx]
                
                if self.send_packet(payload, msg_num=idx+1):
                    idx += 1
                    packets_sent_in_burst += 1
                else:
                    # Janela cheia, sai do burst
                    break
            
            # Fase 2: Recebe ACKs dos pacotes enviados
            acks_to_receive = packets_sent_in_burst if packets_sent_in_burst > 0 else 1
            for _ in range(acks_to_receive):
                if idx <= 0:  # Ainda não enviou nada
                    break
                    
                result = self.receive_ack()
                if result:
                    # Atualiza estatísticas de fase
                    if self.cc.get_phase() == "slow_start":
                        self.stats['slow_start_count'] += 1
                    else:
                        self.stats['cong_avoid_count'] += 1
                    
                    if self.verbose:
                        print(f"\n✅ Pacotes confirmados até agora: {self.stats['acks_received']}/{len(data_list)}\n")
                    elif self.stats['acks_received'] - batch_start_idx >= progress_interval:
                        # Estatísticas em modo benchmark a cada 500 pacotes
                        batch_end_seq = self.next_seq
                        acks_in_batch = self.stats['acks_received'] - batch_start_idx
                        loss_pct = (batch_losses / acks_in_batch * 100) if acks_in_batch > 0 else 0
                        print(f"Pacotes {batch_start_idx+1}-{self.stats['acks_received']}:")
                        print(f"  seq={batch_start_seq} até {batch_end_seq} | "
                              f"Perdas={batch_losses} ({loss_pct:.1f}%) | "
                              f"cwnd={self.cc.cwnd:.0f}b | fase={self.cc.get_phase()}")
                        
                        # Reset para próximo batch
                        batch_start_idx = self.stats['acks_received']
                        batch_start_seq = self.next_seq
                        batch_losses = 0
                else:
                    # Timeout: ajusta idx para reenviar
                    batch_losses += 1
                    idx = self.stats['acks_received']
                    if self.verbose:
                        print(f"\n🔄 Timeout! Voltando para pacote {idx+1}...\n")
            
            # Sleep apenas em modo verbose
            if self.verbose:
                time.sleep(0.3)
        
        # Último batch (se houver resto)
        if not self.verbose and self.stats['acks_received'] > batch_start_idx:
            batch_end_seq = self.next_seq
            acks_in_batch = self.stats['acks_received'] - batch_start_idx
            loss_pct = (batch_losses / acks_in_batch * 100) if acks_in_batch > 0 else 0
            print(f"Pacotes {batch_start_idx+1}-{self.stats['acks_received']}:")
            print(f"  seq={batch_start_seq} até {batch_end_seq} | "
                  f"Perdas={batch_losses} ({loss_pct:.1f}%) | "
                  f"cwnd={self.cc.cwnd:.0f}b | fase={self.cc.get_phase()}")
        
        end_time = time.time()
        duration = end_time - start_time
        
        print("\n" + "═"*70)
        print("🎉 TRANSMISSÃO CONCLUÍDA COM SUCESSO")
        print("═"*70)
        print(f"⏱️  TEMPO TOTAL DECORRIDO: {duration:.2f}s ({duration/60:.1f} minutos)")
        print("═"*70)
        print(f"\n📊 ESTATÍSTICAS FINAIS:")
        print(f"\n  📦 Pacotes enviados: {self.stats['packets_sent']}")
        print(f"  ✅ ACKs recebidos: {self.stats['acks_received']}")
        print(f"  🔄 Pacotes retransmitidos: {self.stats['packets_retransmitted']}")
        print(f"  📊 Taxa de retransmissão: {self.stats['packets_retransmitted']/self.stats['packets_sent']*100:.2f}%")
        print(f"  ⏱️  Timeouts: {self.stats['timeouts']}")
        print(f"  📈 Total de bytes: {self.stats['total_bytes']:,}b ({self.stats['total_bytes']/1024:.1f} KB)")
        print(f"  🚀 Throughput médio: {self.stats['total_bytes']/duration:.0f} bytes/s ({self.stats['total_bytes']/duration/1024:.1f} KB/s)")
        print(f"  📦 Taxa de envio: {len(data_list)/duration:.1f} pacotes/s")
        print(f"\n  [Q4] Controle de Congestionamento:")
        print(f"      • cwnd final = {self.cc.cwnd:.0f}b")
        print(f"      • ssthresh final = {self.cc.ssthresh:.0f}b")
        print(f"      • Fase final = {self.cc.get_phase().upper()}")
        print(f"      • ACKs em Slow Start: {self.stats['slow_start_count']}")
        print(f"      • ACKs em Congestion Avoidance: {self.stats['cong_avoid_count']}")
        print("═"*70)
    
    def close(self):
        """Fecha socket."""
        self.sock.close()


def run_client(use_encryption=False, benchmark=False):
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
    ║  Questão 6: Avaliação (10.000+ pacotes)                          ║
    ╚══════════════════════════════════════════════════════════════════╝
    """)
    
    # Timeout ajustado no modo benchmark: rápido mas permite fast retransmit
    timeout = 0.2 if benchmark else 2.0
    sender = Sender(timeout=timeout, use_encryption=use_encryption, verbose=not benchmark)
    
    # Questão 6: Modo benchmark com 10.000+ pacotes
    if benchmark:
        print("\n🔬 MODO AVALIAÇÃO (QUESTÃO 6): 10.000 pacotes")
        # Gera 10.000 pacotes com dados sintéticos de ~500 bytes cada
        mensagens = [f"Pacote {i:05d}: {'X'*450}" for i in range(10000)]
    else:
        # Modo normal com 8 mensagens para demonstração
        mensagens = [f"Mensagem {i+1}: Dados de teste para transmissão" for i in range(8)]
    
    try:
        sender.send_data(mensagens)
    except KeyboardInterrupt:
        print("\n[SENDER] Transmissão interrompida")
    finally:
        sender.close()


if __name__ == "__main__":
    import sys
    
    # Opções via linha de comando
    use_crypto = "--crypto" in sys.argv or "-c" in sys.argv
    benchmark = "--benchmark" in sys.argv or "--eval" in sys.argv or "-b" in sys.argv
    
    if benchmark:
        print("\n🔬 Modo: BENCHMARK/AVALIAÇÃO (10.000 pacotes - Questão 6)\n")
    elif use_crypto:
        print("\n🔐 Modo: COM CRIPTOGRAFIA\n")
    else:
        print("\n📝 Modo: SEM CRIPTOGRAFIA (use --crypto ou -c para habilitar)")
        print("📊 Use --benchmark ou -b para modo avaliação (10.000 pacotes)\n")
    
    run_client(use_encryption=use_crypto, benchmark=benchmark)
