"""
ALUMNOS que han realizado la práctica:
Antonio Andrés Pérez DNI: 47580369Q Titulación: IST
Javier Zapatero Lera DNI: 54300753F Titulación: IST
Hemos realizado el programa con implementación de color (solo compatible con distribuciones UNIX o macOS)
"""


import getopt
import os
import signal
import socket
import sys
from threading import Thread

import game
import protocols
from game import Game


id = 1
games = {}
clients = {}


# --------------------------------------------------------------------------------------------- #
# Control de Arguments SERVER
# --------------------------------------------------------------------------------------------- #


def parse_args():
    args, trash = getopt.getopt(sys.argv[1:], 'p:', ["port="])  # version corta - y version larga --
    port = 7123
    for arg, val in args:
        if arg in ('-p', '--port'):
            port = val
    return port


def check_args(port):
    try:
        if int(port) > 1024:  # asi esta bien o ponemos int(port) >= 1024 ??????
            return True
        else:
            raise ValueError
    except ValueError:
        print(f"Port number {port} must be between 1024 and 65535")

    # --------------------------------------------------------------------------------------------- #
    # SERVER
    # --------------------------------------------------------------------------------------------- #


class Server(Thread):
    IP = '127.0.0.1'

    def __init__(self, port):
        Thread.__init__(self)
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)  # reuse socket (quitar en la entrega)
        self.socket.bind((Server.IP, port))
        self.socket.listen()

    def run(self):
        ip, port = self.socket.getsockname()
        print(f"Server started at {ip}:{port}")
        while True:
            client_socket, client_address = self.socket.accept()
            client_handler = ClientHandler(client_socket, client_address)
            client_handler.start()

    # --------------------------------------------------------------------------------------------- #
    # CLIENT HANDLER
    # --------------------------------------------------------------------------------------------- #


