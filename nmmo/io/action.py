from pdb import set_trace as T
from ordered_set import OrderedSet
import numpy as np

from enum import Enum, auto

import nmmo
from nmmo.lib import utils
from nmmo.lib.utils import staticproperty

class NodeType(Enum):
   #Tree edges
   STATIC = auto()    #Traverses all edges without decisions
   SELECTION = auto() #Picks an edge to follow

   #Executable actions
   ACTION    = auto() #No arguments
   CONSTANT  = auto() #Constant argument
   VARIABLE  = auto() #Variable argument

class Node(metaclass=utils.IterableNameComparable):
   @classmethod
   def init(cls, config):
       pass

   @staticproperty
   def edges():
      return []

   #Fill these in
   @staticproperty
   def priority():
      return None

   @staticproperty
   def type():
      return None

   @staticproperty
   def leaf():
      return False

   @classmethod
   def N(cls, config):
      return len(cls.edges)

   def deserialize(self, entity, index):
      return index

   def args(self, entity, config):
      return []

class Fixed:
   pass

#ActionRoot
class Action(Node):
   nodeType = NodeType.SELECTION
   hooked   = False

   @classmethod
   def init(cls, config):
      # Sets up serialization domain
      if Action.hooked:
          return

      Action.hooked = True

   #Called upon module import (see bottom of file)
   #Sets up serialization domain
   def hook(self):
      idx = 0
      arguments = []
      for action in Action.edges(self):
         action.init(self)
         for args in action.edges:
            args.init(self)
            if 'edges' not in args.__dict__:
               continue
            for arg in args.edges: 
               arguments.append(arg)
               arg.serial = (idx, )
               arg.idx = idx
               idx += 1
      Action.arguments = arguments

   @staticproperty
   def n():
      return len(Action.arguments)

   @classmethod
   def edges(cls, config):
      '''List of valid actions'''
      edges = [Move]
      if config.COMBAT_SYSTEM_ENABLED:
          edges.append(Attack)
      if config.ITEM_SYSTEM_ENABLED:
          edges += [Use]
      if config.EXCHANGE_SYSTEM_ENABLED:
          edges += [Buy, Sell]
      if config.COMMUNICATION_SYSTEM_ENABLED:
          edges.append(Comm)
      return edges

   def args(self, entity, config):
      return nmmo.Serialized.edges 

class Move(Node):
   priority = 1
   nodeType = NodeType.SELECTION
   def call(self, entity, direction):
      r, c  = entity.pos
      entID = entity.entID
      entity.history.lastPos = (r, c)
      rDelta, cDelta = direction.delta
      rNew, cNew = r+rDelta, c+cDelta

      #One agent per cell
      tile = self.map.tiles[rNew, cNew]
      if tile.occupied and not tile.lava:
         return

      if entity.status.freeze > 0:
         return

      self.dataframe.move(nmmo.Serialized.Entity, entID, (r, c), (rNew, cNew))
      entity.base.r.update(rNew)
      entity.base.c.update(cNew)

      self.map.tiles[r, c].delEnt(entID)
      self.map.tiles[rNew, cNew].addEnt(entity)

      if self.map.tiles[rNew, cNew].lava:
         entity.receiveDamage(None, entity.resources.health.val)

   @staticproperty
   def edges():
      return [Direction]

   @staticproperty
   def leaf():
      return True

class Direction(Node):
   argType = Fixed

   @staticproperty
   def edges():
      return [North, South, East, West]

   def args(self, entity, config):
      return Direction.edges

class North(Node):
   delta = (-1, 0)

class South(Node):
   delta = (1, 0)

class East(Node):
   delta = (0, 1)

class West(Node):
   delta = (0, -1)


