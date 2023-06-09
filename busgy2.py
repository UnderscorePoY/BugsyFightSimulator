import copy
import pickle
from enum import Enum
from math import floor, ceil, sqrt, gcd

# Only handles Bugsy, Totodile spams Rage
# TurnActions.MAX_BAD_OUTCOME limits the search space per fought enemy
#   a "bad outcome" is increasing the enemy defense/lowering the player speed or defense/enemy missing a damaging move/poison


#
# Type
#
class Type(Enum):
    NORMAL = 0
    FIGHTING = 1
    FLYING = 2
    POISON = 3
    GROUND = 4
    ROCK = 5
    BUG = 6
    GHOST = 7
    FIRE = 8
    WATER = 9
    GRASS = 10
    ELECTRIC = 11
    PSYCHIC = 12
    ICE = 13
    DRAGON = 14
    STEEL = 15
    DARK = 16
    NONE = -1

    def isPhysical(self):
        return self.value in range(Type.NORMAL.value, Type.GHOST.value+1)


#
# Experience
#
class ExpCurve(Enum):
    SLOW = 0
    MEDIUM_SLOW = 1
    MEDIUM_FAST = 2
    FAST = 3
    NONE = -1

def expToNextLevel(curve, currLevel, totalExp):
    if curve == ExpCurve.NONE:
        return 0

    n = currLevel + 1
    nextExp = lowestExpForLevel(curve, n)

    return nextExp - totalExp

def lowestExpForLevel(curve, level):
    n = level
    exp = 0
    if curve == ExpCurve.SLOW:
        exp = 5 * n * n * n // 4
    elif curve == ExpCurve.MEDIUM_SLOW:
        exp = 6 * n * n * n // 5 - 15 * n * n + 100 * n - 140
    elif ExpCurve.MEDIUM_FAST:
        exp = n * n * n
    elif ExpCurve.FAST:
        exp = 4 * n * n * n // 5
    return exp

def expForLevel(curve, level):
    return lowestExpForLevel(curve, level + 1) - lowestExpForLevel(curve, level)


#
# Species
#
class Species:
    def __init__(self, name, dex, type1, type2, baseHP, baseAtk, baseDef, baseSpcAtk, baseSpcDef, baseSpd, killExp: int,expCurve: ExpCurve):
        self.name = name
        self.dex = dex
        self.type1 = type1
        self.type2 = type2
        self.baseHP = baseHP
        self.baseAtk = baseAtk
        self.baseDef = baseDef
        self.baseSpcAtk = baseSpcAtk
        self.baseSpcDef = baseSpcDef
        self.baseSpd = baseSpd
        self.killExp = killExp
        self.expCurve = expCurve


METAPOD = Species("Metapod", 11, Type.BUG, Type.NONE, 50, 20, 55, 25, 25, 30, 72, ExpCurve.MEDIUM_FAST)
KAKUNA = Species("Kakuna", 14, Type.BUG, Type.POISON, 45, 25, 50, 25, 25, 35, 71, ExpCurve.MEDIUM_FAST)
SCYTHER = Species("Scyther", 123, Type.BUG, Type.FLYING, 70, 110, 80, 55, 80, 105, 187, ExpCurve.MEDIUM_FAST)
TOTODILE = Species("Totodile", 158, Type.WATER, Type.NONE, 50, 65, 64, 44, 48, 43, 66, ExpCurve.MEDIUM_SLOW)


#
# Pokemon
#
class Pokemon:
    def __init__(self, species, level, ivs,
                 ev_hp, ev_hp_used, ev_atk, ev_atk_used, ev_def, ev_def_used, ev_spd, ev_spd_used, ev_spc, ev_spc_used,
                 moves, wild,
                 elementalBadgeBoosts, atkBadge=False, defBadge=False, spdBadge=False, spcBadge=False,
                 totalExp=0, isPoisoned=False):
        self.species = species
        self.level = level
        self.ivs = ivs
        self.iv_hp = ivs[0]&1<<3|ivs[1]&1<<2|ivs[2]&1<<1|ivs[3]
        self.ev_hp = ev_hp
        self.ev_hp_used = ev_hp_used
        self.ev_atk = ev_atk
        self.ev_atk_used = ev_atk_used
        self.ev_def = ev_def
        self.ev_def_used = ev_def_used
        self.ev_spd = ev_spd
        self.ev_spd_used = ev_spd_used
        self.ev_spc = ev_spc
        self.ev_spc_used = ev_spc_used
        self.moves = moves
        self.wild = wild
        self.elementalBadgeBoosts = elementalBadgeBoosts
        self.atkBadge = atkBadge
        self.defBadge = defBadge
        self.spdBadge = spdBadge
        self.spcBadge = spcBadge
        self.totalExp = totalExp
        self.hp = self.calcHP()
        self.atk = self.calcAtk()
        self.deff = self.calcDef()
        self.spd = self.calcSpd()
        self.spcAtk = self.calcSpcAtk()
        self.spcDef = self.calcSpcDef()
        self.currHP = self.hp
        self.isPoisoned = isPoisoned

    def __copy__(self):
        copyy = copy.deepcopy(self)
        return copyy

    def __repr__(self):
        return f'L{self.level} {self.species.name} ({self.hp}/{self.atk}/{self.deff}/{self.spd}/{self.spcAtk}/{self.spcDef}) currHP={self.currHP}'

    def calcHP(self):
        return self.calcStatNumerator(self.iv_hp, self.species.baseHP, self.ev_hp_used) * self.level // 100 + self.level + 10

    def calcAtk(self):
        return self.calcStatNumerator(self.ivs[0], self.species.baseAtk, self.ev_atk_used) * self.level // 100 + 5

    def calcDef(self):
        return self.calcStatNumerator(self.ivs[1], self.species.baseDef, self.ev_def_used) * self.level // 100 + 5

    def calcSpd(self):
        return self.calcStatNumerator(self.ivs[2], self.species.baseSpd, self.ev_spd_used) * self.level // 100 + 5

    def calcSpcAtk(self):
        return self.calcStatNumerator(self.ivs[3], self.species.baseSpcAtk, self.ev_spc_used) * self.level // 100 + 5

    def calcSpcDef(self):
        return self.calcStatNumerator(self.ivs[3], self.species.baseSpcDef, self.ev_spc_used) * self.level // 100 + 5

    def evCalc(self, ev):
        return min(floor(ceil(sqrt(ev))), 255) // 4

    def calcStatNumerator(self, iv, base, ev):
        return 2 * (iv + base) + self.evCalc(ev)

    def isTypeBoosted(self, ttype):
        return elementalBadgeBoosts[ttype.value]

    def expGiven(self):
        return self.species.killExp * self.level // 7 * 3 // 2  # always trainer

    def expToNextLevel(self):
        return expToNextLevel(self.species.expCurve, self.level, self.totalExp)

    def calculateStats(self):
        self.ev_hp_used = self.ev_hp
        self.ev_atk_used = self.ev_atk
        self.ev_def_used = self.ev_def
        self.ev_spc_used = self.ev_spc
        self.ev_spd_used = self.ev_spd
        oldHP = self.hp
        self.hp = self.calcHP()
        self.atk = self.calcAtk()
        self.deff = self.calcDef()
        self.spd = self.calcSpd()
        self.spcAtk = self.calcSpcAtk()
        self.spcDef = self.calcSpcDef()

        self.currHP += self.hp - oldHP

    def gainExp(self, num):
        self.totalExp += num
        # update lvl if necessary
        while self.expToNextLevel() <= 0 and self.level < 100:
            self.level += 1
            self.calculateStats()

    def gainStatExp(self, s: Species):
        self.ev_hp += s.baseHP
        self.ev_atk += s.baseAtk
        self.ev_def += s.baseDef
        self.ev_spc += s.baseSpcAtk
        self.ev_spd += s.baseSpd


