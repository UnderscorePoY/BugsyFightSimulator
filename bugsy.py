import copy
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
                 totalExp=0, isPoison=False):
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
        self.isPoison = isPoison

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

    def updateToNew(self, numMult, denomMult, idx, scoreDelta):
        copyy = self.__copy__()
        copyy.odds *= Odds(numMult, denomMult)
        copyy.scores[idx] += scoreDelta
        return copyy


#
# AI
#
def ai_setup(moves, playerMod: StatModifier, enemyMod: StatModifier, scoring: Scoring):
    scorings: list[Scoring] = [scoring]
    for i, move in enumerate(moves):
        # Stat-up
        if move.name == HARDEN.name:
            tmp_scorings = []
            if enemyMod.turn == 1:
                for sc in scorings:
                    # 50% greatly encourage
                    scoring1 = sc.updateToNew(1, 2, i, -2)
                    # 50% to do nothing
                    scoring2 = sc.updateToNew(1, 2, i, +0)
                    tmp_scorings.extend([scoring1, scoring2])
                scorings = tmp_scorings
            else:  # enemyMod.turn > 1
                for sc in scorings:
                    # 226/256 to greatly discourage
                    scoring1 = sc.updateToNew(226, 256, i, +2)
                    # 30/256 to do nothing
                    scoring2 = sc.updateToNew(30, 256, i, +0)
                    tmp_scorings.extend([scoring1, scoring2])
                scorings = tmp_scorings
        # end Stat-up

        # Stat-down
        if move.name in [x.name for x in [STRING_SHOT, LEER]]:
            tmp_scorings = []
            if playerMod.turn == 1:
                for sc in scorings:
                    # 50% greatly encourage
                    scoring1 = sc.updateToNew(1, 2, i, -2)
                    # 50% to do nothing
                    scoring2 = sc.updateToNew(1, 2, i, +0)
                    tmp_scorings.extend([scoring1, scoring2])
                scorings = tmp_scorings
            else:  # playerMod.turn > 1
                for sc in scorings:
                    # 226/256 to greatly discourage
                    scoring1 = sc.updateToNew(226, 256, i, +2)
                    # 30/256 to do nothing
                    scoring2 = sc.updateToNew(30, 256, i, +0)
                    tmp_scorings.extend([scoring1, scoring2])
                scorings = tmp_scorings
        # end Stat-down
    return scorings


def ai_smart_furycutter(moves, enemyMod: StatModifier, enemy: Pokemon, scoring: Scoring):
    scorings: list[Scoring] = [scoring]
    for i, move in enumerate(moves):
        if move.name == FURY_CUTTER.name:
            if enemyMod.furycutterNb >= 1:
                scoring.scores[i] -= 1
            if enemyMod.furycutterNb >= 2:
                scoring.scores[i] -= 2
            if enemyMod.furycutterNb >= 3:
                scoring.scores[i] -= 3

            tmp_scorings = []
            if 100 * enemy.currHP / enemy.hp <= 25:  # TODO : is probably not the comparison used in the original code
                # 200/256 to discourage if enemy HP is 25% or below
                scoring1 = scoring.updateToNew(200, 256, i, +1)
                scoring2 = scoring.updateToNew(56, 256, i, +0)
                tmp_scorings.extend([scoring1, scoring2])
            else:
                # 200/256 to greatly encourage
                scoring1 = scoring.updateToNew(200, 256, i, -2)
                scoring2 = scoring.updateToNew(56, 256, i, +0)
                tmp_scorings.extend([scoring1, scoring2])
            scorings = tmp_scorings
    return scorings


