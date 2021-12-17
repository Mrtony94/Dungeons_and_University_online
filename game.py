"""
ALUMNOS que han realizado la práctica:
Antonio Andrés Pérez DNI: 47580369Q Titulación: IST
Javier Zapatero Lera DNI: 54300753F Titulación: IST
Hemos realizado el programa con implementación de color (solo compatible con distribuciones UNIX o macOS)
"""

import json
from character import *
from enemies import *


class Bcolors:
    CHARACTER = '\033[92m'  # GREEN
    STAGE = '\033[93m'  # YELLOW
    MONSTER = '\033[91m'  # RED
    WON = '\033[33m'  # NARANJA
    RESET = '\033[0m'  # RESET COLOR


class Game:
    PLAYERS = 2
    ENEMIES_BY_STAGE = 3
    MIN_STAGES = 1
    MAX_STAGES = 10
    FINALEXAM_LEVEL = 3
    AVAILABLE_CHARACTERS = [Bookworm, Worker, Procrastinator, Whatsapper]
    AVAILABLE_ENEMIES = [PartialExam, FinalExam, TheoricalClass, Teacher]

    def __init__(self, id, creator=None, stages=MIN_STAGES):
        self.id = id
        self.creator = creator
        self.stages = stages
        self.current_stage = 1
        self.players_list = []
        self.dead_players = []
        self.n_players = 0
        self.player_turn = 0  # index at players_list
        self.enemies_list = []
        self.enemies_turn = False
        self.end_game = False
        self.from_file = False

    # --------------------------------------------------------------------------------------------- #
    # @STATIC METHODS FUNCTIONS
    # --------------------------------------------------------------------------------------------- #

    @staticmethod
    def print_available_characters():
        result = f"\n{Bcolors.CHARACTER}************      AVAILABLE CHARACTERS      ************\n"
        for index, character_class in enumerate(Game.AVAILABLE_CHARACTERS):
            result += f"{index + 1}.- "
            result += str(character_class.print_info())
            result += "\n"
        result += f"********************************************************\n"
        return result

    @staticmethod
    def from_file(file, id):
        with open(file) as f:
            str_data = f.read()
        game = Game(id)
        dict_data = json.loads(str_data)
        game.stages = dict_data["stages"]
        game.current_stage = dict_data["current_stage"]
        game.players_list = dict_data["players_list"]
        game.dead_players = dict_data["dead_players"]
        game.n_players = dict_data["n_players"]
        game.player_turn = dict_data["player_turn"]
        game.enemies_turn = dict_data["enemies_turn"]
        game.end_game = dict_data["end_game"]
        game.from_file = dict_data["from_file"]

        return game

    # --------------------------------------------------------------------------------------------- #
    # EXTRA DEF
    # --------------------------------------------------------------------------------------------- #
    def finish_game(self):
        return self.end_game

    def info(self):
        return f"Player: {self.n_players} / {Game.PLAYERS}\n"

    def can_join(self):
        if self.n_players == Game.PLAYERS:
            return True
        else:
            return False

    def stages(self):
        return self.stages

    def add_player(self, character_option, name, client_socket, client_address):
        player = {'character': Game.AVAILABLE_CHARACTERS[character_option - 1](), 'name': name,
                  'client_socket': client_socket, 'client_address': client_address}
        self.players_list.append(player)
        self.n_players += 1
        if self.can_join():
            self.enemies_generate()
        return player

    # --------------------------------------------------------------------------------------------- #
    # PRINT DEF
    # --------------------------------------------------------------------------------------------- #

    def print_stage(self):
        result = f"{Bcolors.STAGE}\n      ***********************\n"\
                 f"      *       STAGE {self.current_stage}       *\n"\
                 f"      ***********************\n" \
                 f"\n"
        return result

    def print_characters_selection(self):
        result = f"{Bcolors.CHARACTER}\n***************PLAYERS*******************"
        for character in self.players_list:
            result += character.display_attributes()
        result += f"*****************************************"
        return result

    def print_enemies(self):
        result = f"{Bcolors.MONSTER}     ---- CURRENT MONSTER ----\n"\
                 f"+++++++++++++++++++++++++++++++++++++++++\n"
        for enemy in self.enemies_list:
            result += enemy.display_attributes()
        result += """+++++++++++++++++++++++++++++++++++++++++

"""
        return result

    # --------------------------------------------------------------------------------------------- #
    # CHARACTER DEF
    # --------------------------------------------------------------------------------------------- #

    def characters_selection(self):
        for player_number in range(1, Game.PLAYERS + 1):
            valid_character_selection = False
            while not valid_character_selection:
                try:
                    characters_selection = int(
                        input(f"{Bcolors.CHARACTER}Player {player_number}, {Bcolors.RESET}Please, choose a character "
                              f"(1-{len(Game.AVAILABLE_CHARACTERS)}): "))
                    if 1 <= characters_selection <= len(Game.AVAILABLE_CHARACTERS):
                        self.players_list.append(Game.AVAILABLE_CHARACTERS[characters_selection - 1]())
                    else:
                        raise ValueError
                except ValueError:
                    print(f"Incorrect choice. Choice must be between (1-{len(Game.AVAILABLE_CHARACTERS)}).")
                else:
                    valid_character_selection = True

    def player_execute_command(self, player, command, file_name=None):
        result = ""
        if command == "a":
            result += self.enemies_random_attack(player)  # player attacks enemy
            if len(self.enemies_list) == 0:
                result += f"current stages -->{self.current_stage} stages -->{self.stages}"
                if self.current_stage == self.stages:
                    self.end_game = True
                else:
                    self.change_turn()
                    self.current_stage += 1
                    for player in self.players_list:
                        player['character'].level_up()
                    self.enemies_generate()
                    result += self.print_stage()
            else:
                if self.player_turn == 1:
                    result += self.play_enemies_turn()
                    if len(self.players_list) != 0:  # si aún hay jugadores vivos
                        # poner la posición del turno a 0
                        self.player_turn = 0
                else:
                    self.change_turn()
        elif command == "s":
            result += self.save_file(file_name)
        return result

    # --------------------------------------------------------------------------------------------- #
    # ENEMIES DEF
    # --------------------------------------------------------------------------------------------- #

    def enemies_generate(self):
        for _ in range(Game.ENEMIES_BY_STAGE):
            valid_enemy = False
            while not valid_enemy:
                enemy_class = random.choice(Game.AVAILABLE_ENEMIES)
                if enemy_class != FinalExam or (
                        enemy_class == FinalExam and self.current_stage >= Game.FINALEXAM_LEVEL):
                    self.enemies_list.append(enemy_class(self.current_stage))
                    valid_enemy = True

    def enemies_random_attack(self, player):  # player no character

        name = player['name']
        result = f"{Bcolors.MONSTER}\n     -----------------------\n"\
                 f"     -    {name.upper()}'s TURN    -\n"\
                 "     -----------------------\n"
        character = player['character']
        enemy = random.choice(self.enemies_list)
        dmg_attack = character.attack(enemy)  # El jugador ataca al enemigo
        if enemy.hp == 0:
            self.enemies_list.remove(enemy)
            result += f"{Bcolors.CHARACTER}The {character.__class__.__name__} ({name}) "\
                     f"{Bcolors.RESET}did {dmg_attack} damage to {Bcolors.MONSTER}{enemy.__class__.__name__}. "\
                     f"{enemy.__class__.__name__} {Bcolors.RESET}dead\n"
        else:
            result += f"{Bcolors.CHARACTER}The {character.__class__.__name__} ({name}) "\
                     f"{Bcolors.RESET}did {dmg_attack} damage to {Bcolors.MONSTER}{enemy.__class__.__name__}. "\
                     f"{enemy.__class__.__name__} {Bcolors.RESET}has {enemy.hp} hp left\n"
        return result

    def play_enemies_turn(self):
        result = f"{Bcolors.MONSTER}\n     -----------------------\n"\
                 "     -    MONSTERS TURN    -\n"\
                 "     -----------------------\n"
        for enemy in self.enemies_list:
            player = random.choice(self.players_list)
            name = player['name']
            character = player['character']
            dmg_attack = enemy.attack(character)
            if character.hp > 0:
                result += f"{Bcolors.MONSTER}The {enemy.__class__.__name__} {Bcolors.RESET}did {dmg_attack}DMG to "\
                         f"{Bcolors.CHARACTER}{character.__class__.__name__} ({name})."\
                         f" {character.__class__.__name__} {Bcolors.RESET} has {character.hp} hp left\n"
            else:
                result += f"{Bcolors.MONSTER}The {enemy.__class__.__name__} {Bcolors.RESET}did {dmg_attack}DMG to "\
                         f"{Bcolors.CHARACTER}{character.__class__.__name__} ({name}). "\
                         f" {character.__class__.__name__} {Bcolors.RESET}left the game\n"
                self.dead_players.append(player)  # se añade al jugador muerto a la lista de muertos
                self.players_list.remove(player)  # se elimina al jugador de la lista de jugadores
            if len(self.players_list) == 0:
                self.end_game = True
                break
        return result

    # --------------------------------------------------------------------------------------------- #
    # PLAY GAME DEF
    # --------------------------------------------------------------------------------------------- #

    def change_turn(self):
        if self.player_turn == 0 and len(self.enemies_list) > 0:  # turno 1
            if len(self.players_list) == Game.PLAYERS:
                self.player_turn = 1
        else:  # turno 2
            self.player_turn = 0
        return self.player_turn

    def player_in_turn(self):  # DUDA
        if self.player_turn == 0:
            return self.players_list[0]
        else:
            return self.players_list[1]

    def another_character(self):  # ESTO DUDA JAVI
        if len(self.players_list) == Game.PLAYERS:
            # devuelve el jugador que no le toca el turno
            return self.players_list[0] if self.player_turn == 1 else self.players_list[1]
        else:
            return self.dead_players

    def all_players(self):
        return self.players_list + self.dead_players

    def player_wins(self):
        if len(self.players_list) == 0:
            result = "\n All characters have been defeated. Try again."
        else:
            result = f"{Bcolors.WON}\nAll the stages have been cleared. You won the game!{Bcolors.RESET}"
        return result

    # --------------------------------------------------------------------------------------------- #
    # FILE DEF
    # --------------------------------------------------------------------------------------------- #

    def save_file(self, file):
        global player
        try:
            game_info = {'stages': self.stages, 'current_stage': self.current_stage,
                         'player_turn': self.player_turn}

            players_list = []
            enemies_list = []
            dead_players = []

            for player in self.players_list:
                character = player['character']
                player_info = {'class': character.__class__.__name__, 'hp': character.hp}
                players_list.append(player_info)
            game_info['players_list'] = players_list

            for enemy in self.enemies_list:
                enemy_info = {'class': enemy.__class__.__name__, 'hp': enemy.hp}
                enemies_list.append(enemy_info)
            game_info['enemies_list'] = enemies_list

            for player_dead in self.dead_players:
                character = player['character']
                player_dead_info = {'class': character.__class__.__name__, 'hp': character.hp}
                dead_players.append(player_dead_info)
            game_info['dead_players'] = dead_players

            with open(file, 'w') as f:
                f.write(json.dumps(game_info))
            result = "The game has been saved!!\n"
        except FileNotFoundError:
            result = "The file was not found."
        return result
