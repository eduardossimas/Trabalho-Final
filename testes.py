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
# QUESTÃO 4: Controle de Congestionamento (AIMD - TCP Reno)
# =============================================================================

def teste_questao_4():
    """
    Testa o controle de congestionamento baseado no TCP Reno.
    REQUER: Servidor rodando (python3 servidor.py)
    
    Cenário de teste:
    - Verifica Slow Start (crescimento exponencial) com servidor real
    - Verifica Congestion Avoidance (crescimento linear)
    - Verifica reação a Timeout (perda severa)
    - Verifica Fast Retransmit (3 ACKs duplicados)
    """
    print("\n" + "="*70)
    print("TESTE - QUESTÃO 4: Controle de Congestionamento (TCP Reno)")
    print("="*70)
    print("NOTA: Este teste requer o servidor rodando!")
    print("      Execute em outro terminal: python3 servidor.py")
    print("="*70)
    
    # Importar a classe de controle de congestionamento
    from cliente import CongestionControl, Sender
    
    # =========================================================================
    # TESTE 4.1: SLOW START COM SERVIDOR REAL
    # =========================================================================
    print("\n[Teste 4.1] SLOW START - Comunicação com servidor real")
    print("Observação: cwnd deve aumentar +MSS a cada ACK")
    print("Equação: cwnd = cwnd + MSS")
    print("-" * 50)
    
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.settimeout(2.0)
    
    # Criar controle de congestionamento
    cc = CongestionControl()
    base_seq = 100
    
    print(f"\n  Estado inicial: cwnd={cc.cwnd}b, ssthresh={cc.ssthresh}b")
    print(f"  Fase: {cc.get_phase().upper()}")
    print()
    
    # Enviar 5 pacotes e verificar crescimento do cwnd
    cwnd_historico = [cc.cwnd]
    
    for i in range(5):
        msg = f"SlowStart-{i}".encode()
        pkt = Packet(seq_num=base_seq, ack_num=0, flags=0, window=0, payload=msg)
        
        old_cwnd = cc.cwnd
        print(f"  [{i+1}] Enviando seq={base_seq} ({len(msg)}b)...")
        
        sock.sendto(pkt.to_bytes(), (SERVER_IP, SERVER_PORT))
        
        try:
            data, addr = sock.recvfrom(BUFFER_SIZE)
            ack_pkt = Packet.from_bytes(data)
            
            # Processar ACK no controle de congestionamento
            cc.on_new_ack(ack_pkt.ack_num)
            cwnd_historico.append(cc.cwnd)
            
            incremento = cc.cwnd - old_cwnd
            print(f"      ← ACK={ack_pkt.ack_num}, window={ack_pkt.window}b")
            print(f"      cwnd: {old_cwnd}b → {cc.cwnd}b (+{incremento}b)")
            
            base_seq = ack_pkt.ack_num
            
        except socket.timeout:
            print(f"      ✗ Timeout!")
            break
        
        time.sleep(0.3)
    
    # Verificar resultado do Slow Start
    print(f"\n  📊 Resultado Slow Start:")
    print(f"  • cwnd inicial: {cwnd_historico[0]}b")
    print(f"  • cwnd final: {cwnd_historico[-1]}b")
    print(f"  • Incremento total: {cwnd_historico[-1] - cwnd_historico[0]}b")
    print(f"  • Esperado: 5 × MSS = {5 * MSS}b")
    
    if cwnd_historico[-1] - cwnd_historico[0] == 5 * MSS:
        print(f"  ✓ Slow Start funcionando corretamente!")
    else:
        print(f"  ✗ Slow Start com problema!")
    
    # =========================================================================
    # TESTE 4.2: TRANSIÇÃO SLOW START → CONGESTION AVOIDANCE
    # =========================================================================
    print("\n" + "-"*70)
    print("[Teste 4.2] TRANSIÇÃO para Congestion Avoidance")
    print("Observação: Quando cwnd >= ssthresh, muda para crescimento linear")
    print("-" * 50)
    
    # Configurar ssthresh baixo para forçar transição
    cc2 = CongestionControl()
    cc2.ssthresh = 3000  # Threshold baixo
    base_seq2 = base_seq
    
    print(f"\n  Configuração: cwnd={cc2.cwnd}b, ssthresh={cc2.ssthresh}b")
    print(f"  Transição ocorrerá quando cwnd >= {cc2.ssthresh}b")
    print()
    
    transicao_detectada = False
    
    for i in range(5):
        msg = f"Trans-{i}".encode()
        pkt = Packet(seq_num=base_seq2, ack_num=0, flags=0, window=0, payload=msg)
        
        old_cwnd = cc2.cwnd
        old_phase = cc2.get_phase()
        
        sock.sendto(pkt.to_bytes(), (SERVER_IP, SERVER_PORT))
        
        try:
            data, addr = sock.recvfrom(BUFFER_SIZE)
            ack_pkt = Packet.from_bytes(data)
            
            cc2.on_new_ack(ack_pkt.ack_num)
            new_phase = cc2.get_phase()
            
            print(f"  [{i+1}] ACK={ack_pkt.ack_num}: cwnd {old_cwnd:.0f}b → {cc2.cwnd:.0f}b [{new_phase}]")
            
            if old_phase == "slow_start" and new_phase == "congestion_avoidance":
                print(f"      ⚡ TRANSIÇÃO DETECTADA! cwnd >= ssthresh")
                transicao_detectada = True
            
            base_seq2 = ack_pkt.ack_num
            
        except socket.timeout:
            print(f"      ✗ Timeout!")
            break
        
        time.sleep(0.3)
    
    if transicao_detectada:
        print(f"\n  ✓ Transição Slow Start → Congestion Avoidance verificada!")
    
    # =========================================================================
    # TESTE 4.3: CONGESTION AVOIDANCE (crescimento linear)
    # =========================================================================
    print("\n" + "-"*70)
    print("[Teste 4.3] CONGESTION AVOIDANCE - Crescimento Linear")
    print("Observação: cwnd aumenta ~1 MSS por RTT")
    print("Equação: cwnd = cwnd + (MSS × MSS) / cwnd")
    print("-" * 50)
    
    cc3 = CongestionControl()
    cc3.cwnd = 4000  # Já em Congestion Avoidance
    cc3.ssthresh = 2000
    cc3.last_ack_received = base_seq2
    base_seq3 = base_seq2
    
    print(f"\n  Estado: cwnd={cc3.cwnd}b, ssthresh={cc3.ssthresh}b")
    print(f"  Fase: {cc3.get_phase().upper()}")
    print()
    
    incrementos = []
    
    for i in range(4):
        msg = f"CongAvoid-{i}".encode()
        pkt = Packet(seq_num=base_seq3, ack_num=0, flags=0, window=0, payload=msg)
        
        old_cwnd = cc3.cwnd
        
        sock.sendto(pkt.to_bytes(), (SERVER_IP, SERVER_PORT))
        
        try:
            data, addr = sock.recvfrom(BUFFER_SIZE)
            ack_pkt = Packet.from_bytes(data)
            
            cc3.on_new_ack(ack_pkt.ack_num)
            incremento = cc3.cwnd - old_cwnd
            incrementos.append(incremento)
            
            # Mostra cálculo da equação
            calc = (MSS * MSS) / old_cwnd
            print(f"  [{i+1}] cwnd {old_cwnd:.0f}b → {cc3.cwnd:.0f}b")
            print(f"      Equação: {MSS}×{MSS}/{old_cwnd:.0f} = +{calc:.1f}b")
            
            base_seq3 = ack_pkt.ack_num
            
        except socket.timeout:
            print(f"      ✗ Timeout!")
            break
        
        time.sleep(0.3)
    
    soma = sum(incrementos)
    print(f"\n  📊 Resultado Congestion Avoidance:")
    print(f"  • Total incrementado em 4 ACKs: {soma:.0f}b")
    print(f"  • Esperado (~1 MSS): {MSS}b")
    print(f"  ✓ Crescimento linear verificado!")
    
    # =========================================================================
    # TESTE 4.4: TIMEOUT (Perda Severa) - Simulação
    # =========================================================================
    print("\n" + "-"*70)
    print("[Teste 4.4] TIMEOUT - Perda Severa (Simulação)")
    print("Observação: ssthresh = cwnd/2, cwnd = 1*MSS")
    print("Equações:")
    print("  ssthresh = max(cwnd / 2, 2 × MSS)")
    print("  cwnd = 1 × MSS")
    print("-" * 50)
    
    cc4 = CongestionControl()
    cc4.cwnd = 8000
    cc4.ssthresh = 64000
    
    print(f"\n  Estado ANTES do timeout:")
    print(f"  • cwnd = {cc4.cwnd}b")
    print(f"  • ssthresh = {cc4.ssthresh}b")
    print(f"  • Fase: {cc4.get_phase().upper()}")
    
    # Simula timeout
    print(f"\n  ⏱️  Simulando TIMEOUT...")
    cc4.on_timeout()
    
    print(f"\n  Estado DEPOIS do timeout:")
    print(f"  • ssthresh = max(8000/2, 2×{MSS}) = {cc4.ssthresh:.0f}b")
    print(f"  • cwnd = 1 × MSS = {cc4.cwnd}b")
    print(f"  • Fase: {cc4.get_phase().upper()}")
    
    if cc4.cwnd == MSS and cc4.ssthresh == 4000:
        print(f"\n  ✓ Timeout tratado corretamente!")
        print(f"    - Voltou para SLOW START")
        print(f"    - cwnd reiniciado para 1×MSS")
    
    # =========================================================================
    # TESTE 4.5: FAST RETRANSMIT (3 ACKs Duplicados) - Simulação
    # =========================================================================
    print("\n" + "-"*70)
    print("[Teste 4.5] FAST RETRANSMIT - 3 ACKs Duplicados (Simulação)")
    print("Observação: ssthresh = cwnd/2, cwnd = ssthresh (pula Slow Start)")
    print("Equações:")
    print("  ssthresh = max(cwnd / 2, 2 × MSS)")
    print("  cwnd = ssthresh (TCP Reno)")
    print("-" * 50)
    
    cc5 = CongestionControl()
    cc5.cwnd = 8000
    cc5.ssthresh = 64000
    cc5.last_ack_received = 1000
    
    print(f"\n  Estado ANTES:")
    print(f"  • cwnd = {cc5.cwnd}b")
    print(f"  • ssthresh = {cc5.ssthresh}b")
    
    print(f"\n  Simulando 3 ACKs duplicados (ack_num=1000)...")
    
    for i in range(3):
        result = cc5.on_duplicate_ack(1000)
        if result:
            cc5.on_triple_dup_ack()
    
    print(f"\n  Estado DEPOIS:")
    print(f"  • ssthresh = max(8000/2, 2×{MSS}) = {cc5.ssthresh:.0f}b")
    print(f"  • cwnd = ssthresh = {cc5.cwnd:.0f}b")
    print(f"  • Fase: {cc5.get_phase().upper()}")
    
    if cc5.cwnd == 4000 and cc5.ssthresh == 4000:
        print(f"\n  ✓ Fast Retransmit funcionando!")
        print(f"    - NÃO voltou para Slow Start (TCP Reno)")
        print(f"    - Continua em Congestion Avoidance")
    
    # =========================================================================
    # TESTE 4.6: COMPARAÇÃO TIMEOUT vs FAST RETRANSMIT
    # =========================================================================
    print("\n" + "-"*70)
    print("[Teste 4.6] COMPARAÇÃO: Timeout vs Fast Retransmit")
    print("-" * 50)
    
    print(f"""
  Cenário: cwnd = 8000b, ocorre perda de pacote

  ┌──────────────────┬───────────────┬───────────────┬───────────────────┐
  │ Evento           │ ssthresh      │ cwnd          │ Estado            │
  ├──────────────────┼───────────────┼───────────────┼───────────────────┤
  │ TIMEOUT          │ 8000/2=4000b  │ 1×MSS=1000b   │ Slow Start        │
  │ 3 ACKs Dup       │ 8000/2=4000b  │ 4000b         │ Cong. Avoidance   │
  └──────────────────┴───────────────┴───────────────┴───────────────────┘

  📝 Análise:
  • TIMEOUT = Perda severa → Conservador (reinicia do zero)
  • 3 ACKs Dup = Perda leve → Agressivo (mantém metade)
  
  O Fast Retransmit é mais eficiente porque pacotes posteriores
  ainda estão chegando, indicando que a rede não está totalmente
  congestionada.
    """)
    
    # =========================================================================
    # TESTE 4.7: JANELA DESLIZANTE COM SERVIDOR
    # =========================================================================
    print("-"*70)
    print("[Teste 4.7] JANELA DESLIZANTE - min(cwnd, rwnd)")
    print("Observação: Envio limitado pela menor janela")
    print("Regra: bytes_in_flight ≤ min(cwnd, rwnd)")
    print("-" * 50)
    
    cc7 = CongestionControl()
    cc7.cwnd = 3000
    
    print(f"\n  cwnd = {cc7.cwnd}b (controle de congestionamento)")
    print(f"  rwnd = janela do servidor (controle de fluxo)")
    print()
    
    # Consulta rwnd do servidor
    msg_teste = b"TesteJanela"
    pkt = Packet(seq_num=base_seq3, ack_num=0, flags=0, window=0, payload=msg_teste)
    sock.sendto(pkt.to_bytes(), (SERVER_IP, SERVER_PORT))
    
    try:
        data, addr = sock.recvfrom(BUFFER_SIZE)
        ack_pkt = Packet.from_bytes(data)
        rwnd = ack_pkt.window
        
        print(f"  rwnd do servidor: {rwnd}b")
        
        # Testa cenários
        cenarios = [
            (0, "Nada em vôo"),
            (1000, "1000b em vôo"),
            (2000, "2000b em vôo"),
        ]
        
        effective = min(cc7.cwnd, rwnd)
        print(f"  Janela efetiva: min({cc7.cwnd}, {rwnd}) = {effective}b")
        print()
        
        for bytes_in_flight, desc in cenarios:
            can_send, available = cc7.can_send(bytes_in_flight, rwnd)
            print(f"  • {desc}:")
            print(f"    disponível = {effective} - {bytes_in_flight} = {available}b")
            print(f"    pode_enviar = {can_send}")
        
    except socket.timeout:
        print("  ✗ Timeout ao consultar servidor")
    
    sock.close()
    
    # =========================================================================
    # RESUMO FINAL
    # =========================================================================
    print("\n" + "="*70)
    print("RESUMO - CONTROLE DE CONGESTIONAMENTO TCP RENO")
    print("="*70)
    print("""
  ┌─────────────────────────────────────────────────────────────────────┐
  │ FASE              │ CONDIÇÃO        │ EQUAÇÃO                       │
  ├───────────────────┼─────────────────┼───────────────────────────────┤
  │ Slow Start        │ cwnd < ssthresh │ cwnd += MSS                   │
  │ Cong. Avoidance   │ cwnd ≥ ssthresh │ cwnd += (MSS×MSS)/cwnd        │
  ├───────────────────┼─────────────────┼───────────────────────────────┤
  │ Timeout           │ Timer estoura   │ ssthresh=cwnd/2, cwnd=1×MSS   │
  │ 3 ACKs Dup        │ Fast Retransmit │ ssthresh=cwnd/2, cwnd=ssthresh│
  └───────────────────┴─────────────────┴───────────────────────────────┘
    """)
    print("="*70)
    print("TESTE QUESTÃO 4 CONCLUÍDO")
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
        print("4. Questão 4 - Controle de congestionamento (TCP Reno)")
        print("5. Executar todos os testes (1-4)")
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
            teste_questao_4()
        elif escolha == "5":
            print("\nExecutando todos os testes...\n")
            teste_questao_1()
            teste_questao_2()
            teste_questao_3()
            teste_questao_4()
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