def ai_aggressive(moves, playerMod: StatModifier, enemyMod: StatModifier, player: Pokemon, enemy: Pokemon, scoring: Scoring):
    # Discourage damaging moves that are not dealing the most damage
    i_max, dmg_max = None, 0

    for i, move in enumerate(moves):
        if move.power <= 1:
            continue

        dmg = calc_damage(move, enemy, player, enemyMod, playerMod, MAX_RANGE-1, crit=False, extra_multiplier=1)
        if dmg > dmg_max:
            i_max, dmg_max = i, dmg

    for i, move in enumerate(moves):
        if i_max is not None and move.power > 1 and i != i_max:
            scoring.scores[i] += 1

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

    #AI_SMART_FURYCUTTER
    tmp_scorings = []
    for sc in scorings:
        tmp_scs = ai_smart_furycutter(moves, enemyMod, enemy, sc)
        tmp_scorings.extend(tmp_scs)
    scorings = tmp_scorings

    #AI_AGGRESSIVE
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

    def __add__(self, other):
        self.in_place_add(other)
        return self

    def in_place_add(self, other):
        if self.numerator == 0 and other.numerator == 0:
            self.numerator = 0
            self.denominator = 1

        self.numerator = self.numerator * other.denominator + other.numerator * self.denominator
        self.denominator = self.denominator * other.denominator
        self.simplify()

    def __mul__(self, other):
        self.in_place_mult(other)
        return self

    def in_place_mult(self, other):
        if self.numerator == 0 or other.numerator == 0:
            self.numerator = 0
            self.denominator = 1

        self.numerator = self.numerator * other.numerator
        self.denominator = self.denominator * other.denominator
        self.simplify()

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
        minn = min(scoring.scores)
        min_idxs = [i for i, _ in enumerate(scoring.scores) if scoring.scores[i] == minn]
        newOdds = scoring.odds * Odds(1, len(min_idxs))
        for i in min_idxs:
            odds_list[i] += newOdds

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
                 wasPoisonApplied=True):
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
        self.remainingBadOutcomes = TurnActions.MAX_BAD_OUTCOME

    def __copy__(self):
        return copy.deepcopy(self)

    def __repr__(self):
        return f'{self.player.currHP=} {self.player.isPoison=} {self.playerMod=} {self.odds =} {self.name} '

    def __hash__(self):
        hashVal = (self.playerMod.spd + 6)
        hashVal <<= 4
        hashVal += self.playerMod.rageNb
        hashVal <<= 6
        hashVal += self.player.currHP
        hashVal <<= 1
        hashVal += 1 if self.player.isPoison else 0
        return hashVal

    # TODO : may be problematic for further usage ?
    def __eq__(self, other):
        return hash(self) == hash(other)


class FightOutcome(Enum):
    STILL_GOING = 0
    PLAYER_KO = 1
    ENEMY_KO = 2


#
# OutcomesDic
#
class OutcomesDic:
    TOTAL_ODDS_IDX = 0
    LIST_TURNS_IDX = 1

    # dict[FightOutcome, dict[TurnActions, tuple[Odds, list[TurnActions]]] = {

    def __init__(self):
        self.dic: dict[FightOutcome, dict[TurnActions, tuple[Odds, list[TurnActions]]]] \
            = {FightOutcome.PLAYER_KO: {}, FightOutcome.ENEMY_KO: {}}
        self.total_odds: dict[FightOutcome, Odds] \
            = {FightOutcome.PLAYER_KO: Odds(0, 1), FightOutcome.ENEMY_KO: Odds(0, 1)}

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
        player = self.total_odds[FightOutcome.PLAYER_KO].percentage()
        enemy = self.total_odds[FightOutcome.ENEMY_KO].percentage()
        total = player + enemy
        return f'PLAYER_KO={player}%, ENEMY_KO={enemy}%, TOTAL={total}%'

    def full_display(self):
        return repr(self.dic) + self.short_display()

    def percentageOfPlayerDeaths(self):
        player = self.total_odds[FightOutcome.PLAYER_KO].percentage()
        enemy = self.total_odds[FightOutcome.ENEMY_KO].percentage()
        total = player + enemy
        return 100 * player / total


