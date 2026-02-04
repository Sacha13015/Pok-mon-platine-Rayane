import pygame
import sys
import os
import random

# ------------------------------------------------------------
# INTRO DBZ "TV qui s'allume" + Babidi/Buu + Goku transfos + Nuages
# FIXES :
#  - Transparence PNG respectée (convert_alpha)
#  - Colorkey noir UNIQUEMENT si l'image n'a pas d'alpha (fallback intelligent)
#  - Scale des persos en pixel art => transform.scale (nearest) pour éviter halos/artefacts
# ------------------------------------------------------------

ASSETS_DIR = "assets/intro"
TV_OFF_FILENAME = "tv_eteinte.png"

TV_SCREEN_RECT_REL = pygame.Rect(210, 125, 860, 470)
DEBUG_DRAW_TV_RECT = False

# Fallback si certains persos sont VRAIMENT sur fond noir sans alpha
# (si tes PNG sont transparents -> laisse True, ça ne s'appliquera pas)
ENABLE_COLORKEY_FALLBACK_FOR_CHARACTERS = True

SKIP_KEYS = (pygame.K_ESCAPE, pygame.K_SPACE, pygame.K_RETURN)


def _must_have_alpha(surf: pygame.Surface) -> bool:
    """Détecte si la surface a un canal alpha utilisable."""
    return bool(surf.get_flags() & pygame.SRCALPHA) or (surf.get_alpha() is not None)


def _load_image_alpha(path: str) -> pygame.Surface:
    if not os.path.exists(path):
        raise FileNotFoundError(f"Image introuvable : {path}")

    # On charge brut puis on convertit proprement
    img = pygame.image.load(path)
    if _must_have_alpha(img):
        return img.convert_alpha()
    return img.convert()


def _load_character(path: str) -> pygame.Surface:
    """
    Charge un perso :
    - Si PNG avec alpha -> convert_alpha (aucun fond noir possible)
    - Sinon -> convert + colorkey noir (fallback) si activé
    """
    img = _load_image_alpha(path)

    # Si pas d'alpha et fallback activé => colorkey noir
    if ENABLE_COLORKEY_FALLBACK_FOR_CHARACTERS and not _must_have_alpha(img):
        img = img.convert()
        img.set_colorkey((0, 0, 0))

    return img


def _fit_to_screen(img: pygame.Surface, screen_size: tuple[int, int]) -> pygame.Surface:
    sw, sh = screen_size
    iw, ih = img.get_size()
    scale = min(sw / iw, sh / ih)
    nw, nh = int(iw * scale), int(ih * scale)
    # Décors/TV : smooth ok
    return pygame.transform.smoothscale(img, (nw, nh))


def _fit_to_box_pixel(img: pygame.Surface, box_w: int, box_h: int) -> pygame.Surface:
    """
    Scale pixel-art (nearest) pour éviter halos et artefacts.
    IMPORTANT : si colorkey existant, on le remet après scale.
    """
    iw, ih = img.get_size()
    if iw == 0 or ih == 0:
        return img

    scale = min(box_w / iw, box_h / ih)
    nw, nh = max(1, int(iw * scale)), max(1, int(ih * scale))

    out = pygame.transform.scale(img, (nw, nh))  # nearest

    ck = img.get_colorkey()
    if ck is not None:
        out.set_colorkey(ck)

    return out


