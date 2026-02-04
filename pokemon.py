import os
import json
import math
import random

from move import Move

TYPE_TRANSLATIONS = {
    "normal": "normal",
    "fire": "feu",
    "water": "eau",
    "electric": "electrik",
    "grass": "plante",
    "ice": "glace",
    "fighting": "combat",
    "poison": "poison",
    "ground": "sol",
    "flying": "vol",
    "psychic": "psy",
    "bug": "insecte",
    "rock": "roche",
    "ghost": "spectre",
    "dragon": "dragon",
    "dark": "tenebres",
    "steel": "acier",
    "fairy": "fee",
}

TYPE_EFFECTIVENESS = {
    "normal": {"roche": 0.5, "spectre": 0.0, "acier": 0.5},
    "feu": {"feu": 0.5, "eau": 0.5, "plante": 2.0, "glace": 2.0, "insecte": 2.0, "roche": 0.5, "dragon": 0.5, "acier": 2.0},
    "eau": {"feu": 2.0, "eau": 0.5, "plante": 0.5, "sol": 2.0, "roche": 2.0, "dragon": 0.5},
    "electrik": {"eau": 2.0, "electrik": 0.5, "plante": 0.5, "sol": 0.0, "vol": 2.0, "dragon": 0.5},
    "plante": {"feu": 0.5, "eau": 2.0, "plante": 0.5, "poison": 0.5, "sol": 2.0, "vol": 0.5, "insecte": 0.5, "roche": 2.0, "dragon": 0.5, "acier": 0.5},
    "glace": {"feu": 0.5, "eau": 0.5, "plante": 2.0, "sol": 2.0, "vol": 2.0, "dragon": 2.0, "acier": 0.5},
    "combat": {"normal": 2.0, "glace": 2.0, "roche": 2.0, "tenebres": 2.0, "acier": 2.0, "poison": 0.5, "vol": 0.5, "psy": 0.5, "insecte": 0.5, "spectre": 0.0, "fee": 0.5},
    "poison": {"plante": 2.0, "poison": 0.5, "sol": 0.5, "roche": 0.5, "spectre": 0.5, "acier": 0.0, "fee": 2.0},
    "sol": {"feu": 2.0, "electrik": 2.0, "plante": 0.5, "poison": 2.0, "vol": 0.0, "insecte": 0.5, "roche": 2.0, "acier": 2.0},
    "vol": {"electrik": 0.5, "plante": 2.0, "combat": 2.0, "insecte": 2.0, "roche": 0.5, "acier": 0.5},
    "psy": {"combat": 2.0, "poison": 2.0, "psy": 0.5, "tenebres": 0.0, "acier": 0.5},
    "insecte": {"feu": 0.5, "plante": 2.0, "combat": 0.5, "poison": 0.5, "vol": 0.5, "psy": 2.0, "spectre": 0.5, "tenebres": 2.0, "acier": 0.5, "fee": 0.5},
    "roche": {"feu": 2.0, "glace": 2.0, "combat": 0.5, "sol": 0.5, "vol": 2.0, "insecte": 2.0, "acier": 0.5},
    "spectre": {"normal": 0.0, "psy": 2.0, "spectre": 2.0, "tenebres": 0.5},
    "dragon": {"dragon": 2.0, "acier": 0.5, "fee": 0.0},
    "tenebres": {"combat": 0.5, "psy": 2.0, "spectre": 2.0, "tenebres": 0.5, "fee": 0.5},
    "acier": {"feu": 0.5, "eau": 0.5, "electrik": 0.5, "glace": 2.0, "roche": 2.0, "fee": 2.0, "acier": 0.5},
    "fee": {"feu": 0.5, "combat": 2.0, "poison": 0.5, "dragon": 2.0, "tenebres": 2.0, "acier": 0.5},
}

def _normalize_type(type_name: str) -> str:
    if not type_name:
        return ""
    normalized = str(type_name).lower().replace("é", "e").replace("è", "e").replace("ê", "e")
    if normalized in TYPE_TRANSLATIONS.values():
        return normalized
    return TYPE_TRANSLATIONS.get(normalized, normalized)

