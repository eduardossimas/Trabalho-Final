"""
Testes do Trabalho Final - Redes de Computadores
Arquivo para documentar e testar cada questão do trabalho
"""

import socket
import time
from utils import *


# =============================================================================
# QUESTÃO 1: Entrega ordenada para aplicação (baseada no número de sequência)
# =============================================================================

def teste_questao_1():
    """
    Testa a entrega ordenada de pacotes com base no número de sequência.
    
    Cenário de teste:
    - Envia múltiplos pacotes com números de sequência crescentes
    - Verifica se o servidor recebe e processa na ordem correta
    - Simula pacotes fora de ordem para testar reordenação
    """
    print("\n" + "="*70)
    print("TESTE - QUESTÃO 1: Entrega Ordenada de Pacotes")
    print("="*70)
    
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.settimeout(2.0)
    
    # Teste 1.1: Envio de pacotes em ordem
    print("\n[Teste 1.1] Enviando pacotes em ordem sequencial...")
    base_seq = 1000
    pacotes_enviados = []
    
    for i in range(5):
        msg = f"Pacote {i+1} - Dados em ordem".encode()
        pkt = Packet(seq_num=base_seq, ack_num=0, flags=0, window=0, payload=msg)
        
        print(f"  → Enviando seq={base_seq}: {msg.decode()}")
        sock.sendto(pkt.to_bytes(), (SERVER_IP, SERVER_PORT))
        pacotes_enviados.append((base_seq, msg))
        
        try:
            data, addr = sock.recvfrom(BUFFER_SIZE)
            ack_pkt = Packet.from_bytes(data)
            print(f"  ← Recebido ACK: ack_num={ack_pkt.ack_num}")
        except socket.timeout:
            print("  ✗ Timeout ao aguardar ACK")
        
        base_seq += len(msg)
        time.sleep(0.5)
    
    # Teste 1.2: Envio de pacotes fora de ordem (simulando rede)
    print("\n[Teste 1.2] Enviando pacotes FORA de ordem...")
    
    # Preparar pacotes
    seq_nums = [2000, 2100, 2050, 2150, 2025]  # Propositalmente fora de ordem
    for i, seq in enumerate(seq_nums):
        msg = f"Pacote {i+1} - seq={seq}".encode()
        pkt = Packet(seq_num=seq, ack_num=0, flags=0, window=0, payload=msg)
        
        print(f"  → Enviando seq={seq}: {msg.decode()}")
        sock.sendto(pkt.to_bytes(), (SERVER_IP, SERVER_PORT))
        
        try:
            data, addr = sock.recvfrom(BUFFER_SIZE)
            ack_pkt = Packet.from_bytes(data)
            print(f"  ← Recebido ACK: ack_num={ack_pkt.ack_num}")
        except socket.timeout:
            print("  ✗ Timeout ao aguardar ACK")
        
        time.sleep(0.5)
    
    # Teste 1.3: Pacotes duplicados (mesmo número de sequência)
    print("\n[Teste 1.3] Testando pacotes duplicados...")
    seq_dup = 3000
    msg_dup = "Pacote duplicado para teste".encode()
    
    for i in range(3):
        pkt = Packet(seq_num=seq_dup, ack_num=0, flags=0, window=0, payload=msg_dup)
        print(f"  → Enviando duplicata {i+1} com seq={seq_dup}")
        sock.sendto(pkt.to_bytes(), (SERVER_IP, SERVER_PORT))
        
        try:
            data, addr = sock.recvfrom(BUFFER_SIZE)
            ack_pkt = Packet.from_bytes(data)
            print(f"  ← Recebido ACK: ack_num={ack_pkt.ack_num}")
        except socket.timeout:
            print("  ✗ Timeout ao aguardar ACK")
        
        time.sleep(0.3)
    
    sock.close()
    print("\n" + "="*70)
    print("TESTE QUESTÃO 1 CONCLUÍDO")
    print("="*70)


# =============================================================================
# QUESTÃO 2: [Adicionar descrição quando implementar]
# =============================================================================

def teste_questao_2():
    """
    [Descrição do teste da questão 2]
    """
    print("\n" + "="*70)
    print("TESTE - QUESTÃO 2: [Título]")
    print("="*70)
    
    # TODO: Implementar teste da questão 2
    print("Teste ainda não implementado")
    
    print("\n" + "="*70)


# =============================================================================
# QUESTÃO 3: [Adicionar descrição quando implementar]
# =============================================================================

def teste_questao_3():
    """
    [Descrição do teste da questão 3]
    """
    print("\n" + "="*70)
    print("TESTE - QUESTÃO 3: [Título]")
    print("="*70)
    
    # TODO: Implementar teste da questão 3
    print("Teste ainda não implementado")
    
    print("\n" + "="*70)


# =============================================================================
# MENU PRINCIPAL
# =============================================================================

def menu_testes():
    """
    Menu interativo para escolher qual teste executar
    """
    while True:
        print("\n" + "="*70)
        print("MENU DE TESTES - Trabalho Final de Redes")
        print("="*70)
        print("1. Questão 1 - Entrega ordenada de pacotes")
        print("2. Questão 2 - [A definir]")
        print("3. Questão 3 - [A definir]")
        print("4. Executar todos os testes")
        print("0. Sair")
        print("="*70)
        
        escolha = input("\nEscolha uma opção: ").strip()
        
        if escolha == "1":
            teste_questao_1()
        elif escolha == "2":
            teste_questao_2()
        elif escolha == "3":
            teste_questao_3()
        elif escolha == "4":
            print("\nExecutando todos os testes...\n")
            teste_questao_1()
            teste_questao_2()
            teste_questao_3()
        elif escolha == "0":
            print("\nEncerrando testes...")
            break
        else:
            print("\n✗ Opção inválida! Tente novamente.")
        
        input("\nPressione ENTER para continuar...")


if __name__ == "__main__":
    print("""
    ╔══════════════════════════════════════════════════════════════════╗
    ║         TESTES - TRABALHO FINAL DE REDES DE COMPUTADORES        ║
    ╚══════════════════════════════════════════════════════════════════╝
    
    IMPORTANTE: Certifique-se de que o servidor está rodando antes
    de executar os testes!
    
    Execute em outro terminal: python3 servidor.py
    """)
    
    menu_testes()
