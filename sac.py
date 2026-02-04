import pygame
import os

ASSETS_PATH = os.path.join(os.path.dirname(__file__), "assets")
SAC_PATH = os.path.join(ASSETS_PATH, "sac")
SAC_IMAGE = os.path.join(SAC_PATH, "sac_moderne.png")

def ouvrir_menu_sac(screen):
    running = True
    width, height = screen.get_size()
    bag_sprite = pygame.image.load(SAC_IMAGE).convert_alpha()
    bag_sprite = pygame.transform.smoothscale(bag_sprite, (200, 200))
    font = pygame.font.SysFont("Arial", 28, bold=True)
    categories = ["Objets", "CT/CS", "Clés", "Pokéballs"]
    selected = 0
    while running:
        screen.fill((18, 22, 34))
        screen.blit(bag_sprite, (width//2 - 100, height//2 - 150))
        for i, cat in enumerate(categories):
            color = (255, 255, 0) if i == selected else (180, 180, 180)
            txt = font.render(cat, True, color)
            screen.blit(txt, (width//2 - 220 + i*170, height//2 + 90))
        pygame.display.flip()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_LEFT and selected > 0:
                    selected -= 1
                elif event.key == pygame.K_RIGHT and selected < len(categories)-1:
                    selected += 1
                elif event.key == pygame.K_ESCAPE or event.key == pygame.K_s:
                    running = False