class ClientHandler(Thread):
    FILE_DIRECTORY = 'games_file'  # carpeta donde se guardan los archivos de los juegos

    def __init__(self, client_socket, client_address):
        Thread.__init__(self)
        self.client_socket = client_socket
        self.client_address = client_address
        # Cada hilo tiene su propio id
        self.name = ""
        self.game = None
        self.player = None
        self.end = False

    # --------------------------------------------------------------------------------------------- #
    # STATIC METHODS
    # --------------------------------------------------------------------------------------------- #

    @staticmethod
    def menu():
        menu = """Welcome to the server! Choose one of this options:
1.- Create new game
2.- Join game
3.- Load game
4.- Exit\n"""
        return menu

    @staticmethod
    def send_server_msg_to_one(text, to):
        msg = {'header': protocols.SERVER_MSG, 'message': text}
        protocols.send_one_msg(to, msg)

    @staticmethod
    def send_server_msg_to_all(text, players_list):
        for player in players_list:
            ClientHandler.send_server_msg_to_one(text, player['client_socket'])

    @staticmethod
    def games_for_join():  # devuelve las partidas que no estan llenas (esta fantasia nose si esta bien)
        return [game for game in games.values() if not game.can_join]

    # --------------------------------------------------------------------------------------------- #
    # JOIN & SEND FUNTIONS
    # --------------------------------------------------------------------------------------------- #

    def handle_join(self, msg):
        self.name = msg['name']
        print(f"(WELCOME) {self.name} has joined the server")
        self.send_welcome()

    def send_welcome(self):
        msg = {'header': protocols.WELCOME, 'menu': ClientHandler.menu(), 'options_range': [1, 2, 3, 4]}
        protocols.send_one_msg(self.client_socket, msg)  # envia el mensaje al cliente

    def send_load_game_answer(self, success, answer):
        msg = {'header': protocols.LOAD_GAME_ANSWER, 'success': success, 'answer': answer}
        protocols.send_one_msg(self.client_socket, msg)

    def send_choose_character(self):
        msg = {'header': protocols.CHOOSE_CHARACTER, 'menu': Game.print_available_characters(),
               'options_range': [1, 2, 3, 4]}
        protocols.send_one_msg(self.client_socket, msg)

    def send_games(self):
        menu = "**********************\n"  # información de los jugadores
        option_range = []
        for game in games.values():  # partidas que no estan llenas
            menu += f"{game.id}.-{game.info()}\n"
            option_range.append(game.id)
        menu += "**********************\n"
        msg = {'header': protocols.GAMES, 'menu': menu,
               'options_range': option_range}  # esto esta mal no lo entiendo javi
        protocols.send_one_msg(self.client_socket, msg)

    def send_dc_server(self):
        msg = {'header': protocols.DC_SERVER, 'answer': "You have been disconnected"}
        protocols.send_one_msg(self.client_socket, msg)
        self.client_socket.close()

    def send_end_game(self):
        global games, clients
        print(f"(GAMEEND) {self.name} game ended. They lost ")  # hay mas de 1 jugador como lo metemos
        msg = {'header': protocols.END_GAME, 'win': self.game.end_game}
        for player in self.game.all_players():
            protocols.send_one_msg(player['client_socket'], msg)
            # eliminar los clientes de la lista de clientes
            del clients[self.player['client_address']]
            # eliminar la partida de la lista de partidas
        if self.game.id in games:
            del games[self.game.id]
        self.end = True

    def send_your_turn(self, player):
        message = f"{self.player['character'].name()}. What do you want to do?"
        options_range = ["a", "g"]
        msg = {'header': protocols.YOUR_TURN, 'message': message, 'options_range': options_range}
        protocols.send_one_msg(player['client_socket'], msg)

    def send_valid_game(self, joined):
        msg = {'header': protocols.VALID_GAMES, 'joined': joined}
        protocols.send_one_msg(self.client_socket, msg)

    # --------------------------------------------------------------------------------------------- #
    # HANDLE FUNTIONS
    # --------------------------------------------------------------------------------------------- #

    def handle_load_game(self, msg):
        file_name = msg['file_name']
        if not file_name.endswith('.json') and not file_name.endswith('.txt'):
            self.send_load_game_answer(False, "File name must end with .json or .txt")
        else:
            file = os.path.join(ClientHandler.FILE_DIRECTORY, file_name)
            global id, games, clients
            try:
                self.game = Game.from_file(file, id)  # carga el juego
                id += 1
                games[self.game.id] = self.game  # agrega el juego a la lista de juegos
                clients[self.client_address] = self.game.id  # agrega él, id del juego a la lista de clientes
                self.player = self.game.player_in_turn()  # obtiene el jugador que tiene el turno
                self.player['name'] = self.name
                self.player['client'] = self.client_socket
                self.player['address'] = self.client_address
                self.game.creator = self.name
                self.game.n_players = 1
                self.send_load_game_answer(True,
                                           f"File found, the game has been loaded. The {self.player['character'].name()} character was assigned to you.")
                print(f"(LOAD) {self.name} File loaded from {file_name}")
            except FileNotFoundError:
                self.send_load_game_answer(False, "The file was not found ")

    def handle_server_option(self, msg):
        # storage in variables the part of message less the header, if the client selected the option 1, write in the
        # terminal the message "(CREATE="
        option = msg['option']
        stages = msg['stages']
        if option == 1:
            global id, games, clients
            print(f"(CREATE) {self.name} has created a new game")
            # crea un nuevo juego pasandole el id, el nombre del jugador
            self.game = Game(id, self.name, stages)  # crea el juego esta bien javi?
            games[id] = self.game  # agrega el juego a la lista de juegos
            clients[self.client_address] = id  # agrega él, id del juego a la lista de clientes
            id += 1
            self.send_choose_character()  # envia el mensaje al cliente
        elif option == 2:
            self.send_games()
        elif option == 3:
            pass  # Cargar partida de un fichero
        else:
            print(f"(EXIT) {self.name} disconnected")
            self.send_dc_server()  # mirar esto de donde sale!!!!!!!
            self.end = True

    def handle_character(self, msg):
        character = msg['option']
        self.player = self.game.add_player(character, self.name, self.client_socket, self.client_address)
        print(self.game.can_join())
        if self.game.can_join:
            print(f"(START) {self.name} has started the game")
            ClientHandler.send_server_msg_to_all("Texto a enviarle stages, jugadores.....", self.game.players_list)  # como se hace la parte de tecto de la info? llamamos la info de game.py?
            # sacamos el turno del jugador y lo enviamos como se hace esto?
            player = self.game.player_in_turn()
            # self.current_player = self.game.player_turn
            self.send_your_turn(player)
        else:
            ClientHandler.send_server_msg_to_one("We have wait the other gamers", self.player['client_socket'])

    def handle_character_command(self, msg):
        global result, file
        command = msg['command']
        file_name = msg['file_name']
        if file_name:
            if not file_name.endswith('.json') and not file_name.endswith('.txt'):
                ClientHandler.send_server_msg_to_one(
                    f"The name provided is not correct (the file needs to finish with txt or .json). Try again: ",
                    self.player['client_socket'])
            else:
                file = os.path.join(ClientHandler.FILE_DIRECTORY, file_name)
                result = self.game.player_execute_command(self.player, command, file)
                ClientHandler.send_server_msg_to_one(result, self.player['client_socket'])
                player = self.game.player_in_turn()  # el jugador que le toca el turno
                # Enviar un mensaje your_turn al jugador que le toca el turno
                # Cual tendriamos que usar?
                self.send_your_turn(player)
        else:
            result = self.game.player_execute_command(self.player, command)
            ClientHandler.send_server_msg_to_all(result, self.game.all_players())
        # si la partida ha terminado
        if self.game.is_over():
            # enviar un mensaje a todos los clientes de la partida con el mensaje (END_GAME) a todos los jugadores
            self.send_end_game()
        else:
            # extraer el jugador al que le toca el turno y enviarle un mensaje con el mensaje (YOUR_TURN)
            player = self.game.player_in_turn()  # el jugador que le toca el turno
            # Enviar un mensaje your_turn al jugador que le toca el turno
            self.send_your_turn(player)

    def handle_game_choice(self, msg):
        global games
        option = msg['option']
        # games_for_join = ClientHandler.games_for_join()
        # if 1 <= option <= len(games_for_join):
        if option in games:
            game = games[option]
            if game.can_join:
                global clients
                self.game = game
                clients[self.client_address] = self.game.id
                print(f"(JOIN).....")
                self.send_valid_game(True)  # enviar a true
                # si la partida se carga desde un fichero
                if game.from_file:  # ¿esto seria asi?
                    self.player = self.game.another_character()  # el jugador que se mete es el otro
                    # asignas valor a las  claves name, client, y address del self.player
                    self.player['name'] = self.player['name']
                    self.player['client_socket'] = self.player['client_socket']
                    self.player['client_address'] = self.player['client_address']
                    self.game.n_players += 1
                    # self.game.add_player(self.player, character)
                    # enviar un mensaje server
                    self.send_server_msg_to_one(f"{self.player['name']} has joined the game", self.player['client_socket'])
                    print(f"(START).....")
                    # extraer el jugador al que le toca el turno y enviarle un mensaje con el mensaje (SERVER) a
                    player = self.game.player_in_turn()  # el jugador que le toca el turno
                    # todos los jugadores con la información de la partida
                    self.send_server_msg_to_all(f"{self.player['name']} has joined the game", self.game.all_players())
                    # Enviar un mensaje your_turn al jugador que le toca el turno
                    self.send_your_turn(player)
                else:
                    # enviar un mensaje choose_character al cliente
                    self.send_choose_character()
            else:
                print(f"Entro por el False, recibo -> {game.can_join()}, está llena, salgo de la partida")
                self.send_valid_game(False)

    def handle_dc_me(self):
        global clients, games
        print(f"(EXIT) {self.name} disconnected.")
        if self.game:  # si el cliente se va con la partida iniciada
            msg = {'header': protocols.DC_SERVER, 'reason': f"{self.name} disconnected"}
            for player in self.game.all_players():
                if player != self.player:
                    print(f"(DC) {self.name} was disconnected.")
                    protocols.send_one_msg(player['client_socket'], msg)
                    # borrar al cliente del diccionario de clientes
                    del clients[player['client_address']]
            # borrar la partida del diccionario de partidas
            del games[self.game['name']]
            print(f"{self.name} was disconnected from {self.game['name']} game.")
            # borrar al cliente actual del diccionario de clientes
            del clients[self.player['client_address']]
            self.end = True

    # --------------------------------------------------------------------------------------------- #
    # MAIN HANDLER
    # --------------------------------------------------------------------------------------------- #

    def handle_msg(self, msg):
        header = msg['header']
        if header == protocols.JOIN:
            self.handle_join(msg)
        elif header == protocols.CHARACTER_COMMAND:
            self.handle_character_command(msg)  # Send_character, ese no es
        elif header == protocols.GAMES_CHOICE:
            self.handle_game_choice(msg)
        elif header == protocols.DC_ME:
            self.handle_dc_me()
        elif header == protocols.LOAD_GAME:
            self.handle_load_game(msg)
        elif header == protocols.SERVER_OPTION:
            self.handle_server_option(msg)
        elif header == protocols.CHARACTER:
            self.handle_character(msg)

    def run(self):
        while not self.end:
            try:
                msg = protocols.receive_one_msg(self.client_socket)  # recibe mensaje del cliente
                self.handle_msg(msg)  # maneja el mensaje
            except protocols.ConnectionClosed:  # si se cierra la connexion
                self.end = True
                print(f"{self.name} has left the game")
        self.client_socket.close()

    # --------------------------------------------------------------------------------------------- #
    # MAIN
    # --------------------------------------------------------------------------------------------- #


pid = os.getpid()
try:
    port = parse_args()
    port_ok = check_args(port)
    if port_ok:
        server = Server(int(port))
        server.start()
        stop = False
        while not stop:
            input()
            stop = True
    else:
        print("The format of the chosen port is incorrect."
              "You must provide an integer number bigger than 1024")
except getopt.GetoptError:
    print("invalid arguments")
except KeyboardInterrupt:
    print("\nThe server is closing.")
    sys.exit(0)
os.kill(pid, signal.SIGTERM)
