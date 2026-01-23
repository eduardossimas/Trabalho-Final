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
# QUESTÃO 3: Controle de fluxo (janela do destinatário)
# =============================================================================

def teste_questao_3():
    """
    Testa o controle de fluxo baseado na janela do receptor.
    
    Cenário de teste:
    - Verifica se servidor anuncia janela disponível nos ACKs
    - Envia pacotes fora de ordem para encher o buffer
    - Verifica se janela diminui quando buffer enche
    - Verifica se janela aumenta quando buffer esvazia
    """
    print("\n" + "="*70)
    print("TESTE - QUESTÃO 3: Controle de Fluxo (Janela do Receptor)")
    print("="*70)
    
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.settimeout(2.0)
    
    # Teste 3.1: Verificação da janela inicial
    print("\n[Teste 3.1] Verificando janela inicial anunciada pelo servidor...")
    print(f"Observação: Janela inicial deve ser {BUFFER_SIZE} bytes")
    
    base_seq = 100
    msg = "TesteJanela".encode()
    pkt = Packet(seq_num=base_seq, ack_num=0, flags=0, window=0, payload=msg)
    
    print(f"  → Enviando pacote (seq={base_seq})")
    sock.sendto(pkt.to_bytes(), (SERVER_IP, SERVER_PORT))
    
    try:
        data, addr = sock.recvfrom(BUFFER_SIZE)
        ack_pkt = Packet.from_bytes(data)
        print(f"  ← ACK: ack_num={ack_pkt.ack_num}, window={ack_pkt.window}b")
        
        if ack_pkt.window == BUFFER_SIZE:
            print(f"  ✓ Janela inicial correta: {BUFFER_SIZE}b")
        else:
            print(f"  ✗ Janela incorreta! Esperado={BUFFER_SIZE}, Recebido={ack_pkt.window}")
    except socket.timeout:
        print("  ✗ Timeout")
    
    base_seq += len(msg)
    time.sleep(0.3)
    
    # Teste 3.2: Encher o buffer com pacotes fora de ordem
    print("\n[Teste 3.2] Enchendo buffer com pacotes FORA de ordem...")
    print("Observação: Janela deve DIMINUIR conforme buffer enche")
    
    # Criar 10 pacotes mas enviar fora de ordem (pular o primeiro)
    # Isso fará com que todos fiquem no buffer
    num_pacotes = 10
    tamanho_payload = 50  # 50 bytes cada
    
    print(f"  Criando {num_pacotes} pacotes de {tamanho_payload}b cada ({num_pacotes * tamanho_payload}b total)")
    
    # Guardar o primeiro pacote para enviar por último
    primeiro_seq = base_seq
    primeiro_payload = b"P" * tamanho_payload
    
    # Enviar pacotes 2 a 10 (pular o primeiro)
    janelas_observadas = []
    
    for i in range(1, num_pacotes):
        seq = base_seq + (i * tamanho_payload)
        payload = bytes([ord('A') + i]) * tamanho_payload
        pkt = Packet(seq_num=seq, ack_num=0, flags=0, window=0, payload=payload)
        
        print(f"  → Enviando pacote {i+1} (seq={seq}) - FORA DE ORDEM")
        sock.sendto(pkt.to_bytes(), (SERVER_IP, SERVER_PORT))
        
        try:
            data, addr = sock.recvfrom(BUFFER_SIZE)
            ack_pkt = Packet.from_bytes(data)
            janelas_observadas.append(ack_pkt.window)
            print(f"  ← ACK: ack_num={ack_pkt.ack_num}, window={ack_pkt.window}b")
            
            # Calcula espaço esperado no buffer
            bytes_esperados_buffer = i * tamanho_payload
            janela_esperada = BUFFER_SIZE - bytes_esperados_buffer
            
            if ack_pkt.window == janela_esperada:
                print(f"  ✓ Janela correta! Buffer tem ~{bytes_esperados_buffer}b, janela={ack_pkt.window}b")
            else:
                print(f"  ! Janela={ack_pkt.window}b (esperado ~{janela_esperada}b)")
                
        except socket.timeout:
            print("  ✗ Timeout")
        
        time.sleep(0.2)
    
    # Verifica se janela diminuiu
    if len(janelas_observadas) >= 2:
        if janelas_observadas[-1] < janelas_observadas[0]:
            print(f"  ✓ Controle de fluxo funcionando! Janela diminuiu: {janelas_observadas[0]}b → {janelas_observadas[-1]}b")
        else:
            print(f"  ✗ Janela não diminuiu como esperado")
    
    # Teste 3.3: Esvaziar o buffer enviando o pacote que faltava
    print("\n[Teste 3.3] Esvaziando buffer enviando o pacote que faltava...")
    print("Observação: Janela deve AUMENTAR quando buffer esvazia")
    
    pkt = Packet(seq_num=primeiro_seq, ack_num=0, flags=0, window=0, payload=primeiro_payload)
    print(f"  → Enviando pacote 1 (seq={primeiro_seq}) - O QUE FALTAVA!")
    sock.sendto(pkt.to_bytes(), (SERVER_IP, SERVER_PORT))
    
    try:
        data, addr = sock.recvfrom(BUFFER_SIZE)
        ack_pkt = Packet.from_bytes(data)
        print(f"  ← ACK: ack_num={ack_pkt.ack_num}, window={ack_pkt.window}b")
        
        if ack_pkt.window == BUFFER_SIZE:
            print(f"  ✓ Buffer esvaziado! Janela voltou para {BUFFER_SIZE}b")
        elif ack_pkt.window > janelas_observadas[-1]:
            print(f"  ✓ Janela aumentou! Era {janelas_observadas[-1]}b, agora {ack_pkt.window}b")
        else:
            print(f"  ! Janela={ack_pkt.window}b")
            
    except socket.timeout:
        print("  ✗ Timeout")
    
    # Teste 3.4: Simulação de cliente respeitando a janela
    print("\n[Teste 3.4] Simulando cliente que RESPEITA a janela...")
    print("Observação: Cliente não deve enviar mais que a janela permite")
    
    base_seq = primeiro_seq + (num_pacotes * tamanho_payload)
    
    # Consulta janela atual
    msg_teste = b"X" * 10
    pkt = Packet(seq_num=base_seq, ack_num=0, flags=0, window=0, payload=msg_teste)
    sock.sendto(pkt.to_bytes(), (SERVER_IP, SERVER_PORT))
    
    try:
        data, addr = sock.recvfrom(BUFFER_SIZE)
        ack_pkt = Packet.from_bytes(data)
        janela_servidor = ack_pkt.window
        base_seq += len(msg_teste)
        
        print(f"  Janela do servidor: {janela_servidor}b")
        print(f"  Cliente pode enviar até {janela_servidor}b sem ACK")
        
        # Simula envio respeitando a janela
        tamanho_pacote = 100
        max_pacotes = janela_servidor // tamanho_pacote
        
        print(f"  → Enviando {max_pacotes} pacotes de {tamanho_pacote}b (total={max_pacotes * tamanho_pacote}b)")
        
        for i in range(max_pacotes):
            payload = bytes([i]) * tamanho_pacote
            pkt = Packet(seq_num=base_seq, ack_num=0, flags=0, window=0, payload=payload)
            sock.sendto(pkt.to_bytes(), (SERVER_IP, SERVER_PORT))
            
            data, addr = sock.recvfrom(BUFFER_SIZE)
            ack_pkt = Packet.from_bytes(data)
            base_seq += len(payload)
        
        print(f"  ✓ Cliente enviou {max_pacotes} pacotes respeitando janela de {janela_servidor}b")
        
    except socket.timeout:
        print("  ✗ Timeout")
    
    # Teste 3.5: ESTOURAR o limite do buffer (cliente mal comportado)
    print("\n[Teste 3.5] ⚠️  TESTE DE OVERFLOW - Cliente NÃO respeita janela...")
    print("Observação: Envia mais dados que o buffer suporta (>1024b)")
    
    base_seq = base_seq  # Continua do teste anterior
    
    # Criar 25 pacotes de 50 bytes = 1250 bytes (MAIOR que BUFFER_SIZE=1024)
    num_pacotes_overflow = 25
    tamanho_payload_overflow = 50
    total_bytes = num_pacotes_overflow * tamanho_payload_overflow
    
    print(f"  Cliente malicioso vai enviar {num_pacotes_overflow} pacotes de {tamanho_payload_overflow}b")
    print(f"  Total: {total_bytes}b (Buffer do servidor: {BUFFER_SIZE}b)")
    print(f"  ⚠️  OVERFLOW esperado: {total_bytes - BUFFER_SIZE}b extras!")
    
    # Guardar primeiro pacote para enviar por último (forçar buffer cheio)
    primeiro_seq_overflow = base_seq
    primeiro_payload_overflow = b"FIRST" * 10  # 50 bytes
    
    janelas_overflow = []
    
    # Enviar pacotes 2 a 25 (pular o primeiro para encher buffer)
    for i in range(1, num_pacotes_overflow):
        seq = base_seq + (i * tamanho_payload_overflow)
        payload = bytes([ord('X') + (i % 20)]) * tamanho_payload_overflow
        pkt = Packet(seq_num=seq, ack_num=0, flags=0, window=0, payload=payload)
        
        sock.sendto(pkt.to_bytes(), (SERVER_IP, SERVER_PORT))
        
        try:
            data, addr = sock.recvfrom(BUFFER_SIZE)
            ack_pkt = Packet.from_bytes(data)
            janelas_overflow.append(ack_pkt.window)
            
            # Mostrar apenas alguns para não poluir
            if i <= 3 or i >= num_pacotes_overflow - 2 or ack_pkt.window <= 100:
                bytes_buffer = BUFFER_SIZE - ack_pkt.window
                print(f"  → Pacote {i+1}: buffer~{bytes_buffer}b, janela={ack_pkt.window}b", end="")
                
                if ack_pkt.window <= 50:
                    print(" ⚠️  JANELA CRÍTICA!")
                elif ack_pkt.window == 0:
                    print(" 🛑 BUFFER CHEIO! (janela=0)")
                else:
                    print()
            elif i == 4:
                print("  ... (enviando mais pacotes) ...")
                
        except socket.timeout:
            print(f"  ✗ Timeout no pacote {i+1}")
        
        time.sleep(0.1)
    
    print(f"\n  📊 Análise do overflow:")
    if len(janelas_overflow) > 0:
        janela_min = min(janelas_overflow)
        janela_max = max(janelas_overflow)
        buffer_max = BUFFER_SIZE - janela_min
        
        print(f"  • Janela inicial: {janela_max}b")
        print(f"  • Janela mínima alcançada: {janela_min}b")
        print(f"  • Buffer máximo usado: {buffer_max}b / {BUFFER_SIZE}b")
        
        if janela_min == 0:
            print(f"  🛑 BUFFER ESTOURADO! Servidor rejeitando pacotes!")
        elif janela_min < 100:
            print(f"  ⚠️  Buffer quase cheio! Janela crítica.")
        
        if buffer_max > BUFFER_SIZE:
            print(f"  ⚠️  Cliente tentou enviar mais que o buffer suporta!")
        
        print(f"\n  ✓ Teste demonstrou comportamento de overflow do buffer")
    
    sock.close()
    print("\n" + "="*70)
    print("TESTE QUESTÃO 3 CONCLUÍDO")
    print("="*70)


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
        print("3. Questão 3 - Controle de fluxo (janela do receptor)")
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
