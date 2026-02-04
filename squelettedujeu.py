/code/
  main.py            # Lance le jeu, gère intro/menu/cinématique/chambre etc.
  game.py            # Gameplay en “free roam”, collisions, interactions.
  map.py             # Gestion des maps et transitions
  player.py          # Joueur (déplacement, animation, collision)
  dialog_box.py      # Affichage des dialogues overlay
  menu_pause.py      # Menu Pause, Sac, Boîte à Badges, etc.
  badges.py          # Gestion et affichage des badges
  fight/             # (dossier) Toute la logique de combat Pokémon
    battle.py        # Système de combat principal
    pokemon.py       # Classes et stats de chaque Pokémon
    attacks.py       # Données des attaques, types, efficacité
  inventory.py       # Sac à dos, items, utilisation objets etc.
  team.py            # Gestion de l’équipe, switch, stats, heal, etc.
  pnj.py             # PNJ classiques
  events.py          # Systèmes d’événements contextuels (surf, coupe, vélo…)
  fly.py             # Système de vol rapide
  worldmap.py        # Affichage carte du monde
