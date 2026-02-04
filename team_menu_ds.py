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

    def run(self):
        original = list(self.team)

        running = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return original, False

                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        return original, False

                    if event.key in (pygame.K_UP, pygame.K_z, pygame.K_w):
                        self.sel = max(0, self.sel - 1)

                    elif event.key in (pygame.K_DOWN, pygame.K_s):
                        self.sel = min(len(self.team) - 1, self.sel + 1)

                    # move up
                    elif event.key in (pygame.K_q, pygame.K_LEFT):
                        if self.sel > 0:
                            self.team[self.sel - 1], self.team[self.sel] = self.team[self.sel], self.team[self.sel - 1]
                            self.sel -= 1

                    # move down
                    elif event.key in (pygame.K_d, pygame.K_RIGHT):
                        if self.sel < len(self.team) - 1:
                            self.team[self.sel + 1], self.team[self.sel] = self.team[self.sel], self.team[self.sel + 1]
                            self.sel += 1

                    elif event.key == pygame.K_RETURN:
                        return self.team, True

            self.draw()
            pygame.display.flip()
            self.clock.tick(60)

        return original, False

    def draw(self):
        self.screen.fill((18, 18, 24))

        title = self.font.render("ÉQUIPE", True, (255, 255, 255))
        self.screen.blit(title, (48, 32))

        help_txt = self.small.render("Z/S : sélectionner   Q/D : déplacer   Entrée : valider   Échap : annuler", True, (200, 200, 200))
        self.screen.blit(help_txt, (48, 72))

        y = 125
        for i, pid in enumerate(self.team):
            name = self.name_fn(pid)
            color = (255, 230, 80) if i == self.sel else (235, 235, 235)
            line = self.font.render(f"{i+1}. {name}", True, color)
            self.screen.blit(line, (68, y))
            y += 44
