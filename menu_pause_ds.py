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

        # ❌ Pokémon retiré (comme demandé)
        self.tabs = [
            ("Pokédex", "Pokedex.png"),
            ("Sac", "Sac_face.png"),
            ("Pokégear", "carte.png"),
            ("Références", "references.png"),
            ("Sauvegarder", "sauvegarder.png"),
            ("Options", "paramètre.png"),
            ("Quitter le jeu", "quitter.png"),
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

        menu_w = self.screen.get_width() // 2
        menu_h = self.screen.get_height() - 100
        menu_x = 50
        menu_y = 50

        icon_size = 56
        font = pygame.font.SysFont("arial", 32, bold=True)
        tab_height = 68

        choice = None

        while self.running:
            self.screen.blit(blurred, (0, 0))

            overlay = pygame.Surface(self.screen.get_size(), pygame.SRCALPHA)
            overlay.fill((255, 255, 255, 70))
            self.screen.blit(overlay, (0, 0))

            menu_rect = pygame.Rect(menu_x, menu_y, menu_w, menu_h)
            pygame.draw.rect(self.screen, (235, 238, 255), menu_rect, border_radius=24)
            pygame.draw.rect(self.screen, (150, 160, 170), menu_rect, 5, border_radius=24)

            for i, (tab, icon_file) in enumerate(self.tabs):
                y = menu_y + 20 + i * tab_height
                selected = (i == self.selected)

                is_ok = self._is_accessible(tab)
                color = (60, 140, 255) if selected and is_ok else (50, 50, 50)
                if not is_ok:
                    color = (120, 120, 120)

                tab_rect = pygame.Rect(menu_x + 10, y, menu_w - 20, tab_height - 8)
                if selected:
                    pygame.draw.rect(self.screen, (210, 230, 255), tab_rect, border_radius=16)

                icon = self._get_icon(icon_file, icon_size, is_ok)
                self.screen.blit(icon, (tab_rect.x + 12, tab_rect.y + 6))

                label = font.render(tab, True, color)
                self.screen.blit(label, (tab_rect.x + icon_size + 30, tab_rect.y + 12))

                if not is_ok:
                    fade = pygame.Surface(tab_rect.size, pygame.SRCALPHA)
                    fade.fill((180, 180, 180, 130))
                    self.screen.blit(fade, tab_rect.topleft)

            pygame.display.flip()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()

                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        self.running = False
                        break

                    if event.key in (pygame.K_DOWN, pygame.K_s):
                        self.selected = (self.selected + 1) % len(self.tabs)

                    if event.key in (pygame.K_UP, pygame.K_z, pygame.K_w):
                        self.selected = (self.selected - 1) % len(self.tabs)

                    if event.key in (pygame.K_RETURN, pygame.K_SPACE):
                        tab_name = self.tabs[self.selected][0]

                        if tab_name == "Quitter le jeu":
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
