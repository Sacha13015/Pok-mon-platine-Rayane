import os
import math
import glob
import pygame
from dataclasses import dataclass


def clamp(v, a, b):
    return a if v < a else b if v > b else v


def ease_in_out(t: float) -> float:
    # smoothstep
    return t * t * (3 - 2 * t)


@dataclass
class StarterChoiceResult:
    chosen: bool
    starter_id: int | None  # 1..4


class _Camera:
    """
    Mini caméra "fausse 3D": projection perspective + pitch.
    """
    def __init__(self, screen_size: tuple[int, int]):
        self.w, self.h = screen_size
        self.pitch_deg = -30.0
        self.distance = 300.0
        self.target = [0.0, 0.0, 0.0]
        self.fov = 420.0

    def project(self, x: float, y: float, z: float) -> tuple[int, int, float]:
        x -= self.target[0]
        y -= self.target[1]
        z -= self.target[2]

        pitch = math.radians(self.pitch_deg)
        cp = math.cos(pitch)
        sp = math.sin(pitch)

        y2 = y * cp - z * sp
        z2 = y * sp + z * cp

        z2 += self.distance
        z2 = max(1.0, z2)

        scale = self.fov / z2
        sx = int(self.w * 0.5 + x * scale)
        sy = int(self.h * 0.50 + y2 * scale)
        return sx, sy, scale


class _Tween3:
    def __init__(self, a: float, b: float, frames: int):
        self.a = a
        self.b = b
        self.frames = max(1, frames)

    def value_at(self, i: int) -> float:
        i = clamp(i, 0, self.frames)
        t = i / float(self.frames)
        return self.a + (self.b - self.a) * t


