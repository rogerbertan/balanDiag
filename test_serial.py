import serial
import time

now = time.monotonic()

def ler_peso_da_balanca(porta_serial, baudrate, tamanho_esperado):
    ser = serial.Serial(
                port=porta_serial,
                baudrate=baudrate,
                bytesize=serial.SEVENBITS,
                parity=serial.PARITY_EVEN,
                stopbits=serial.STOPBITS_ONE,
                timeout=1
            )

    buffer = ""
    while True:
        byte = ser.read().decode(errors='ignore')

        if byte in ('\r', ' '):  # fim da linha
            linha = buffer.strip()
            buffer = ""

            if len(linha) == tamanho_esperado:
                print("Linha recebida:", linha)
                peso = extrair_peso(linha)
                print("Peso:", peso)
                print("Tempo: ", time.monotonic() - now)
            else:
                print("Linha descartada:", linha)
        else:
            buffer += byte


def extrair_peso(linha):
    peso_str = linha[6:11]  # mesmo que getBeginIndex() e getEndIndex()
    peso = int(peso_str)
    
    id_char = linha[2]  # equivalente a getIdentifier()
    if id_char in ['z', 'r']:
        peso *= -1

    return peso

ler_peso_da_balanca('COM3', 4800, 11)