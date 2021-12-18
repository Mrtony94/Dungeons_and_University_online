"""
ALUMNOS que han realizado la práctica:
Antonio Andrés Pérez DNI: 47580369Q Titulación: IST
Javier Zapatero Lera DNI: 54300753F Titulación: IST
Hemos realizado el programa con implementación de color (solo compatible con distribuciones UNIX o macOS)
"""

import random


# --------------------------------------------------------------------------------------------- #
# CLASS ENEMY (clase padre)
# --------------------------------------------------------------------------------------------- #

class Enemy:
    def __init__(self, hp, dmg, stage):
        self.hp = hp
        self.dmg = dmg
        self.stage = stage

    def __str__(self):
        result = f"HP: {self.hp} DMG: {self.dmg}"
        return result

    def attack(self, character):
        dmg_attack = random.randint(1, self.dmg)
        character.decrease_hp(dmg_attack)
        return dmg_attack

    def decrease_hp(self, n):
        self.hp -= n
        if self.hp <= 0:
            self.hp = 0

    def display_attributes(self):
        result = f"{self.__class__.__name__}: Stats: {self.hp} HP and {self.dmg} DMG\n"
        return result

    def info_enemy(self):
        return {'class': self.__class__.__name__, 'hp': self.hp}

    # --------------------------------------------------------------------------------------------- #
    # MONSTERS CLASS (clases hijas)
    # --------------------------------------------------------------------------------------------- #


class PartialExam(Enemy):
    HP_MAX = 20
    DMG = 6

    def __init__(self, stage, hp=HP_MAX):
        super().__init__(hp, PartialExam.DMG, stage)


class FinalExam(Enemy):
    HP_MAX = 40
    DMG = 12

    def __init__(self, stage, hp=HP_MAX):
        super().__init__(hp, FinalExam.DMG, stage)


class TheoricalClass(Enemy):
    HP_MAX = 8
    DMG = 4

    def __init__(self, stage, hp=HP_MAX):
        super().__init__(hp, TheoricalClass.DMG, stage)

    def attack(self, character):
        dmg_attack = random.randint(1, self.DMG) + self.stage
        character.decrease_hp(dmg_attack)
        return dmg_attack


class Teacher(Enemy):
    HP_MAX = 15
    DMG = 7

    def __init__(self, stage, hp=HP_MAX):
        super().__init__(hp, Teacher.DMG, stage)

    def attack(self, character):
        dmg_attack = random.randint(1, self.DMG)
        if dmg_attack == 7:
            dmg_attack = 14
        character.decrease_hp(dmg_attack)
        return dmg_attack