def doPlayerTurn(t: TurnActions, outcomesDic: OutcomesDic):
    # Normal hits
    playerNormalDamages = allNormalDamage(RAGE, t.player, t.enemy, t.playerMod, t.enemyMod, extraMultiplier=t.playerMod.rageNb)
    for dmg, roll in playerNormalDamages.dic.items():
        next_turn = t.__copy__()
        next_turn.name += f'Player->Rage{t.playerMod.rageNb}->noCrit->{dmg}|'

        next_turn.odds *= Odds(15, 16)  # no crit
        next_turn.odds *= Odds(roll, 39)  # roll odds

        # enemyCopy = t.enemy.__copy__()
        # enemyCopy.currHP -= dmg
        # next_turn.enemy = enemyCopy
        next_turn.enemy.currHP -= dmg

        next_turn.hasPlayerPlayed = True
        next_turn.whoFightsNext = WhoFights.ENEMY
        fightUntilKO(next_turn, outcomesDic)
        # fallthrough

    # Crit hits
    if not allow_crits_for_player:
        return

    playerCritDamages = allCritDamage(RAGE, t.player, t.enemy, t.playerMod, t.enemyMod, extraMultiplier=t.playerMod.rageNb)
    for dmg, roll in playerCritDamages.dic.items():
        next_turn = t.__copy__()
        next_turn.name += f'Player->Rage{t.playerMod.rageNb}->crit->{dmg}|'

        next_turn.odds *= Odds(1, 16)  # crit
        next_turn.odds *= Odds(roll, 39)  # roll odds

        # enemyCopy = t.enemy.__copy__()
        # enemyCopy.currHP -= dmg
        # next_turn.enemy = enemyCopy
        next_turn.enemy.currHP -= dmg

        next_turn.hasPlayerPlayed = True
        next_turn.whoFightsNext = WhoFights.ENEMY
        fightUntilKO(next_turn, outcomesDic)
    ###


def enemyMultiplier(move: Move, enemyMod: StatModifier):
    return 1 << enemyMod.furycutterNb if move.name == FURY_CUTTER.name else 1


