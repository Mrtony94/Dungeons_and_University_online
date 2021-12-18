import os
import getopt
from threading import Thread
import socket
from game import Game
import protocol


MIN_MENU_OPTION = 1
MAX_MENU_OPTION = 4
DIRECTORY = "games"

id = 1
games = {}
client_game = {}
clients_names = {}  # Added

client_threads_running = []


def parse_args():
    import sys

    opts, _ = getopt.getopt(sys.argv[1:], "p:", ["port"])

    port = 7123
    for o, a in opts:
        if o in ("-p", "--port"):
            port = a

    return port


def check_args(port):
    port_ok = True

    try:
        int(port)
    except ValueError:
        port_ok = False

    return port_ok


def menu():
    return """Welcome to the server. Choose one of this options:
1.- Create game
2.- Join game
3.- Load game
4.- Exit
"""


def handle_join(message, client_socket, client_address):
    global clients_names

    name = message["name"]
    clients_names[client_address] = name
    print(f"(WELCOME) {name} joined the server")

    send_welcome(client_socket)


def send_welcome(client_socket):
    message = {"header": protocol.WELCOME, "menu": menu(),
               "options_range": [*range(MIN_MENU_OPTION, MAX_MENU_OPTION + 1, 1)]}
    protocol.send_one_message(client_socket, message)


def handle_load_game(message, client_socket, client_address):
    global id, games, client_game, clients_names

    file_name = message["file_name"]

    valid = False
    if not (file_name.endswith(".txt") or file_name.endswith(".json")):
        answer = "The name provided is not correct (the file needs to finish with .txt or .json). "
    else:
        file = os.path.join(DIRECTORY, file_name)
        try:
            game = Game.load_from_file(file, id)
            id += 1
            games[game.id] = game
            client_game[client_address] = game.id
            player = game.first_player()
            name = clients_names[client_address]
            player['name'] = name
            player['client_socket'] = client_socket
            player['client_address'] = client_address
            game.creator = name
            game.current_number_of_players = 1
            valid = True
            answer = f"File found, the game has been loaded. " \
                     f"{player['character'].name()} was assigned to you"
            answer += "\nWaiting for other player to join the game"
            print(f"(LOAD) {name} loads a game from {file_name}")
        except FileNotFoundError:
            answer = "The file was not found. "

    send_load_game_answer(client_socket, valid, answer)


def send_load_game_answer(client_socket, valid, answer):
    message = {"header": protocol.LOAD_GAME_ANSWER, "valid": valid, "answer": answer}
    protocol.send_one_message(client_socket, message)


def handle_server_option(message, client_socket, client_address):
    global id, games, client_game, clients_names

    option = message["option"]
    stages = message["stages"]

    name = clients_names[client_address]
    stop = False
    if option == 1:
        print(f"(CREATE) {name} created a game")
        game = Game(id, name, stages)
        id += 1
        games[game.id] = game
        client_game[client_address] = game.id

        send_choose_character(client_socket)
    elif option == 2:
        send_games(client_socket, client_address)
    elif option == 3:
        pass  # Comment
    else:  # option == 4
        print(f"(EXIT) {name} disconnected")

        send_dc_server(client_socket)
        stop = True
    return stop


def send_choose_character(client_socket):
    message = {"header": protocol.CHOOSE_CHARACTER, "menu": Game.available_characters(),
               "options_range": [*range(1, len(Game.AVAILABLE_CHARACTERS) + 1, 1)]}
    protocol.send_one_message(client_socket, message)


def send_dc_server(client_socket):
    message = {"header": protocol.DC_SERVER, "reason": "Bye!"}
    protocol.send_one_message(client_socket, message)


def send_games(client_socket, client_address):
    global games, clients_names

    options_range = []
    menu = "********************************************\n"
    for game in games.values():
        menu += f"{game.id}.- {game.info()}\n"
        options_range.append(game.id)
    menu += "********************************************\n"
    if options_range:
        message = {"header": protocol.GAMES, "menu": menu, "options_range": options_range}
        protocol.send_one_message(client_socket, message)
    else:
        send_server_message_to_one("Sorry, there aren't games to join", client_socket)
        send_dc_server(client_socket)
        del clients_names[client_address]


def handle_character(message, client_socket, client_address):
    global games, client_game, clients_names

    option = message["option"]

    name = clients_names[client_address]
    game_id = client_game[client_address]
    game = games[game_id]
    game.add_player(option, name, client_socket, client_address)
    if game.is_full():
        print(f"(START) {game.players_names()} started a game")
        player = game.player_in_turn()
        send_server_message_to_all(game.summary(), game.all_players())
        send_server_message_to_all(game.stage_info(), game.all_players())
        send_your_turn(game.current_turn_info(), player['client_socket'])
    else:
        send_server_message_to_one("Waiting for other players to join the game", client_socket)


def send_server_message_to_one(text, to):
    message = {"header": protocol.SERVER_MESSAGE, "text": text}
    protocol.send_one_message(to, message)


def send_server_message_to_all(text, players):
    for player in players:
        send_server_message_to_one(text, player['client_socket'])


def send_your_turn(text, to):
    message = {"header": protocol.YOUR_TURN, "text": text, "commands": Game.AVAILABLE_COMMANDS}
    protocol.send_one_message(to, message)


