import math
import os
import random
import unicodedata

import pygame
import pytmx
import pyscroll

from pokemon_names import POKEMON_NAMES
from pnj import PNJ


def _norm(s: str) -> str:
    """lower + retire accents + garde lettres/chiffres/_"""
    s = s.lower()
    s = unicodedata.normalize("NFD", s)
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    return s


def _abs_from_code(rel_path: str) -> str:
    base_dir = os.path.dirname(os.path.abspath(__file__))  # .../EP9-Save/code
    return os.path.normpath(os.path.join(base_dir, rel_path))


def _remove_green_screen(surface: pygame.Surface, g_min=130, rg_max=140, bg_max=140) -> pygame.Surface:
    """
    Supprime un fond vert même si ce n'est PAS exactement (0,255,0).
    Règle simple :
      - G >= g_min
      - R <= rg_max
      - B <= bg_max
    => alors pixel devient transparent.
    """
    surf = surface.convert_alpha()
    w, h = surf.get_size()

    # PixelArray pour accès rapide
    px = pygame.PixelArray(surf)
    try:
        for y in range(h):
            for x in range(w):
                r, g, b, a = surf.unmap_rgb(px[x, y])
                if g >= g_min and r <= rg_max and b <= bg_max:
                    px[x, y] = (0, 0, 0, 0)
    finally:
        del px
    return surf


