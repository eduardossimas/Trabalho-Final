import socket
import random
from utils import *

def run_server():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((SERVER_IP, SERVER_PORT))
    
    print(f"Servidor ouvindo em {SERVER_IP}:{SERVER_PORT}...")
    
    # Probabilidade de perda (ex: 10%)
    LOSS_PROBABILITY = 0.1 

    while True:
        try:
            data, addr = sock.recvfrom(BUFFER_SIZE)
            
            # Simulação de PERDA DE PACOTE (Requisito 6.2)
            if random.random() < LOSS_PROBABILITY:
                print(f"[SIMULAÇÃO] Pacote de {addr} foi perdido/descartado.")
                continue  # O servidor ignora este pacote, forçando timeout no cliente

            # Converte bytes brutos para nosso objeto Packet
            packet = Packet.from_bytes(data)
            
            print(f"Recebido de {addr}: {packet}")

            # Lógica simples de resposta (Echo ou ACK)
            # Aqui futuramente entra a lógica de verificar ordem e buffer
            
            # Exemplo: Enviar um ACK de volta
            ack_packet = Packet(seq_num=0, ack_num=packet.seq_num + len(packet.payload), flags=ACK, window=1000)
            sock.sendto(ack_packet.to_bytes(), addr)

        except Exception as e:
            print(f"Erro: {e}")

if __name__ == "__main__":
    run_server()