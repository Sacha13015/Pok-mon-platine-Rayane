import json
import zipfile

# ==========================
# CONFIG
# ==========================
ZIP_PATH = "pokemon.zip"   # le zip doit être dans le même dossier
OUTPUT_JSON = "pokemon_names_fr.json"

# ==========================
# TABLE OFFICIELLE EN → FR
# (on l'agrandira après)
# ==========================
OFFICIAL_FR = {
    "bulbasaur": "Bulbizarre",
    "ivysaur": "Herbizarre",
    "venusaur": "Florizarre",
    "charmander": "Salamèche",
    "charmeleon": "Reptincel",
    "charizard": "Dracaufeu",
    "squirtle": "Carapuce",
    "wartortle": "Carabaffe",
    "blastoise": "Tortank",

    "lillipup": "Ponchiot",
    "herdier": "Ponchien",
    "stoutland": "Mastouffe",
}

# ==========================
# EXTRACTION DES IDS EN
# ==========================
found_ids = set()

with zipfile.ZipFile(ZIP_PATH, "r") as z:
    for filename in z.namelist():
        if filename.endswith(".json"):
            with z.open(filename) as f:
                try:
                    data = json.load(f)
                    if "dbSymbol" in data:
                        found_ids.add(data["dbSymbol"].lower())
                except Exception:
                    pass

# ==========================
# GÉNÉRATION DU JSON FR
# ==========================
result = {}

for poke_id in sorted(found_ids):
    # si pas encore traduit → fallback propre
    result[poke_id] = OFFICIAL_FR.get(poke_id, poke_id.capitalize())

with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
    json.dump(result, f, ensure_ascii=False, indent=2)

print("✅ Terminé !")
print("Pokémon trouvés :", len(result))
print("Fichier généré :", OUTPUT_JSON)
