import socket
import random
from utils import *

def run_server():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((SERVER_IP, SERVER_PORT))
    
    # Simula o handshake (assumindo que já ocorreu)
    # Numa implementação real, pegue esses valores do retorno da função handshake()
    expected_seq = 100  # Supondo que o handshake definiu que começa no 100
    
    # O BUFFER DE RECEPÇÃO: Dicionário para guardar pacotes fora de ordem
    # Chave: seq_num, Valor: payload
    recv_buffer = {} 

    print(f"Servidor ouvindo e aguardando a partir do Seq={expected_seq}...")
    
    LOSS_PROBABILITY = 0.05

    while True:
        try:
            data, addr = sock.recvfrom(BUFFER_SIZE)
            
            # Simulação de Perda (Requisito 6.2)
            if random.random() < LOSS_PROBABILITY:
                print(f"[x] Pacote perdido na simulação.")
                continue

            pkt = Packet.from_bytes(data)
            
            # --- LÓGICA DE ORDENAÇÃO (REQUISITO 1) ---
            
            # Caso 1: Pacote chegou na ordem certa
            if pkt.seq_num == expected_seq:
                print(f"[V] Recebido CORRETO: Seq={pkt.seq_num}")
                
                # "Entrega" para a aplicação (aqui apenas imprimimos/salvamos)
                payload_size = len(pkt.payload)
                # SE TIVER CRIPTOGRAFIA, DESCRIPTOGRAFA AQUI
                
                # Avança o esperado
                expected_seq += payload_size
                
                # Caso 2: Verifica se o próximo pacote já estava no buffer esperando
                while expected_seq in recv_buffer:
                    print(f"[!] Recuperando do Buffer: Seq={expected_seq}")
                    buffered_payload = recv_buffer.pop(expected_seq)
                    expected_seq += len(buffered_payload)
                    
            # Caso 3: Pacote chegou adiantado (fora de ordem) -> Vai pro Buffer
            elif pkt.seq_num > expected_seq:
                print(f"[!] Fora de ordem. Esperado={expected_seq}, Chegou={pkt.seq_num}. Guardando no Buffer.")
                recv_buffer[pkt.seq_num] = pkt.payload
                
            # Caso 4: Pacote duplicado/antigo (seq < expected)
            else:
                print(f"[R] Duplicado descartado: Seq={pkt.seq_num}")

            # --- ENVIO DO ACK (REQUISITO 2 - CUMULATIVO) ---
            # Sempre confirmamos o que estamos esperando receber a seguir
            ack_pkt = Packet(seq_num=0, 
                             ack_num=expected_seq, 
                             flags=ACK, 
                             window=BUFFER_SIZE)
            sock.sendto(ack_pkt.to_bytes(), addr)

        except Exception as e:
            print(f"Erro: {e}")

if __name__ == "__main__":
    run_server()