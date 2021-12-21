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
import errno

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
    args, trash = getopt.getopt(sys.argv[1:], 'p:', ["port="])
    port = 7123
    for arg, val in args:
        if arg in ('-p', '--port'):
            port = val
    return port


def check_args(port):
    try:
        if int(port) > 1024:
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
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)  # Reuse socket
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
    FILE_DIRECTORY = 'games_file'

    def __init__(self, client_socket, client_address):
        Thread.__init__(self)
        self.client_socket = client_socket
        self.client_address = client_address
        self.name = ""
        self.game = None
        self.player = None
        self.end = False

    # --------------------------------------------------------------------------------------------- #
    # STATIC METHODS
    # --------------------------------------------------------------------------------------------- #

    @staticmethod
    def menu():
        menu = f"""{game.Bcolors.WON}
Welcome to the server! Choose one of this options:{game.Bcolors.RESET}

MENU:       

1.- Create new game
2.- Join game
3.- Load game
4.- Exit
"""
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
    def games_for_join():
        return [game for game in games.values() if not game.can_join]

    # --------------------------------------------------------------------------------------------- #
    # JOIN & SEND FUNCTIONS
    # --------------------------------------------------------------------------------------------- #

    def handle_join(self, msg):
        self.name = msg['name']
        print(f"(WELCOME) {self.name} has joined the server")
        self.send_welcome()

    def send_welcome(self):
        msg = {'header': protocols.WELCOME, 'menu': ClientHandler.menu(), 'options_range': [1, 2, 3, 4]}
        protocols.send_one_msg(self.client_socket, msg)

    def send_load_game_answer(self, valid, message):
        msg = {'header': protocols.LOAD_GAME_ANSWER, 'valid': valid, 'message': message}
        protocols.send_one_msg(self.client_socket, msg)

    def send_choose_character(self):
        msg = {'header': protocols.CHOOSE_CHARACTER, 'menu': Game.print_available_characters(),
               'options_range': [1, 2, 3, 4]}
        protocols.send_one_msg(self.client_socket, msg)

    def send_games(self):
        if games:
            menu = f"""
GAMES
**********************\n"""
        else:
            menu = """**********************
There are not GAMES
**********************
"""
            self.send_server_msg_to_one(menu, self.client_socket)
            self.send_dc_server()

        option_range = []
        for game in games.values():
            menu += f"{game.id}.-{game.info()}\n"
            option_range.append(game.id)
        menu += "**********************\n"
        msg = {'header': protocols.GAMES, 'menu': menu,
               'options_range': option_range}
        protocols.send_one_msg(self.client_socket, msg)

    def send_dc_server(self):
        msg = {'header': protocols.DC_SERVER, 'reason': "You have been disconnected"}
        protocols.send_one_msg(self.client_socket, msg)
        self.client_socket.close()

    def send_end_game_all_players(self):
        global games, clients
        print(f"(GAME_END) {self.name} game ended.")
        msg = {'header': protocols.END_GAME, 'win': self.game.player_wins()}
        for player in self.game.all_players():
            protocols.send_one_msg(player['client_socket'], msg)
            if clients[player['client_address']]:
                clients.pop(player['client_address'])
        if self.game.id in games:
            del games[self.game.id]
        self.end = True

    def send_your_turn(self, player):
        message = f"The {game.Bcolors.CHARACTER}{player['character'].name()} ({player['name']}):{game.Bcolors.RESET} What are you going to do? >> "
        options_range = ["a", "s"]
        msg = {'header': protocols.YOUR_TURN, 'message': message, 'options_range': options_range}
        protocols.send_one_msg(player['client_socket'], msg)

    def send_valid_game(self, joined):
        msg = {'header': protocols.VALID_GAMES, 'joined': joined}
        protocols.send_one_msg(self.client_socket, msg)

    # --------------------------------------------------------------------------------------------- #
    # HANDLE FUNCTIONS
    # --------------------------------------------------------------------------------------------- #

    def handle_load_game(self, msg):
        global text
        file_name = msg['file_name']
        if not file_name.endswith('.json') and not file_name.endswith('.txt'):
            self.send_load_game_answer(False, "File name must end with .json or .txt")
        else:
            file = os.path.join(ClientHandler.FILE_DIRECTORY, file_name)
            global id, games, clients
            try:
                self.game = Game.from_file(file, id)
                id += 1
                games[self.game.id] = self.game
                clients[self.client_address] = self.game.id
                self.player = self.game.player_in_turn()
                self.player['name'] = self.name
                self.player['client_socket'] = self.client_socket
                self.player['client_address'] = self.client_address
                self.game.creator = self.name
                self.game.n_players = 1
                text = f"{game.Bcolors.STAGE}File found, the game has been loaded. The {self.player['name']} character was assigned to you.{game.Bcolors.RESET}"
                text += "\nWaiting for other player to join the game"
                self.send_load_game_answer(True, text)
                print(f"(LOAD) {self.name} File loaded from {file_name}")
            except FileNotFoundError:
                text = f"File not found, please check the file name and try again."
                self.send_load_game_answer(False, text)

    def handle_server_option(self, msg):
        option = msg['option']
        stages = msg['stages']
        if option == 1:
            global id, games, clients
            print(f"(CREATE) {self.name} has created a new game")
            self.game = Game(id, self.name, stages)
            games[id] = self.game
            clients[self.client_address] = id
            id += 1
            self.send_choose_character()
        elif option == 2:
            self.send_games()
        elif option == 3:
            pass
        else:
            print(f"(EXIT) {self.name} disconnected")
            self.send_dc_server()
            self.end = True

    def handle_character(self, msg):
        global clients, games
        option = msg['option']
        self.player = self.game.add_player(option, self.name, self.client_socket, self.client_address)
        if self.game.can_join():
            print(f"(START) {self.name} has started the game")
            ClientHandler.send_server_msg_to_all(f"{self.game.print_stage()}{self.game.print_enemies()}",
                                                 self.game.all_players())
            ClientHandler.send_server_msg_to_all(
                f"A game with {self.game.stages} stage(s) will be set up for {self.game.PLAYERS} players.\n",
                self.game.all_players())
            player = self.game.player_in_turn()
            self.send_your_turn(player)
        else:
            ClientHandler.send_server_msg_to_one("\nWaiting for other players to join the game",
                                                 self.player['client_socket'])

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
                try:
                    os.mkdir(ClientHandler.FILE_DIRECTORY)
                except OSError as e:
                    if e.errno != errno.EEXIST:
                        raise
                result = self.game.player_execute_command(self.player, command, file)
                ClientHandler.send_server_msg_to_one(result, self.player['client_socket'])
                player = self.game.player_in_turn()
                self.send_your_turn(player)
        else:
            result = self.game.player_execute_command(self.player, command)
            ClientHandler.send_server_msg_to_all(result, self.game.all_players())
            if self.game.finish_game():
                self.send_end_game_all_players()
            else:
                player = self.game.player_in_turn()
                self.send_your_turn(player)

    def handle_game_choice(self, msg):
        global games
        option = msg['option']
        if option in games:
            game = games[option]
            if game.can_join():
                self.send_valid_game(False)
            else:
                global clients
                self.game = game
                clients[self.client_address] = self.game.id
                print(f"(JOIN) {self.name} joined {game.creator}'s game")
                self.send_valid_game(True)
                if game.from_file:
                    self.player = self.game.another_character()
                    self.player['name'] = self.name
                    self.player['client_socket'] = self.client_socket
                    self.player['client_address'] = self.client_address
                    self.game.n_players += 1
                    self.send_server_msg_to_one(f"{self.player['name']} has joined the game",
                                                self.player['client_socket'])
                    print(f"(START) {game.players_names()} continued a game")

                    player = self.game.player_in_turn()
                    ClientHandler.send_server_msg_to_all(f"{self.game.print_stage()}{self.game.print_enemies()}",
                                                         self.game.all_players())
                    self.send_your_turn(player)
                else:
                    self.send_choose_character()
        else:
            self.send_valid_game(False)

    def handle_dc_me(self):
        global clients, games
        print(f"(EXIT) {self.name} disconnected.")
        if self.game:  # si el cliente se va con la partida iniciada
            msg = {'header': protocols.DC_SERVER, 'reason': f"{self.name} disconnected"}
            for player in self.game.all_players():
                if player != self.player:
                    print(f"(DC_ME) {self.name} was disconnected.")
                    protocols.send_one_msg(player['client_socket'], msg)
                    del clients[player['client_address']]
            del games[self.game.id]
            print(f"{self.name} was disconnected from {self.game.id} game.")
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
            self.handle_character_command(msg)
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
                msg = protocols.receive_one_msg(self.client_socket)
                self.handle_msg(msg)
            except protocols.ClosedConnection:
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
os.kill(pid, signal.SIGTERM)
