import random




class Task:
    def __init__(self, *relations):
        self.relations = relations

    def to_natural_language(self):
        return ' '.join([e.to_natural_language() for e in self.relations])

class Relation:
    def __init__(self, team):
        self.team = team

    def to_natural_language(self):
        pass

    def short_circuit_mech(self):
        pass

    @property
    def param_space(self):
        pass

    @staticmethod
    def sample(self):
        return random.sample(self.param_space,k=1)

class Equipment(Relation):

    def __init__(self, teams, level):
        super().__init__(teams)
        assert level in self.param_space
        self.level = level

    @property
    def param_space(self):
        return [1, 5, 10]

    def completed(self, realm):
        return self.team.equipment.total(lambda e: e.level) > self.level


class TeamKills(Relation):

    def __init__(self, teams, level):
        super().__init__(teams)
        assert level in self.param_space
        self.level = level

    @property
    def param_space(self):
        return [1, 4, 8]

    def completed(self, realm):
        return self.team.history.playerKills > self.level



atomic_equipment_task = Task(Equipment(5))
atomic_teamkill_task = Task(TeamKills(4))





