import serial
import time
import re
import random

class SerialFake:
    def __init__(self, file_path):
        with open(file_path, 'r') as f:
            # Lê as linhas e adiciona \r a cada uma se já não tiver
            self.lines = [line.strip() + '\r' for line in f.readlines()]
        
        self.current_line_index = 0
        self.char_position = 0
        self.is_open = True
        self.last_read_time = time.time()
        self.delay_between_lines = 0.2
        
        # Define o primeiro conjunto de dados
        if len(self.lines) > 0:
            self.current_line = self.lines[0]
        else:
            self.current_line = ""

    @property
    def in_waiting(self):
        now = time.time()
        # Se passou tempo suficiente desde a última leitura completa
        if self.char_position >= len(self.current_line):
            if now - self.last_read_time > self.delay_between_lines:
                # Prepara a próxima linha
                self.current_line_index = (self.current_line_index + 1) % len(self.lines)
                self.current_line = self.lines[self.current_line_index]
                self.char_position = 0
                self.last_read_time = now
                return 1  # Indica que há dados disponíveis
            return 0
        else:
            return len(self.current_line) - self.char_position

    def read(self, size=1):
        time.sleep(random.uniform(0.005, 0.01))
        
        if self.char_position >= len(self.current_line):
            # Já leu toda a linha atual
            return b''
        
        # Lê os caracteres da posição atual
        end_pos = min(self.char_position + size, len(self.current_line))
        chunk = self.current_line[self.char_position:end_pos]
        self.char_position = end_pos
        
        # Se chegou ao final da linha, atualiza o tempo
        if self.char_position >= len(self.current_line):
            self.last_read_time = time.time()
        
        return chunk.encode('ascii')

    def reset_input_buffer(self):
        self.char_position = 0

    def reset_output_buffer(self):
        pass

    def write(self, data):
        pass

    def close(self):
        self.is_open = False

def extrair_peso(linha):
    peso_str = linha[6:11]
    peso = int(peso_str)

    id_char = linha[2]
    if id_char in ['z', 'r']:
        peso *= -1
    return peso

def ler_balanca_simples(porta_serial, baudrate=4800, usar_mock=False, debug=False):
    # Configuração da porta serial
    try:
        if usar_mock:
            ser = SerialFake(porta_serial)
        else:
            ser = serial.Serial(
                port=porta_serial,
                baudrate=baudrate,
                bytesize=serial.SEVENBITS,
                parity=serial.PARITY_EVEN,
                stopbits=serial.STOPBITS_ONE,
                timeout=1
            )

        print(f"Conectado à porta {porta_serial}")
        
        padrao = re.compile(r'i.\s+(\d{11})')

        buffer = ""
        ultimo_peso = 0
        peso_estabilizado = None
        tempo_ultima_exibicao = time.monotonic()
        tempo_estabilizacao = time.monotonic()
        tempo_ultimo_buffer_limpo = time.monotonic()
        tempo_ultimo_keepalive = time.monotonic()
        tempo_ultima_reconexao = time.monotonic()
        
        print("Lendo dados da balança. Pressione Ctrl+C para encerrar...")
        
        while True:
            agora = time.monotonic()
            if len(buffer) > 0 and agora - tempo_ultimo_buffer_limpo > 5.0:
                if debug:
                    print(f"DEBUG: Limpando buffer por timeout: '{buffer}'")

                buffer = ""
                tempo_ultimo_buffer_limpo = agora
                ser.reset_input_buffer()

            if ser.in_waiting > 0:

                char = ser.read(1).decode('ascii', errors='replace')
                
                if ord(char) < 32 and char != '\r':
                    if debug and char != '\n':
                        print(f"DEBUG: Ignorando caractere inválido: {ord(char)}")
                    continue

                if char == '\r':
                    if debug:
                        print(f"DEBUG: Buffer recebido antes do parse: '{buffer}'") #DEBUG
                    

                    match = padrao.search(buffer)
                    if match:
                        valor_numerico = match.group(1)
                        peso_kg = int(valor_numerico[:5])

                        if debug:
                            print(f"DEBUG: Match encontrado! Valor: {valor_numerico}, Peso extraído: {peso_kg} kg") #DEBUG
                        if peso_kg != ultimo_peso:
                            print(f"Leitura alterada: [{valor_numerico}] Peso: {peso_kg} kg")
                            ultimo_peso = peso_kg
                            tempo_ultima_exibicao = agora
                            tempo_estabilizacao = agora
                        else:
                            tempo_decorrido = agora - tempo_estabilizacao
                            if debug:
                                print(f"DEBUG: Peso igual ({peso_kg} kg). Tempo desde mudança: {tempo_decorrido:.2f}s. Último estabilizado: {peso_estabilizado}") #DEBUG
                            if tempo_decorrido >= 3:
                                if peso_estabilizado != peso_kg:
                                    peso_estabilizado = peso_kg
                                    print(f"Peso estabilizado: {peso_estabilizado} kg")
                                elif debug:
                                    print(f"DEBUG: Peso {peso_kg} kg já foi marcado como estável anteriormente.") #DEBUG
                    elif debug:
                        print(f"DEBUG: ATENÇÃO! Padrão regex não encontrado no buffer: '{buffer}'") #DEBUG

                    buffer = ""
                    tempo_ultimo_buffer_limpo = agora
                else:
                    if ord(char) >= 32 and ord(char) <= 126:    
                        buffer += char
                    
                    if len(buffer) > 50:
                        if debug:
                            print(f"DEBUG: Buffer muito grande, limpando: '{buffer}'")
                        buffer = ""
                        tempo_ultimo_buffer_limpo = agora
            # time.sleep(0.01)
            
    except serial.SerialException as e:
        print(f"Erro na comunicação serial: {e}")
    except KeyboardInterrupt:
        print("\nLeitura interrompida pelo usuário")
    finally:
        if 'ser' in locals() and ser.is_open:
            ser.close()
            print("Conexão serial fechada")

if __name__ == "__main__":
    porta = "COM3"  #"dados_balanca.txt" #COM3
    baudrate = 4800
    usar_mock = False
    debug = True
    
    ler_balanca_simples(porta, baudrate, usar_mock, debug)