def doEnemyTurn(t: TurnActions, outcomesDic: OutcomesDic):
    # AI
    ai_scorings = perform_ai_turn(t.enemy.moves, t.playerMod, t.enemyMod, t.player, t.enemy)
    move_odds = extract_move_odds(ai_scorings)

    for i, oddsToChooseMove in enumerate(move_odds):
        move = t.enemy.moves[i]

        next_t = t.__copy__()
        next_t.name += f'{t.enemy.species.name}->{move.name}'
        if move.name == FURY_CUTTER.name:
            next_t.name += f'{next_t.enemyMod.furycutterNb+1}'

        next_t.odds *= oddsToChooseMove
        # Move deals damage
        if move.power >= 2:
            # Normal hits
            enemyNormalDamages = allNormalDamage(move, t.enemy, t.player, t.enemyMod, t.playerMod,
                                                  extraMultiplier=enemyMultiplier(move, t.enemyMod))
            for dmg, roll in enemyNormalDamages.dic.items():
                next_turn = next_t.__copy__()
                next_turn.name += f'->noCrit->{dmg}'

                next_turn.odds *= Odds(move.accuracy, 100)  # no miss
                next_turn.odds *= Odds(15, 16)  # no crit
                next_turn.odds *= Odds(roll, 39)  # roll odds

                # playerCopy = next_t.player.__copy__()
                # playerCopy.currHP -= dmg
                # next_turn.player = playerCopy
                next_turn.player.currHP -= dmg

                # Update Rage
                # playerModCopy = next_t.playerMod.__copy__()
                # playerModCopy.rageNb = min(8, playerModCopy.rageNb + 1)
                # next_turn.playerMod = playerModCopy
                next_turn.playerMod.rageNb = min(8, next_turn.playerMod.rageNb + 1)
                if move.name == FURY_CUTTER.name:
                    next_turn.enemyMod.furycutterNb = min(5, next_turn.enemyMod.furycutterNb + 1)

                next_turn.hasEnemyPlayed = True
                next_turn.whoFightsNext = WhoFights.PLAYER

                if move.effect == MoveEffect.POISON_HIT and not next_turn.player.isPoison:
                    # no poison
                    next_turn_noPSN = next_turn.__copy__()
                    next_turn_noPSN.name += '|'
                    next_turn_noPSN.odds *= Odds(100-move.effectChance, 100)
                    fightUntilKO(next_turn_noPSN, outcomesDic)

                    # poison
                    next_turn_PSN = next_turn.__copy__()
                    next_turn_PSN.name += '->PSN|'
                    next_turn_PSN.odds *= Odds(move.effectChance, 100)
                    next_turn_PSN.remainingBadOutcomes -= 1

                    # playerCopy2 = next_turn_PSN.player.__copy__()
                    # playerCopy2.isPoison = True
                    # next_turn_PSN.player = playerCopy2
                    next_turn_PSN.player.isPoison = True

                    fightUntilKO(next_turn_PSN, outcomesDic)
                else:
                    next_turn.name += '|'
                    fightUntilKO(next_turn, outcomesDic)


            # Crit hits
            if allow_crits_for_enemy:
                enemyCritDamages = allCritDamage(move, t.enemy, t.player, t.enemyMod, t.playerMod,
                                                     extraMultiplier=enemyMultiplier(move, t.enemyMod))
                for dmg, roll in enemyCritDamages.dic.items():
                    next_turn = next_t.__copy__()
                    next_turn.name += f'->crit->{dmg}'

                    next_turn.odds *= Odds(move.accuracy, 100)  # no miss
                    next_turn.odds *= Odds(1, 16)  # no crit
                    next_turn.odds *= Odds(roll, 39)  # roll odds

                    # playerCopy = next_t.player.__copy__()
                    # playerCopy.currHP -= dmg
                    # next_turn.player = playerCopy
                    next_turn.player.currHP -= dmg

                    # Update Rage
                    # playerModCopy = next_t.playerMod.__copy__()
                    # playerModCopy.rageNb += 1
                    # next_turn.playerMod = playerModCopy
                    next_turn.playerMod.rageNb = min(8, next_turn.playerMod.rageNb + 1)

                    next_turn.hasEnemyPlayed = True
                    next_turn.whoFightsNext = WhoFights.PLAYER

                    if move.effect == MoveEffect.POISON_HIT and not next_turn.player.isPoison:
                        # no poison
                        next_turn_noPSN = next_turn.__copy__()
                        next_turn_noPSN.name += '|'
                        next_turn_noPSN.odds *= Odds(100-move.effectChance, 100)
                        fightUntilKO(next_turn_noPSN, outcomesDic)

                        # poison
                        next_turn_PSN = next_turn.__copy__()
                        next_turn_PSN.name += '->PSN|'
                        next_turn_PSN.odds *= Odds(move.effectChance, 100)
                        next_turn_PSN.remainingBadOutcomes -= 1

                        # playerCopy2 = next_turn_PSN.player.__copy__()
                        # playerCopy2.isPoison = True
                        # next_turn_PSN.player = playerCopy2
                        next_turn_PSN.player.isPoison = True

                        fightUntilKO(next_turn_PSN, outcomesDic)
                    else:
                        next_turn.name += '|'
                        fightUntilKO(next_turn, outcomesDic)
                    # fallthrough

            # Move can miss
            if move.accuracy < 100:
                next_turn = next_t.__copy__()
                next_turn.name += '->miss|'
                next_turn.odds *= Odds(100-move.accuracy, 100)
                if move.name == FURY_CUTTER.name:
                    next_turn.enemyMod.furycutterNb = 0
                next_turn.remainingBadOutcomes -= 1

                next_turn.hasEnemyPlayed = True
                next_turn.whoFightsNext = WhoFights.PLAYER
                fightUntilKO(next_turn, outcomesDic)

        # Move deals no damage
        if move.power == 0:
            if move.effect == MoveEffect.DEFENSE_UP:
                next_turn = next_t.__copy__()
                next_turn.name += f'|'

                # enemyModCopy = next_t.enemyMod.__copy__()
                # enemyModCopy.deff = enemyModCopy.bound(enemyModCopy.deff + 1)
                # next_turn.enemyMod = enemyModCopy
                next_turn.enemyMod.deff = next_turn.enemyMod.bound(next_turn.enemyMod.deff + 1)

                next_turn.remainingBadOutcomes -= 1

                next_turn.hasEnemyPlayed = True
                next_turn.whoFightsNext = WhoFights.PLAYER
                fightUntilKO(next_turn, outcomesDic)
            elif move.effect == MoveEffect.SPEED_DOWN or move.effect == MoveEffect.DEFENSE_DOWN:
                # Move doesn't miss
                next_turn = next_t.__copy__()
                next_turn.name += f'->hit|'
                next_turn.remainingBadOutcomes -= 1

                next_turn.odds *= Odds(move.accuracy, 100)  # no miss

                next_turn.odds *= Odds(3, 4)  # no AI miss

                # playerModCopy = next_turn.playerMod.__copy__()
                # if move.effect == MoveEffect.SPEED_DOWN:
                #     playerModCopy.spd = playerModCopy.bound(playerModCopy.spd - 1)
                # elif move.effect == MoveEffect.DEFENSE_DOWN:
                #     playerModCopy.deff = playerModCopy.bound(playerModCopy.deff - 1)
                # next_turn.playerMod = playerModCopy
                if move.effect == MoveEffect.SPEED_DOWN:
                    next_turn.playerMod.spd = next_turn.playerMod.bound(next_turn.playerMod.spd - 1)
                elif move.effect == MoveEffect.DEFENSE_DOWN:
                    next_turn.playerMod.deff = next_turn.playerMod.bound(next_turn.playerMod.deff - 1)

                next_turn.hasEnemyPlayed = True
                next_turn.whoFightsNext = WhoFights.PLAYER
                fightUntilKO(next_turn, outcomesDic)
                # fallthrough

                # Move can miss
                if move.effect == MoveEffect.SPEED_DOWN:
                    next_turn = next_t.__copy__()
                    next_turn.name += f'->miss|'
                    next_turn.remainingBadOutcomes -= 1

                    next_turn.odds *= (Odds(100-move.accuracy, 100) + Odds(move.accuracy, 100)*Odds(1, 4))  # miss or 'no miss w/ AI miss'

                    next_turn.hasEnemyPlayed = True
                    next_turn.whoFightsNext = WhoFights.PLAYER
                    fightUntilKO(next_turn, outcomesDic)


