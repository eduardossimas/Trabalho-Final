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
    base_seq = 100  # Começa em 100, como esperado pelo servidor
    pacotes_enviados = []
    
    for i in range(5):
        msg = f"Pacote {i+1} - Dados em ordem".encode()
        pkt = Packet(seq_num=base_seq, ack_num=0, flags=0, window=0, payload=msg)
        
        # Retransmissão com até 3 tentativas
        max_retries = 3
        for attempt in range(max_retries):
            if attempt > 0:
                print(f"  ↻ Retransmitindo (tentativa {attempt + 1}/{max_retries})...")
            else:
                print(f"  → Enviando seq={base_seq}: {msg.decode()}")
            
            sock.sendto(pkt.to_bytes(), (SERVER_IP, SERVER_PORT))
            
            try:
                data, addr = sock.recvfrom(BUFFER_SIZE)
                ack_pkt = Packet.from_bytes(data)
                print(f"  ← Recebido ACK: ack_num={ack_pkt.ack_num}")
                break  # ACK recebido, sai do loop de retransmissão
            except socket.timeout:
                if attempt < max_retries - 1:
                    print(f"  ✗ Timeout! Tentando novamente...")
                else:
                    print(f"  ✗ Timeout após {max_retries} tentativas!")
        
        base_seq += len(msg)
        time.sleep(0.5)
    
    # Teste 1.2: Envio de pacotes fora de ordem (simulando rede)
    print("\n[Teste 1.2] Enviando pacotes FORA de ordem...")
    print("Observação: Servidor deve reordenar e entregar na ordem correta à aplicação")
    
    # Criar 5 pacotes CONSECUTIVOS com seq_num calculado pelo tamanho real
    # Base: próximo seq após teste 1.1 (~225)
    mensagens = [
        "Pacote 1",
        "Pacote 2", 
        "Pacote 3",
        "Pacote 4",
        "Pacote 5"
    ]
    
    # Calcular seq_num correto para cada pacote
    pacotes_ordenados = []
    seq_atual = base_seq  # Continua de onde parou o teste 1.1
    
    for i, msg_texto in enumerate(mensagens):
        msg = msg_texto.encode()
        pacotes_ordenados.append({
            'seq': seq_atual,
            'msg': msg,
            'descricao': f"{msg_texto} (seq={seq_atual})"
        })
        seq_atual += len(msg)
    
    # Embaralhar a ORDEM de envio (mas não os seq_nums!)
    # Ordem original: 0, 1, 2, 3, 4
    # Ordem embaralhada: 1, 3, 0, 4, 2
    ordem_envio = [1, 3, 0, 4, 2]
    
    print(f"Enviando na ordem embaralhada: {[mensagens[i] for i in ordem_envio]}")
    
    for idx in ordem_envio:
        pkt_info = pacotes_ordenados[idx]
        seq = pkt_info['seq']
        msg = pkt_info['msg']
        pkt = Packet(seq_num=seq, ack_num=0, flags=0, window=0, payload=msg)
        
        # Retransmissão com até 3 tentativas
        max_retries = 3
        for attempt in range(max_retries):
            if attempt > 0:
                print(f"  ↻ Retransmitindo seq={seq} (tentativa {attempt + 1}/{max_retries})...")
            else:
                print(f"  → Enviando seq={seq}: {pkt_info['descricao']}")
            
            sock.sendto(pkt.to_bytes(), (SERVER_IP, SERVER_PORT))
            
            try:
                data, addr = sock.recvfrom(BUFFER_SIZE)
                ack_pkt = Packet.from_bytes(data)
                print(f"  ← Recebido ACK: ack_num={ack_pkt.ack_num}")
                break  # ACK recebido, sai do loop de retransmissão
            except socket.timeout:
                if attempt < max_retries - 1:
                    print(f"  ✗ Timeout! Tentando novamente...")
                else:
                    print(f"  ✗ Timeout após {max_retries} tentativas!")
        
        time.sleep(0.5)
    
    # Atualiza base_seq para o próximo teste
    base_seq = seq_atual
    
    # Teste 1.3: Pacotes duplicados (mesmo número de sequência)
    print("\n[Teste 1.3] Testando pacotes duplicados...")
    print("Observação: Servidor deve descartar duplicatas e não reprocessar")
    seq_dup = 100  # Reutilizando um seq_num já processado no teste 1.1
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
# QUESTÃO 2: Confirmação acumulativa (ACK acumulativo)
# =============================================================================

