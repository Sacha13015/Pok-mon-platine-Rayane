import pygame
import pytmx
import pyscroll
import os
import unicodedata


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
        self.renderer.zoom = force_zoom if force_zoom else max(min(auto_zoom, max_zoom), min_zoom)

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

    def is_collision(self, x, y):
        for rect in self.obj_collisions:
            if rect.collidepoint(x, y):
                return True

        for layer in self.tmx_data.visible_layers:
            if hasattr(layer, "name") and "collision" in layer.name.lower():
                tile_x = int(x // self.tmx_data.tilewidth)
                tile_y = int(y // self.tmx_data.tileheight)
                if 0 <= tile_x < self.tmx_data.width and 0 <= tile_y < self.tmx_data.height:
                    gid = layer.data[tile_x][tile_y]
                    if gid != 0:
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