def fightUntilKO(previous_turn: TurnActions, outcomesDic: OutcomesDic):
    # Just so it feels like it's working
    global total_entries
    if total_entries > 0 and total_entries % 10_000 == 0:
        print(total_entries)

    t = previous_turn

    # Check for too many bad outcomes
    if t.remainingBadOutcomes < 0:
        return

    # Check if there are no Rage PP left
    if t.playerMod.turn > 20:
        outcomesDic.add(FightOutcome.PLAYER_KO, t)  # TODO : create another FightOutcome ?
        total_entries += 1
        return

    # Check for KO
    if t.enemy.currHP <= 0 or t.player.currHP <= 0:
        if t.enemy.currHP <= 0:
            outcome = FightOutcome.ENEMY_KO
        else:
            outcome = FightOutcome.PLAYER_KO
        outcomesDic.add(outcome, t)
        total_entries += 1
        return

    # Check if everyone has fought during a turn
    if t.hasPlayerPlayed and t.hasEnemyPlayed:
        # Poison tick
        if t.player.isPoison and not t.wasPoisonApplied:
            # next_turn = t.__copy__()
            next_turn = t

            next_turn.name += f'|playerpsn->{t.player.hp // 8}'

            # playerCopy = next_turn.player.__copy__()
            # playerCopy.currHP -= playerCopy.hp // 8
            # next_turn.player = playerCopy
            next_turn.player.currHP -= next_turn.player.hp // 8

            next_turn.wasPoisonApplied = True
            fightUntilKO(next_turn, outcomesDic)

        # Who plays next ?
        next_turn = t.__copy__()
        next_turn.name += '|'
        next_turn.hasPlayerPlayed = False
        next_turn.hasEnemyPlayed = False
        next_turn.wasPoisonApplied = False
        next_turn.playerMod.turn += 1
        next_turn.enemyMod.turn += 1

        playerSpd = t.playerMod.modSpd(t.player)
        enemySpd = t.enemyMod.modSpd(t.enemy)
        if playerSpd >= enemySpd:
            if playerSpd == enemySpd:
                next_turn.odds *= Odds(1, 2)
            next_turn.whoFightsNext = WhoFights.PLAYER
            fightUntilKO(next_turn, outcomesDic)
        if playerSpd <= enemySpd:
            if playerSpd == enemySpd:
                next_turn.odds *= Odds(1, 2)
            next_turn.whoFightsNext = WhoFights.ENEMY
            fightUntilKO(next_turn, outcomesDic)

    # Not everyone has fought : perform next half-turn
    if not t.hasPlayerPlayed and t.whoFightsNext == WhoFights.PLAYER:
        doPlayerTurn(t, outcomesDic)  # Calls fightUntilKO

    if not t.hasEnemyPlayed and t.whoFightsNext == WhoFights.ENEMY:
        doEnemyTurn(t, outcomesDic)  # Calls fightUntilKO


