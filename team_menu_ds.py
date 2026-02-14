import pygame


class TeamMenuDS:
    """
    Menu équipe minimal DS-like:
    - Z/S ou ↑/↓ : sélectionner
    - Q/D ou ←/→ : déplacer le pokémon dans l'ordre
    - Entrée : valider (applique ordre)
    - Échap : annuler
    """

    def __init__(self, screen, team_ids, name_fn=None):
        self.screen = screen
        self.team = list(team_ids)
        self.sel = 0
        self.clock = pygame.time.Clock()
        self.name_fn = name_fn or (lambda x: x)

        self.font = pygame.font.Font(None, 34)
        self.small = pygame.font.Font(None, 24)
        self.tiny = pygame.font.Font(None, 20)
        self.icon_cache = {}
        self.move_mode = False
        self.move_from = None

    def run(self):
        original = list(self.team)

        running = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return original, False

                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        if self.move_mode:
                            self.move_mode = False
                            self.move_from = None
                        else:
                            return original, False

                    if event.key in (pygame.K_UP, pygame.K_z, pygame.K_w):
                        if self.team:
                            self.sel = max(0, self.sel - 1)

                    elif event.key in (pygame.K_DOWN, pygame.K_s):
                        if self.team:
                            self.sel = min(len(self.team) - 1, self.sel + 1)

                    elif event.key == pygame.K_RETURN:
                        if not self.team:
                            return original, False
                        if not self.move_mode:
                            self.move_mode = True
                            self.move_from = self.sel
                        else:
                            if self.move_from is not None:
                                self.team[self.move_from], self.team[self.sel] = self.team[self.sel], self.team[self.move_from]
                                self.sel = self.move_from
                            self.move_mode = False
                            self.move_from = None
                            return self.team, True

            self.draw()
            pygame.display.flip()
            self.clock.tick(60)

        return original, False

    def draw(self):
        self.screen.fill((18, 18, 24))

        title = self.font.render("ÉQUIPE", True, (255, 255, 255))
        self.screen.blit(title, (48, 32))

        help_text = "Z/S : sélectionner   Entrée : déplacer   Échap : annuler"
        if self.move_mode:
            help_text = "Choisis une nouvelle position puis Entrée"
        help_txt = self.small.render(help_text, True, (200, 200, 200))
        self.screen.blit(help_txt, (48, 72))

        y = 125
        slot_h = 62
        for i in range(6):
            entry = self.team[i] if i < len(self.team) else None
            is_selected = (i == self.sel)
            box_rect = pygame.Rect(48, y, 680, slot_h)
            pygame.draw.rect(self.screen, (32, 36, 44), box_rect, border_radius=8)
            if is_selected:
                pygame.draw.rect(self.screen, (120, 160, 220), box_rect, 3, border_radius=8)
            elif self.move_mode and self.move_from == i:
                pygame.draw.rect(self.screen, (240, 200, 80), box_rect, 3, border_radius=8)

            if entry:
                name, level, hp, maxhp, icon = self._entry_display(entry)
                icon_surf = self._load_icon(icon)
                self.screen.blit(icon_surf, (58, y + 8))

                name_color = (255, 230, 80) if is_selected else (235, 235, 235)
                line = self.font.render(name, True, name_color)
                self.screen.blit(line, (120, y + 6))

                level_txt = self.small.render(f"Nv. {level}", True, (200, 200, 200))
                self.screen.blit(level_txt, (120, y + 32))

                hp_text = self.small.render(f"PV {hp}/{maxhp}", True, (200, 200, 200))
                self.screen.blit(hp_text, (320, y + 32))

                self._draw_hp_bar(420, y + 38, 200, 10, hp, maxhp)
            else:
                empty_txt = self.small.render("Emplacement vide", True, (120, 120, 120))
                self.screen.blit(empty_txt, (120, y + 18))

            y += slot_h + 8

    def _entry_display(self, entry):
        if isinstance(entry, dict):
            pid = entry.get("id") or entry.get("name") or entry.get("dbSymbol") or "Pokémon"
            name = self.name_fn(pid)
            level = entry.get("level", 5)
            hp = entry.get("hp", 20)
            maxhp = entry.get("maxhp", max(1, hp))
            icon = entry.get("icon") or entry.get("icon_path")
            return name, level, hp, maxhp, icon
        pid = entry
        name = self.name_fn(pid)
        return name, 5, 20, 20, None

    def _load_icon(self, icon_path):
        key = icon_path or "placeholder"
        if key in self.icon_cache:
            return self.icon_cache[key]
        size = 40
        if icon_path:
            try:
                icon = pygame.image.load(icon_path).convert_alpha()
                icon = pygame.transform.smoothscale(icon, (size, size))
                self.icon_cache[key] = icon
                return icon
            except Exception:
                pass
        icon = pygame.Surface((size, size), pygame.SRCALPHA)
        pygame.draw.circle(icon, (90, 90, 110), (size // 2, size // 2), size // 2)
        pygame.draw.circle(icon, (170, 170, 200), (size // 2, size // 2), size // 2 - 4, 2)
        self.icon_cache[key] = icon
        return icon

    def _draw_hp_bar(self, x, y, w, h, hp, maxhp):
        maxhp = max(1, maxhp)
        ratio = max(0.0, min(1.0, hp / maxhp))
        pygame.draw.rect(self.screen, (40, 40, 40), (x, y, w, h), border_radius=4)
        fill_w = int(w * ratio)
        color = (80, 220, 120) if ratio > 0.5 else (240, 200, 80) if ratio > 0.2 else (240, 80, 80)
        pygame.draw.rect(self.screen, color, (x, y, fill_w, h), border_radius=4)