#
# MoveEffect
#
class MoveEffect(Enum):
    NORMAL_HIT = 0
    DEFENSE_UP = 1
    SPEED_DOWN = 2
    POISON_HIT = 3
    FURY_CUTTER = 4
    PRIORITY_HIT = 5
    DEFENSE_DOWN = 6
    RAGE = 7


#
# Move
#
class Move:
    def __init__(self, name, index, effect, power, ttype, accuracy, pp, effectChance):
        self.name = name
        self.index = index
        self.effect = effect
        self.power = power
        self.type = ttype
        self.accuracy = accuracy
        self.pp = pp
        self.effectChance = effectChance

    def __repr__(self):
        return f'{self.name}'


TACKLE = Move("Tackle", 33, MoveEffect.NORMAL_HIT, 35, Type.NORMAL, 95, 35, 0)
HARDEN = Move("Harden", 106, MoveEffect.DEFENSE_UP, 0, Type.NORMAL, 100, 30, 0)
STRING_SHOT = Move("String Shot", 81, MoveEffect.SPEED_DOWN, 0, Type.BUG, 95, 40, 0)
POISON_STING = Move("Poison Sting", 40, MoveEffect.POISON_HIT, 15, Type.POISON, 100, 35, 30)
FURY_CUTTER = Move("Fury Cutter", 210, MoveEffect.FURY_CUTTER, 10, Type.BUG, 95, 20, 0)
QUICK_ATTACK = Move("Quick Attack", 98, MoveEffect.PRIORITY_HIT, 40, Type.NORMAL, 100, 30, 0)
LEER = Move("Leer", 43, MoveEffect.DEFENSE_DOWN, 0, Type.NORMAL, 100, 30, 0)
RAGE = Move("Rage", 99, MoveEffect.RAGE, 20, Type.NORMAL, 100, 20, 0)


#
# StatModifier
#
class StatModifier:
    def __init__(self, atk=0, deff=0, spd=0, spcAtk=0, spcDef=0,
                 atkBB=False, defBB=False, spdBB=False, spcBB=False,
                 rageNb=1, furycutterNb=0,
                 turn=0):
        self.atk = atk
        self.deff = deff
        self.spd = spd
        self.spcAtk = spcAtk
        self.spcDef = spcDef
        self.atkBB = atkBB
        self.defBB = defBB
        self.spdBB = spdBB
        self.spcBB = spcBB
        self.rageNb = rageNb
        self.furycutterNb = furycutterNb
        self.turn = turn

    def __copy__(self):
        return copy.deepcopy(self)

    def __repr__(self):
        return f'(stages={self.atk}/{self.deff}/{self.spd}/{self.spcAtk}/{self.spcDef}) {self.rageNb=} {self.furycutterNb=} {self.turn=}'

    def bound(self, stage):
        if stage < -6:
            return -6
        if stage > 6:
            return 6
        return stage

    multipliers = [ 25,  28,  33,  40,  50,  66, 1, 15, 2, 25, 3, 35, 4]
    divisors    = [100, 100, 100, 100, 100, 100, 1, 10, 1, 10, 1, 10, 1]

    def modifyStat(self, original, stage):
        return original * StatModifier.multipliers[stage + 6] // StatModifier.divisors[stage + 6]

    def modAtk(self, pokemon):
        a = max(self.modifyStat(pokemon.atk, self.atk), 1)
        if pokemon.atkBadge:
            a = 9 * a // 8
        return a

    def modDef(self, pokemon):
        a = max(self.modifyStat(pokemon.deff, self.deff), 1)
        if pokemon.defBadge:
            a = 9 * a // 8
        return a

    def modSpcAtk(self, pokemon):
        a = max(self.modifyStat(pokemon.spcAtk, self.spcAtk), 1)
        if pokemon.spcBadge:
            a = 9 * a // 8
        return a

    def modSpcDef(self, pokemon):
        a = max(self.modifyStat(pokemon.spcDef, self.spcDef), 1)
        if pokemon.spcBadge and (pokemon.spcAtk in range(206, 433) or pokemon.spcAtk >= 661):
            a = 9 * a // 8
        return a

    def modSpd(self, pokemon):
        a = max(self.modifyStat(pokemon.spd, self.spd), 1)
        if pokemon.spdBadge:
            a = 9 * a // 8
        return a