class TeamFollower(pygame.sprite.Sprite):
    """
    Follower DS-like:
    - spritesheet auto-detect (2x4 ou 4x4) + anim
    - suit player.history avec offset + vitesse
    - compatible pyscroll (update sans args)

    IMPORTANT:
    - gère le fond vert même si c'est un greenscreen imparfait
    - animation rendue VISIBLE (timer stable + stop_threshold élargi)
    """

    def __init__(
        self,
        player,
        spritesheet_path,
        offset_frames=6,
        speed=2,
        y_offset=28,
        anim_every=8,
        remove_green=True
    ):
        super().__init__()
        self.player = player
        self.offset = max(0, int(offset_frames))
        self.speed = max(1, int(speed))
        self.y_offset = int(y_offset)
        self.anim_every = max(1, int(anim_every))
        self.happy_timer = 0

        full_path = _abs_from_code(spritesheet_path)

        # On charge en alpha, puis on nettoie le green screen si besoin
        raw = pygame.image.load(full_path).convert_alpha()
        self.sheet = _remove_green_screen(raw) if remove_green else raw

        w, h = self.sheet.get_width(), self.sheet.get_height()
        ratio = w / float(h) if h else 1.0

        # Auto-detect:
        # - 4x4 => ratio ~ 1.0
        # - 2x4 => ratio ~ 0.5
        # (Tolérance large)
        self.cols = 4 if ratio >= 0.75 else 2
        self.rows = 4

        self.frame_w = max(1, w // self.cols)
        self.frame_h = max(1, h // self.rows)

        # 0=down,1=left,2=right,3=up (même convention que Player)
        self.direction = 0
        self.frame = 0
        self.timer = 0

        self.frames = self._cut()
        self.image = self.frames[self.direction][self.frame]
        self.rect = self.image.get_rect(topleft=(player.rect.x, player.rect.y + self.y_offset))

    def _cut(self):
        out = []
        for d in range(4):
            row = []
            for f in range(self.cols):
                x = f * self.frame_w
                y = d * self.frame_h

                # sécurité: évite subsurface hors limite si sheet pas parfait
                rect = pygame.Rect(x, y, self.frame_w, self.frame_h)
                rect.clamp_ip(pygame.Rect(0, 0, self.sheet.get_width(), self.sheet.get_height()))

                img = self.sheet.subsurface(rect).copy()
                row.append(img)
            if len(row) == 1:
                # si pas assez de frames, duplique pour "simuler" marche
                row = [row[0], row[0]]
            out.append(row)
        return out

    def _dir_from_delta(self, dx, dy):
        if abs(dx) > abs(dy):
            return 2 if dx > 0 else 1
        return 0 if dy > 0 else 3

    def update(self):
        hist = getattr(self.player, "history", None)
        if not hist:
            self.rect.topleft = (self.player.rect.x, self.player.rect.y + self.y_offset)
            self.frame = 0
            self.timer = 0
            self.direction = getattr(self.player, "direction", 0)
            self.image = self.frames[self.direction][self.frame]
            self._apply_happy_effects()
            return

        # target derrière le joueur
        if len(hist) <= self.offset:
            tx, ty = hist[-1]
        else:
            tx, ty = hist[self.offset]
        ty += self.y_offset

        dx = tx - self.rect.x
        dy = ty - self.rect.y

        # ✅ zone "stop" plus large => l'anim a le temps d'être visible
        stop_threshold = self.speed * 2
        if abs(dx) <= stop_threshold and abs(dy) <= stop_threshold:
            self.rect.x, self.rect.y = tx, ty
            self.frame = 0
            self.timer = 0
            # option: direction suit le player à l'arrêt
            self.direction = getattr(self.player, "direction", self.direction)
            self.image = self.frames[self.direction][self.frame]
            return

        moved = False

        # 1 axe à la fois (style Pokémon DS)
        if abs(dx) > abs(dy):
            step = self.speed if dx > 0 else -self.speed
            self.direction = self._dir_from_delta(step, 0)
            self.rect.x += step
            moved = True
        else:
            step = self.speed if dy > 0 else -self.speed
            self.direction = self._dir_from_delta(0, step)
            self.rect.y += step
            moved = True

        # ✅ animation stable (pas de modulo)
        if moved:
            self.timer += 1
            if self.timer >= self.anim_every:
                self.timer = 0
                # Alterne 0/1 si cols=2 (DS-like), sinon cycle normal
                if self.cols == 2:
                    self.frame = 1 - self.frame
                else:
                    self.frame = (self.frame + 1) % self.cols
        else:
            self.frame = 0
            self.timer = 0

        # clamp sécurité
        self.frame = max(0, min(self.frame, len(self.frames[self.direction]) - 1))
        self.image = self.frames[self.direction][self.frame]
        self._apply_happy_effects()

    def play_happy_animation(self, duration=40):
        self.happy_timer = max(self.happy_timer, int(duration))

    def _apply_happy_effects(self):
        if self.happy_timer <= 0:
            return
        self.happy_timer -= 1

        jump = int(4 * abs(math.sin(self.happy_timer / 4.0)))
        self.rect.y -= jump

        happy_image = self.image.copy()
        bubble_pos = (happy_image.get_width() - 7, 6)
        pygame.draw.circle(happy_image, (255, 255, 255, 230), bubble_pos, 5)
        pygame.draw.circle(happy_image, (255, 200, 0, 240), bubble_pos, 3)
        self.image = happy_image


class WildPokemonSprite(pygame.sprite.Sprite):
    _sheet_cache = None

    def __init__(self, position, tile_size, spritesheet_path, species, species_index):
        super().__init__()
        self.tile_size = tile_size
        self.species = species
        self.species_index = species_index
        self.image = self._get_frame_for_species(spritesheet_path)
        self.rect = self.image.get_rect(topleft=position)
        self.bob_timer = random.randint(0, 30)
        self.base_y = self.rect.y

    def _get_frame_for_species(self, spritesheet_path):
        if WildPokemonSprite._sheet_cache is None:
            try:
                WildPokemonSprite._sheet_cache = pygame.image.load(spritesheet_path).convert_alpha()
            except Exception:
                fallback = pygame.Surface((self.tile_size, self.tile_size), pygame.SRCALPHA)
                pygame.draw.circle(fallback, (200, 80, 80), (self.tile_size // 2, self.tile_size // 2), self.tile_size // 2)
                return fallback

        sheet = WildPokemonSprite._sheet_cache
        frame_w = self.tile_size
        frame_h = self.tile_size
        cols = max(1, sheet.get_width() // frame_w)
        rows = max(1, sheet.get_height() // frame_h)
        total = cols * rows
        index = self.species_index % total if total else 0
        fx = index % cols
        fy = index // cols
        rect = pygame.Rect(fx * frame_w, fy * frame_h, frame_w, frame_h)
        frame = sheet.subsurface(rect).copy()
        return pygame.transform.smoothscale(frame, (self.tile_size, self.tile_size))

    def update(self):
        self.bob_timer = (self.bob_timer + 1) % 60
        offset = 1 if self.bob_timer < 30 else -1
        self.rect.y = self.base_y + offset


class ItemSprite(pygame.sprite.Sprite):
    def __init__(self, name, position, image_path=None, size=24):
        super().__init__()
        self.name = name
        self.image = None
        if image_path:
            try:
                self.image = pygame.image.load(image_path).convert_alpha()
            except Exception:
                self.image = None
        if self.image is None:
            self.image = pygame.Surface((size, size), pygame.SRCALPHA)
            pygame.draw.circle(self.image, (180, 120, 60), (size // 2, size // 2), size // 2)
            pygame.draw.circle(self.image, (120, 80, 40), (size // 2, size // 2), size // 2, 2)
        self.rect = self.image.get_rect(topleft=position)


class Map:
    def __init__(
        self,
        map_file,
        player,
        screen_size=(1280, 720),
        follower_sprite_path=None,   # ✅ None => pas de follower
        follower_debug=False
    ):
        self.tmx_data = pytmx.util_pygame.load_pygame(map_file)
        self.map_layer = pyscroll.data.TiledMapData(self.tmx_data)
        self.renderer = pyscroll.BufferedRenderer(self.map_layer, screen_size, clamp_camera=True)

        # --- Zoom DS automatique + forçage pour Bourrely ---
        force_zoom = None
        if "Bourrely" in map_file:
            force_zoom = 2.2

        min_zoom = 1.5
        max_zoom = 3.0
        zoom_w = screen_size[0] / (self.tmx_data.width * self.tmx_data.tilewidth)
        zoom_h = screen_size[1] / (self.tmx_data.height * self.tmx_data.tileheight)
        auto_zoom = min(zoom_w, zoom_h)
        self.default_zoom = force_zoom if force_zoom else max(min(auto_zoom, max_zoom), min_zoom)
        self.full_zoom = min(zoom_w, zoom_h)
        self.overview_zoom = False
        self.renderer.zoom = self.default_zoom

        # Group pyscroll (caméra + draw)
        self.group = pyscroll.PyscrollGroup(map_layer=self.renderer, default_layer=2)

        self.player = player
        self.player.map = self

        # Layer du player (Bourrely plus haut)
        if "Bourrely" in map_file:
            self.group.add(self.player, layer=5)
            self._player_layer = 5
        else:
            self.group.add(self.player, layer=2)
            self._player_layer = 2

        # NPCs
        self.npcs = pygame.sprite.Group()

        # Data map
        self.spawns = self.get_spawns()
        self.exits = self.get_exits()
        self.obj_collisions = []
        self.load_object_collisions()
        self.interact_zones = self.get_interact_zones()
        self.grass_tiles = self._collect_grass_tiles()
        self.water_tiles = self._collect_water_tiles()
        self.load_npcs()
        self.items = pygame.sprite.Group()
        self.load_items()

        self.wild_pokemons = pygame.sprite.Group()
        self._wild_spritesheet = _abs_from_code("sprites_pokemons.png")
        self._spawn_wild_pokemons()
        self.wild_encounter_cooldown_ms = 1500
        self.last_wild_encounter = 0

        # ✅ Follower seulement si sprite fourni (slot 1 équipe)
        self.follower = None
        if follower_sprite_path:
            self.set_follower(follower_sprite_path, follower_debug=follower_debug)

    def set_follower(self, follower_sprite_path: str, follower_debug=False):
        """Crée (ou remplace) le follower (slot 1 équipe)."""
        if self.follower:
            try:
                self.group.remove(self.follower)
            except Exception:
                pass
            self.follower = None

        if follower_debug:
            print("[Follower] using:", follower_sprite_path)

        # speed: au moins run_speed pour suivre quand tu cours
        spd = max(int(getattr(self.player, "run_speed", 3)), 2)

        self.follower = TeamFollower(
            player=self.player,
            spritesheet_path=follower_sprite_path,
            offset_frames=6,      # plus collé
            speed=spd,            # réactif (suit même en course)
            y_offset=28,
            anim_every=6,         # ✅ un peu plus rapide => on voit la marche
            remove_green=True     # ✅ kill le fond vert (tolérant)
        )
        self.group.add(self.follower, layer=max(0, self._player_layer - 1))

    def remove_follower(self):
        if self.follower:
            try:
                self.group.remove(self.follower)
            except Exception:
                pass
        self.follower = None

    def _collect_grass_tiles(self):
        tiles = []
        for layer in self.tmx_data.visible_layers:
            if not hasattr(layer, "name"):
                continue
            name_lower = layer.name.lower()
            if "herbe" not in name_lower and "grass" not in name_lower:
                continue
            if not hasattr(layer, "tiles"):
                continue
            for x, y, gid in layer.tiles():
                if gid:
                    rect = pygame.Rect(
                        x * self.tmx_data.tilewidth,
                        y * self.tmx_data.tileheight,
                        self.tmx_data.tilewidth,
                        self.tmx_data.tileheight
                    )
                    tiles.append(rect)
        return tiles

    def _is_water_gid(self, gid: int) -> bool:
        if not gid:
            return False
        props = self.tmx_data.get_tile_properties_by_gid(gid)
        if not props:
            return False
        for key in ("water", "eau", "surf", "swim"):
            if key in props:
                return True
        terrain = props.get("terrain") or props.get("type")
        if terrain:
            return str(terrain).lower() in ("water", "eau", "lac", "mer", "river")
        return False

    def _collect_water_tiles(self):
        tiles = []
        for layer in self.tmx_data.visible_layers:
            if not hasattr(layer, "name"):
                continue
            name_lower = layer.name.lower()
            is_water_layer = any(token in name_lower for token in ("water", "eau", "lac", "mer", "river"))
            if not hasattr(layer, "tiles"):
                continue
            for x, y, gid in layer.tiles():
                if not gid:
                    continue
                if is_water_layer or self._is_water_gid(gid):
                    rect = pygame.Rect(
                        x * self.tmx_data.tilewidth,
                        y * self.tmx_data.tileheight,
                        self.tmx_data.tilewidth,
                        self.tmx_data.tileheight
                    )
                    tiles.append(rect)
        return tiles

    def is_water_tile(self, x, y):
        for rect in self.water_tiles:
            if rect.collidepoint(x, y):
                return True
        return False

    def _random_grass_position(self):
        if not self.grass_tiles:
            return None
        rect = random.choice(self.grass_tiles)
        return rect.topleft

    def _pick_wild_species(self):
        pool = [name for name in POKEMON_NAMES if not name.endswith("_femelle")]
        if not pool:
            return "pokemon"
        return random.choice(pool)

    @staticmethod
    def _format_species_name(species: str) -> str:
        parts = species.split("_", 1)
        name = parts[1] if len(parts) > 1 else species
        return name.replace("_", " ").capitalize()

    def _spawn_wild_pokemons(self):
        if not self.grass_tiles:
            return
        count = min(8, max(2, len(self.grass_tiles) // 20))
        for _ in range(count):
            pos = self._random_grass_position()
            if pos is None:
                continue
            species = self._pick_wild_species()
            species_index = POKEMON_NAMES.index(species) if species in POKEMON_NAMES else 0
            sprite = WildPokemonSprite(pos, self.tmx_data.tilewidth, self._wild_spritesheet, species, species_index)
            self.wild_pokemons.add(sprite)
            self.group.add(sprite, layer=self._player_layer)

    def _respawn_wild_pokemon(self):
        pos = self._random_grass_position()
        if pos is None:
            return
        species = self._pick_wild_species()
        species_index = POKEMON_NAMES.index(species) if species in POKEMON_NAMES else 0
        sprite = WildPokemonSprite(pos, self.tmx_data.tilewidth, self._wild_spritesheet, species, species_index)
        self.wild_pokemons.add(sprite)
        self.group.add(sprite, layer=self._player_layer)

    def is_player_in_grass(self, player_rect):
        for rect in self.grass_tiles:
            if rect.colliderect(player_rect):
                return True
        return False

    def check_wild_encounter(self, player_rect):
        now = pygame.time.get_ticks()
        if now - self.last_wild_encounter < self.wild_encounter_cooldown_ms:
            return None
        if not self.is_player_in_grass(player_rect):
            return None
        for sprite in list(self.wild_pokemons):
            if sprite.rect.colliderect(player_rect):
                if random.random() <= 0.35:
                    self.last_wild_encounter = now
                    self.wild_pokemons.remove(sprite)
                    try:
                        self.group.remove(sprite)
                    except Exception:
                        pass
                    self._respawn_wild_pokemon()
                    return sprite
        return None

    def load_object_collisions(self):
        for obj in self.tmx_data.objects:
            if obj.name and "collision" in obj.name.lower():
                rect = pygame.Rect(int(obj.x), int(obj.y), int(obj.width), int(obj.height))
                self.obj_collisions.append(rect)

    def get_spawns(self):
        spawns = {}
        for obj in self.tmx_data.objects:
            if obj.name and obj.x is not None and obj.y is not None:
                spawns[obj.name.strip()] = (int(obj.x), int(obj.y))
        return spawns

    def get_exits(self):
        exits = []
        for obj in self.tmx_data.objects:
            if obj.name and "switch" in obj.name.lower():
                exits.append({
                    "rect": pygame.Rect(int(obj.x), int(obj.y), int(obj.width), int(obj.height)),
                    "to_map": obj.properties.get("target_map") or obj.properties.get("to_map", None),
                    "to_spawn": obj.properties.get("target_spawn") or obj.properties.get("to_spawn", "Player"),
                })
        return exits

    def load_items(self):
        for obj in self.tmx_data.objects:
            group = getattr(obj, "group", None) or getattr(obj, "parent", None)
            group_name = getattr(group, "name", None)
            if not group_name:
                continue
            if group_name.lower() != "items":
                continue
            image_path = obj.properties.get("image")
            name = obj.name or "item"
            item = ItemSprite(name, (obj.x, obj.y), image_path=image_path)
            self.items.add(item)
            self.group.add(item, layer=self._player_layer)

    def remove_item(self, name: str):
        for item in list(self.items):
            if item.name == name:
                self.items.remove(item)
                try:
                    self.group.remove(item)
                except Exception:
                    pass

    def load_npcs(self):
        for obj in self.tmx_data.objects:
            group = getattr(obj, "group", None) or getattr(obj, "parent", None)
            group_name = getattr(group, "name", None)
            if not group_name:
                continue
            if group_name.lower() not in ("pnjs", "npcs"):
                continue
            image_path = obj.properties.get("image")
            if not image_path:
                continue
            patrol_x = obj.properties.get("x2")
            patrol_y = obj.properties.get("y2")
            patrol_to = None
            if patrol_x is not None and patrol_y is not None:
                patrol_to = (float(patrol_x), float(patrol_y))
            speed = obj.properties.get("speed", 1)
            npc = PNJ(obj.x, obj.y, image_path, patrol_to=patrol_to, speed=speed)
            self.npcs.add(npc)
            self.group.add(npc, layer=self._player_layer)

    def get_interact_zones(self):
        zones = []
        for obj in self.tmx_data.objects:
            if not obj.name:
                continue

            name_lower = obj.name.lower()
            props = obj.properties or {}

            is_named_interact = (
                "interact" in name_lower or
                "panneau" in name_lower or
                "sac" in name_lower or
                "starter_table" in name_lower or
                "table_starter" in name_lower or
                (name_lower == "starter") or
                ("starter" in name_lower)
            )
            is_event_starter = (props.get("event") == "starter_choice")

            if is_named_interact or is_event_starter:
                zones.append({
                    "name": obj.name,
                    "rect": pygame.Rect(int(obj.x), int(obj.y), int(obj.width), int(obj.height)),
                    "text": props.get("text", ""),
                    "properties": props,
                })
        return zones

    def is_collision(self, x, y, ignore_water=False):
        if ignore_water and self.is_water_tile(x, y):
            ignore_water = True
        for rect in self.obj_collisions:
            if rect.collidepoint(x, y):
                return True

        for layer in self.tmx_data.visible_layers:
            if hasattr(layer, "name") and "collision" in layer.name.lower():
                tile_x = int(x // self.tmx_data.tilewidth)
                tile_y = int(y // self.tmx_data.tileheight)
                if 0 <= tile_x < self.tmx_data.width and 0 <= tile_y < self.tmx_data.height:
                    gid = layer.data[tile_x][tile_y]
                    if gid != 0 and not (ignore_water and self.is_water_tile(x, y)):
                        return True
        return False

    def check_exit(self, player_rect):
        for ex in self.exits:
            if ex["rect"].colliderect(player_rect):
                return ex
        return None

    def update(self):
        # Game.update() appelle déjà player.update()
        # Donc pas self.group.update() (sinon double update player).
        self.npcs.update()

        # On force update follower (car group.update() non appelé)
        if self.follower:
            self.follower.update()
        if self.wild_pokemons:
            self.wild_pokemons.update()

    def set_overview_zoom(self, enabled: bool):
        self.overview_zoom = bool(enabled)
        if self.overview_zoom:
            self.renderer.zoom = self.full_zoom
        else:
            self.renderer.zoom = self.default_zoom

    def draw(self, screen):
        self.group.center(self.player.rect.center)
        self.group.draw(screen)


# --- Compat: certains fichiers appellent get_interaction_zone ---
if not hasattr(Map, "get_interaction_zone"):
    def get_interaction_zone(self, player_rect):
        for zone in self.interact_zones:
            if zone["rect"].colliderect(player_rect):
                return zone
        return None

    setattr(Map, "get_interaction_zone", get_interaction_zone)
