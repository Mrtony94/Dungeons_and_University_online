"""
ALUMNOS que han realizado la práctica:
Antonio Andrés Pérez DNI: 47580369Q Titulación: IST
Javier Zapatero Lera DNI: 54300753F Titulación: IST
Hemos realizado el programa con implementación de color (solo compatible con distribuciones UNIX o macOS)
"""
import random


# --------------------------------------------------------------------------------------------- #
# CHARACTER CLASS (clase padre)
# --------------------------------------------------------------------------------------------- #

class Character:
    def __init__(self, hp_max, dmg, hp):
        self.hp_max = hp_max
        self.dmg = dmg
        self.hp = hp

    def __str__(self):
        result = f"HP_MAX: {self.hp_max} HP: {self.hp} DMG: {self.dmg}"
        return result

    def attack(self, enemy):
        dmg_attack = random.randint(1, self.dmg)
        enemy.decrease_hp(dmg_attack)
        return dmg_attack

    def increase_hp(self, c):
        self.hp += c
        if self.hp > self.hp_max:
            self.hp = self.hp_max

    def decrease_hp(self, n):
        self.hp -= n
        if self.hp <= 0:
            self.hp = 0

    def level_up(self):
        if self.hp > 0:
            self.increase_hp(0.25 * self.hp_max)

    def display_attributes(self):
        result = f"{self.__class__.__name__}: Stats: {self.hp} HP and {self.dmg} DMG"
        return result

    def info_player(self):
        return {'class': self.__class__.__name__, 'hp': self.hp}

    def name(self):
        return self.__class__.__name__

    def is_dead(self):
        return self.hp <= 0

    # --------------------------------------------------------------------------------------------- #
    # PLAYERS CLASS (clases hijas)
    # --------------------------------------------------------------------------------------------- #


class Bookworm(Character):
    HP_MAX = 25
    DMG = 9

    @staticmethod
    def print_info():  # Imprimir estadísticas del personaje (HP_MAX y DMG)
        result = f"BookWorm -> Stats: {Bookworm.HP_MAX} HP, {Bookworm.DMG} DMG"
        return result

    def __init__(self, hp=HP_MAX):
        super().__init__(Bookworm.HP_MAX, Bookworm.DMG, hp)  # súper hace referencia al padre


class Worker(Character):
    HP_MAX = 40
    DMG = 10

    @staticmethod
    def print_info():
        result = f"Worker -> Stats: {Worker.HP_MAX} HP, {Worker.DMG} DMG"
        return result

    def __init__(self, hp=HP_MAX):
        super().__init__(Worker.HP_MAX, Worker.DMG, hp)


class Procrastinator(Character):
    HP_MAX = 30
    DMG = 6

    @staticmethod
    def print_info():
        result = f"Procrastinator -> Stats: {Procrastinator.HP_MAX} HP, {Procrastinator.DMG} DMG"
        return result

    def __init__(self, hp=HP_MAX):
        super().__init__(Procrastinator.HP_MAX, Procrastinator.DMG, hp)


class Whatsapper(Character):
    HP_MAX = 20
    DMG = 6

    @staticmethod
    def print_info():
        result = f"Whatsapper -> Stats: {Whatsapper.HP_MAX} HP, {Whatsapper.DMG} DMG"
        return result

    def __init__(self, hp=HP_MAX):
        super().__init__(Whatsapper.HP_MAX, Whatsapper.DMG, hp)