def handle_character_command(message, client_socket, client_address):
    global games, client_game

    command = message["command"]
    file_name = message["file_name"]

    game_id = client_game[client_address]
    game = games[game_id]
    stop = False
    if command == "s":
        if not (file_name.endswith(".txt") or file_name.endswith(".json")):
            send_server_message_to_one("The name provided is not correct "
                                       "(the file needs to finish with .txt or .json). ", client_socket)
        else:
            file = os.path.join(DIRECTORY, file_name)
            result = game.player_save_file(file)
            send_server_message_to_one(result, client_socket)
        send_your_turn(game.current_turn_info(), client_socket)
    else:
        result = game.player_attack()
        send_server_message_to_all(result, game.all_players())
        if game.has_finished():
            send_end_game(game)
            stop = True
        else:
            player = game.player_in_turn()
            send_your_turn(game.current_turn_info(), player['client_socket'])
    return stop


def send_end_game(game):
    global games, client_game

    print(f"(GAMEEND) {game.players_names()} game ended. They ", end="")
    if game.players_wins():
        print("won.")
    else:
        print("lost.")
    message = {"header": protocol.END_GAME, "win": game.players_wins()}
    for player in game.all_players():
        protocol.send_one_message(player['client_socket'], message)
        if client_game[player['client_address']]:
            del client_game[player['client_address']]
    if games[game.id]:
        del games[game.id]


def handle_game_choice(message, client_socket, client_address):
    global games, clients_names

    option = message["option"]

    name = clients_names[client_address]
    if option in games:
        game = games[option]
        if game.is_full():
            send_valid_game(client_socket, False)
            del clients_names[client_address]
        else:
            client_game[client_address] = game.id
            print(f"(JOIN) {name} joined {game.creator}'s game")
            send_valid_game(client_socket, True)
            if game.is_loaded_from_file:
                player = game.second_player()
                player['name'] = name
                player['client_socket'] = client_socket
                player['client_address'] = client_address
                game.current_number_of_players += 1
                send_server_message_to_one(f"Game was loaded from file. "
                                           f"{player['character'].name()} was assigned to you", client_socket)
                print(f"(START) {game.players_names()} continued a game")

                player = game.player_in_turn()
                send_server_message_to_all(game.stage_info(), game.all_players())
                send_your_turn(game.current_turn_info(), player['client_socket'])
            else:
                send_choose_character(client_socket)
    else:
        send_valid_game(client_socket, False)
        del clients_names[client_address]


def send_valid_game(client_socket, joined):
    message = {"header": protocol.VALID_GAME, "joined": joined}
    protocol.send_one_message(client_socket, message)


def handle_dc_me(client_address):
    global games, client_game, clients_names

    name = clients_names[client_address]

    print(f"(EXIT) {name} disconnected")
    if client_address in client_game:
        game_id = client_game[client_address]
        game = games[game_id]

        reason = f"{name} disconnected. The game can not continue."
        message = {"header": protocol.DC_SERVER, "reason": reason}
        for player in game.all_players():
            if player['name'] != name:
                print(f"(DC) {player['name']} was disconnected")
                protocol.send_one_message(player['client_socket'], message)
                if client_game[player['client_address']]:
                    del client_game[player['client_address']]
        if games[game.id]:
            del games[game.id]

        del client_game[client_address]


class ClientThread(Thread):
    def __init__(self, client_socket, client_address):
        Thread.__init__(self)
        self.client_socket = client_socket
        self.client_address = client_address
        self.stop = False

    def handle_message(self, message):
        header = message["header"]
        if header == protocol.JOIN:
            handle_join(message, self.client_socket, self.client_address)
        elif header == protocol.LOAD_GAME:
            handle_load_game(message, self.client_socket, self.client_address)
        elif header == protocol.SERVER_OPTION:
            self.stop = handle_server_option(message, self.client_socket, self.client_address)
        elif header == protocol.CHARACTER:
            handle_character(message, self.client_socket, self.client_address)
        elif header == protocol.CHARACTER_COMMAND:
            self.stop = handle_character_command(message, self.client_socket, self.client_address)
        elif header == protocol.GAME_CHOICE:
            handle_game_choice(message, self.client_socket, self.client_address)
        elif header == protocol.DC_ME:
            handle_dc_me(self.client_address)
            self.stop = True
        else:
            print("ERROR: Invalid message received")

    def run(self):
        while not self.stop:
            try:
                message = protocol.recv_one_message(self.client_socket)
                self.handle_message(message)
            except OSError:
                print(f"ClientThread is closing...")
                self.stop = True
            except protocol.ConnectionClosed:
                self.stop = True


class ServerThread(Thread):
    IP = "127.0.0.1"

    @staticmethod
    def close_client_connections():
        global client_threads_running
        for th in client_threads_running:
            th.client_socket.close()

    def __init__(self, port):
        Thread.__init__(self)
        self.stop = False
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket.bind((ServerThread.IP, port))
        self.socket.listen()

    def run(self):
        global client_threads_running
        while not self.stop:
            try:
                client_socket, client_address = self.socket.accept()
                client_handler = ClientThread(client_socket, client_address)
                client_handler.start()

                client_threads_running.append(client_handler)
            except OSError:
                self.stop = True
                ServerThread.close_client_connections()
        print("Server closed")


server = None
try:
    port = parse_args()
    port_ok = check_args(port)
    if port_ok:
        server = ServerThread(int(port))
        server.start()

        stop = False
        while not stop:
            input()
            stop = True
        server.socket.close()
    else:
        print("The format of the chosen port is incorrect. You must provide an integer number bigger than 1024")
except getopt.GetoptError:
    print("Invalid arguments")
except KeyboardInterrupt:
    if server:
        server.socket.close()
