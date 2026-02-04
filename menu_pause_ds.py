import os
import pygame
import sys


class PauseMenuDS:
    def __init__(self, screen, can_access, assets_folder=None):
        self.screen = screen
        self.can_access = can_access

        # ✅ On rend le loader robuste: plusieurs dossiers possibles
        # Mets tes nouvelles icônes dans l’un de ces dossiers, ça marchera.
        self.icon_folders = []
        if assets_folder:
            self.icon_folders.append(assets_folder)

        self.icon_folders += [
            "assets/images/menu_icons",
            "assets/images/menu_pause",
            "assets/images/ui/menu_icons",
            "assets/images/ui",
            "assets/menu_icons",
        ]

        # Menu circulaire demandé
        self.tabs = [
            ("SAC", "Sac_face.png"),
            ("EQUIPE", "equipe.png"),
            ("POKEDEX", "Pokedex.png"),
            ("PARAMETRE", "paramètre.png"),
            ("SAUVEGARDE", "sauvegarder.png"),
            ("QUITTER LE JEU", "quitter.png"),
        ]

        self.selected = 0
        self.running = True
        self._icon_cache = {}

    def blur_surface(self, surface):
        small = pygame.transform.smoothscale(
            surface,
            (max(1, surface.get_width() // 8), max(1, surface.get_height() // 8))
        )
        return pygame.transform.smoothscale(small, surface.get_size())

    def _is_accessible(self, tab_name):
        return bool(self.can_access.get(tab_name, True))

    def _find_icon_path(self, icon_file):
        # variantes de noms acceptées
        variants = [icon_file]
        low = icon_file.lower()

        if low in ("paramètre.png", "parametre.png", "option.png", "options.png"):
            variants = ["paramètre.png", "parametre.png", "option.png", "options.png"]

        # essaie tous les dossiers
        for folder in self.icon_folders:
            for v in variants:
                p = os.path.join(folder, v)
                if os.path.exists(p):
                    return p

            # fallback: case-insensitive
            if os.path.isdir(folder):
                for fn in os.listdir(folder):
                    if fn.lower() == icon_file.lower():
                        return os.path.join(folder, fn)

        # dernier recours: chemin direct
        return os.path.join(self.icon_folders[0], icon_file) if self.icon_folders else icon_file

    def _get_icon(self, icon_file, size, is_ok):
        key = (icon_file, size, is_ok)
        if key in self._icon_cache:
            return self._icon_cache[key]

        path = self._find_icon_path(icon_file)

        try:
            icon = pygame.image.load(path).convert_alpha()
            icon = pygame.transform.smoothscale(icon, (size, size))
            if not is_ok:
                icon.set_alpha(120)
        except Exception:
            icon = pygame.Surface((size, size), pygame.SRCALPHA)
            pygame.draw.circle(icon, (0, 0, 0, 60), (size // 2, size // 2), size // 2)
            pygame.draw.circle(icon, (255, 255, 255, 180), (size // 2, size // 2), size // 2 - 4, 3)

        self._icon_cache[key] = icon
        return icon

    def run(self):
        orig_volume = pygame.mixer.music.get_volume()
        pygame.mixer.music.set_volume(orig_volume * 0.3)

        background = self.screen.copy()
        blurred = self.blur_surface(background)
        clock = pygame.time.Clock()

        w, h = self.screen.get_size()
        center = (w // 2, h // 2)
        radius = min(w, h) // 3

        font = pygame.font.SysFont("arial", 28, bold=True)
        small_font = pygame.font.SysFont("arial", 18, bold=True)

        choice = None

        while self.running:
            self.screen.blit(blurred, (0, 0))

            overlay = pygame.Surface(self.screen.get_size(), pygame.SRCALPHA)
            overlay.fill((255, 255, 255, 70))
            self.screen.blit(overlay, (0, 0))

            pygame.draw.circle(self.screen, (235, 238, 255), center, radius + 40)
            pygame.draw.circle(self.screen, (150, 160, 170), center, radius + 40, 6)
            pygame.draw.circle(self.screen, (245, 248, 255), center, radius - 30)

            # Titre
            title = small_font.render("MENU", True, (70, 70, 70))
            self.screen.blit(title, (center[0] - title.get_width() // 2, center[1] - title.get_height() // 2))

            # Options autour du cercle
            total = len(self.tabs)
            for i, (tab, icon_file) in enumerate(self.tabs):
                angle = -90 + (360 / total) * i
                vector = pygame.math.Vector2(1, 0).rotate(angle)
                x = int(center[0] + radius * 0.95 * vector.x)
                y = int(center[1] + radius * 0.95 * vector.y)

                is_ok = self._is_accessible(tab)
                selected = (i == self.selected)
                color = (60, 140, 255) if selected and is_ok else (50, 50, 50)
                if not is_ok:
                    color = (120, 120, 120)

                label = font.render(tab, True, color)
                label_rect = label.get_rect(center=(x, y))

                if selected:
                    pygame.draw.circle(self.screen, (210, 230, 255), label_rect.center, label_rect.width // 2 + 18)
                    pygame.draw.circle(self.screen, (120, 160, 220), label_rect.center, label_rect.width // 2 + 18, 3)

                self.screen.blit(label, label_rect)

            pygame.display.flip()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()

                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        self.running = False
                        break

                    if event.key in (pygame.K_DOWN, pygame.K_s, pygame.K_RIGHT, pygame.K_d):
                        self.selected = (self.selected + 1) % len(self.tabs)

                    if event.key in (pygame.K_UP, pygame.K_z, pygame.K_w, pygame.K_LEFT, pygame.K_q):
                        self.selected = (self.selected - 1) % len(self.tabs)

                    if event.key in (pygame.K_RETURN, pygame.K_SPACE):
                        tab_name = self.tabs[self.selected][0]

                        if tab_name == "QUITTER LE JEU":
                            pygame.quit()
                            sys.exit()

                        if not self._is_accessible(tab_name):
                            continue

                        choice = tab_name
                        self.running = False
                        break

            clock.tick(30)

        pygame.mixer.music.set_volume(orig_volume)
        return choice