#
# Main code
#


# "globals"
total_entries = 0

TurnActions.MAX_BAD_OUTCOME = 1
allow_crits_for_player = False
allow_crits_for_enemy = False
store_all_scenarii = False


# Player
totodileDVs = [0]*4
elementalBadgeBoosts = [False]*17
elementalBadgeBoosts[Type.FLYING.value] = True
player = Pokemon(TOTODILE, 16, totodileDVs,
                       868, 868, 1108, 1108, 1019, 1019, 1203, 1203, 800, 800,
                       [RAGE], False,
                       elementalBadgeBoosts, atkBadge=True, defBadge=False, spdBadge=False, spcBadge=False,
                       totalExp=2733)
playerMod = StatModifier()

info_str = f'{TurnActions.MAX_BAD_OUTCOME=}, {allow_crits_for_player=}, {allow_crits_for_enemy=}, {totodileDVs=}, {player.currHP=}'
print(info_str)

# FIRST MON
metapod = Pokemon(METAPOD, 14, [9, 8, 8, 8],
                       0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                       [TACKLE, STRING_SHOT, HARDEN], False,
                       [False]*17)
metapodMod = StatModifier()

outcomesDic1 = OutcomesDic()
starting_turn = TurnActions("", player, metapod, playerMod, metapodMod, Odds(1, 1))
fightUntilKO(starting_turn, outcomesDic1)

# print total
print(outcomesDic1.full_display())
print(outcomesDic1.short_display())


# SECOND MON
kakuna = Pokemon(KAKUNA, 14, [9, 8, 8, 8],
                       0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                       [POISON_STING, STRING_SHOT, HARDEN], False,
                       [False]*17)
kakunaMod = StatModifier()
outcomesDic2 = OutcomesDic()
outcomesDic2[FightOutcome.PLAYER_KO] = outcomesDic1[FightOutcome.PLAYER_KO]  # propagate player deaths

for turn, tuplee in outcomesDic1[FightOutcome.ENEMY_KO].items():
    odds: Odds = tuplee[OutcomesDic.TOTAL_ODDS_IDX]
    # Update player
    turn.player.gainStatExp(metapod.species)
    turn.player.gainExp(metapod.expGiven())

    # Update scenario
    turn.odds = odds
    turn.hasEnemyPlayed = True
    turn.hasPlayerPlayed = True
    turn.wasPoisonApplied = False
    turn.enemy = kakuna  # .__copy__()
    turn.enemyMod = kakunaMod  # .__copy__()
    fightUntilKO(turn, outcomesDic2)

# print total
print(outcomesDic2.full_display())
print(outcomesDic2.short_display())

# THIRD MON
scyther = Pokemon(SCYTHER, 16, [9, 8, 8, 8],
                       0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                       [QUICK_ATTACK, LEER, FURY_CUTTER], False,
                       [False]*17)
scytherMod = StatModifier()
outcomesDic3 = OutcomesDic()
outcomesDic3[FightOutcome.PLAYER_KO] = outcomesDic2[FightOutcome.PLAYER_KO]  # propagate player deaths

for turn, tuplee in outcomesDic2[FightOutcome.ENEMY_KO].items():
    odds: Odds = tuplee[OutcomesDic.TOTAL_ODDS_IDX]
    # Update player
    turn.player.gainStatExp(kakuna.species)
    turn.player.gainExp(kakuna.expGiven())

    # Update scenario
    turn.odds = odds
    turn.hasEnemyPlayed = True
    turn.hasPlayerPlayed = True
    turn.wasPoisonApplied = False
    turn.enemy = scyther  # .__copy__()
    turn.enemyMod = scytherMod  # .__copy__()
    fightUntilKO(turn, outcomesDic3)

# print total
print(outcomesDic3.full_display())
print(info_str, f'{total_entries=}')
print(outcomesDic3.short_display())
print(f'playerKO_ratio={outcomesDic3.percentageOfPlayerDeaths()}%')
