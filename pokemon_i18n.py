import json
import os

BASE_DIR = os.path.dirname(__file__)
NAMES_PATH = os.path.join(BASE_DIR, "assets", "json", "pokemon_names_fr.json")

_names_cache = None

def _load():
    global _names_cache
    if _names_cache is None:
        try:
            with open(NAMES_PATH, "r", encoding="utf-8") as f:
                _names_cache = json.load(f)
        except Exception:
            _names_cache = {}
    return _names_cache

def fr_name(pokemon_id: str) -> str:
    if not pokemon_id:
        return ""
    names = _load()
    return names.get(pokemon_id.lower(), pokemon_id)
