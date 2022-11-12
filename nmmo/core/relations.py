import random

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
    
    def to_string(self):
        pass

    def short_circuit_mech(self):
        pass

    @staticmethod
    def sample_relation(relations):
        relations_keys = list(relations.keys())
        return random.sample(len(relations_keys),k=1)