#
# Damage calculation
#
MIN_RANGE = 217
MAX_RANGE = 255


def calc_damage(attack: Move, attacker, defender, atkMod, defMod, rangeNum, crit, extra_multiplier):
    if rangeNum < MIN_RANGE:
        rangeNum = MIN_RANGE
    if rangeNum > MAX_RANGE:
        rangeNum = MAX_RANGE
    modAttack = attack

    # stat modifiers
    aa_orig = attacker.atk
    atk_atk = atkMod.modAtk(attacker)
    dd_orig = defender.deff
    def_def = defMod.modDef(defender)
    as_orig = attacker.spcAtk
    atk_spc = atkMod.modSpcAtk(attacker)
    ds_orig = defender.spcDef
    dsa_orig_bug = defender.spcAtk  # TODO: when is it used and why is this not implemented ?
    atk_spc_orig_bug = defMod.modSpcAtk(defender)
    def_spc = defMod.modSpcDef(defender)

    STAB = modAttack.type != Type.NONE and \
           (modAttack.type == attacker.species.type1
            or modAttack.type == attacker.species.type2)
    # Skip effectiveness
    effectiveMult = 1
    #effectiveMult = Type.effectiveness(modAttack.getType(), defender
    #                                   .getSpecies().getType1(), defender.getSpecies().getType2())
    if effectiveMult == 0:
        return 0

    effective_atk, effective_def = 0, 0
    applyAtkModifiers = (not crit) or crit and (defMod.deff < atkMod.atk)
    applyDefModifiers = applyAtkModifiers
    applySpcAtkModifiers = (not crit) or crit and (defMod.spcDef < atkMod.spcAtk)
    applySpcDefModifiers = applySpcAtkModifiers

    if modAttack.type.isPhysical():
        effective_atk = atk_atk if applyAtkModifiers else aa_orig
        effective_def = def_def if applyDefModifiers else dd_orig
    else:
        effective_atk = atk_spc if applySpcAtkModifiers else as_orig
        effective_def = def_spc if applySpcDefModifiers else ds_orig

    if effective_atk > 255 or effective_def > 255:
        effective_atk = max(1, effective_atk // 4)
        effective_def = max(1, effective_def // 4)

    damage = (attacker.level * 2 // 5 + 2) * modAttack.power * effective_atk
    damage //= effective_def
    damage //= 50

    if crit:
        damage *= 2

    damage = min(damage, 997) + 2

    # Type boosts
    if attacker.isTypeBoosted(modAttack.type):
        typeboost = max(damage // 8, 1)
        damage += typeboost

    # STAB
    if STAB:
        damage = damage * 3 // 2

    # Skipped effectiveness
    damage *= extra_multiplier
    damage = damage * rangeNum // 255
    return max(damage, 1)


class DamageDic:
    def __init__(self):
        self.dic = {}

    def add(self, roll):
        if roll in self.dic:
            self.dic[roll] += 1
        else:
            self.dic[roll] = 1

    def __repr__(self):
        return repr(self.dic)


def allNormalDamage(move, attacker, defender, attackerMod, defenderMod, extraMultiplier=1):
    dmgDic = DamageDic()
    for r in range(MIN_RANGE, MAX_RANGE + 1):
        dmg = calc_damage(move, attacker, defender, attackerMod, defenderMod, r, crit=False,
                          extra_multiplier=extraMultiplier)
        dmgDic.add(dmg)
    return dmgDic


def allCritDamage(move, attacker, defender, attackerMod, defenderMod, extraMultiplier=1):
    dmgDic = DamageDic()
    for r in range(MIN_RANGE, MAX_RANGE + 1):
        dmg = calc_damage(move, attacker, defender, attackerMod, defenderMod, r, crit=True,
                          extra_multiplier=extraMultiplier)
        dmgDic.add(dmg)
    return dmgDic


#
# AI Scoring
#
class Scoring:
    def __init__(self, length):
        self.odds = Odds(1, 1)
        self.scores = [20]*length

    def __repr__(self):
        return f'{"-".join(str(x) for x in self.scores)} {self.odds.__repr__()}'

    def __copy__(self):
        copyy = Scoring(len(self.scores))
        copyy.odds = self.odds.__copy__()
        for i, val in enumerate(self.scores):
            copyy.scores[i] = val
        return copyy

    def updateToNew(self, odds_mult, idx, scoreDelta):
        copyy = self.__copy__()
        copyy.odds *= odds_mult
        copyy.scores[idx] += scoreDelta
        return copyy


#
# AI
#

# TODO : missing some AI layers (so far, only handles Bugsy correctly)

def ai_setup(moves, playerMod: StatModifier, enemyMod: StatModifier, scoring: Scoring):
    scorings: list[Scoring] = [scoring]
    # TODO : add all the other stat-up/stat-down effects
    for i, move in enumerate(moves):
        # Stat-up
        if move.effect in [MoveEffect.DEFENSE_UP]:
            tmp_scorings = []
            if enemyMod.turn == 1:
                for sc in scorings:
                    # 50% greatly encourage
                    scoring1 = sc.updateToNew(Odds(1, 2), i, -2)
                    # 50% to do nothing
                    scoring2 = sc.updateToNew(Odds(1, 2), i, +0)
                    tmp_scorings.extend([scoring1, scoring2])
                scorings = tmp_scorings
            else:  # enemyMod.turn > 1
                for sc in scorings:
                    # 226/256 to greatly discourage
                    scoring1 = sc.updateToNew(Odds(226, 256), i, +2)
                    # 30/256 to do nothing
                    scoring2 = sc.updateToNew(Odds(30, 256), i, +0)
                    tmp_scorings.extend([scoring1, scoring2])
                scorings = tmp_scorings
        # end Stat-up

        # Stat-down
        if move.effect in [MoveEffect.DEFENSE_DOWN, MoveEffect.SPEED_DOWN]:
            tmp_scorings = []
            if playerMod.turn == 1:
                for sc in scorings:
                    # 50% greatly encourage
                    scoring1 = sc.updateToNew(Odds(1, 2), i, -2)
                    # 50% to do nothing
                    scoring2 = sc.updateToNew(Odds(1, 2), i, +0)
                    tmp_scorings.extend([scoring1, scoring2])
                scorings = tmp_scorings
            else:  # playerMod.turn > 1
                for sc in scorings:
                    # 226/256 to greatly discourage
                    scoring1 = sc.updateToNew(Odds(226, 256), i, +2)
                    # 30/256 to do nothing
                    scoring2 = sc.updateToNew(Odds(30, 256), i, +0)
                    tmp_scorings.extend([scoring1, scoring2])
                scorings = tmp_scorings
        # end Stat-down
    return scorings


def ai_smart_furycutter(moves, enemyMod: StatModifier, enemy: Pokemon, scoring: Scoring):
    scorings: list[Scoring] = [scoring]
    # TODO : factor code out when creating Rollout layer
    for i, move in enumerate(moves):
        if move.effect == MoveEffect.FURY_CUTTER:
            if enemyMod.furycutterNb >= 1:
                scoring.scores[i] -= 1
            if enemyMod.furycutterNb >= 2:
                scoring.scores[i] -= 2
            if enemyMod.furycutterNb >= 3:
                scoring.scores[i] -= 3

            tmp_scorings = []
            if 100 * enemy.currHP / enemy.hp <= 25:  # TODO : is probably not the comparison used in the original code
                # 200/256 to discourage if enemy HP is 25% or below
                scoring1 = scoring.updateToNew(Odds(200, 256), i, +1)
                scoring2 = scoring.updateToNew(Odds(56, 256), i, +0)
                tmp_scorings.extend([scoring1, scoring2])
            else:
                # 200/256 to greatly encourage
                scoring1 = scoring.updateToNew(Odds(200, 256), i, -2)
                scoring2 = scoring.updateToNew(Odds(56, 256), i, +0)
                tmp_scorings.extend([scoring1, scoring2])
            scorings = tmp_scorings
    return scorings


def ai_aggressive(moves, playerMod: StatModifier, enemyMod: StatModifier, player: Pokemon, enemy: Pokemon, scoring: Scoring):
    # Discourage damaging moves that are not dealing the most damage
    idx_max, dmg_max = None, 0

    for idx, move in enumerate(moves):
        if move.power <= 1:
            continue

        dmg = calc_damage(move, enemy, player, enemyMod, playerMod, MAX_RANGE, crit=False, extra_multiplier=1)
        if dmg > dmg_max:
            idx_max, dmg_max = idx, dmg

    for idx, move in enumerate(moves):
        if idx_max is not None and move.power > 1 and idx != idx_max:
            scoring.scores[idx] += 1

    return scoring


def ai_risky(moves, playerMod: StatModifier, enemyMod: StatModifier, player: Pokemon, enemy: Pokemon,
                  scoring: Scoring):
    for i, move in enumerate(moves):
        dmg = calc_damage(move, enemy, player, enemyMod, playerMod, MAX_RANGE, crit=False, extra_multiplier=1)
        if dmg > player.currHP:  # this check should be dmg >= currHP, it's an oversight from the original code
            scoring.scores[i] -= 5

    return scoring


def perform_ai_turn(moves, playerMod, enemyMod, player, enemy):
    scoring = Scoring(len(moves))
    scorings: list[Scoring] = [scoring]

    # AI_SETUP
    scorings = ai_setup(moves, playerMod, enemyMod, scoring)

    # AI_SMART_FURYCUTTER
    tmp_scorings = []
    for sc in scorings:
        tmp_scs = ai_smart_furycutter(moves, enemyMod, enemy, sc)
        tmp_scorings.extend(tmp_scs)
    scorings = tmp_scorings

    # AI_AGGRESSIVE
    tmp_scorings = []
    for sc in scorings:
        tmp_sc = ai_aggressive(moves, playerMod, enemyMod, player, enemy, sc)
        tmp_scorings.append(tmp_sc)
    scorings = tmp_scorings

    # AI_RISKY
    tmp_scorings = []
    for sc in scorings:
        tmp_sc = ai_risky(moves, playerMod, enemyMod, player, enemy, sc)
        tmp_scorings.append(tmp_sc)
    scorings = tmp_scorings

    return scorings


#
# Odds
#
class Odds:
    def __init__(self, numerator: int, denominator: int):
        self.numerator = numerator
        self.denominator = denominator
        self.simplify()

    def simplify(self):
        gcdd = gcd(self.numerator, self.denominator) if self.numerator != 0 else 1
        self.numerator //= gcdd
        self.denominator //= gcdd

    def __add__(self, other):  # Creates a new object
        new = self.__copy__()
        new += other
        return new

    def __iadd__(self, other):  # Doesn't create an object
        self.in_place_add(other)
        return self

    def in_place_add(self, other):  # Useful for in-place tuple modifications
        if self.numerator == 0 and other.numerator == 0:
            self.numerator = 0
            self.denominator = 1

        self.numerator = self.numerator * other.denominator + other.numerator * self.denominator
        self.denominator = self.denominator * other.denominator
        self.simplify()

    def __sub__(self, other):  # Creates a new object
        new = self.__copy__()
        new -= other
        return new

    def __isub__(self, other):  # Doesn't create an object
        self.in_place_add(other.opposite())
        return self

    def opposite(self):
        return Odds(-self.numerator, self.denominator)

    def __mul__(self, other):  # Creates a new object
        new = self.__copy__()
        new *= other
        return new

    def __imul__(self, other):  # Doesn't create an object
        self.in_place_mult(other)
        return self

    def in_place_mult(self, other):  # Useful for in-place tuple modifications
        if self.numerator == 0 or other.numerator == 0:
            self.numerator = 0
            self.denominator = 1

        self.numerator = self.numerator * other.numerator
        self.denominator = self.denominator * other.denominator
        self.simplify()

    def __lt__(self, other):
        return (self - other).numerator < 0

    def __copy__(self):
        new = Odds(self.numerator, self.denominator)
        return new

    def __repr__(self):
        return f'({self.numerator}/{self.denominator}={self.percentage()}%)'

    def percentage(self):
        return self.numerator*100/self.denominator


def extract_move_odds(scorings: list[Scoring]):
    odds_list: list[Odds] = []
    for _ in scorings[0].scores:
        odds_list.append(Odds(0, 1))

    for scoring in scorings:
        min_score = min(scoring.scores)
        min_idxs = [i for i, _ in enumerate(scoring.scores) if scoring.scores[i] == min_score]
        new_odds = scoring.odds * Odds(1, len(min_idxs))
        for idx in min_idxs:
            odds_list[idx] += new_odds

    return odds_list


#
# Battle logic
#
class WhoFights(Enum):
    PLAYER = 0
    ENEMY = 1


class TurnActions:
    MAX_BAD_OUTCOME = 0
    def __init__(self, name: str, player: Pokemon, enemy: Pokemon, playerMod: StatModifier, enemyMod: StatModifier, odds: Odds,
                 hasPlayerPlayed=True, hasEnemyPlayed=True, whoFightsNext=WhoFights.PLAYER,
                 wasPoisonApplied=True, wasJustPoisoned=False):
        self.name = name
        self.player = player
        self.enemy = enemy
        self.playerMod = playerMod
        self.enemyMod = enemyMod
        self.odds = odds
        self.hasPlayerPlayed = hasPlayerPlayed
        self.hasEnemyPlayed = hasEnemyPlayed
        self.whoFightsNext = whoFightsNext
        self.wasPoisonApplied = wasPoisonApplied
        self.wasJustPoisoned = wasJustPoisoned
        self.remainingBadOutcomes = TurnActions.MAX_BAD_OUTCOME

    def __copy__(self):
        return copy.deepcopy(self)

    def __repr__(self):
        return f'{self.player.currHP=} {self.player.isPoisoned=} {self.playerMod=} {self.odds =} {self.name} '

    def __hash__(self):
        hashVal = (self.playerMod.spd + 6)

        hashVal <<= 4
        hashVal += (self.playerMod.deff + 6)  # 0-12

        hashVal <<= 4
        hashVal += self.playerMod.rageNb  # 0-8

        hashVal <<= 6
        hashVal += self.player.currHP  # 0-50ish

        hashVal <<= 1
        hashVal += 1 if self.player.isPoisoned else 0

        return hashVal

    # TODO : may be problematic for further usage ?
    def __eq__(self, other):
        return hash(self) == hash(other)


class FightOutcome(Enum):
    STILL_GOING = 0
    PLAYER_IS_KO = 1
    ENEMY_IS_KO = 2


#
# OutcomesDic
#
class OutcomesDic:
    TOTAL_ODDS_IDX = 0
    LIST_TURNS_IDX = 1

    def __init__(self):
        self.dic: dict[FightOutcome, dict[TurnActions, tuple[Odds, list[TurnActions]]]] \
            = {FightOutcome.PLAYER_IS_KO: {}, FightOutcome.ENEMY_IS_KO: {}}
        self.total_odds: dict[FightOutcome, Odds] \
            = {FightOutcome.PLAYER_IS_KO: Odds(0, 1), FightOutcome.ENEMY_IS_KO: Odds(0, 1)}

    def __getitem__(self, item):
        return self.dic[item]

    def __setitem__(self, key, value):
        self.dic[key] = value  # no copy/deepcopy here

    def add(self, outcome: FightOutcome, t: TurnActions):
        if t in self[outcome].keys():  # only checks for some variables inside t, not the whole object
            self[outcome][t][OutcomesDic.TOTAL_ODDS_IDX].in_place_add(t.odds)
            if store_all_scenarii:  # global defined in main
                self[outcome][t][OutcomesDic.LIST_TURNS_IDX].append(t)
        else:
            self[outcome][t] = (t.odds, [t])

        self.total_odds[outcome].in_place_add(t.odds)

    def short_display(self):
        player_percent = self.total_odds[FightOutcome.PLAYER_IS_KO].percentage()
        enemy_percent = self.total_odds[FightOutcome.ENEMY_IS_KO].percentage()
        total_percent = player_percent + enemy_percent
        return f'{FightOutcome.PLAYER_IS_KO.name}={player_percent}%, {FightOutcome.ENEMY_IS_KO.name}={enemy_percent}%, TOTAL={total_percent}%'

    def full_display(self):
        return repr(self.dic) + self.short_display()

    def percentageOfPlayerDeaths(self):
        player_percent = self.total_odds[FightOutcome.PLAYER_IS_KO].percentage()
        enemy_percent = self.total_odds[FightOutcome.ENEMY_IS_KO].percentage()
        total_percent = player_percent + enemy_percent
        return 100 * player_percent / total_percent


def doPlayerTurn(t: TurnActions, initial_turn: TurnActions, outcomesDic: OutcomesDic):
    for is_crit in [False, True] if allow_crits_for_player else [False]:
        damages = allNormalDamage(RAGE, t.player, t.enemy, t.playerMod, t.enemyMod, extraMultiplier=t.playerMod.rageNb) \
                  if not is_crit \
                  else allCritDamage(RAGE, t.player, t.enemy, t.playerMod, t.enemyMod, extraMultiplier=t.playerMod.rageNb)

        for dmg, roll in damages.dic.items():
            next_turn = t.__copy__()
            next_turn.name += f'Player->Rage{t.playerMod.rageNb}->{"crit" if is_crit else "noCrit"}->{dmg}|'

            next_turn.odds *= Odds(15, 16) if not is_crit else Odds(1, 16)
            next_turn.odds *= Odds(roll, 39)  # roll odds

            next_turn.enemy.currHP -= dmg

            next_turn.hasPlayerPlayed = True
            next_turn.whoFightsNext = WhoFights.ENEMY
            fightUntilKO(next_turn, initial_turn, outcomesDic)


def enemyMultiplier(move: Move, enemyMod: StatModifier):
    return 1 << enemyMod.furycutterNb if move.name == FURY_CUTTER.name else 1


def doEnemyTurn(t: TurnActions, initial_turn: TurnActions, outcomesDic: OutcomesDic):
    # AI
    ai_scorings = perform_ai_turn(t.enemy.moves, t.playerMod, t.enemyMod, t.player, t.enemy)
    move_odds = extract_move_odds(ai_scorings)

    for idx, oddsToChooseMove in enumerate(move_odds):
        move = t.enemy.moves[idx]

        tmp_turn_after_move_choice = t.__copy__()
        tmp_turn_after_move_choice.name += f'{t.enemy.species.name}->{move.name}'
        if move.name == FURY_CUTTER.name:
            tmp_turn_after_move_choice.name += f'{tmp_turn_after_move_choice.enemyMod.furycutterNb+1}'

        tmp_turn_after_move_choice.odds *= oddsToChooseMove
        # Move deals damage
        if move.power >= 2:
            for is_crit in [False, True] if allow_crits_for_player else [False]:
                damages = allNormalDamage(move, t.enemy, t.player, t.enemyMod, t.playerMod,
                                                  extraMultiplier=enemyMultiplier(move, t.enemyMod)) \
                          if not is_crit \
                          else allCritDamage(move, t.enemy, t.player, t.enemyMod, t.playerMod,
                                                     extraMultiplier=enemyMultiplier(move, t.enemyMod))

                for dmg, roll in damages.dic.items():
                    next_turn = tmp_turn_after_move_choice.__copy__()
                    next_turn.name += f'->{"crit" if is_crit else "noCrit"}->{dmg}'

                    next_turn.odds *= Odds(move.accuracy, 100)  # no miss
                    next_turn.odds *= Odds(15, 16) if not is_crit else Odds(1, 16)  # (no)crit odds
                    next_turn.odds *= Odds(roll, 39)  # roll odds

                    next_turn.player.currHP -= dmg

                    # Update Rage & Fury Cutter | TODO : proper handling of Rage's turn 1
                    next_turn.playerMod.rageNb = min(8, next_turn.playerMod.rageNb + 1)
                    if move.name == FURY_CUTTER.name:
                        next_turn.enemyMod.furycutterNb = min(5, next_turn.enemyMod.furycutterNb + 1)

                    next_turn.hasEnemyPlayed = True
                    next_turn.whoFightsNext = WhoFights.PLAYER

                    if move.effect == MoveEffect.POISON_HIT and not t.player.isPoisoned:
                        # no poison
                        next_turn_noPSN = next_turn.__copy__()
                        next_turn_noPSN.name += '|'
                        next_turn_noPSN.odds *= Odds(100 - move.effectChance, 100)
                        fightUntilKO(next_turn_noPSN, initial_turn, outcomesDic)

                        # poison
                        next_turn_PSN = next_turn.__copy__()
                        next_turn_PSN.name += '->PSN|'
                        next_turn_PSN.odds *= Odds(move.effectChance, 100)
                        next_turn_PSN.remainingBadOutcomes -= 1

                        next_turn_PSN.player.isPoisoned = True
                        next_turn_PSN.wasJustPoisoned = True

                        fightUntilKO(next_turn_PSN, initial_turn, outcomesDic)
                    else:
                        next_turn.name += '|'
                        fightUntilKO(next_turn, initial_turn, outcomesDic)

            # Move can miss
            if move.accuracy < 100:
                next_turn = tmp_turn_after_move_choice.__copy__()
                next_turn.name += '->miss|'
                next_turn.odds *= Odds(100-move.accuracy, 100)
                if move.name == FURY_CUTTER.name:
                    next_turn.enemyMod.furycutterNb = 0
                next_turn.remainingBadOutcomes -= 1

                next_turn.hasEnemyPlayed = True
                next_turn.whoFightsNext = WhoFights.PLAYER
                fightUntilKO(next_turn, initial_turn, outcomesDic)

        # Move deals no damage
        elif move.power == 0:
            if move.effect == MoveEffect.DEFENSE_UP:
                next_turn = tmp_turn_after_move_choice.__copy__()
                next_turn.name += f'|'

                next_turn.enemyMod.deff = next_turn.enemyMod.bound(next_turn.enemyMod.deff + 1)

                next_turn.remainingBadOutcomes -= 1

                next_turn.hasEnemyPlayed = True
                next_turn.whoFightsNext = WhoFights.PLAYER
                fightUntilKO(next_turn, initial_turn, outcomesDic)
            elif move.effect == MoveEffect.SPEED_DOWN or move.effect == MoveEffect.DEFENSE_DOWN:
                # Move doesn't miss
                next_turn = tmp_turn_after_move_choice.__copy__()
                next_turn.name += f'->hit|'
                next_turn.remainingBadOutcomes -= 1

                next_turn.odds *= Odds(move.accuracy, 100)  # no miss
                next_turn.odds *= Odds(3, 4)  # no AI miss

                if move.effect == MoveEffect.SPEED_DOWN:
                    next_turn.playerMod.spd = next_turn.playerMod.bound(next_turn.playerMod.spd - 1)
                elif move.effect == MoveEffect.DEFENSE_DOWN:
                    next_turn.playerMod.deff = next_turn.playerMod.bound(next_turn.playerMod.deff - 1)

                next_turn.hasEnemyPlayed = True
                next_turn.whoFightsNext = WhoFights.PLAYER
                fightUntilKO(next_turn, initial_turn, outcomesDic)
                # fallthrough

                # Move can miss
                next_turn = tmp_turn_after_move_choice.__copy__()
                next_turn.name += f'->miss|'
                next_turn.remainingBadOutcomes -= 1

                miss_odds = Odds(100-move.accuracy, 100)  # normal miss
                miss_odds += Odds(move.accuracy, 100) * Odds(1, 4)  # AI miss

                next_turn.odds *= miss_odds

                next_turn.hasEnemyPlayed = True
                next_turn.whoFightsNext = WhoFights.PLAYER
                fightUntilKO(next_turn, initial_turn, outcomesDic)


def checkOddsValidity(final_turn: TurnActions, initial_turn: TurnActions):
    if final_turn.odds > initial_turn.odds:
        raise ValueError(f'Final odds are too high. Final:{final_turn}. Initial:{initial_turn}')


def fightUntilKO(previous_turn: TurnActions, initial_turn: TurnActions, outcomesDic: OutcomesDic):
    global total_entries

    # Check for too many bad outcomes
    if previous_turn.remainingBadOutcomes < 0:
        return

    # Check if there are no Rage PP left
    if previous_turn.playerMod.turn > 20:
        # checkOddsValidity(previous_turn, initial_turn)
        outcomesDic.add(FightOutcome.PLAYER_IS_KO, previous_turn)  # TODO : create another FightOutcome ?
        total_entries += 1
        print(total_entries) if total_entries % 10_000 == 0 else None
        return

    # Check for KO
    if previous_turn.enemy.currHP <= 0 or previous_turn.player.currHP <= 0:
        if previous_turn.enemy.currHP <= 0:
            outcome = FightOutcome.ENEMY_IS_KO
        else:
            outcome = FightOutcome.PLAYER_IS_KO
        # checkOddsValidity(previous_turn, initial_turn)
        outcomesDic.add(outcome, previous_turn)
        total_entries += 1
        print(total_entries) if total_entries % 10_000 == 0 else None
        return

    # Check if everyone has fought during a turn
    if previous_turn.hasPlayerPlayed and previous_turn.hasEnemyPlayed:
        # Poison tick
        if previous_turn.wasJustPoisoned:
            # If player was just poisoned, don't apply poison tick
            previous_turn.wasJustPoisoned = False
        elif previous_turn.player.isPoisoned and not previous_turn.wasPoisonApplied:
            next_turn = previous_turn

            next_turn.name += f'playerpsn->{previous_turn.player.hp // 8}|'

            next_turn.player.currHP -= previous_turn.player.hp // 8

            next_turn.wasPoisonApplied = True
            fightUntilKO(next_turn, initial_turn, outcomesDic)

        # Who plays next ?
        next_turn = previous_turn.__copy__()
        next_turn.name += '|'
        next_turn.hasPlayerPlayed = False
        next_turn.hasEnemyPlayed = False
        next_turn.wasPoisonApplied = False
        next_turn.playerMod.turn += 1
        next_turn.enemyMod.turn += 1

        playerSpd = previous_turn.playerMod.modSpd(previous_turn.player)
        enemySpd = previous_turn.enemyMod.modSpd(previous_turn.enemy)
        if playerSpd >= enemySpd:
            if playerSpd == enemySpd:
                next_turn.odds *= Odds(1, 2)
            next_turn.whoFightsNext = WhoFights.PLAYER
            fightUntilKO(next_turn, initial_turn, outcomesDic)
        if playerSpd <= enemySpd:
            if playerSpd == enemySpd:
                next_turn.odds *= Odds(1, 2)
            next_turn.whoFightsNext = WhoFights.ENEMY
            fightUntilKO(next_turn, initial_turn, outcomesDic)

    # Not everyone has fought : perform next half-turn
    if not previous_turn.hasPlayerPlayed and previous_turn.whoFightsNext == WhoFights.PLAYER:
        doPlayerTurn(previous_turn, initial_turn, outcomesDic)  # Calls fightUntilKO

    if not previous_turn.hasEnemyPlayed and previous_turn.whoFightsNext == WhoFights.ENEMY:
        doEnemyTurn(previous_turn, initial_turn, outcomesDic)  # Calls fightUntilKO


#
# Main code
#


# "globals"
total_entries = 0

TurnActions.MAX_BAD_OUTCOME = 2
allow_crits_for_player = True
allow_crits_for_enemy = True
store_all_scenarii = False


# Player
totodileDVs = [0]*4
elementalBadgeBoosts = [False]*17
elementalBadgeBoosts[Type.FLYING.value] = True
# player = Pokemon(TOTODILE, 16, totodileDVs,
#                        868, 868, 1108, 1108, 1019, 1019, 1203, 1203, 800, 800,
#                        [RAGE], False,
#                        elementalBadgeBoosts, atkBadge=True, defBadge=False, spdBadge=False, spcBadge=False,
#                        totalExp=2733)
playerMod = StatModifier()



metapod = Pokemon(METAPOD, 14, [9, 8, 8, 8],
                       0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                       [TACKLE, STRING_SHOT, HARDEN], False,
                       [False]*17)
kakuna = Pokemon(KAKUNA, 14, [9, 8, 8, 8],
                       0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                       [POISON_STING, STRING_SHOT, HARDEN], False,
                       [False]*17)
scyther = Pokemon(SCYTHER, 16, [9, 8, 8, 8],
                       0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                       [QUICK_ATTACK, LEER, FURY_CUTTER], False,
                       [False]*17)


party = [scyther]
# oldOutcomesDic = OutcomesDic()
with open('emptydics/Kakuna,TurnActions.MAX_BAD_OUTCOME=2,allow_crits_for_player=True,allow_crits_for_enemy=True,totodileDVs=[0, 0, 0, 0],player.currHP=43', 'rb') as file:
    oldOutcomesDic: OutcomesDic = pickle.load(file)
    print(oldOutcomesDic.short_display())  # To visually check the data is the desired one

partialOutcomesList = []
player = list(oldOutcomesDic[FightOutcome.ENEMY_IS_KO].keys())[0].player
previous_enemy: Pokemon = list(oldOutcomesDic[FightOutcome.ENEMY_IS_KO].keys())[0].enemy  # None

info_str = f'{TurnActions.MAX_BAD_OUTCOME=},{allow_crits_for_player=},{allow_crits_for_enemy=},{store_all_scenarii=},{totodileDVs=},{player.currHP=}'
print(info_str)

for enemy in party:
    newOutcomesDic = OutcomesDic()
    enemyMod = StatModifier()
    if len(oldOutcomesDic[FightOutcome.ENEMY_IS_KO]) == 0:
        # First Pokémon
        starting_turn = TurnActions("", player, enemy, playerMod, enemyMod, Odds(1, 1))
        fightUntilKO(starting_turn, starting_turn, newOutcomesDic)
    else:
        # Other Pokémon
        newOutcomesDic[FightOutcome.PLAYER_IS_KO] = oldOutcomesDic[FightOutcome.PLAYER_IS_KO]  # propagate player deaths
        newOutcomesDic.total_odds[FightOutcome.PLAYER_IS_KO] = oldOutcomesDic.total_odds[FightOutcome.PLAYER_IS_KO]

        for turn, tuplee in oldOutcomesDic[FightOutcome.ENEMY_IS_KO].items():
            # Saving previous total odds
            total_player_odds_before: Odds = newOutcomesDic.total_odds[FightOutcome.PLAYER_IS_KO]
            total_enemy_odds_before: Odds = newOutcomesDic.total_odds[FightOutcome.ENEMY_IS_KO]
            total_odds_before = total_player_odds_before + total_enemy_odds_before

            odds: Odds = tuplee[OutcomesDic.TOTAL_ODDS_IDX]  # Odds are not copied, but that shouldn't matter because fightUntilKO copies everything itself
            # Update player
            turn.player.gainStatExp(previous_enemy.species)
            turn.player.gainExp(previous_enemy.expGiven())

            # Update scenario
            turn.odds = odds
            turn.hasEnemyPlayed = True
            turn.hasPlayerPlayed = True
            turn.wasPoisonApplied = True
            turn.wasJustPoisoned = False
            turn.enemy = enemy
            turn.enemyMod = enemyMod
            fightUntilKO(turn, turn, newOutcomesDic)

            # Check if total added odds are valid for this scenario
            total_player_odds_after: Odds = newOutcomesDic.total_odds[FightOutcome.PLAYER_IS_KO]
            total_enemy_odds_after: Odds = newOutcomesDic.total_odds[FightOutcome.ENEMY_IS_KO]
            total_odds_after = total_player_odds_after + total_enemy_odds_after

            if odds < total_odds_after - total_odds_before:
                raise ValueError(f'Odds added for this scenario are too high. Maximum odds = {odds} < added = {total_odds_after - total_odds_before}. Starting turn:{turn}, {newOutcomesDic.short_display()}.')
            else:
                print(f'{total_odds_after - total_odds_before} out of {odds} added for scenario {turn}')

    oldOutcomesDic = newOutcomesDic
    previous_enemy = enemy
    partialOutcomesList.append(f'After {enemy.species.name}: {newOutcomesDic.short_display()}')
    with open(f'emptydics/{enemy.species.name},{info_str}_fromKakuna', 'wb') as file:
        pickle.dump(newOutcomesDic, file)

# print total
print(party)
# print(oldOutcomesDic.full_display())
print(info_str, f'{total_entries=}')
print(*partialOutcomesList, sep='\n')
print(f'playerKO_ratio={oldOutcomesDic.percentageOfPlayerDeaths()}%')