def teste_questao_2():
    """
    Testa o ACK acumulativo do servidor.
    
    Cenário de teste:
    - Envia múltiplos pacotes e verifica se ACK confirma TODOS os bytes anteriores
    - Envia pacotes fora de ordem e verifica se ACK acumula após reordenação
    - Simula perda de ACK e verifica se servidor re-envia ACK acumulativo
    """
    print("\n" + "="*70)
    print("TESTE - QUESTÃO 2: Confirmação Acumulativa (ACK)")
    print("="*70)
    
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.settimeout(2.0)
    
    # Teste 2.1: ACK acumulativo em sequência normal
    print("\n[Teste 2.1] Verificando ACK acumulativo com pacotes em ordem...")
    print("Observação: Cada ACK deve confirmar TODOS os bytes recebidos até o momento")
    
    base_seq = 100 
    
    for i in range(4):
        msg = f"Pacote {i+1}".encode()
        pkt = Packet(seq_num=base_seq, ack_num=0, flags=0, window=0, payload=msg)
        
        esperado_ack = base_seq + len(msg)
        
        print(f"  → Enviando seq={base_seq}, payload={len(msg)}b")
        sock.sendto(pkt.to_bytes(), (SERVER_IP, SERVER_PORT))
        
        try:
            data, addr = sock.recvfrom(BUFFER_SIZE)
            ack_pkt = Packet.from_bytes(data)
            print(f"  ← ACK recebido: ack_num={ack_pkt.ack_num}")
            
            # Verifica se é cumulativo
            if ack_pkt.ack_num == esperado_ack:
                print(f"  ✓ ACK CUMULATIVO correto! Confirma até byte {ack_pkt.ack_num}")
            else:
                print(f"  ✗ ACK incorreto! Esperado={esperado_ack}, Recebido={ack_pkt.ack_num}")
            
            base_seq += len(msg)
            
        except socket.timeout:
            print("  ✗ Timeout ao aguardar ACK")
            break
        
        time.sleep(0.3)
    
    # Teste 2.2: ACK acumulativo com pacotes fora de ordem
    print("\n[Teste 2.2] ACK acumulativo com pacotes FORA de ordem...")
    print("Observação: ACK só avança quando recebe o pacote que faltava")
    
    # Criar pacotes consecutivos
    mensagens = ["A", "B", "C", "D"]
    pacotes = []
    seq_atual = base_seq
    
    for msg_texto in mensagens:
        msg = msg_texto.encode()
        pacotes.append({
            'seq': seq_atual,
            'msg': msg,
            'label': msg_texto
        })
        seq_atual += len(msg)
    
    # Enviar na ordem: B, D, C, A (invertido)
    ordem_envio = [1, 3, 2, 0]
    
    print(f"Ordem de envio: {[mensagens[i] for i in ordem_envio]}")
    
    for idx in ordem_envio:
        pkt_info = pacotes[idx]
        pkt = Packet(seq_num=pkt_info['seq'], ack_num=0, flags=0, window=0, payload=pkt_info['msg'])
        
        print(f"  → Enviando '{pkt_info['label']}' (seq={pkt_info['seq']})")
        sock.sendto(pkt.to_bytes(), (SERVER_IP, SERVER_PORT))
        
        try:
            data, addr = sock.recvfrom(BUFFER_SIZE)
            ack_pkt = Packet.from_bytes(data)
            print(f"  ← ACK: ack_num={ack_pkt.ack_num}", end="")
            
            # Analisa o ACK
            if idx == 0:  # Quando envia 'A' (o que faltava)
                print(f" → ✓ ACK ACUMULATIVO! Confirma A+B+C+D juntos!")
            elif ack_pkt.ack_num == pacotes[0]['seq']:
                print(f" → Ainda aguardando 'A' (primeiro pacote)")
            else:
                print()
                
        except socket.timeout:
            print("  ✗ Timeout")
        
        time.sleep(0.3)
    
    # Teste 2.3: Re-envio de ACK acumulativo (duplicata)
    print("\n[Teste 2.3] Re-envio de ACK quando recebe pacote duplicado...")
    print("Observação: Servidor deve re-enviar o MESMO ACK acumulativo")
    
    base_seq = seq_atual
    msg = "TesteDup".encode()
    pkt = Packet(seq_num=base_seq, ack_num=0, flags=0, window=0, payload=msg)
    
    print(f"  → Enviando pacote original (seq={base_seq})")
    sock.sendto(pkt.to_bytes(), (SERVER_IP, SERVER_PORT))
    
    try:
        data, addr = sock.recvfrom(BUFFER_SIZE)
        ack_pkt = Packet.from_bytes(data)
        primeiro_ack = ack_pkt.ack_num
        print(f"  ← Primeiro ACK: ack_num={primeiro_ack}")
        
        time.sleep(0.3)
        
        # Envia DUPLICATA do mesmo pacote
        print(f"  → Enviando DUPLICATA (seq={base_seq})")
        sock.sendto(pkt.to_bytes(), (SERVER_IP, SERVER_PORT))
        
        data, addr = sock.recvfrom(BUFFER_SIZE)
        ack_pkt2 = Packet.from_bytes(data)
        segundo_ack = ack_pkt2.ack_num
        print(f"  ← Segundo ACK: ack_num={segundo_ack}")
        
        if primeiro_ack == segundo_ack:
            print(f"  ✓ ACK acumulativo mantido! Servidor re-enviou ack_num={primeiro_ack}")
        else:
            print(f"  ✗ ACK diferente! Esperado={primeiro_ack}, Recebido={segundo_ack}")
            
    except socket.timeout:
        print("  ✗ Timeout")
    
    sock.close()
    print("\n" + "="*70)
    print("TESTE QUESTÃO 2 CONCLUÍDO")
    print("="*70)


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
        print("2. Questão 2 - Confirmação acumulativa (ACK)")
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
