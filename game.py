import pygame
import os
import unicodedata

from pokemon_i18n import fr_name
from map import Map
from player import Player
from dialogues_interactions import get_dialogue
from menu_pause_ds import PauseMenuDS
from characters import Glitch, Otomai
from starter_scene import StarterChoiceScene3D


MAPS_PATH = "assets/map"
SPRITES_PATH = "assets/sprite"
SOUNDS_PATH = "assets/sounds"
POKEMON_ASSETS_DIR = os.path.join("assets", "pokemon")


def _norm(s: str) -> str:
    s = s.lower()
    s = unicodedata.normalize("NFD", s)
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    return s


class Game:
    def __init__(self, screen, genre, prenom, personnage, map_name="chambre_joueur", spawn_name="Player"):
        self.screen = screen
        self.genre = genre
        self.prenom = prenom
        self.personnage = personnage
        self.current_map_name = map_name
        self.current_spawn_name = spawn_name

        self.has_bag = False
        self.has_pokedex = False
        self.has_team = False
        self.has_bike = False
        self.has_surf = False
        self.overview_mode = False
        self.day_night_cycle_ms = 60_000
        self.day_duration_ms = 30_000
        self.day_night_start = pygame.time.get_ticks()
        self.easter_input = ""
        self.sacha_cooldown_ms = 0
        self.surf_block_cooldown_ms = 1200
        self.last_surf_block_time = 0

        # ✅ équipe: slot 1 = follower
        self.team = []
        self.team_order_path = self._team_order_save_path()
        saved_order = self._load_team_order()
        if saved_order:
            self.team = [self._make_team_entry(pid) for pid in saved_order]
            self.has_team = True

        # FLAGS HISTOIRE
        self.telecommande = False
        self.telecommande_active = False
        self.glitch_event_done = False
        self.just_remonte_chambre = False
        self.cinematique_otomai_done = False
        self.glitch_scene_running = False
        self.historia_en_cours = False

        self.starter_chosen = None

        player_sheet = pygame.image.load(os.path.join(SPRITES_PATH, "hero_01_red_m_walk.png")).convert_alpha()
        self.p_cols, self.p_rows = 4, 4
        self.pw = player_sheet.get_width() // self.p_cols
        self.ph = player_sheet.get_height() // self.p_rows

        if not pygame.mixer.get_init():
            pygame.mixer.init()

        self.running = True
        self.fullscreen = False
        self.first_launch = True
        self.clock = None

        self.load_map(self.current_map_name, self.current_spawn_name)

    # ----------------------------
    # MUSIQUES
    # ----------------------------
    def play_historia(self):
        try:
            pygame.mixer.music.load(os.path.join(SOUNDS_PATH, "historia.mp3"))
            pygame.mixer.music.set_volume(0.7)
            pygame.mixer.music.play(-1)
            self.historia_en_cours = True
        except Exception as e:
            print("Erreur musique historia :", e)

    def stop_historia(self):
        if self.historia_en_cours:
            pygame.mixer.music.stop()
            self.historia_en_cours = False

    # ----------------------------
    # FOLLOWER (slot 1 équipe) + LIVE SYNC
    # ----------------------------
    def _find_best_pokemon_sprite(self, pokemon_id: str):
        pokemon_id = self._team_entry_id(pokemon_id)
        if not pokemon_id:
            return None
        base_dir = os.path.dirname(os.path.abspath(__file__))  # .../code
        folder = os.path.normpath(os.path.join(base_dir, POKEMON_ASSETS_DIR))

        if not os.path.isdir(folder):
            print("[Follower] dossier introuvable:", folder)
            return None

        pid = _norm(pokemon_id)

        keys = {
            "bulbasaur": ["bulbizarre", "bulbasaur", "001", "0001"],
            "charmander": ["salameche", "salamèche", "charmander", "004", "0004", "005", "0005"],
            "squirtle": ["carapuce", "squirtle", "007", "0007"],
            "pikachu": ["pikachu", "025", "0025"],
        }
        candidates = keys.get(pid, [pid])

        pngs = [f for f in os.listdir(folder) if f.lower().endswith(".png")]
        if not pngs:
            return None

        for kw in candidates:
            nkw = _norm(kw)
            for fn in pngs:
                if nkw in _norm(fn):
                    return os.path.join(POKEMON_ASSETS_DIR, fn)

        return os.path.join(POKEMON_ASSETS_DIR, pngs[0])

    def get_team_follower_sprite(self):
        if not self.team:
            return None
        return self._find_best_pokemon_sprite(self.team[0])

    def sync_follower_with_team(self):
        """Follower = slot 1. Change instant en live."""
        if not hasattr(self, "map") or self.map is None:
            return

        if not self.team:
            if hasattr(self.map, "remove_follower"):
                self.map.remove_follower()
            return

        sprite_path = self.get_team_follower_sprite()
        if sprite_path:
            self.map.set_follower(sprite_path, follower_debug=True)
        else:
            if hasattr(self.map, "remove_follower"):
                self.map.remove_follower()

    def set_team_order(self, new_team_list):
        self.team = list(new_team_list)
        self.has_team = len(self.team) > 0
        self.sync_follower_with_team()
        self._save_team_order(self.team)

    def _team_entry_id(self, entry):
        if entry is None:
            return None
        if isinstance(entry, str):
            return entry
        if isinstance(entry, dict):
            return entry.get("id") or entry.get("dbSymbol") or entry.get("name")
        return getattr(entry, "id", None) or getattr(entry, "dbSymbol", None) or getattr(entry, "name", None)

    def _make_team_entry(self, pokemon_id: str):
        return {
            "id": pokemon_id,
            "level": 5,
            "hp": 20,
            "maxhp": 20,
            "icon": None,
        }

    def _team_order_save_path(self):
        base_dir = os.path.dirname(os.path.abspath(__file__))
        return os.path.join(base_dir, "app", "saves", "team_order.json")

    def _save_team_order(self, team_list):
        order = [self._team_entry_id(entry) for entry in team_list if self._team_entry_id(entry)]
        if not order:
            return
        save_dir = os.path.dirname(self.team_order_path)
        os.makedirs(save_dir, exist_ok=True)
        with open(self.team_order_path, "w", encoding="utf-8") as f:
            import json
            json.dump({"order": order}, f, indent=2, ensure_ascii=False)

    def _load_team_order(self):
        if not os.path.exists(self.team_order_path):
            return []
        try:
            import json
            with open(self.team_order_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return data.get("order", [])
        except Exception:
            return []

    # ----------------------------
    # MAP LOADING
    # ----------------------------
    def load_map(self, map_name, spawn_name):
        map_file_path = os.path.join(MAPS_PATH, map_name + ".tmx")

        temp_player = Player(0, 0, self.genre)
        temp_map = Map(map_file_path, temp_player, self.screen.get_size(), follower_sprite_path=None)
        spawns = temp_map.spawns

        print("Switching to map:", map_name, "| Spawn demandé:", spawn_name, "| Spawns trouvés:", spawns)
        spawn_pos = spawns.get(spawn_name, (100, 100))

        self.player = Player(spawn_pos[0], spawn_pos[1], self.genre)
        self.player.has_bike = self.has_bike
        self.player.has_surf = self.has_surf
        if map_name == "chambre_joueur":
            self.player.set_seated(True)
            self.player.direction = 3

        follower_sprite = self.get_team_follower_sprite()
        self.map = Map(
            map_file_path,
            self.player,
            self.screen.get_size(),
            follower_sprite_path=follower_sprite,
            follower_debug=True
        )
        self.player.map = self.map
        if self.overview_mode and hasattr(self.map, "set_overview_zoom"):
            self.map.set_overview_zoom(True)

        if map_name == "chambre_joueur":
            if not self.historia_en_cours:
                self.play_historia()

        elif map_name == "laboratoire_otomaï":
            self.stop_historia()
            try:
                pygame.mixer.music.load(os.path.join(SOUNDS_PATH, "astrub_rétro.mp3"))
                pygame.mixer.music.set_volume(0.8)
                pygame.mixer.music.play(-1)
            except Exception as e:
                print("Erreur musique labo :", e)

        else:
            if not self.historia_en_cours:
                self.play_historia()

    # ----------------------------
    # STARTER HELPERS
    # ----------------------------
    def _zone_to_world_rect(self, zone: dict):
        if not zone:
            return None
        r = zone.get("rect")
        if isinstance(r, pygame.Rect):
            return r
        keys = ("x", "y", "width", "height")
        if all(k in zone for k in keys):
            return pygame.Rect(int(zone["x"]), int(zone["y"]), int(zone["width"]), int(zone["height"]))
        obj = zone.get("obj") or zone.get("object")
        if obj is not None and hasattr(obj, "x"):
            return pygame.Rect(int(obj.x), int(obj.y), int(obj.width), int(obj.height))
        return None

    def _world_rect_to_screen_rect(self, rect_world: pygame.Rect):
        if rect_world is None:
            return None
        if hasattr(self.map, "group") and hasattr(self.map.group, "view"):
            view = self.map.group.view
            return rect_world.move(-int(view.left), -int(view.top))
        if hasattr(self.map, "renderer") and hasattr(self.map.renderer, "view_rect"):
            vr = self.map.renderer.view_rect
            return rect_world.move(-int(vr.left), -int(vr.top))
        return rect_world

    def _is_starter_zone(self, zone: dict):
        if not zone:
            return False
        name_lower = str(zone.get("name", "")).lower()
        props = zone.get("properties") or {}
        by_name = any(key in name_lower for key in ("starter_table", "table_starter", "starter"))
        by_prop = (props.get("event") == "starter_choice")
        return by_name or by_prop

    # ----------------------------
    # ✅ CINEMATIC ZOOM (nouveau)
    # ----------------------------
    def _cinematic_zoom(self, base_frame: pygame.Surface, focus_rect: pygame.Rect, duration_ms=420, zoom=1.7):
        """
        Zoom smooth centré sur focus_rect (coords écran).
        Effet DS: léger voile blanc en plus.
        """
        if base_frame is None or focus_rect is None:
            return

        clock = self.clock if self.clock else pygame.time.Clock()
        start = pygame.time.get_ticks()

        w, h = self.screen.get_size()
        cx, cy = focus_rect.center

        while True:
            t = (pygame.time.get_ticks() - start) / max(1, duration_ms)
            if t >= 1.0:
                t = 1.0

            # easing (doux)
            ease = 1 - (1 - t) * (1 - t)

            z = 1.0 + (zoom - 1.0) * ease
            scaled = pygame.transform.smoothscale(base_frame, (int(w * z), int(h * z)))

            sx = int(cx * z - w / 2)
            sy = int(cy * z - h / 2)
            sx = max(0, min(sx, scaled.get_width() - w))
            sy = max(0, min(sy, scaled.get_height() - h))

            self.screen.blit(scaled, (-sx, -sy))

            overlay = pygame.Surface((w, h), pygame.SRCALPHA)
            overlay.fill((255, 255, 255, int(40 * ease)))
            self.screen.blit(overlay, (0, 0))

            pygame.display.flip()
            clock.tick(60)

            if t >= 1.0:
                break

    # ----------------------------
    # STARTER SCENE (améliorée)
    # ----------------------------
    def _run_starter_choice_with_pikachu(self, focus_rect_screen: pygame.Rect):
        clock = self.clock if self.clock else pygame.time.Clock()

        # On capture le frame AVANT la scène
        base_frame = self.screen.copy()

        # ✅ zoom cinématique sur la table
        self._cinematic_zoom(base_frame, focus_rect_screen, duration_ms=420, zoom=1.7)

        select_sound = os.path.join(SOUNDS_PATH, "select_sound-121244.mp3")
        if not os.path.exists(select_sound):
            select_sound = None

        scene = StarterChoiceScene3D(
            screen=self.screen,
            clock=clock,
            base_frame=base_frame,
            focus_rect=focus_rect_screen,
            assets_root="assets",
            select_sound_path=select_sound,
        )
        result = scene.run()
        if not result.chosen:
            return None

        mapping = {1: "bulbasaur", 2: "charmander", 3: "squirtle", 4: "pikachu"}
        return mapping.get(result.starter_id)

    # ----------------------------
    # EVENTS
    # ----------------------------
    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_b:
                from dialog_box import show_dialog_box_overlay
                if not self.has_bike:
                    show_dialog_box_overlay(self.screen, ["Tu n'as pas encore ton vélo."])
                else:
                    self.player.switch_bike()

            if event.key == pygame.K_n:
                self.overview_mode = not self.overview_mode
                if hasattr(self.map, "set_overview_zoom"):
                    self.map.set_overview_zoom(self.overview_mode)

            # Pause
            if event.key == pygame.K_ESCAPE:
                # ✅ IMPORTANT: les clés doivent matcher PauseMenuDS.tabs
                # (tu as retiré "Pokémon", donc on l'enlève ici aussi)
                can_access = {
                    "POKEDEX": self.has_pokedex,
                    "SAC": self.has_bag,
                    "EQUIPE": self.has_team,
                    "PARAMETRE": True,
                    "SAUVEGARDE": True,
                    "QUITTER LE JEU": True,
                }

                choice = PauseMenuDS(self.screen, can_access).run()
                if choice == "SAC":
                    from bag_menu import BagMenu
                    BagMenu(self.screen).run()
                if choice == "EQUIPE":
                    from team_menu_ds import TeamMenuDS
                    from pokemon_i18n import fr_name
                    team_entries = list(self.team)
                    menu = TeamMenuDS(self.screen, team_entries, name_fn=fr_name)
                    new_team, changed = menu.run()
                    if changed:
                        self.set_team_order(new_team)

            # Fullscreen
            if event.key == pygame.K_F11:
                self.fullscreen = not getattr(self, "fullscreen", False)
                if self.fullscreen:
                    self.screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
                else:
                    self.screen = pygame.display.set_mode((1280, 720), pygame.RESIZABLE)
                self.map.renderer.set_size(self.screen.get_size())

            # Interaction
            if event.key in (pygame.K_RETURN, pygame.K_e):
                if self._try_follower_interaction():
                    return
                zone = self.map.get_interaction_zone(self.player.rect)
                if zone:
                    from dialog_box import show_dialog_box_overlay
                    name_lower = str(zone.get("name", "")).lower()

                    # ✅ STARTER TABLE
                    if self.current_map_name == "laboratoire_otomaï" and self._is_starter_zone(zone):
                        if self.starter_chosen is not None:
                            show_dialog_box_overlay(self.screen, ["Tu as déjà choisi ton Pokémon !"])
                            return

                        rect_world = self._zone_to_world_rect(zone)
                        focus_rect_screen = self._world_rect_to_screen_rect(rect_world)

                        if focus_rect_screen is None:
                            show_dialog_box_overlay(self.screen, ["(Debug) Rect de la table introuvable."])
                            return

                        chosen_id = self._run_starter_choice_with_pikachu(focus_rect_screen)
                        if chosen_id:
                            self.starter_chosen = chosen_id

                            # ✅ équipe officielle: starter devient slot 1
                            self.team = [self._make_team_entry(chosen_id)]
                            self.has_team = True
                            self._save_team_order(self.team)

                            show_dialog_box_overlay(self.screen, [f"Tu as choisi {fr_name(chosen_id)} !"])
                            print("Starter choisi:", chosen_id)

                            # ✅ follower instant
                            self.sync_follower_with_team()
                        return

                    # SAC
                    if "sac" in name_lower and not self.has_bag:
                        show_dialog_box_overlay(self.screen, ["Tu as récupéré ton sac.", "Appuie sur [Échap] pour accéder au menu."])
                        self.has_bag = True
                        if hasattr(self.map, "remove_item"):
                            self.map.remove_item("sac")

                    elif "panneau_chambre2" in name_lower:
                        dialogue = get_dialogue(zone["name"], deja_remonte=self.just_remonte_chambre)
                        show_dialog_box_overlay(self.screen, dialogue)
                        if self.just_remonte_chambre:
                            self.just_remonte_chambre = False

                    else:
                        dialogue = get_dialogue(zone["name"])
                        show_dialog_box_overlay(self.screen, dialogue)

    def _try_follower_interaction(self):
        follower = getattr(self.map, "follower", None)
        if not follower:
            return False

        player_center = self.player.rect.center
        follower_center = follower.rect.center
        dx = follower_center[0] - player_center[0]
        dy = follower_center[1] - player_center[1]
        distance_sq = dx * dx + dy * dy

        if distance_sq > 60 * 60:
            return False

        direction = getattr(self.player, "direction", 0)
        facing = False
        if direction == 0 and dy > 0 and abs(dx) < 40:
            facing = True
        elif direction == 3 and dy < 0 and abs(dx) < 40:
            facing = True
        elif direction == 1 and dx < 0 and abs(dy) < 40:
            facing = True
        elif direction == 2 and dx > 0 and abs(dy) < 40:
            facing = True

        if not facing:
            return False

        from dialog_box import show_dialog_box_overlay
        if hasattr(follower, "play_happy_animation"):
            follower.play_happy_animation()
        show_dialog_box_overlay(self.screen, ["Ton Pokémon te regarde avec joie !"])
        return True

                    if "pokedex" in name_lower:
                        self.has_pokedex = True

            # Télécommande (T)
            if event.key == pygame.K_t:
                from dialog_box import show_dialog_box_overlay
                if self.telecommande:
                    if self.telecommande_active:
                        pygame.mixer.Sound(os.path.join(SOUNDS_PATH, "vibreur_telephone.mp3")).play()
                        show_dialogue = ["La télécommande vibre dans ta poche..."]
                        show_dialog_box_overlay(self.screen, show_dialogue)
                    else:
                        show_dialog_box_overlay(self.screen, ["Elle te sert à rien ici, range-moi ça !"])

            if self.current_map_name == "Bourrely" and event.unicode:
                self._handle_sacha_easter_egg(event.unicode)

    def _handle_sacha_easter_egg(self, char: str):
        if not char.isalpha():
            return
        now = pygame.time.get_ticks()
        if now < self.sacha_cooldown_ms:
            return
        self.easter_input = (self.easter_input + char.lower())[-5:]
        if self.easter_input.endswith("sacha"):
            self.sacha_cooldown_ms = now + 2000
            base_dir = os.path.dirname(os.path.abspath(__file__))
            candidates = [
                os.path.join(base_dir, "assets", "eastereggs", "SACHA.mp3"),
                os.path.join(base_dir, "assets", "eastereggs", "SACHA.wav"),
                os.path.join(base_dir, "assets", "eastereggs", "SACHA.ogg"),
            ]
            for path in candidates:
                if os.path.exists(path):
                    try:
                        pygame.mixer.Sound(path).play()
                    except Exception:
                        pass
                    break

    def update(self):
        self.player.update()
        self.map.update()

        if getattr(self.player, "blocked_reason", None) == "water":
            now = pygame.time.get_ticks()
            if now - self.last_surf_block_time >= self.surf_block_cooldown_ms:
                from dialog_box import show_dialog_box_overlay
                show_dialog_box_overlay(
                    self.screen,
                    ["Ah, à moins que tu possèdes le Thousand Sunny dans la poche...",
                     "Reviens avec la capacité SURF, mon pote !"]
                )
                self.last_surf_block_time = now
            self.player.blocked_reason = None

        encounter = self.map.check_wild_encounter(self.player.rect)
        if encounter:
            from dialog_box import show_dialog_box_overlay
            species_name = getattr(encounter, "species", "")
            display_name = self.map._format_species_name(species_name) if hasattr(self.map, "_format_species_name") else "pokémon"
            show_dialog_box_overlay(self.screen, [f"Un {display_name} sauvage apparaît !"])

        # --- EVENT GLITCH sur Bourrely ---
        if self.current_map_name == "Bourrely" and not self.glitch_event_done and not self.glitch_scene_running:
            event = self.map.get_event_zone(self.player.rect, "event_glitch")
            if event:
                self.glitch_scene_running = True
                self.declencher_event_glitch()

        # --- Cinématique labo Otomaï ---
        if self.current_map_name == "laboratoire_otomaï" and not self.cinematique_otomai_done:
            self.cinematique_otomai_done = True
            self.declencher_cinematique_otomai()

        # --- Exits ---
        exit_data = self.map.check_exit(self.player.rect)
        if exit_data and exit_data["to_map"]:
            old_map = self.current_map_name
            self.current_map_name = exit_data["to_map"]
            self.current_spawn_name = exit_data["to_spawn"]

            if old_map == "salon_maisonjoueur" and self.current_map_name == "chambre_joueur":
                self.just_remonte_chambre = True

            if old_map == "laboratoire_otomaï" and self.current_map_name != "laboratoire_otomaï":
                self.stop_historia()
                self.play_historia()

            self.load_map(self.current_map_name, self.current_spawn_name)

    def draw(self):
        self.map.draw(self.screen)
        if self._is_night():
            overlay = pygame.Surface(self.screen.get_size(), pygame.SRCALPHA)
            overlay.fill((30, 40, 90, 110))
            self.screen.blit(overlay, (0, 0))

    def _is_night(self) -> bool:
        elapsed = pygame.time.get_ticks() - self.day_night_start
        cycle_pos = elapsed % self.day_night_cycle_ms
        return cycle_pos >= self.day_duration_ms

    def run(self):
        clock = pygame.time.Clock()
        self.clock = clock

        if self.current_map_name == "chambre_joueur" and self.first_launch:
            self.first_launch = False
            from dialog_box import show_dialog_box_overlay
            dialogue_maman = [
                f"{self.prenom} !",
                "Dépêche-toi, tu vas être en retard !",
                "N’oublie pas de récupérer ton sac sur le bureau avant de sortir,",
                "et va vite voir le Professeur Otomaï à son laboratoire.",
                "Et surtout, n’oublie pas tes pantoufles !"
            ]
            show_dialog_box_overlay(self.screen, dialogue_maman)

        while self.running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                self.handle_event(event)

            self.update()
            self.draw()
            pygame.display.flip()
            clock.tick(60)

    # --- EVENT GLITCH ---
    from characters import Glitch

    def declencher_event_glitch(self):
        self.stop_historia()
        try:
            pygame.mixer.music.load(os.path.join(SOUNDS_PATH, "glitch_pokemonmusic.MP3"))
            pygame.mixer.music.set_volume(0.7)
            pygame.mixer.music.play(-1)
        except Exception as e:
            print("Erreur musique Glitch :", e)

        self.glitch_event_done = True
        from dialog_box import show_dialog_box_overlay

        glitch = Glitch(-self.pw, self.player.rect.centery - self.ph // 2 - 8)
        target_x = self.player.rect.centerx - self.pw // 2

        for step in range(-self.pw, target_x, 24):
            glitch.rect.x = step
            glitch.direction = 2
            glitch.update(moving=True)
            self.draw()
            self.screen.blit(glitch.image, glitch.rect)
            pygame.display.flip()
            pygame.time.wait(28)

        for _ in range(10):
            glitch.rect.x = target_x
            glitch.direction = 2
            glitch.update(moving=True)
            self.draw()
            self.screen.blit(glitch.image, glitch.rect)
            pygame.display.flip()
            pygame.time.wait(100)

        pygame.time.wait(200)

        dialogue_bug = [
            "ȼ4€£æ... 0uI3|]ç¿µ*#@{][ ~",
            "1!#%%ç^ç—æd",
            "QzRR---..°ˇ≈Ω√∆˙ø",
            "[zzzzzZ ZZZ ZZZ]",
            "t&$-|||r4uio$`((°!",
            "/?.....ɨɨɨɨɨɨ-‡",
            "⧈⧈⧈⧈⧈⧈⧈⧈⧈⧈⧈",
            "… bzzzZ BZZzzz …",
            "ERROR404 SYSTEM",
            "...",
            "fin bref, t'as compris quoi.",
            "Tu reçois une télécommande étrange."
        ]
        show_dialog_box_overlay(self.screen, dialogue_bug)
        self.telecommande = True
        self.telecommande_active = False

        end_x = self.screen.get_width() + self.pw
        for step in range(target_x, end_x, 32):
            glitch.rect.x = step
            glitch.direction = 2
            glitch.update(moving=True)
            self.draw()
            self.screen.blit(glitch.image, glitch.rect)
            pygame.display.flip()
            pygame.time.wait(26)

        pygame.mixer.music.stop()
        self.play_historia()
        pygame.time.wait(100)
        self.glitch_scene_running = False

    # --- EVENT LABO OTOMAÏ ---
    from characters import Otomai

    def declencher_cinematique_otomai(self):
        try:
            pygame.mixer.music.load(os.path.join(SOUNDS_PATH, "astrub_rétro.mp3"))
            pygame.mixer.music.set_volume(0.8)
            pygame.mixer.music.play(-1)
        except Exception as e:
            print("Erreur musique labo :", e)

        from dialog_box import show_dialog_box_overlay

        otomai = Otomai(self.player.rect.centerx + 90, self.player.rect.centery - self.ph // 2 - 12)
        destination_x = self.player.rect.centerx - 50

        for dx in range(otomai.rect.x, destination_x, -18):
            otomai.rect.x = dx
            otomai.direction = 1
            otomai.update(moving=True)
            self.draw()
            self.screen.blit(otomai.image, otomai.rect)
            pygame.display.flip()
            pygame.time.wait(36)

        otomai.rect.x = destination_x
        for _ in range(8):
            otomai.direction = 0
            otomai.update(moving=True)
            self.draw()
            self.screen.blit(otomai.image, otomai.rect)
            pygame.display.flip()
            pygame.time.wait(110)

        dialogue_otomai = [
            "Salut ! J'espère que tu aimes bien la musique, elle me rend nostalgique, moi !",
            "Désolé de t'avoir fait attendre, je travaillais sur une nouvelle invention, le 'ZAAP'... mais chuuuut, c'est pas encore au point !",
            "Alors... sur la table, tu trouveras trois Pokémon : Salamèche, Bulbizarre et Carapuce. Classique, rangés dans le classeur.",
            "C'est à toi de choisir, mais surtout, n'oublie pas pourquoi tu es là...",
            "Tu dois partir à la recherche des refs ET devenir le plus grand Maître Pokémon !",
            "Tiens, prends ce Pokédex, et... un autre cadeau, le Pokéref. Il t'aidera à recenser toutes les références que tu trouveras.",
            "Oh, c'est quoi cette télécommande que tu as... ?",
            "Hmmm... C'est un outil dangereux, ça. Ça se voit... J'espère que tu sauras t'en servir au bon moment.",
            "Mais réfléchis bien avant de l'utiliser, d'accord ? Ne te sens pas obligé de t'en servir, les choix ont parfois des conséquences irréversibles... Ça fait peur, hein ? Mais bon, tranquille, ici c'est Pokémon, c'est pas un serveur ombre.",
            "Allez, va vivre ton aventure !"
        ]
        show_dialog_box_overlay(self.screen, dialogue_otomai)
        self.telecommande_active = True


def get_event_zone(self, player_rect, event_name):
    for obj in self.tmx_data.objects:
        if obj.name and event_name in obj.name and pygame.Rect(
            int(obj.x), int(obj.y), int(obj.width), int(obj.height)
        ).colliderect(player_rect):
            return obj
    return None


setattr(Map, "get_event_zone", get_event_zone)
