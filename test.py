class Game:
    MIN_STAGES = 1
    MAX_STAGES = 10

    def __init__(self, stages=MIN_STAGES):
        self.stages = stages
        self.current_stage = 1
        self.end_game = False

    def stages(self):
        return self.stages

    def current_stage(self):
        return self.current_stage

    def subir_nivel(self):
        global result
        self.stages = 1
        if self.current_stage == self.stages:
            result = f"entra en el if"
            self.end_game = True
        else:
            result = f"entra en el else"
        return result


game = Game(1)
print(Game.subir_nivel(game))
