import pygame

class BagMenu:
    def __init__(self, screen):
        self.screen = screen
        self.tabs = ["Objets", "Pokéballs", "Soins", "CT/CS", "Baies", "Objets clés"]
        self.selected = 0
        self.font = pygame.font.SysFont("Arial", 30)
        self.running = False

    def run(self):
        self.running = True
        clock = pygame.time.Clock()
        while self.running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    exit()
                if event.type == pygame.KEYDOWN:
                    if event.key in [pygame.K_ESCAPE, pygame.K_x]:
                        self.running = False
                    elif event.key == pygame.K_LEFT:
                        self.selected = (self.selected - 1) % len(self.tabs)
                    elif event.key == pygame.K_RIGHT:
                        self.selected = (self.selected + 1) % len(self.tabs)
            # Affichage simple (améliorable)
            self.screen.fill((15,30,60))
            w, h = self.screen.get_size()
            slot_w = max(1, w // len(self.tabs))
            for i, tab in enumerate(self.tabs):
                col = (255, 255, 0) if i == self.selected else (180, 180, 180)
                txt = self.font.render(tab, True, col)
                x = i * slot_w + (slot_w // 2 - txt.get_width() // 2)
                self.screen.blit(txt, (x, h // 4))
            pygame.display.flip()
            clock.tick(60)
