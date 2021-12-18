import json

from characters import *
from enemies import *


class Game:
    PLAYERS = 2
    MIN_STAGES = 1
    MAX_STAGES = 10
    ENEMIES_BY_STAGE = 3
    FINALEXAM_LEVEL = 3
    AVAILABLE_CHARACTERS = [Bookworm, Worker, Procrastinator, Whatsapper]
    AVAILABLE_ENEMIES = [PartialExam, FinalExam, TheoreticalClass, Teacher]
    ATTACK_COMMAND = "a"
    SAVE_FILE_COMMAND = "s"
    AVAILABLE_COMMANDS = [ATTACK_COMMAND, SAVE_FILE_COMMAND]

    @staticmethod
    def available_characters():
        result = "*********** AVAILABLE CHARACTERS ***********\n"
        for index, character_class in enumerate(Game.AVAILABLE_CHARACTERS):
            result += f"{index + 1}.- "
            result += character_class.info()
            result += "\n"
        result += "********************************************\n"
        return result

    def __init__(self, id, creator=None, stages=MIN_STAGES):
        self.id = id
        self.creator = creator
        self.stages = stages
        self.current_stage = 1
        self.alive_players = []
        self.dead_players = []
        self.enemies = []
        self.finish = False
        self.current_turn = 0
        self.current_number_of_players = 0
        self.is_loaded_from_file = False

    def __str__(self):
        return f"Creator: {self.creator} | Stages: {self.stages} | Current stage: {self.current_stage} | " \
               f"Alive players: {self.alive_players} | Dead players: {self.dead_players} | Enemies: {self.enemies} | " \
               f"Current turn: {self.current_turn} | Current number of players: {self.current_number_of_players} | " \
               f"Is loaded from file?: {self.is_loaded_from_file}"

    def __repr__(self):
        return self.__str__()

    def info(self):
        return f"Players: {self.current_number_of_players}/{Game.PLAYERS}"

    def is_full(self):
        return self.current_number_of_players == Game.PLAYERS

    def add_player(self, character_option, name, client_socket, client_address):
        player = {'character': Game.AVAILABLE_CHARACTERS[character_option - 1](),
                  'name': name,
                  'client_socket': client_socket,
                  'client_address': client_address}
        self.alive_players.append(player)
        self.current_number_of_players += 1
        if self.is_full():
            self.enemies_generate()
        return player

    @staticmethod
    def load_from_file(file, id):
        with open(file) as f:
            str_data = f.read()

        game = Game(id)
        dict_data = json.loads(str_data)
        game.stages = dict_data['stages']
        game.current_stage = dict_data['current_stage']
        game.current_turn = dict_data['current_turn']

        for player_dict in dict_data['alive_players']:
            character_dict = player_dict['character']
            if character_dict['class'] == Bookworm.__name__:
                game.alive_players.append({'character': Bookworm(character_dict['hp'])})
            elif character_dict['class'] == Worker.__name__:
                game.alive_players.append({'character': Worker(character_dict['hp'])})
            elif character_dict['class'] == Procrastinator.__name__:
                game.alive_players.append({'character': Procrastinator(character_dict['hp'])})
            else:  # character_dict['class'] == Whatsapper.__class__.__name__:
                game.alive_players.append({'character': Whatsapper(character_dict['hp'])})

        for player_dict in dict_data['dead_players']:
            character_dict = player_dict['character']
            if character_dict['class'] == Bookworm.__name__:
                game.dead_players.append({'character': Bookworm(character_dict['hp'])})
            elif character_dict['class'] == Worker.__name__:
                game.dead_players.append({'character': Worker(character_dict['hp'])})
            elif character_dict['class'] == Procrastinator.__name__:
                game.dead_players.append({'character': Procrastinator(character_dict['hp'])})
            else:  # character_dict['class'] == Whatsapper.__class__.__name__:
                game.dead_players.append({'character': Whatsapper(character_dict['hp'])})

        for enemy_dict in dict_data['enemies']:
            if enemy_dict['class'] == PartialExam.__name__:
                game.enemies.append(PartialExam(enemy_dict['hp']))
            elif enemy_dict['class'] == FinalExam.__name__:
                game.enemies.append(FinalExam(enemy_dict['hp']))
            elif enemy_dict['class'] == TheoreticalClass.__name__:
                game.enemies.append(TheoreticalClass(game.current_stage, enemy_dict['hp']))
            else:  # enemy_dict['class'] == Teacher.__class__.__name__:
                game.enemies.append(Teacher(enemy_dict['hp']))
        game.is_loaded_from_file = True

        return game

    def summary(self):
        return f"A game with {self.stages} stage(s) will be set up for {Game.PLAYERS} players."

    def enemies_generate(self):
        for _ in range(Game.ENEMIES_BY_STAGE):
            valid_enemy = False
            while not valid_enemy:
                enemy = random.choice(Game.AVAILABLE_ENEMIES)
                if enemy == TheoreticalClass:
                    self.enemies.append(enemy(self.current_stage))
                    valid_enemy = True
                elif enemy != FinalExam or (enemy == FinalExam and self.current_stage >= Game.FINALEXAM_LEVEL):
                    self.enemies.append(enemy())
                    valid_enemy = True

    def stage_info(self):
        result = f"----- STAGE {self.current_stage} -----\n"
        result += self.enemies_info()
        return result

    def enemies_info(self):
        result = "---- CURRENT ENEMIES ----\n"
        for enemy in self.enemies:
            result += f"{enemy}\n"
        return result

    def player_in_turn(self):
        return self.alive_players[self.current_turn]

    def another_player(self):
        if len(self.alive_players) == Game.PLAYERS:
            return self.alive_players[(self.current_turn + 1) % len(self.alive_players)]
        else:
            return self.dead_players[0]

    def character_name_player_in_turn(self):
        return self.alive_players[self.current_turn]['character'].__class__.__name__

    def has_more_than_one_players(self):
        return len(self.alive_players) != 1

    def current_turn_info(self):
        current_player = self.player_in_turn()
        return f"{current_player['character'].name()} ({current_player['name']}). " \
               f"What are you doing to do? {Game.AVAILABLE_COMMANDS}: "

    def is_last_player_on_turn(self):
        return self.current_turn == (len(self.alive_players) - 1)

    def player_attack(self):
        result = self.player_attacks_enemy(self.player_in_turn())
        if self.have_all_the_enemies_been_defeated():
            if self.current_stage == self.stages:
                self.finish = True
            else:
                self.change_turn()
                self.current_stage += 1
                self.all_players_go_level()
                self.enemies_generate()
                result += self.stage_info()
        else:
            if self.is_last_player_on_turn():
                result += self.play_enemies_turn()
                if not self.have_all_the_players_been_defeated():
                    self.set_turn()
            else:
                self.change_turn()
        return result

    def player_save_file(self, file):
        return self.write_to_file(file)

    def player_attacks_enemy(self, player):
        name = player['name']
        character = player['character']

        enemy = random.choice(self.enemies)
        dmg = character.attack(enemy)
        result = f"The {character.__class__.__name__} (Player {name}) " \
                 f"did {dmg} damage to {enemy.__class__.__name__}. {enemy}"
        if not enemy.is_alive():
            result += f" {enemy.__class__.__name__} has been defeated"
            self.enemies.remove(enemy)
        result += "\n"
        return result

    def write_to_file(self, file):
        try:
            dict_data = {'stages': self.stages,
                         'current_stage': self.current_stage,
                         'current_turn': self.current_turn}
            dict_alive_players = []
            for player in self.alive_players:
                player_dict = {'character': player['character'].dict_info()}
                dict_alive_players.append(player_dict)
            dict_data['alive_players'] = dict_alive_players

            dict_dead_players = []
            for player in self.dead_players:
                player_dict = {'character': player['character'].dict_info()}
                dict_dead_players.append(player_dict)
            dict_data['dead_players'] = dict_dead_players

            dict_enemies = []
            for enemy in self.enemies:
                dict_enemies.append(enemy.dict_info())
            dict_data['enemies'] = dict_enemies

            with open(file, 'w') as f:
                f.write(json.dumps(dict_data))

            result = "The game has been saved!!"
        except FileNotFoundError:
            result = "The file was not found."
        return result

    def change_turn(self):
        self.current_turn = (self.current_turn + 1) % len(self.alive_players)

    def set_turn(self):
        self.current_turn = 0

    def play_enemies_turn(self):
        result = "\n----- ENEMIES TURN -----\n"
        for enemy in self.enemies:
            player = random.choice(self.alive_players)
            name = player['name']
            character = player['character']

            dmg = enemy.attack(character)
            result += f"The {enemy.__class__.__name__} did {dmg} damage to " \
                      f"{character.__class__.__name__} (Player {name}). {character}"
            if not character.is_alive():
                result += f" {character.__class__.__name__} (Player {name}) has been defeated"
                self.alive_players.remove(player)
                self.dead_players.append(player)

            result += "\n"

            if self.have_all_the_players_been_defeated():
                self.finish = True
                break
        return result

    def have_all_the_enemies_been_defeated(self):
        return len(self.enemies) == 0

    def have_all_the_players_been_defeated(self):
        return len(self.alive_players) == 0

    def players_wins(self):
        return self.have_all_the_enemies_been_defeated()

    def all_players(self):
        return self.alive_players + self.dead_players

    def all_players_go_level(self):
        for player in self.all_players():
            player['character'].go_level()

    def players_names(self):
        all_players = self.all_players()
        result = ""
        for player in all_players[:len(all_players) - 1]:
            result = f"{player['name']}, "
        result += all_players[-1]['name']
        return result

    def has_finished(self):
        return self.finish

    def first_player(self):
        return self.alive_players[0]

    def second_player(self):
        if len(self.alive_players) == Game.PLAYERS:
            return self.alive_players[1]
        else:
            return self.dead_players[0]