class StarterChoiceScene3D:
    """
    Choix starter "fausse 3D" style DS, version améliorée:
    - entrée avec petite respiration (pas brusque)
    - support 4 starters (dont Pikachu)
    - preview qui pulse
    - sortie légèrement retardée (fade-out visible)
    """

    def __init__(
        self,
        screen: pygame.Surface,
        clock: pygame.time.Clock,
        base_frame: pygame.Surface,
        focus_rect: pygame.Rect,
        *,
        assets_root: str = "assets",
        # timing
        fade_ms: int = 280,
        entry_pause_frames: int = 18,      # ✅ nouveau: respiration au début
        bag_wait_frames: int = 36,
        open_anim_fps: int = 30,
        cursor_bob_amp: float = 8.0,
        cursor_bob_period: float = 0.55,
        select_sound_path: str | None = None,
        bag_sound_path: str | None = None,
        confirm_sound_path: str | None = None,
        camera_move_frames: int = 6,
        # ✅ starters: Bulbizarre, Salamèche, Carapuce + Pikachu easter egg
        starter_ids: tuple[int, int, int, int] = (1, 2, 3, 4),
    ):
        self.screen = screen
        self.clock = clock
        self.base_frame = base_frame.convert_alpha()
        self.focus_rect = focus_rect.copy()
        self.assets_root = assets_root

        self.fade_ms = fade_ms
        self.entry_pause_frames = max(0, entry_pause_frames)
        self.bag_wait_frames = bag_wait_frames
        self.open_anim_fps = open_anim_fps
        self.cursor_bob_amp = cursor_bob_amp
        self.cursor_bob_period = max(0.1, cursor_bob_period)
        self.camera_move_frames = max(1, camera_move_frames)
        self.starter_ids = starter_ids

        self.snd_select = self._load_sound(select_sound_path)
        self.snd_bag = self._load_sound(bag_sound_path)
        self.snd_confirm = self._load_sound(confirm_sound_path)

        self.font = pygame.font.Font(None, 40)
        self.small = pygame.font.Font(None, 26)

        # --- assets UI / scène ---
        self.dir_3d = os.path.join(self.assets_root, "images", "choix_starter_3d")

        self.briefcase_open_frames = self._load_frames(os.path.join(self.dir_3d, "briefcase", "open_*.png"))
        self.briefcase_open_img = self._load_image(os.path.join(self.dir_3d, "briefcase", "open_static.png"))
        self.briefcase_closed_img = self._load_image(os.path.join(self.dir_3d, "briefcase", "closed.png"))

        self.ball_img = self._load_image(os.path.join(self.dir_3d, "pokeballs", "ball.png"))
        self.cursor_img = self._load_image(os.path.join(self.dir_3d, "ui", "cursor.png"))

        # ✅ pokémon previews: on utilise tes sprites "output_pokemon"
        # -> recommandé: extraire le zip dans assets/pokemon/
        self.poke_img = {
            1: self._load_pokemon_any([
                os.path.join(self.assets_root, "pokemon", "001_Bulbizarre.png"),
                os.path.join(self.assets_root, "images", "choix_starter", "pokemon", "bulbizarre.png"),
                os.path.join(self.assets_root, "images", "choix_starter", "pokemon", "001_Bulbizarre.png"),
            ]),
            2: self._load_pokemon_any([
                os.path.join(self.assets_root, "pokemon", "005_Salamèche.png"),
                os.path.join(self.assets_root, "images", "choix_starter", "pokemon", "salameche.png"),
                os.path.join(self.assets_root, "images", "choix_starter", "pokemon", "005_Salamèche.png"),
            ]),
            3: self._load_pokemon_any([
                os.path.join(self.assets_root, "pokemon", "008_Carapuce.png"),
                os.path.join(self.assets_root, "images", "choix_starter", "pokemon", "carapuce.png"),
                os.path.join(self.assets_root, "images", "choix_starter", "pokemon", "008_Carapuce.png"),
            ]),
            4: self._load_pokemon_any([
                os.path.join(self.assets_root, "pokemon", "026_Pikachu.png"),
                os.path.join(self.assets_root, "images", "choix_starter", "pokemon", "pikachu.png"),
                os.path.join(self.assets_root, "images", "choix_starter", "pokemon", "026_Pikachu.png"),
            ]),
        }

        self.camera = _Camera(self.screen.get_size())

        # ✅ positions balles (3 + pikachu)
        self.ball_pos = [
            (-58.0, -4.0, 34.0),  # left
            (-16.0, -4.0, 62.0),  # mid-left
            (18.0, -4.0, 62.0),   # mid-right
            (60.0, -4.0, 30.0),   # right
        ]

        # positions 2D de curseur, style DS (référencées 256x192 puis rescale)
        self.cursor_pos_2d = [
            (62, 58),
            (110, 88),
            (148, 88),
            (196, 58),
        ]

        self.main_state = 0
        self.sub_state = 0
        self.block_input = True
        self.timer_frames = 0

        self.sel_index = 1  # default
        self.preview_choice = 0
        self.available_count = 3
        self.pikachu_unlocked = False
        self.pikachu_cycles = 0

        self.cam_t = 0
        self.tw_pitch = _Tween3(-30.0, -50.0, self.camera_move_frames)
        self.tw_dist = _Tween3(300.0, 200.0, self.camera_move_frames)
        self.tw_tz = _Tween3(0.0, 36.0, self.camera_move_frames)

        self.fade = 1.0
        self.fade_dir = -1
        self.fade_t = 0

        self.open_frame = 0
        self.open_accum = 0.0

        self.key_cooldown = 0
        self._result: StarterChoiceResult | None = None

    # --------------------
    # LOADING
    # --------------------
    def _load_image(self, path: str) -> pygame.Surface | None:
        try:
            if path and os.path.exists(path):
                return pygame.image.load(path).convert_alpha()
        except Exception:
            pass
        return None

    def _load_frames(self, pattern: str) -> list[pygame.Surface]:
        frames: list[pygame.Surface] = []
        for p in sorted(glob.glob(pattern)):
            img = self._load_image(p)
            if img:
                frames.append(img)
        return frames

    def _load_sound(self, path: str | None):
        if not path:
            return None
        try:
            if os.path.exists(path):
                return pygame.mixer.Sound(path)
        except Exception:
            return None
        return None

    def _play(self, snd):
        if snd:
            try:
                snd.play()
            except Exception:
                pass

    def _load_pokemon_any(self, candidates: list[str]) -> pygame.Surface | None:
        # tente plusieurs chemins + si rien, tente de scanner assets/pokemon/ avec des mots clés
        for p in candidates:
            img = self._load_image(p)
            if img:
                return img

        # scan "assets/pokemon" si présent
        folder = os.path.join(self.assets_root, "pokemon")
        if os.path.isdir(folder):
            # on essaie une recherche approximative
            wanted = []
            joined = " ".join(candidates).lower()
            if "bulb" in joined or "001_" in joined:
                wanted = ["001_", "bulb"]
            elif "sala" in joined or "005_" in joined:
                wanted = ["005_", "sala"]
            elif "cara" in joined or "008_" in joined:
                wanted = ["008_", "cara"]
            elif "pika" in joined or "026_" in joined:
                wanted = ["026_", "pika"]

            for fn in os.listdir(folder):
                low = fn.lower()
                if low.endswith(".png") and all(w in low for w in wanted):
                    img = self._load_image(os.path.join(folder, fn))
                    if img:
                        return img

        return None

    # --------------------
    # PUBLIC
    # --------------------
    def run(self) -> StarterChoiceResult:
        self.fade = 1.0
        self.fade_dir = -1
        self.fade_t = 0

        # ✅ respiration au début
        self.block_input = True
        self.timer_frames = self.entry_pause_frames

        while True:
            dt_ms = self.clock.tick(60)
            dt = dt_ms / 1000.0
            self.key_cooldown = max(0, self.key_cooldown - dt_ms)

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return StarterChoiceResult(False, None)
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        return StarterChoiceResult(False, None)
                    self._handle_key(event.key)

            self._update(dt, dt_ms)
            self._draw()
            pygame.display.flip()

            if self._result is not None:
                return self._result

    # --------------------
    # INPUT
    # --------------------
    def _handle_key(self, key: int):
        if self.key_cooldown > 0:
            return
        if self.main_state < 3 or self.block_input:
            return

        # preview oui/non
        if self.main_state == 4:
            if key in (pygame.K_LEFT, pygame.K_q, pygame.K_RIGHT, pygame.K_d):
                self.preview_choice = 1 - self.preview_choice
                self._play(self.snd_select)
                self.key_cooldown = 90
                return

            if key in (pygame.K_RETURN, pygame.K_SPACE, pygame.K_e):
                if self.preview_choice == 0:
                    self._play(self.snd_confirm)
                    self.main_state = 5
                    self._start_fade_out()
                    return
                self._play(self.snd_select)
                self.main_state = 3
                self.block_input = False
                self.key_cooldown = 110
                return

        # selection loop
        n = self.available_count
        if key in (pygame.K_LEFT, pygame.K_q):
            prev = self.sel_index
            self.sel_index = (self.sel_index - 1) % n
            if prev == 0 and self.sel_index == n - 1:
                self._count_pikachu_cycle()
            self._play(self.snd_select)
            self.key_cooldown = 90
        elif key in (pygame.K_RIGHT, pygame.K_d):
            prev = self.sel_index
            self.sel_index = (self.sel_index + 1) % n
            if prev == n - 1 and self.sel_index == 0:
                self._count_pikachu_cycle()
            self._play(self.snd_select)
            self.key_cooldown = 90
        elif key in (pygame.K_RETURN, pygame.K_SPACE, pygame.K_e):
            self._play(self.snd_confirm)
            self.main_state = 4
            self.sub_state = 0
            self.block_input = True
            self.preview_choice = 0
            self.key_cooldown = 120

    # --------------------
    # UPDATE
    # --------------------
    def _start_fade_out(self):
        self.fade_dir = +1
        self.fade_t = 0

    def _update_fade(self, dt_ms: int):
        if self.fade_dir == 0:
            return

        self.fade_t += dt_ms
        t = clamp(self.fade_t / float(self.fade_ms), 0.0, 1.0)

        if self.fade_dir < 0:
            self.fade = 1.0 - t
            if t >= 1.0:
                self.fade = 0.0
                self.fade_dir = 0
        else:
            self.fade = t
            if t >= 1.0:
                self.fade = 1.0

    def _update(self, dt: float, dt_ms: int):
        self._update_fade(dt_ms)

        # ✅ entrée: mini pause
        if self.timer_frames > 0:
            self.timer_frames -= 1
            return

        if self.main_state == 0:
            self.block_input = True
            self.timer_frames = self.bag_wait_frames
            self.main_state = 1

        elif self.main_state == 1:
            self.timer_frames -= 1
            if self.timer_frames <= 0:
                self._play(self.snd_bag)
                self.main_state = 2
                self.open_frame = 0
                self.open_accum = 0.0

        elif self.main_state == 2:
            fps = max(1, self.open_anim_fps)
            self.open_accum += dt * fps
            if self.briefcase_open_frames:
                self.open_frame = int(self.open_accum)
                if self.open_frame >= len(self.briefcase_open_frames) - 1:
                    self.open_frame = len(self.briefcase_open_frames) - 1
                    self.main_state = 3
                    self.block_input = False
                    self.cam_t = 0
            else:
                self.open_accum += dt * 2.0
                if self.open_accum > 1.0:
                    self.main_state = 3
                    self.block_input = False
                    self.cam_t = 0

        elif self.main_state == 3:
            if self.cam_t <= self.camera_move_frames:
                self.camera.pitch_deg = self.tw_pitch.value_at(self.cam_t)
                self.camera.distance = self.tw_dist.value_at(self.cam_t)
                self.camera.target[2] = self.tw_tz.value_at(self.cam_t)
                self.cam_t += 1

        elif self.main_state == 4:
            if self.sub_state == 0:
                self.timer_frames = 6
                self.sub_state = 1
            elif self.sub_state == 1:
                self.timer_frames -= 1
                if self.timer_frames <= 0:
                    self.block_input = False
                    self.sub_state = 2

        elif self.main_state == 5:
            if self.fade_dir == 0:
                self._start_fade_out()

    # --------------------
    # DRAW HELPERS
    # --------------------
    def _draw_background_zoom(self):
        w, h = self.screen.get_size()
        focus_center = self.focus_rect.center
        scale = 1.15

        scaled_w = int(w * scale)
        scaled_h = int(h * scale)

        scaled = pygame.transform.smoothscale(self.base_frame, (scaled_w, scaled_h))
        fx, fy = focus_center
        target_x = int(fx * scale - (w / 2))
        target_y = int(fy * scale - (h / 2))

        self.screen.blit(scaled, (-target_x, -target_y))

        overlay = pygame.Surface((w, h), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 90))
        self.screen.blit(overlay, (0, 0))

    def _blit_centered_scaled(self, img: pygame.Surface, cx: int, cy: int, scale: float, alpha: int = 255):
        if not img:
            return
        scale = max(0.01, scale)
        w = max(1, int(img.get_width() * scale))
        h = max(1, int(img.get_height() * scale))
        surf = pygame.transform.smoothscale(img, (w, h))
        if alpha < 255:
            surf.set_alpha(alpha)
        self.screen.blit(surf, (cx - w // 2, cy - h // 2))

    def _draw_title(self):
        w, h = self.screen.get_size()
        title = self.font.render("Choisis ton Pokémon", True, (255, 255, 255))
        self.screen.blit(title, (w // 2 - title.get_width() // 2, int(h * 0.06)))

        hint = self.small.render("← → choisir • Entrée/Espace valider • ESC annuler", True, (220, 220, 220))
        self.screen.blit(hint, (w // 2 - hint.get_width() // 2, int(h * 0.12)))

    def _draw_briefcase(self):
        x, y, z = (0.0, 10.0, 35.0)
        sx, sy, sc = self.camera.project(x, y, z)

        if self.main_state < 2:
            img = self.briefcase_closed_img or self.briefcase_open_img
        elif self.main_state == 2 and self.briefcase_open_frames:
            img = self.briefcase_open_frames[self.open_frame]
        else:
            img = self.briefcase_open_img or (self.briefcase_open_frames[-1] if self.briefcase_open_frames else None) or self.briefcase_closed_img

        if img:
            self._blit_centered_scaled(img, sx, sy, sc * 2.2)
        else:
            rect = pygame.Rect(0, 0, int(260 * sc), int(150 * sc))
            rect.center = (sx, sy)
            pygame.draw.rect(self.screen, (60, 60, 60), rect, border_radius=14)
            pygame.draw.rect(self.screen, (0, 0, 0), rect, 4, border_radius=14)

    def _draw_balls(self):
        if self.main_state < 3:
            return

        items = []
        for i, (x, y, z) in enumerate(self.ball_pos[: self.available_count]):
            sx, sy, sc = self.camera.project(x, y, z)
            items.append((sc, i, sx, sy))
        items.sort()

        for sc, i, sx, sy in items:
            is_sel = (i == self.sel_index)

            pulse = 1.0
            if is_sel:
                pulse = 1.08 + 0.02 * math.sin(pygame.time.get_ticks() / 120.0)

            if self.ball_img:
                self._blit_centered_scaled(self.ball_img, sx, sy, sc * 1.6 * pulse)
            else:
                r = int(28 * sc * pulse)
                pygame.draw.circle(self.screen, (255, 255, 255), (sx, sy), r, 5)
                pygame.draw.circle(self.screen, (0, 0, 0), (sx, sy), r, 2)

            sid = self.starter_ids[i]
            preview = self.poke_img.get(sid)
            if preview:
                target = int(34 * sc)
                scale = min(target / max(1, preview.get_width()), target / max(1, preview.get_height()))
                self._blit_centered_scaled(preview, sx, sy - int(10 * sc), scale)

            if is_sel:
                ring_r = int(36 * sc * pulse)
                pygame.draw.circle(self.screen, (255, 255, 200), (sx, sy + int(6 * sc)), ring_r, 3)

            if self.pikachu_unlocked and i == 3:
                glow_r = int(46 * sc)
                pygame.draw.circle(self.screen, (255, 240, 180), (sx, sy), glow_r, 4)

    def _draw_cursor(self):
        if self.main_state < 3 or self.main_state == 4:
            return

        w, h = self.screen.get_size()
        base_x, base_y = self.cursor_pos_2d[self.sel_index]

        t = pygame.time.get_ticks() / 1000.0
        bob = self.cursor_bob_amp * math.sin((2 * math.pi / self.cursor_bob_period) * t)

        cx = int((base_x / 256.0) * w)
        cy = int((base_y / 192.0) * h + bob)

        if self.cursor_img:
            self._blit_centered_scaled(self.cursor_img, cx, cy, 1.0)
        else:
            pts = [(cx, cy), (cx - 14, cy + 22), (cx + 14, cy + 22)]
            pygame.draw.polygon(self.screen, (255, 255, 255), pts)
            pygame.draw.polygon(self.screen, (0, 0, 0), pts, 2)

    def _count_pikachu_cycle(self):
        if self.pikachu_unlocked:
            return
        self.pikachu_cycles += 1
        if self.pikachu_cycles >= 3:
            self.pikachu_unlocked = True
            self.available_count = 4

    def _draw_preview(self):
        if self.main_state != 4:
            return

        w, h = self.screen.get_size()
        sid = self.starter_ids[self.sel_index]
        img = self.poke_img.get(sid)

        veil = pygame.Surface((w, h), pygame.SRCALPHA)
        veil.fill((0, 0, 0, 140))
        self.screen.blit(veil, (0, 0))

        card = pygame.Rect(0, 0, int(w * 0.62), int(h * 0.55))
        card.center = (w // 2, int(h * 0.48))
        pygame.draw.rect(self.screen, (245, 245, 245), card, border_radius=18)
        pygame.draw.rect(self.screen, (0, 0, 0), card, 4, border_radius=18)

        title = self.font.render("Tu le veux ?", True, (0, 0, 0))
        self.screen.blit(title, (card.centerx - title.get_width() // 2, card.top + 18))

        # ✅ pulse léger sur le pokemon
        if img:
            target = int(min(card.w, card.h) * 0.55)
            sc = min(target / max(1, img.get_width()), target / max(1, img.get_height()))
            pulse = 1.0 + 0.03 * math.sin(pygame.time.get_ticks() / 250.0)
            self._blit_centered_scaled(img, card.centerx, card.centery - 20, sc * pulse)
        else:
            txt = self.small.render("(sprite manquant)", True, (0, 0, 0))
            self.screen.blit(txt, (card.centerx - txt.get_width() // 2, card.centery - 10))

        btn_w, btn_h = int(card.w * 0.26), 52
        gap = 22
        left = pygame.Rect(0, 0, btn_w, btn_h)
        right = pygame.Rect(0, 0, btn_w, btn_h)
        left.center = (card.centerx - btn_w // 2 - gap, card.bottom - 70)
        right.center = (card.centerx + btn_w // 2 + gap, card.bottom - 70)

        def draw_btn(r: pygame.Rect, label: str, selected: bool):
            pygame.draw.rect(self.screen, (255, 255, 255), r, border_radius=14)
            pygame.draw.rect(self.screen, (0, 0, 0), r, 3, border_radius=14)
            if selected:
                pygame.draw.rect(self.screen, (40, 140, 255), r.inflate(8, 8), 4, border_radius=16)
            t = self.small.render(label, True, (0, 0, 0))
            self.screen.blit(t, (r.centerx - t.get_width() // 2, r.centery - t.get_height() // 2))

        draw_btn(left, "Oui", self.preview_choice == 0)
        draw_btn(right, "Non", self.preview_choice == 1)

    def _draw_fade(self):
        if self.fade <= 0.0:
            return
        w, h = self.screen.get_size()
        a = int(255 * clamp(self.fade, 0.0, 1.0))
        surf = pygame.Surface((w, h), pygame.SRCALPHA)
        surf.fill((0, 0, 0, a))
        self.screen.blit(surf, (0, 0))

    # --------------------
    # DRAW
    # --------------------
    def _draw(self):
        self._draw_background_zoom()
        self._draw_title()
        self._draw_briefcase()
        self._draw_balls()
        self._draw_cursor()
        self._draw_preview()
        self._draw_fade()

        # ✅ fin de scène: quand fade-out terminé, on renvoie résultat proprement
        if self.main_state == 5 and self.fade >= 1.0:
            pygame.time.delay(80)
            sid = self.starter_ids[self.sel_index]
            self._result = StarterChoiceResult(True, sid)


# Alias compat
StarterChoiceScene = StarterChoiceScene3D
