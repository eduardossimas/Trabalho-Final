import socket
import time
from utils import *

def run_client():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.settimeout(2.0) # Espera o máximo de 2 segundos por resposta do ACK

    # Simulação de envio de múltiplos pacotes
    base_seq = 100
    
    for i in range(5): # Envia 5 pacotes de teste
        msg = f"Dados do pacote {i}".encode()
        
        # Cria o pacote
        # seq_num cresce, ack_num é 0 (pois estamos enviando), flags=0 (dados normais), window=0
        pkt = Packet(seq_num=base_seq, ack_num=0, flags=0, window=0, payload=msg)
        
        print(f"Enviando: {pkt}")
        sock.sendto(pkt.to_bytes(), (SERVER_IP, SERVER_PORT))
        
        try:
            # Espera ACK
            data, addr = sock.recvfrom(BUFFER_SIZE)
            ack_pkt = Packet.from_bytes(data)
            print(f"Recebido ACK: {ack_pkt}")
            base_seq += len(msg) # Avança a sequência
            
        except socket.timeout:
            print("Tempo limite excedido! (Provável perda de pacote simulada)")
            # Aqui entrará a lógica de retransmissão e ajuste de cwnd (AIMD)
        
        time.sleep(1) # Pausa dramática para visualizarmos

if __name__ == "__main__":
    run_client()