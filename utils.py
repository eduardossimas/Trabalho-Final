import struct
import socket
import random

# Configurações
SERVER_IP = '127.0.0.1'
SERVER_PORT = 5005
BUFFER_SIZE = 1024
MSS = 1000  # Tamanho máximo do payload

# Flags
SYN = 0b00000001
ACK = 0b00000010
FIN = 0b00000100
ENC = 0b00001000  # Flag indicando pacote criptografado

# Estados da Conexão
STATE_CLOSED = 0
STATE_LISTEN = 1
STATE_SYN_SENT = 2
STATE_SYN_RCVD = 3
STATE_ESTABLISHED = 4
STATE_FIN_WAIT = 5

class Security:
    """Implementa criptografia simples (XOR) para Questão 5."""
    
    def __init__(self, key=b'Redes2026'):
        self.key = key
        self.encryption_enabled = False
    
    def encrypt(self, data):
        """Criptografa dados com XOR."""
        if not self.encryption_enabled or not data:
            return data
        
        output = bytearray()
        key_len = len(self.key)
        for i, byte in enumerate(data):
            output.append(byte ^ self.key[i % key_len])
        return bytes(output)
    
    def decrypt(self, data):
        """Descriptografa dados (XOR é simétrico)."""
        return self.encrypt(data)  # XOR: (A ^ B) ^ B = A
    
    def generate_key(self):
        """Gera chave aleatória de 8 bytes para demonstração."""
        import random
        self.key = bytes([random.randint(0, 255) for _ in range(8)])
        return self.key
    
    def set_key(self, key):
        """Define chave de criptografia."""
        self.key = key
        self.encryption_enabled = True

class Packet:
    def __init__(self, seq_num, ack_num, flags, window, payload=b''):
        self.seq_num = seq_num
        self.ack_num = ack_num
        self.flags = flags
        self.window = window
        self.payload = payload

    def to_bytes(self):
        header = struct.pack('!IIHH', self.seq_num, self.ack_num, self.flags, self.window)
        return header + self.payload

    @staticmethod
    def from_bytes(packet_bytes):
        # Verifica se o pacote tem o tamanho mínimo do cabeçalho
        if len(packet_bytes) < 12:
            raise ValueError("Pacote muito pequeno / corrompido")
            
        header_size = struct.calcsize('!IIHH')
        header = packet_bytes[:header_size]
        payload = packet_bytes[header_size:]
        
        seq_num, ack_num, flags, window = struct.unpack('!IIHH', header)
        return Packet(seq_num, ack_num, flags, window, payload)

    def __repr__(self):
        flag_str = []
        if self.flags & SYN: flag_str.append("SYN")
        if self.flags & ACK: flag_str.append("ACK")
        if self.flags & FIN: flag_str.append("FIN")
        if self.flags & ENC: flag_str.append("ENC")
        return f"[Seq={self.seq_num} | Ack={self.ack_num} | Win={self.window} | Flags={'|'.join(flag_str)} | Payload={len(self.payload)}b]"
