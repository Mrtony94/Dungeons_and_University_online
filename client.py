"""
ALUMNOS que han realizado la práctica:
Antonio Andrés Pérez DNI: 47580369Q Titulación: IST
Javier Zapatero Lera DNI: 54300753F Titulación: IST
Hemos realizado el programa con implementación de color (solo compatible con distribuciones UNIX o macOS)
"""

import getopt
import socket
import sys
import game
import protocols


# --------------------------------------------------------------------------------------------- #
# Control de Arguments SERVER
# --------------------------------------------------------------------------------------------- #

def parse_args():
    args, trash = getopt.getopt(sys.argv[1:], 's:n:i:p:',
                                ["stages=", "name=", "ip=", "port="])  # version corta - y version larga --
    port = 7123
    ip = '127.0.0.1'
    name = ""
    stages = 1
    for arg, val in args:
        if arg in ('-s', '--stages'):
            stages = val
        elif arg in ('-n', '--name'):
            name = val
        elif arg in ('-i', '--ip'):
            ip = val
        elif arg in ('-p', '--port'):
            port = val
    return stages, name, ip, port


def check_args(stages, name, server_port):
    stages_ok = False
    name_ok = False
    server_port_ok = False
    try:
        if 1 <= int(stages) <= 10 and int(server_port) and name[0].isalpha() and name is not None:
            stages_ok = True
            name_ok = True
            server_port_ok = True
    except ValueError:
        print("Error en los argumentos introducidos")
    return stages_ok, name_ok, server_port_ok


# --------------------------------------------------------------------------------------------- #
# CLASE CLIENTE
# --------------------------------------------------------------------------------------------- #