def play_intro_tv_dbz(screen: pygame.Surface, fps: int = 60) -> None:
    clock = pygame.time.Clock()
    W, H = screen.get_size()

    # ----------- Chargement images -----------
    tv_off = _load_image_alpha(os.path.join(ASSETS_DIR, TV_OFF_FILENAME))
    tv_allumage = _load_image_alpha(os.path.join(ASSETS_DIR, "tv_allumage.png"))
    decor_tv_src = _load_image_alpha(os.path.join(ASSETS_DIR, "décors.png"))
    clouds = _load_image_alpha(os.path.join(ASSETS_DIR, "nuage.png"))

    goku_base = _load_image_alpha(os.path.join(ASSETS_DIR, "goku_base.png"))
    goku_trans = _load_image_alpha(os.path.join(ASSETS_DIR, "goku_transition.png"))
    goku_ssj = _load_image_alpha(os.path.join(ASSETS_DIR, "goku_ssj.png"))
    goku_ssj2 = _load_image_alpha(os.path.join(ASSETS_DIR, "goku_ssj2.png"))
    goku_ssj3 = _load_image_alpha(os.path.join(ASSETS_DIR, "goku ssj3.png"))

    # Persos : load intelligent (alpha sinon colorkey fallback)
    babidi = _load_character(os.path.join(ASSETS_DIR, "babidi.png"))
    buu = _load_character(os.path.join(ASSETS_DIR, "buu.png"))

    # ----------- Mise à l'échelle écran -----------
    tv_off = _fit_to_screen(tv_off, (W, H))
    tv_allumage = _fit_to_screen(tv_allumage, (W, H))
    decor_tv = _fit_to_screen(decor_tv_src, (W, H))

    clouds_scale = W / clouds.get_width()
    clouds = pygame.transform.smoothscale(
        clouds, (W, max(1, int(clouds.get_height() * clouds_scale)))
    )

    # ----------- Placement TV -----------
    tv_rect = decor_tv.get_rect(center=(W // 2, H // 2))

    decor_original_w = decor_tv_src.get_width()
    decor_original_h = decor_tv_src.get_height()
    sx = decor_tv.get_width() / decor_original_w
    sy = decor_tv.get_height() / decor_original_h

    tv_screen_rect = pygame.Rect(
        tv_rect.x + int(TV_SCREEN_RECT_REL.x * sx),
        tv_rect.y + int(TV_SCREEN_RECT_REL.y * sy),
        int(TV_SCREEN_RECT_REL.w * sx),
        int(TV_SCREEN_RECT_REL.h * sy),
    )

    # ----------- Helpers : rendu contenu écran TV -----------
    def blit_tv_content(content_surf: pygame.Surface, jitter: int = 0, alpha: int = 255):
        c = pygame.transform.smoothscale(content_surf, (tv_screen_rect.w, tv_screen_rect.h))
        if jitter > 0:
            jx = random.randint(-jitter, jitter)
            jy = random.randint(-jitter, jitter)
        else:
            jx = jy = 0

        if alpha != 255:
            c = c.copy()
            c.set_alpha(alpha)

        screen.blit(c, (tv_screen_rect.x + jx, tv_screen_rect.y + jy))

    # ----------- Effets -----------
    def flash_white(strength: int):
        f = pygame.Surface((W, H), pygame.SRCALPHA)
        f.fill((255, 255, 255, max(0, min(255, strength))))
        screen.blit(f, (0, 0))

    def tv_noise(intensity: int):
        n = pygame.Surface((tv_screen_rect.w, tv_screen_rect.h), pygame.SRCALPHA)
        for _ in range(intensity):
            x = random.randint(0, tv_screen_rect.w - 1)
            y = random.randint(0, tv_screen_rect.h - 1)
            a = random.randint(25, 110)
            n.set_at((x, y), (255, 255, 255, a))
        for y in range(0, tv_screen_rect.h, 4):
            pygame.draw.line(n, (0, 0, 0, 18), (0, y), (tv_screen_rect.w, y))
        screen.blit(n, tv_screen_rect.topleft)

    # ----------- Animation Nuages -----------
    clouds_x = 0.0

    # ----------- Timeline (ms) -----------
    steps = [
        ("tv_off", 900),
        ("tv_on_anim", 1400),
        ("buu_babidi", 2400),
        ("goku_transform", 7200),
        ("clouds_scene", 3200),
        ("fade_out", 1200),
    ]

    step_idx = 0
    step_start = pygame.time.get_ticks()

    running = True
    while running:
        dt = clock.tick(fps)
        now = pygame.time.get_ticks()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if SKIP_KEYS is not None and event.type == pygame.KEYDOWN and event.key in SKIP_KEYS:
                running = False

        step_name, step_dur = steps[step_idx]
        t = now - step_start

        screen.fill((0, 0, 0))

        # ========== RENDU ==========
        if step_name == "tv_off":
            rect = tv_off.get_rect(center=(W // 2, H // 2))
            screen.blit(tv_off, rect)

        elif step_name == "tv_on_anim":
            rect = tv_allumage.get_rect(center=(W // 2, H // 2))
            screen.blit(tv_allumage, rect)

            if t < 300:
                flash_white(210 - int(t * 0.6))
            tv_noise(520)

        elif step_name == "buu_babidi":
            screen.blit(decor_tv, tv_rect)

            # Contenu TV
            content = pygame.Surface((tv_screen_rect.w, tv_screen_rect.h), pygame.SRCALPHA)
            content.fill((0, 0, 0, 0))  # fond 100% transparent

            box_w = tv_screen_rect.w
            box_h = tv_screen_rect.h

            # Scale pixel-art (nearest)
            bab_s = _fit_to_box_pixel(babidi, int(box_w * 0.42), int(box_h * 0.82))
            buu_s = _fit_to_box_pixel(buu, int(box_w * 0.42), int(box_h * 0.86))

            # Positions : plus bas, plus sur les côtés
            bab_x = int(box_w * 0.04)
            buu_x = int(box_w * 0.56)
            bab_y = int(box_h * 0.22)
            buu_y = int(box_h * 0.18)

            content.blit(bab_s, (bab_x, bab_y))
            content.blit(buu_s, (buu_x, buu_y))

            blit_tv_content(content, jitter=1)  # rend dans la TV avec le bon scale
            tv_noise(260)

            if 1000 < t < 1180:
                flash_white(75)

        elif step_name == "goku_transform":
            screen.blit(decor_tv, tv_rect)

            if t < 1600:
                blit_tv_content(goku_base, jitter=0)
                if 1200 < t < 1600:
                    flash_white(18)
            elif t < 3000:
                blit_tv_content(goku_trans, jitter=5)
                tv_noise(420)
                if (t // 90) % 2 == 0:
                    flash_white(60)
            elif t < 4500:
                blit_tv_content(goku_ssj, jitter=1)
                tv_noise(160)
                if 3000 < t < 3300:
                    flash_white(85)
            elif t < 5900:
                blit_tv_content(goku_ssj2, jitter=2)
                tv_noise(220)
                if (t // 160) % 2 == 0:
                    flash_white(35)
            else:
                blit_tv_content(goku_ssj3, jitter=0)
                tv_noise(120)
                if 5900 < t < 6400:
                    flash_white(55)

        elif step_name == "clouds_scene":
            clouds_x -= 0.25 * dt
            if clouds_x <= -W:
                clouds_x = 0

            screen.blit(clouds, (int(clouds_x), H - clouds.get_height()))
            screen.blit(clouds, (int(clouds_x) + W, H - clouds.get_height()))

            g = _fit_to_screen(goku_ssj3, (int(W * 0.5), int(H * 0.75)))
            grect = g.get_rect(center=(W // 2, int(H * 0.50)))
            screen.blit(g, grect)

            if (t // 320) % 2 == 0:
                flash_white(18)

        elif step_name == "fade_out":
            screen.blit(clouds, (0, H - clouds.get_height()))
            g = _fit_to_screen(goku_ssj3, (int(W * 0.5), int(H * 0.75)))
            grect = g.get_rect(center=(W // 2, int(H * 0.50)))
            screen.blit(g, grect)

            alpha = min(255, int(255 * (t / step_dur)))
            f = pygame.Surface((W, H), pygame.SRCALPHA)
            f.fill((0, 0, 0, alpha))
            screen.blit(f, (0, 0))

        if DEBUG_DRAW_TV_RECT:
            pygame.draw.rect(screen, (255, 0, 0), tv_screen_rect, 2)

        pygame.display.flip()

        # ========== NEXT STEP ==========
        if t >= step_dur:
            step_idx += 1
            if step_idx >= len(steps):
                running = False
            else:
                step_start = pygame.time.get_ticks()


if __name__ == "__main__":
    pygame.init()
    screen = pygame.display.set_mode((1280, 720))
    pygame.display.set_caption("Intro TV DBZ (fixed alpha)")
    play_intro_tv_dbz(screen)
    pygame.quit()
