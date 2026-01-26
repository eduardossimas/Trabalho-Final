"""
Servidor UDP com Transporte Confiável

Implementa:
- Questão 1: Ordenação de pacotes por seq_num
- Questão 2: ACK cumulativo
- Questão 3: Controle de fluxo (rwnd)
- Questão 4: Interage com controle de congestionamento do cliente
- Questão 5: Descriptografia
"""

import socket
import random
from utils import *

def run_server():
    print("""
    ╔══════════════════════════════════════════════════════════════════╗
    ║          TRABALHO FINAL - REDES DE COMPUTADORES (UFJF)          ║
    ║                   Servidor UDP Confiável                         ║
    ╠══════════════════════════════════════════════════════════════════╣
    ║  Questão 1: Ordenação por número de sequência                   ║
    ║  Questão 2: ACK cumulativo                                       ║
    ║  Questão 3: Controle de fluxo (rwnd)                             ║
    ║  Questão 4: Suporte a controle de congestionamento              ║
    ║  Questão 5: Descriptografia (XOR)                                ║
    ╚══════════════════════════════════════════════════════════════════╝
    """)
    
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((SERVER_IP, SERVER_PORT))
    
    # ────── QUESTÃO 1: Buffer de Reordenação ──────
    expected_seq = 100  # Próximo byte esperado
    recv_buffer = {}    # Pacotes fora de ordem {seq_num: payload}
    
    # ────── QUESTÃO 5: Criptografia ──────
    security = Security()
    encryption_negotiated = False
    
    LOSS_PROBABILITY = 0.05  # 5% de perda para simulação
    packet_count = 0

    print(f"\n{'═'*70}")
    print(f"🚀 SERVIDOR INICIADO")
    print(f"{'═'*70}")
    print(f"  • Endereço: {SERVER_IP}:{SERVER_PORT}")
    print(f"  • Buffer: {BUFFER_SIZE}b")
    print(f"  • Esperando seq_num inicial: {expected_seq}")
    print(f"  • Simulação de perda: {LOSS_PROBABILITY*100}%")
    print(f"{'═'*70}\n")
    print("⏳ Aguardando conexões...\n")
    
    while True:
        try:
            data, addr = sock.recvfrom(BUFFER_SIZE)
            packet_count += 1
            
            print(f"\n{'='*70}")
            print(f"📥 PACOTE RECEBIDO #{packet_count}")
            print(f"{'='*70}")
            print(f"  De: {addr}")
            print(f"  Tamanho bruto: {len(data)}b")
            
            # ────── SIMULAÇÃO DE PERDA ──────
            if random.random() < LOSS_PROBABILITY:
                print(f"\n❌ PACOTE PERDIDO (simulação {LOSS_PROBABILITY*100}%)")
                print(f"   Cliente detectará via timeout ou ACK duplicado")
                print(f"{'='*70}\n")
                continue

            pkt = Packet.from_bytes(data)
            
            print(f"\n📦 PACOTE DECODIFICADO:")
            print(f"  • seq_num = {pkt.seq_num}")
            print(f"  • ack_num = {pkt.ack_num}")
            print(f"  • flags = {bin(pkt.flags)} {_format_flags(pkt.flags)}")
            print(f"  • window = {pkt.window}b")
            print(f"  • payload = {len(pkt.payload)}b")
            
            # ────── QUESTÃO 5: HANDSHAKE DE CRIPTOGRAFIA ──────
            if pkt.flags & SYN and pkt.flags & ENC:
                print(f"\n{'─'*70}")
                print(f"🔐 [Q5] HANDSHAKE DE CRIPTOGRAFIA")
                print(f"{'─'*70}")
                
                key = pkt.payload
                security.set_key(key)
                encryption_negotiated = True
                
                print(f"  • Chave recebida: {key.hex()}")
                print(f"  • Tamanho: {len(key)} bytes")
                print(f"  • Algoritmo: XOR (simétrico)")
                print(f"  ✅ Criptografia habilitada")
                
                # Envia ACK confirmando
                ack_pkt = Packet(seq_num=0, ack_num=0, flags=ACK|ENC, window=BUFFER_SIZE)
                sock.sendto(ack_pkt.to_bytes(), addr)
                print(f"  → ACK enviado confirmando criptografia")
                print(f"{'─'*70}\n")
                continue
            
            # ────── QUESTÃO 5: DESCRIPTOGRAFIA ──────
            if pkt.flags & ENC and encryption_negotiated:
                print(f"\n{'─'*70}")
                print(f"🔓 [Q5] DESCRIPTOGRAFANDO PAYLOAD")
                print(f"{'─'*70}")
                
                encrypted = pkt.payload[:40] if len(pkt.payload) >= 40 else pkt.payload
                pkt.payload = security.decrypt(pkt.payload)
                
                print(f"  • Criptografado: {encrypted}...")
                print(f"  • Descriptografado: {pkt.payload[:40]}...")
                print(f"  ✅ Descriptografia concluída")
                print(f"{'─'*70}\n")
            
            # ────── QUESTÃO 1: ORDENAÇÃO POR SEQ_NUM ──────
            print(f"{'─'*70}")
            print(f"[Q1] ORDENAÇÃO POR NÚMERO DE SEQUÊNCIA")
            print(f"{'─'*70}")
            print(f"  • Esperado: seq={expected_seq}")
            print(f"  • Recebido: seq={pkt.seq_num}")
            print(f"  • Payload: {len(pkt.payload)}b")
            
            # Caso 1: Pacote na ordem correta
            if pkt.seq_num == expected_seq:
                print(f"  ✅ ORDEM CORRETA!")
                print(f"     Entregando para aplicação...")
                
                # "Entrega" para aplicação (aqui apenas mostramos)
                payload_preview = pkt.payload[:50] if len(pkt.payload) >= 50 else pkt.payload
                print(f"     Dados: {payload_preview}")
                
                # Avança esperado
                expected_seq += len(pkt.payload)
                print(f"     Próximo esperado: seq={expected_seq}")
                
                # Caso 2: Verifica se há pacotes no buffer que agora podem ser processados
                delivered_count = 0
                while expected_seq in recv_buffer:
                    print(f"\n  ➡️  Recuperando do buffer: seq={expected_seq}")
                    buffered_payload = recv_buffer.pop(expected_seq)
                    expected_seq += len(buffered_payload)
                    delivered_count += 1
                    print(f"     Próximo esperado: seq={expected_seq}")
                
                if delivered_count > 0:
                    print(f"  📦 {delivered_count} pacote(s) entregue(s) do buffer")
                    
            # Caso 3: Pacote fora de ordem (futuro) -> Armazena no buffer
            elif pkt.seq_num > expected_seq:
                print(f"  ⚠️  FORA DE ORDEM (adiantado)")
                print(f"     Guardando no buffer...")
                recv_buffer[pkt.seq_num] = pkt.payload
                gap = pkt.seq_num - expected_seq
                print(f"     Faltam {gap}b até este pacote")
                print(f"     Buffer agora tem {len(recv_buffer)} pacote(s)")
                
            # Caso 4: Pacote duplicado ou atrasado
            else:
                print(f"  🔁 DUPLICADO/ATRASADO (descartando)")
                print(f"     Este seq_num já foi processado")
            
            print(f"{'─'*70}\n")

            # ────── QUESTÃO 3: CONTROLE DE FLUXO ──────
            print(f"{'─'*70}")
            print(f"[Q3] CONTROLE DE FLUXO (JANELA DO RECEPTOR)")
            print(f"{'─'*70}")
            
            bytes_no_buffer = sum(len(payload) for payload in recv_buffer.values())
            janela_disponivel = max(0, BUFFER_SIZE - bytes_no_buffer)
            
            print(f"  • Buffer total: {BUFFER_SIZE}b")
            print(f"  • Bytes no buffer: {bytes_no_buffer}b ({len(recv_buffer)} pacotes)")
            print(f"  • Janela disponível (rwnd): {janela_disponivel}b")
            
            percent = (bytes_no_buffer / BUFFER_SIZE) * 100 if BUFFER_SIZE > 0 else 0
            print(f"  • Uso do buffer: {percent:.1f}%")
            
            if janela_disponivel < BUFFER_SIZE * 0.2:
                print(f"  ⚠️  Buffer ficando cheio!")
            elif janela_disponivel == BUFFER_SIZE:
                print(f"  ✅ Buffer vazio (janela máxima)")
            
            print(f"{'─'*70}\n")

            # ────── QUESTÃO 2: ACK CUMULATIVO ──────
            print(f"{'─'*70}")
            print(f"[Q2] ENVIANDO ACK CUMULATIVO")
            print(f"{'─'*70}")
            print(f"  • ack_num = {expected_seq} (próximo byte que espero)")
            print(f"  • window = {janela_disponivel}b (quanto posso receber)")
            print(f"  📝 Significado: 'Recebi tudo até byte {expected_seq-1}, envie a partir de {expected_seq}'")
            print(f"{'─'*70}\n")
            
            ack_pkt = Packet(seq_num=0, 
                             ack_num=expected_seq, 
                             flags=ACK, 
                             window=janela_disponivel)
            sock.sendto(ack_pkt.to_bytes(), addr)
            
            print(f"✅ ACK ENVIADO")
            print(f"{'='*70}\n")

        except Exception as e:
            print(f"\n❌ ERRO: {e}")
            import traceback
            traceback.print_exc()
            print()

def _format_flags(flags):
    """Formata flags para exibição."""
    flag_str = []
    if flags & SYN: flag_str.append("SYN")
    if flags & ACK: flag_str.append("ACK")
    if flags & FIN: flag_str.append("FIN")
    if flags & ENC: flag_str.append("ENC")
    return f"({'|'.join(flag_str) if flag_str else 'NONE'})"

if __name__ == "__main__":
    run_server()
