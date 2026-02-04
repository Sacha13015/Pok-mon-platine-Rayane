import os
import pygame


def abs_path_from_code(relative_path: str) -> str:
    base_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.normpath(os.path.join(base_dir, relative_path))


def _remove_green_screen_to_alpha(surface: pygame.Surface,
                                 g_min=140, rg_max=120, bg_max=120,
                                 feather=0) -> pygame.Surface:
    """
    Enlève un fond vert même s'il n'est pas exactement (0,255,0).
    Convertit en surface avec alpha et rend transparents les pixels "assez verts".

    Critère simple:
      - G >= g_min
      - R <= rg_max
      - B <= bg_max

    feather optionnel : 0 recommandé (simple et net).
    """
    # On garantit un format avec alpha
    surf = surface.convert_alpha()
    w, h = surf.get_size()

    # Pixel access (rapide)
    px = pygame.PixelArray(surf)
    try:
        for y in range(h):
            for x in range(w):
                r, g, b, a = surf.unmap_rgb(px[x, y])
                if g >= g_min and r <= rg_max and b <= bg_max:
                    # transparent
                    px[x, y] = (0, 0, 0, 0)
    finally:
        del px

    return surf


class Follower(pygame.sprite.Sprite):
    """
    Follower DS-like:
    - suit player.history avec offset
    - déplacement 1 axe à la fois
    - animation 2 frames visible quand ça bouge
    - suppression fond vert robuste (même si pas exactement 0,255,0)

    Layout supportés :
    - "rows": directions en LIGNES, frames en COLONNES (le plus courant)
      rows = 4 (down,left,right,up), cols = nb_frames (souvent 2)
      [down row]
      [left row]
      [right row]
      [up row]

    - "cols": directions en COLONNES, frames en LIGNES (moins courant)
      cols = 4 (down,left,right,up), rows = nb_frames
    """

    def __init__(
        self,
        player,
        spritesheet_path: str,
        cols: int,
        rows: int,
        offset_frames: int = 8,
        speed: int = 2,
        y_offset: int = 28,
        anim_every: int = 8,
        layout: str = "rows",          # "rows" (reco) ou "cols"
        remove_green: bool = True      # True = enlève le fond vert même approximatif
    ):
        super().__init__()
        self.player = player
        self.offset = max(0, int(offset_frames))
        self.speed = max(1, int(speed))
        self.y_offset = int(y_offset)

        self.anim_every = max(1, int(anim_every))
        self.anim_timer = 0

        # DS-like: 0=down,1=left,2=right,3=up
        self.direction = 0

        # Animation "DS-like" = 2 frames (0/1) quand ça bouge
        self.walk_frame = 0

        self.layout = layout.lower().strip()
        if self.layout not in ("rows", "cols"):
            self.layout = "rows"

        sheet_full = abs_path_from_code(spritesheet_path)

        # IMPORTANT :
        # - Si ton image est "green screen" (pas d'alpha), convert() + nettoyage est plus fiable
        # - Si elle a un alpha correct, convert_alpha() suffit, mais remove_green ne gêne pas
        raw = pygame.image.load(sheet_full)
        # On part sur un format alpha sûr
        self.spritesheet = raw.convert_alpha()

        if remove_green:
            # nettoyage tolérant (pas besoin d'un vert exact)
            self.spritesheet = _remove_green_screen_to_alpha(self.spritesheet)

        self.cols = int(cols)
        self.rows = int(rows)
        if self.cols <= 0 or self.rows <= 0:
            raise ValueError("cols et rows doivent être > 0")

        self.frame_w = self.spritesheet.get_width() // self.cols
        self.frame_h = self.spritesheet.get_height() // self.rows

        self.images = self._cut_frames()

        self.image = self.images[self.direction][self.walk_frame]
        self.rect = self.image.get_rect(
            topleft=(player.rect.x, player.rect.y + self.y_offset)
        )

    def _cut_frames(self):
        """
        Retour: images[direction][frame]
        direction: 0..3 (down,left,right,up)
        frame: 0..(nframes-1)
        """
        images = [[], [], [], []]

        if self.layout == "rows":
            # directions en lignes: row = direction
            # frames en colonnes: col = frame
            # => rows doit être >= 4 idéalement
            # Si rows > 4, on prend les 4 premières lignes
            dir_rows = [0, 1, 2, 3]
            nframes = self.cols
            for d, row in enumerate(dir_rows):
                frames = []
                y = row * self.frame_h
                for f in range(nframes):
                    x = f * self.frame_w
                    frame = self.spritesheet.subsurface((x, y, self.frame_w, self.frame_h)).copy()
                    frames.append(frame)
                images[d] = frames

        else:
            # directions en colonnes: col = direction
            # frames en lignes: row = frame
            dir_cols = [0, 1, 2, 3]
            nframes = self.rows
            for d, col in enumerate(dir_cols):
                frames = []
                x = col * self.frame_w
                for f in range(nframes):
                    y = f * self.frame_h
                    frame = self.spritesheet.subsurface((x, y, self.frame_w, self.frame_h)).copy()
                    frames.append(frame)
                images[d] = frames

        # Si le sheet n'a qu'1 frame, on duplique pour avoir une anim 2 frames
        for d in range(4):
            if len(images[d]) == 1:
                images[d] = [images[d][0], images[d][0]]

        return images

    def _dir_from_step(self, dx, dy):
        if abs(dx) > abs(dy):
            return 2 if dx > 0 else 1
        return 0 if dy > 0 else 3

    def update(self):
        hist = getattr(self.player, "history", None)
        if not hist:
            self.rect.topleft = (self.player.rect.x, self.player.rect.y + self.y_offset)
            self.walk_frame = 0
            self.anim_timer = 0
            self.image = self.images[self.direction][self.walk_frame]
            return

        # cible derrière le joueur
        if len(hist) <= self.offset:
            tx, ty = hist[-1]
        else:
            tx, ty = hist[self.offset]
        ty += self.y_offset

        dx = tx - self.rect.x
        dy = ty - self.rect.y

        # Stop moins agressif (sinon anim jamais visible)
        stop_threshold = self.speed * 2
        if abs(dx) <= stop_threshold and abs(dy) <= stop_threshold:
            self.rect.x = tx
            self.rect.y = ty
            self.walk_frame = 0
            self.anim_timer = 0
            self.image = self.images[self.direction][self.walk_frame]
            return

        # mouvement DS: 1 axe à la fois
        moved = False
        if abs(dx) > abs(dy):
            step = self.speed if dx > 0 else -self.speed
            self.direction = self._dir_from_step(step, 0)
            self.rect.x += step
            moved = True
        else:
            step = self.speed if dy > 0 else -self.speed
            self.direction = self._dir_from_step(0, step)
            self.rect.y += step
            moved = True

        # Animation 2 frames (visible)
        if moved:
            self.anim_timer += 1
            if self.anim_timer >= self.anim_every:
                self.anim_timer = 0
                # alterne 0/1 (DS-like)
                self.walk_frame = 1 - self.walk_frame
        else:
            self.walk_frame = 0
            self.anim_timer = 0

        # clamp au cas où
        frames = self.images[self.direction]
        self.walk_frame = max(0, min(self.walk_frame, len(frames) - 1))
        self.image = frames[self.walk_frame]
