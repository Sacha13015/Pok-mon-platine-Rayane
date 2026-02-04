import pygame
import sys

# =============== CONFIGURATION ===================
SCREEN_WIDTH, SCREEN_HEIGHT = 1280, 720
FONT_PATH = "assets/fonts/pokemon-ds.ttf"
SPRITE_FOLDER = "assets/sprite"
CHARACTERS = [
    {"name": "Mario", "image": f"{SPRITE_FOLDER}/Mario.png", "default_name": "Mario"},
    {"name": "Red", "image": f"{SPRITE_FOLDER}/Playerred.png", "default_name": "Red"},
    {"name": "Luigi", "image": f"{SPRITE_FOLDER}/Luigi.png", "default_name": "Luigi"},
]

# =============== INITIALISATION ===================
pygame.init()
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Choix du personnage")
font = pygame.font.Font(FONT_PATH, 48)
clock = pygame.time.Clock()

# =============== CHARGEMENT DES IMAGES ===============
for character in CHARACTERS:
    character["surface"] = pygame.image.load(character["image"]).convert_alpha()
    character["surface"] = pygame.transform.scale(character["surface"], (256, 256))


# =============== FONCTIONS ==========================
def draw_character_selection(index):
    screen.fill((0, 0, 0))
    name_text = font.render(CHARACTERS[index]["name"], True, (255, 255, 255))
    name_rect = name_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 100))

    image = CHARACTERS[index]["surface"]
    image_rect = image.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 50))

    screen.blit(image, image_rect)
    screen.blit(name_text, name_rect)
    pygame.display.flip()


def ask_player_name(default_name):
    input_box = pygame.Rect(SCREEN_WIDTH // 2 - 150, SCREEN_HEIGHT // 2 + 100, 300, 50)
    color_active = pygame.Color('white')
    color_inactive = pygame.Color('gray')
    color = color_inactive
    active = True
    text = ''
    font_small = pygame.font.Font(FONT_PATH, 32)

    while True:
        screen.fill((0, 0, 0))
        title = font_small.render("Entre ton prénom :", True, (255, 255, 255))
        screen.blit(title, (SCREEN_WIDTH // 2 - title.get_width() // 2, SCREEN_HEIGHT // 2 + 50))

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN:
                    return text if text.strip() != "" else default_name
                elif event.key == pygame.K_BACKSPACE:
                    text = text[:-1]
                elif len(text) < 12:
                    text += event.unicode

        txt_surface = font_small.render(text, True, color)
        width = max(300, txt_surface.get_width() + 10)
        input_box.w = width
        pygame.draw.rect(screen, color, input_box, 2)
        screen.blit(txt_surface, (input_box.x + 5, input_box.y + 5))

        pygame.display.flip()
        clock.tick(30)


# =============== BOUCLE PRINCIPALE ===================
def start_character_selection():
    selected_index = 0
    draw_character_selection(selected_index)

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.KEYDOWN:
                if event.key in [pygame.K_RIGHT, pygame.K_d]:
                    selected_index = (selected_index + 1) % len(CHARACTERS)
                elif event.key in [pygame.K_LEFT, pygame.K_q]:
                    selected_index = (selected_index - 1) % len(CHARACTERS)
                elif event.key in [pygame.K_RETURN, pygame.K_SPACE]:
                    chosen = CHARACTERS[selected_index]
                    name = ask_player_name(chosen["default_name"])
                    return chosen["name"], name

        draw_character_selection(selected_index)
        clock.tick(15)


# Pour test en standalone
if __name__ == "__main__":
    chosen, name = start_character_selection()
    print("Personnage choisi :", chosen)
    print("Nom du joueur :", name)