class Pokemon:
    """
    Pokémon class to manage the Pokémons
    """
    def __init__(self, data, level: int) -> None:
        self.klass = data['klass']
        self.id = data['id']
        self.dbSymbol = data['dbSymbol']
        self.forms = data['forms']
        self.evolutions = self.forms[0]['evolutions']
        self.type = self.get_types()
        self.baseHp = self.forms[0]['baseHp']
        self.baseAtk = self.forms[0]['baseAtk']
        self.baseDfe = self.forms[0]['baseDfe']
        self.baseSpd = self.forms[0]['baseSpd']
        self.baseAts = self.forms[0]['baseAts']
        self.baseDfs = self.forms[0]['baseDfs']
        self.evHp = self.forms[0]['evHp']
        self.evAtk = self.forms[0]['evAtk']
        self.evDfe = self.forms[0]['evDfe']
        self.evSpd = self.forms[0]['evSpd']
        self.evAts = self.forms[0]['evAts']
        self.evDfs = self.forms[0]['evDfs']
        self.experienceType = self.forms[0]['experienceType']
        self.baseExperience = self.forms[0]['baseExperience']
        self.baseLoyalty = self.forms[0]['baseLoyalty']
        self.catchRate = self.forms[0]['catchRate']
        self.femaleRate = self.forms[0]['femaleRate']
        self.breedGroups = self.forms[0]['breedGroups']
        self.hatchSteps = self.forms[0]['hatchSteps']
        self.babyDbSymbol = self.forms[0]['babyDbSymbol']
        self.babyForm = self.forms[0]['babyForm']
        self.itemHeld = self.forms[0]['itemHeld']
        self.abilities = self.forms[0]['abilities']
        self.frontOffsetY = self.forms[0]['frontOffsetY']
        self.resources = self.forms[0]['resources']
        self.moveSet = self.forms[0]['moveSet']

        self.level = level
        self.gender = "female" if random.randint(1, 100) <= self.femaleRate else "male"
        if self.femaleRate == -1:
            self.gender = "genderless"
        self.ivs = {key: random.randint(1, 31) for key in self.get_base_stats().keys()}
        self.base_stats = self.get_base_stats()

        self.maxhp = self.update_stats("hp")
        self.hp = self.update_stats("hp")
        self.atk = self.update_stats("atk")
        self.dfe = self.update_stats("dfe")
        self.ats = self.update_stats("ats")
        self.dfs = self.update_stats("dfs")
        self.spd = self.update_stats("spd")

        self.shiny = "shiny" if random.randint(1, 30) == 1 else ""
        self.xp = 0
        self.points_ev = 0

        self.moves: list[Move] = self.set_moves()
        self.status = ""

        self.xp_to_next_level = self.get_xp_to_next_level()

        self.evolution = None

    def get_types(self):
        type1 = _normalize_type(self.forms[0]['type1'])
        type2 = _normalize_type(self.forms[0]['type2'])
        if type2 == "__undef__":
            return [type1]
        return [type1, type2]

    def get_base_stats(self):
        return {
            "hp": self.forms[0]['baseHp'],
            "atk": self.forms[0]['baseAtk'],
            "dfe": self.forms[0]['baseDfe'],
            "spd": self.forms[0]['baseSpd'],
            "ats": self.forms[0]['baseAts'],
            "dfs": self.forms[0]['baseDfs'],
        }

    def update_stats(self, stat):
        base_stat = self.get_base_stats()[stat]
        iv = self.ivs[stat]
        ev = self.get_ev()[stat]
        level = self.level
        nature = 1.0
        if stat == "hp":
            return math.floor(((2 * base_stat + iv + math.floor(ev / 4)) * level / 100) + level / 10)
        return math.floor((((2 * base_stat + iv + math.floor(ev / 4)) * level / 100) + 5) * nature)

    def get_xp_to_next_level(self):
        if self.level == 100:
            return 0
        if self.experienceType == 1:
            return math.floor((4 * (self.level ** 3)) / 5)
        elif self.experienceType == 3:
            return math.floor(((6 / 5) * (self.level ** 3)) - (15 * (self.level ** 2)) + (100 * self.level) - 140)
        elif self.experienceType == 0:
            return self.level ** 3
        elif self.experienceType == 2:
            return 5 * (self.level ** 3) / 4
        elif self.experienceType == 4:
            if self.level <= 50:
                return math.floor((self.level ** 3) * (100 - self.level) / 50)
            elif self.level <= 68:
                return math.floor((self.level ** 3) * (150 - self.level) / 100)
            elif self.level <= 98:
                return math.floor((self.level ** 3) * math.floor((1911 - 10 * self.level) / 3) / 500)
            elif self.level <= 100:
                return math.floor((self.level ** 3) * (160 - self.level) / 100)

    def set_moves(self):
        list_move: list[dict] = []
        list_attack: list[Move] = []
        for move in self.moveSet:
            try:
                if move['level'] <= self.level:
                    list_move.append(move)
            except:
                pass
        minimum = 2
        if len(list_move) < minimum:
            minimum = len(list_move)
        maximum = 4
        if len(list_move) < 4:
            maximum = len(list_move)
        for i in range(random.randint(minimum, maximum)):
            chosen = random.choice(list_move)
            list_move.remove(chosen)
            list_attack.append(Move.createMove(chosen['move']))
        return list_attack

    def get_ev(self):
        return {
            "hp": self.forms[0]["evHp"],
            "atk": self.forms[0]["evAtk"],
            "dfe": self.forms[0]["evDfe"],
            "ats": self.forms[0]["evAts"],
            "dfs": self.forms[0]["evDfs"],
            "spd": self.forms[0]["evSpd"]
        }

    def gain_xp(self, amount: int):
        if amount <= 0 or self.level >= 100:
            return []
        self.xp += amount
        levels_gained = []
        while self.level < 100 and self.xp >= self.xp_to_next_level:
            self.level += 1
            levels_gained.append(self.level)
            old_max = self.maxhp
            self._recalculate_stats()
            self.xp_to_next_level = self.get_xp_to_next_level()
            self.hp = min(self.maxhp, self.hp + (self.maxhp - old_max))
        return levels_gained

    def _recalculate_stats(self):
        self.maxhp = self.update_stats("hp")
        self.atk = self.update_stats("atk")
        self.dfe = self.update_stats("dfe")
        self.ats = self.update_stats("ats")
        self.dfs = self.update_stats("dfs")
        self.spd = self.update_stats("spd")

    @staticmethod
    def type_multiplier(move_type: str, defender_types: list[str]) -> float:
        if not move_type:
            return 1.0
        move_type = _normalize_type(move_type)
        multiplier = 1.0
        for def_type in defender_types:
            def_type = _normalize_type(def_type)
            multiplier *= TYPE_EFFECTIVENESS.get(move_type, {}).get(def_type, 1.0)
        return multiplier

    @staticmethod
    def calculate_damage(attacker: "Pokemon", defender: "Pokemon", move: Move, critical: bool = False) -> dict:
        if move is None or not move.power:
            return {"damage": 0, "modifier": 0, "effectiveness": 0}

        category = str(getattr(move, "category", "")).lower()
        if category in ("special", "sp", "special_attack"):
            attack_stat = max(1, attacker.ats)
            defense_stat = max(1, defender.dfs)
        else:
            attack_stat = max(1, attacker.atk)
            defense_stat = max(1, defender.dfe)

        level_factor = (2 * attacker.level / 5) + 2
        base_damage = (((level_factor * move.power * (attack_stat / defense_stat)) / 50) + 2)

        move_type = _normalize_type(move.type) if move.type else ""
        stab = 1.5 if move_type and move_type in [_normalize_type(t) for t in attacker.type] else 1.0
        effectiveness = Pokemon.type_multiplier(move_type, defender.type)
        crit = 1.5 if critical else 1.0
        rand = random.uniform(0.85, 1.0)

        modifier = stab * effectiveness * crit * rand
        damage = max(1, int(base_damage * modifier))
        return {"damage": damage, "modifier": modifier, "effectiveness": effectiveness}

    def to_dict(self):
        return {
            'klass': self.klass,
            'id': self.id,
            'dbSymbol': self.dbSymbol,
            'forms': self.forms,
            'type': self.type,
            'level': self.level,
            'gender': self.gender,
            'ivs': self.ivs,
            'base_stats': self.base_stats,
            'maxhp': self.maxhp,
            'hp': self.hp,
            'atk': self.atk,
            'dfe': self.dfe,
            'ats': self.ats,
            'dfs': self.dfs,
            'spd': self.spd,
            'shiny': self.shiny,
            'xp': self.xp,
            'points_ev': self.points_ev,
            'moves': [move.to_dict() for move in self.moves],
            'status': self.status,
            'xp_to_next_level': self.xp_to_next_level,
            'evolution': self.evolution
        }

    @staticmethod
    def from_dict(data: dict) -> "Pokemon":
        pokemon = Pokemon.__new__(Pokemon)
        pokemon.__dict__.update(data)
        pokemon.moves = [Move.from_dict(move_data) for move_data in data["moves"]]
        return pokemon

    @staticmethod
    def create_pokemon(name: str, level: int) -> "Pokemon":
        base_path = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        file_path = os.path.join(base_path, "assets", "json", "pokemon", f"{name.lower()}.json")
        with open(file_path, "r", encoding="utf-8") as f:
            return Pokemon(json.load(f), level)