class Client:
    def __init__(self, stages, name, server_ip, server_port):
        self.stages = stages
        self.name = name
        self.server_ip = server_ip
        self.server_port = server_port
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.connect((self.server_ip, self.server_port))
        self.end = False

    # --------------------------------------------------------------------------------------------- #
    # FUNCIONES @staticmethod
    # --------------------------------------------------------------------------------------------- #

    @staticmethod
    def get_int_option(text, option_range):
        option = None
        valid = False
        while not valid:
            print(text, end="")
            try:
                option = int(input("\nChoose your option >> "))
                if option in option_range:
                    valid = True
                else:
                    raise ValueError
            except ValueError:
                print(f"ERROR: Invalid option. Must be between {option} and {option_range[-1]}")
        return option

    @staticmethod
    def get_string_command(text, commands):
        command = None
        valid = False
        while not valid:
            print(text, end="")
            try:
                command = input(" ")
                if command in commands:
                    valid = True
                else:
                    raise ValueError
            except ValueError:
                print(f"ERROR: Invalid option. Must be between {commands}")
        return command

    # --------------------------------------------------------------------------------------------- #
    # JOIN
    # --------------------------------------------------------------------------------------------- #

    def send_join(self):
        msg = {'header': protocols.JOIN, 'name': self.name}
        protocols.send_one_msg(self.socket, msg)

    def handle_welcome(self, msg):
        option = Client.get_int_option(msg['menu'], msg['options_range'])
        if option == 3:
            file_name = input("What's the name of the game: ")
            self.send_load_game(file_name)
        else:
            self.send_server_option(option)

    # --------------------------------------------------------------------------------------------- #
    # FUNCIONES SEND
    # --------------------------------------------------------------------------------------------- #

    def send_load_game(self, file_name):
        msg = {'header': protocols.LOAD_GAME, 'file_name': file_name}
        protocols.send_one_msg(self.socket, msg)

    def send_server_option(self, option):
        msg = {'header': protocols.SERVER_OPTION, 'option': option, 'stages': self.stages}
        protocols.send_one_msg(self.socket, msg)

    def send_character(self, option):
        msg = {'header': protocols.CHARACTER, 'option': option}
        protocols.send_one_msg(self.socket, msg)

    def send_game_choice(self, option):
        msg = {'header': protocols.GAMES_CHOICE, 'option': option}
        protocols.send_one_msg(self.socket, msg)

    def send_dc_me_msg(self):
        msg = {'header': protocols.DC_ME}
        protocols.send_one_msg(self.socket, msg)

    def send_character_command(self, command, file_name=None):
        msg = {'header': protocols.CHARACTER_COMMAND, 'command': command, 'file_name': file_name}
        protocols.send_one_msg(self.socket, msg)

    # --------------------------------------------------------------------------------------------- #
    # FUNCIONES HANDLER
    # --------------------------------------------------------------------------------------------- #

    def handle_choose_character(self, msg):
        option = Client.get_int_option(msg['menu'], msg['options_range'])
        self.send_character(option)

    def handle_games(self, msg):
        option = Client.get_int_option(msg['menu'], msg['options_range'])
        self.send_game_choice(option)

    def handle_your_turn(self, msg):
        command = Client.get_string_command(msg['message'], msg['options_range'])
        if command == 's':
            file_name = input("what's the name of the file: ")
            if file_name == 'cancel':
                print("The game was not saved.")
                self.handle_your_turn(msg)
            else:
                self.send_character_command(command, file_name)
        else:
            self.send_character_command(command)

    def handle_valid_game(self, msg):
        joined = msg['joined']
        if not joined:
            print("Game is not valid. Bye!")
            self.end = True

    def handle_end_game(self, msg):
        win = msg['win']
        if win:
            print(f"All the stages haven been cleared. {game.Bcolors.WON}YOU WON THE GAME\n{game.Bcolors.RESET}")
        else:
            print(f"{game.Bcolors.MONSTER}All characters have been defeated. {game.Bcolors.RESET}Try again\n")
        self.end = True

    def handle_dc_server(self, msg):
        reason = msg['reason']
        print(reason)
        self.end = True

    def handle_load_game_answer(self, msg):
        valid = msg['valid']
        message = msg['message']
        if valid:
            print(message)
        else:
            print(message, end="")
            file_name = input("Try again: ")
            self.send_load_game(file_name)

    @staticmethod
    def handle_server_msg(msg):
        text = msg['message']
        print(text)

    # --------------------------------------------------------------------------------------------- #
    # MANEJADO DE MENSAJES RECIBIDOS
    # --------------------------------------------------------------------------------------------- #

    def handle_msg(self, msg):
        header = msg['header']
        if header == protocols.WELCOME:
            self.handle_welcome(msg)
        elif header == protocols.CHOOSE_CHARACTER:
            self.handle_choose_character(msg)
        elif header == protocols.GAMES:
            self.handle_games(msg)
        elif header == protocols.YOUR_TURN:
            self.handle_your_turn(msg)
        elif header == protocols.VALID_GAMES:
            self.handle_valid_game(msg)
        elif header == protocols.END_GAME:
            self.handle_end_game(msg)
        elif header == protocols.DC_SERVER:
            self.handle_dc_server(msg)
        elif header == protocols.LOAD_GAME_ANSWER:
            self.handle_load_game_answer(msg)
        elif header == protocols.SERVER_MSG:
            self.handle_server_msg(msg)
        else:
            print(f"Unknown header: {header}")
            self.end = True

    def run(self):
        self.send_join()
        while not self.end:
            try:
                msg = protocols.receive_one_msg(self.socket)
                self.handle_msg(msg)
            except KeyboardInterrupt:
                self.send_dc_me_msg()
                self.end = True
            except protocols.ClosedConnection as e:
                print(e)
                self.end = True
        self.socket.close()


try:
    stages, name, server_ip, server_port = parse_args()
    stages_ok, name_ok, server_port_ok = check_args(stages, name, server_port)
    if stages_ok and name_ok and server_port_ok:
        client = Client(stages, name, server_ip, int(server_port))
        Client.run(client)
    else:
        if not stages_ok:
            print(f"the number os stages must be between {game.Game.MIN_STAGES} and {game.Game.MAX_STAGES}")
        if not name_ok:
            print(f"The format os the chosen name is incorrect. you must provide a name that starts with a letter ")
        if not server_port_ok:
            print(f"The port must be between 1024 and 65535")
except getopt.GetoptError:
    print("Invalid arguments")
except (ConnectionRefusedError, TimeoutError) as err:
    print(f"Could not connect to the server. Are you sure you have provided the correct ip and port?")