class Attack(Node):
   priority = 0
   nodeType = NodeType.SELECTION
   @staticproperty
   def n():
      return 3

   @staticproperty
   def edges():
      return [Style, Target]

   @staticproperty
   def leaf():
      return True

   def inRange(self, stim, config, N):
      R, C = stim.shape
      R, C = R//2, C//2

      rets = OrderedSet([self])
      for r in range(R-N, R+N+1):
         for c in range(C-N, C+N+1):
            for e in stim[r, c].ents.values():
               rets.add(e)

      rets = list(rets)
      return rets

   def l1(self, cent):
      r, c = self
      rCent, cCent = cent
      return abs(r - rCent) + abs(c - cCent)

   def call(self, entity, style, targ):
      config = self.config

      if entity.isPlayer and not config.COMBAT_SYSTEM_ENABLED:
         return 

      # Testing a spawn immunity against old agents to avoid spawn camping
      immunity = config.COMBAT_SPAWN_IMMUNITY
      if entity.isPlayer and targ.isPlayer and entity.history.timeAlive.val > immunity and targ.history.timeAlive < immunity:
         return

      #Check if self targeted
      if entity.entID == targ.entID:
         return

      #ADDED: POPULATION IMMUNITY
      if not config.COMBAT_FRIENDLY_FIRE and entity.isPlayer and entity.base.population.val == targ.base.population.val:
         return

      #Check attack range
      rng     = style.attackRange(config)
      start   = np.array(entity.base.pos)
      end     = np.array(targ.base.pos)
      dif     = np.max(np.abs(start - end))

      #Can't attack same cell or out of range
      if dif == 0 or dif > rng:
         return 

      #Execute attack
      entity.history.attack = {'target': targ.entID, 'style': style.__name__}
      targ.attacker = entity
      targ.attackerID.update(entity.entID)

      from nmmo.systems import combat
      dmg = combat.attack(self, entity, targ, style.skill)

      if style.freeze and dmg > 0:
         targ.status.freeze.update(config.COMBAT_FREEZE_TIME)

      return dmg

class Style(Node):
   argType = Fixed
   @staticproperty
   def edges():
      return [Melee, Range, Mage]

   def args(self, entity, config):
      return Style.edges


class Target(Node):
   argType = None

   @classmethod
   def N(cls, config):
      #return config.WINDOW ** 2
      return config.PLAYER_N_OBS

   def deserialize(self, entity, index):
      return self.entity(index)

   def args(self, entity, config):
      #Should pass max range?
      return Attack.inRange(entity, self, config, None)

class Melee(Node):
   nodeType = NodeType.ACTION
   freeze=False

   def attackRange(self):
      return self.COMBAT_MELEE_REACH

   def skill(self):
      return self.skills.melee

class Range(Node):
   nodeType = NodeType.ACTION
   freeze=False

   def attackRange(self):
      return self.COMBAT_RANGE_REACH

   def skill(self):
      return self.skills.range

class Mage(Node):
   nodeType = NodeType.ACTION
   freeze=False

   def attackRange(self):
      return self.COMBAT_MAGE_REACH

   def skill(self):
      return self.skills.mage

class Use(Node):
    priority = 3

    @staticproperty
    def edges():
        return [Item]

    def call(self, entity, item):
       if item not in entity.inventory:
           return

       return item.use(entity)

class Give(Node):
    priority = 2

    @staticproperty
    def edges():
        return [Item, Target]

    def call(self, entity, item, target):
       if item not in entity.inventory:
           return

       if not target.isPlayer:
           return

       if not target.inventory.space:
           return

       entity.inventory.remove(item, quantity=1)
       item = type(item)(self, item.level.val)
       target.inventory.receive(item)

       return True


class Item(Node):
    argType  = 'Entity'

    @classmethod
    def N(cls, config):
        return config.ITEM_N_OBS

    def args(self, entity, config):
       return self.exchange.items()

    def deserialize(self, entity, index):
       return self.items[index]

class Buy(Node):
    priority = 4
    argType  = Fixed

    @staticproperty
    def edges():
        return [Item]

    def call(self, entity, item):
       #Do not process exchange actions on death tick
       if not entity.alive:
           return

       if not entity.inventory.space:
           return

       return self.exchange.buy(self, entity, item)

class Sell(Node):
    priority = 4
    argType  = Fixed

    @staticproperty
    def edges():
        return [Item, Price]

    def call(self, entity, item, price):
       #Do not process exchange actions on death tick
       if not entity.alive:
           return

       # TODO: Find a better way to check this
       # Should only occur when item is used on same tick
       # Otherwise should not be possible
       if item not in entity.inventory:
           return

       if type(price) != int:
           price = price.val

       return self.exchange.sell(self, entity, item, price)

def init_discrete(values):
    classes = []
    for i in values:
        name = f'Discrete_{i}'
        cls  = type(name, (object,), {'val': i})
        classes.append(cls)
    return classes

class Price(Node):
    argType  = Fixed

    @classmethod
    def init(cls, config):
        Price.classes = init_discrete(list(range(100)))

    @staticproperty
    def edges():
        return Price.classes

    def args(self, entity, config):
       return Price.edges

class Token(Node):
    argType  = Fixed

    @classmethod
    def init(cls, config):
        Comm.classes = init_discrete(range(config.COMMUNICATION_NUM_TOKENS))

    @staticproperty
    def edges():
        return Comm.classes

    def args(self, entity, config):
       return Comm.edges

class Comm(Node):
    argType  = Fixed
    priority = 0

    @staticproperty
    def edges():
        return [Token]

    def call(self, entity, token):
       entity.base.comm.update(token.val)

#TODO: Solve AGI
class BecomeSkynet:
   pass
