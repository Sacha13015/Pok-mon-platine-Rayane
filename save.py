import os
import json
import pathlib

from map import Map
from player import Player
from sql import SQL
from keylistener import KeyListener
from dialogue import Dialogue

class Save:
    """
    Save class to manage the save
    """
    def __init__(self, path: str, map: Map, player: Player, keylistener: KeyListener, dialogue: Dialogue):
        self.path: str = path
        self.map: Map = map
        self.player: Player = player
        self.keylistener: KeyListener = keylistener
        self.dialogue: Dialogue = dialogue
        self.sql: SQL = SQL()

    def save(self) -> None:
        position = self.map.player.position
        player_info = {
            "name": self.map.player.name,
            "gender": self.player.gender,
            "position": {
                "x": position[0],
                "y": position[1]
            },
            "direction": self.map.player.direction,
            "pokemons": [pokemon.to_dict() for pokemon in self.player.pokemons],
            "inventory": self.map.player.inventory,
            "pokedex": self.map.player.pokedex,
            "pokedollars": self.map.player.pokedollars,
            "ingame_time": self.map.player.ingame_time.total_seconds()
        }
        map_info = {
            "path": self.map.current_map.name,
            "map_name": self.map.map_name
        }
        data = {
            "player": player_info,
            "map": map_info
        }

        save_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../assets/saves", self.path))
        save_file = os.path.join(save_dir, "data.pkmn")

        if not os.path.exists(save_dir):
            os.makedirs(save_dir)
        with open(save_file, "w", encoding="utf-8") as file:
            file.write(self.dump(data))

        self.dialogue.load_data(100, 0)

    def load(self) -> None:
        save_file = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../assets/saves", self.path, "data.pkmn"))
        if os.path.exists(save_file):
            with open(save_file, "r", encoding="utf-8") as file:
                data = json.load(file)
            self.map.load_map(data["map"]["path"])
            self.player.from_dict(data["player"])
        else:
            self.map.load_map("map_0")
            self.player.set_position(512, 288)
        self.map.add_player(self.player)

    def dump(self, element: dict) -> str:
        return json.dumps(element, indent=4)
