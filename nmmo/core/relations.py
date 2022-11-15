import random

from nmmo import Task

"""

Copied from nmmo-baselines.tasks

"""

class Tier:
    REWARD_SCALE = 15
    EASY         = 4  / REWARD_SCALE
    NORMAL       = 6  / REWARD_SCALE
    HARD         = 11 / REWARD_SCALE

def player_kills(realm, player):
    return player.history.playerKills

def equipment(realm, player):
    return player.equipment.total(lambda e: e.level)

def exploration(realm, player):
    return player.history.exploration

def foraging(realm, player):
    return max(
            player.skills.fishing.level.val,
            player.skills.herbalism.level.val,
            player.skills.prospecting.level.val,
            player.skills.carving.level.val,
            player.skills.alchemy.level.val)

def combat(realm, player):
    return max(
            player.skills.mage.level.val,
            player.skills.range.level.val,
            player.skills.melee.level.val)


"""

End of the copied section

"""

RELATIONS = [player_kills, equipment, exploration, foraging, combat]


class Relations:

    def __init__(self,teams):
        
        self.teams = teams

        if self.teams == 'all':
            pass
        
        elif self.teams == 'left':
            pass

        elif self.teams == 'right':
            pass

        else:
            raise ValueError(f"{self.teams} is invalid argument")

    def atomic_tasks(self):
        pass
    
    def natural_language_to_string(self):
        pass

    def short_circuit_mech(self):
        pass

    @staticmethod
    def sample_relation(relations):
        return random.sample(len(relations),k=1)

class Hoarding(Relations):

    def __init__(self,teams):
        super().__init__(teams)
        

    def atomic_tasks(self):
        
        relation = self.sample_relation(RELATIONS)

        assert len(relation) == 1

        
        if relation == equipment:
            return [Task(equipment, 1,  Tier.EASY),
                    Task(equipment, 5, Tier.NORMAL),
                    Task(equipment, 10, Tier.HARD)]

        elif relation == exploration:
            return [Task(exploration, 16,  Tier.EASY),
                    Task(exploration, 32,  Tier.NORMAL),
                    Task(exploration, 64, Tier.HARD)]

        elif relation == foraging:
            return [Task(foraging, 2, Tier.EASY),
                    Task(foraging, 3, Tier.NORMAL),
                    Task(foraging, 4, Tier.HARD)]


    
    def natural_language_to_string(self):
        pass

    def short_circuit_mech(self):
        pass

    @staticmethod
    def sample_relation(relations):
        return random.sample(len(relations),k=1)





