"""
ALUMNOS que han realizado la práctica:
Antonio Andrés Pérez DNI: 47580369Q Titulación: IST
Javier Zapatero Lera DNI: 54300753F Titulación: IST
Hemos realizado el programa con implementación de color (solo compatible con distribuciones UNIX o macOS)
"""

import json
import struct

# MSG
JOIN = 'JOIN'  # Mensaje que le envía el cliente al servidor para pedirle el menú principal.
WELCOME = 'WELCOME'  # Mensaje que le envía el servidor al cliente una vez se conecta

LOAD_GAME = 'LOAD_GAME'  # Mensaje que le envía el cliente al servidor para cargar una partida
LOAD_GAME_ANSWER = 'LOAD_GAME_ANSWER'  # Mensaje que le envía el servidor al cliente con el resultado de cargar una partida

CHOOSE_CHARACTER = 'CHOOSE_CHARACTER'  # Mensaje que le envía el servidor al cliente cuando crea una partida o se une a una partida para seleccionar un personaje

SERVER_MSG = 'SERVER_MSG'  # Mensaje que le envía el servidor al cliente con texto.

YOUR_TURN = 'YOUR_TURN'  # Mensaje que le envía el servidor al cliente para decirle que es su turno y pedirle una acción.

# SEND's

CHARACTER_COMMAND = 'CHARACTER_COMMAND'  # Mensaje que el cliente al servidor con el comando seleccionado.
GAMES = 'GAMES'  # Mensaje que le envía el servidor al cliente con la lista de partidas disponibles.
GAMES_CHOICE = 'GAMES_CHOICE'  # Mensaje que le envía el cliente al servidor con la partida seleccionada
VALID_GAMES = 'VALID_GAMES'  # Mensaje que envía el servidor al cliente si se ha podido unir a la partida seleccionada
END_GAME = 'END_GAME'  # Mensaje que envía el servidor al cliente cuando una partida finalizar (Tanto si es por
# derrota de los jugadores como por victoria).
DC_ME = 'DC_ME'  # Mensaje que le envía el cliente al servidor para informarle de que se desconecta. El servidor debe
# desconectar a todos los jugadores que están en esa partida.
DC_SERVER = 'DC_SERVER'  # Mensaje que envía el servidor al cliente para desconectarlo.
SERVER_OPTION = 'SERVER_OPTION'  # Mensaje que le envía el cliente al servidor con una opción del menú anterior
CHARACTER = 'CHARACTER'  # Mensaje que le envía el cliente al servidor cuando se selecciona un personaje


class ConnectionClosed(Exception):  # CAMBIAR NOMBRE closedconnection

    def __init__(self):
        super().__init__('Connection closed by other')


class InvalidProtocol(Exception):

    def __init__(self):
        super().__init__("Unknown message received")


def send_one_msg(sock, msg):  # to --> message(dic)
    data_encode = json.dumps(msg).encode()  # transforma el diccionario en un string y lo codifica en 1 y 0
    length = len(data_encode)  # obtiene el tamaño del string
    header = struct.pack('!I', length)  # codifica el tamaño en un formato de 4 bytes
    sock.sendall(header)  # envía el tamaño
    sock.sendall(data_encode)  # envía el string


def receive_one_msg(sock):  # from --> message(dic)
    header_buffer = receive_all(sock, 4)  # recibe el tamaño del string
    # recibe el tamaño del string, ponemos 4 porque se refiere a numeros en binario de 0 a 9
    if not header_buffer:  # si no hay datos
        raise ConnectionClosed()
    else:
        header = struct.unpack('!I', header_buffer)  # decodifica el tamaño
        length = header[0]  # obtiene el tamaño del string
        data_encoded = receive_all(sock, length)  # recibe el string
        msg = json.loads(data_encoded.decode())  # decodifica el string proceso inverso a dumps
        return msg


def receive_all(sock, length):  # from --> message(dic)
    buffer = b''  # crea un buffer vacio
    while length != 0:  # mientras el tamaño del buffer sea menor al tamaño del string
        buffer_aux = sock.recv(length)  # recibe el string
        if not buffer_aux:  # si no hay datos
            return None
        buffer += buffer_aux  # agrega los datos al buffer
        length -= len(buffer_aux)  # resta el tamaño del buffer al tamaño del string
    return buffer
