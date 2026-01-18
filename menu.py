import pygame
import sys
import os
import random
import cv2

# ======== CHEMINS D'ASSETS ========
ASSETS_PATH = r"C:\Users\Rayan\OneDrive\Bureau\Projet jeu rayane\Version test\EP9-Save\code\assets"
DRESSEUR_PATH = os.path.join(ASSETS_PATH, "images", "dresseurs")  # change si nécessaire

VIDEO_INTRO = os.path.join(ASSETS_PATH, "videos", "intro.mp4")
MUSIQUE_MENU = os.path.join(ASSETS_PATH, "sounds", "Enter_the_galaxy.mp3")
SON_DEPLACEMENT_MENU = os.path.join(ASSETS_PATH, "sounds", "pause-piano.mp3")
MENU_IMAGE = os.path.join(ASSETS_PATH, "images", "image_menu.png")
TRANSITIONS_PATH = os.path.join(ASSETS_PATH, "images", "transitions")

DRESSEUR_GARCON = os.path.join(DRESSEUR_PATH, "dresseur_garcon.png")
DRESSEUR_FILLE = os.path.join(DRESSEUR_PATH, "dresseur_fille.png")

# ======== FONCTIONS UTILES ========
def get_display_size():
    info = pygame.display.Info()
    return info.current_w, info.current_h

def scale_image(img, window_size):
    return pygame.transform.smoothscale(img, window_size)

# ======== INTRO VIDEO ========
def play_intro_video(screen, window_size):
    cap = cv2.VideoCapture(VIDEO_INTRO)
    fps = cap.get(cv2.CAP_PROP_FPS)
    clock = pygame.time.Clock()
    running = True
    skip = False
    while cap.isOpened() and running:
        ret, frame = cap.read()
        if not ret:
            break
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                skip = True
            if event.type == pygame.KEYDOWN or event.type == pygame.MOUSEBUTTONDOWN:
                skip = True
                break
        if skip:
            break
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        frame = cv2.resize(frame, window_size)
        surf = pygame.surfarray.make_surface(frame.swapaxes(0, 1))
        screen.blit(surf, (0, 0))
        pygame.display.update()
        clock.tick(fps)
    cap.release()

# ======== MENU PRINCIPAL ========
def afficher_menu(screen, window_size):
    font = pygame.font.SysFont("Arial", 48)
    options = ["Nouvelle Partie", "Charger la Partie"]
    selected = 0
    menu_running = True
    fond = pygame.image.load(MENU_IMAGE).convert()
    fond = pygame.transform.smoothscale(fond, window_size)
    # Musique de fond
    pygame.mixer.music.load(MUSIQUE_MENU)
    pygame.mixer.music.play(-1)
    son_deplacement = pygame.mixer.Sound(SON_DEPLACEMENT_MENU)
    while menu_running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_UP:
                    selected = (selected - 1) % len(options)
                    son_deplacement.play()
                elif event.key == pygame.K_DOWN:
                    selected = (selected + 1) % len(options)
                    son_deplacement.play()
                elif event.key in [pygame.K_RETURN, pygame.K_SPACE]:
                    menu_running = False
                elif event.key == pygame.K_F11:
                    toggle_fullscreen(screen)
                    fond = pygame.transform.smoothscale(pygame.image.load(MENU_IMAGE).convert(), screen.get_size())

        window_size = screen.get_size()
        fond = pygame.transform.smoothscale(pygame.image.load(MENU_IMAGE).convert(), window_size)
        screen.blit(fond, (0, 0))

        # Affiche les boutons du menu (plus bas sous le logo)
        for i, option in enumerate(options):
            color = (255, 255, 0) if i == selected else (255, 255, 255)
            txt = font.render(option, True, color)
            y = window_size[1]//2 + i * 80 + 180  # ajuste +180 si tu veux +haut/+bas
            screen.blit(txt, ((window_size[0] - txt.get_width()) // 2, y))

        pygame.display.update()
    pygame.mixer.music.stop()
    return selected


# ======== TRANSITION ========
def afficher_transition(screen, window_size):
    transitions = [os.path.join(TRANSITIONS_PATH, f) for f in os.listdir(TRANSITIONS_PATH) if f.endswith((".png", ".jpg"))]
    img = pygame.image.load(random.choice(transitions)).convert()
    img = scale_image(img, window_size)
    screen.blit(img, (0, 0))
    pygame.display.update()
    pygame.time.wait(1200)

# ======== CHOIX DRESSEUR ========
def choix_dresseur(screen, window_size):
    font = pygame.font.SysFont("Arial", 36)
    options = ["Garçon", "Fille"]
    selected = 0
    dresseur_garcon = pygame.image.load(DRESSEUR_GARCON).convert_alpha()
    dresseur_fille = pygame.image.load(DRESSEUR_FILLE).convert_alpha()
    fond = pygame.Surface(window_size)
    fond.fill((20, 20, 40))
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key in [pygame.K_LEFT, pygame.K_RIGHT]:
                    selected = 1 - selected
                elif event.key in [pygame.K_RETURN, pygame.K_SPACE]:
                    running = False
                elif event.key == pygame.K_F11:
                    toggle_fullscreen(screen)
                    fond = pygame.Surface(screen.get_size())
                    fond.fill((20, 20, 40))
                    window_size = screen.get_size()
        window_size = screen.get_size()
        fond = pygame.Surface(window_size)
        fond.fill((20, 20, 40))
        width = window_size[0]
        height = window_size[1]
        garcon_scaled = pygame.transform.smoothscale(dresseur_garcon, (width//4, int(height*0.65)))
        fille_scaled = pygame.transform.smoothscale(dresseur_fille, (width//4, int(height*0.65)))
        if selected == 0:
            garcon_scaled.set_alpha(255)
            fille_scaled.set_alpha(100)
        else:
            garcon_scaled.set_alpha(100)
            fille_scaled.set_alpha(255)
        screen.blit(fond, (0, 0))
        screen.blit(garcon_scaled, (width//8, height//7))
        screen.blit(fille_scaled, (width-width//8-width//4, height//7))
        txt_garcon = font.render("Garçon", True, (255,255,255) if selected==0 else (180,180,180))
        txt_fille = font.render("Fille", True, (255,255,255) if selected==1 else (180,180,180))
        screen.blit(txt_garcon, (width//8 + garcon_scaled.get_width()//2 - txt_garcon.get_width()//2, int(height*0.87)))
        screen.blit(txt_fille, (width-width//8-width//4 + fille_scaled.get_width()//2 - txt_fille.get_width()//2, int(height*0.87)))
        pygame.display.update()
    return options[selected]

# ======== PLEIN ECRAN/FENETRE ========
def toggle_fullscreen(screen):
    is_fullscreen = screen.get_flags() & pygame.FULLSCREEN
    if is_fullscreen:
        pygame.display.set_mode((1280, 720), pygame.RESIZABLE)
    else:
        info = pygame.display.Info()
        pygame.display.set_mode((info.current_w, info.current_h), pygame.FULLSCREEN)

def demander_nom_joueur(screen, window_size):
    font = pygame.font.SysFont("Arial", 42)
    info_font = pygame.font.SysFont("Arial", 32)
    input_box = pygame.Rect(window_size[0] // 2 - 200, window_size[1] // 2 - 40, 400, 60)
    color_inactive = pygame.Color('lightskyblue3')
    color_active = pygame.Color('dodgerblue2')
    color = color_inactive
    active = True
    text = ''
    done = False
    clock = pygame.time.Clock()

    while not done:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.KEYDOWN:
                if active:
                    if event.key == pygame.K_RETURN:
                        if len(text.strip()) > 0:
                            done = True
                    elif event.key == pygame.K_BACKSPACE:
                        text = text[:-1]
                    elif len(text) < 12 and event.unicode.isprintable():
                        text += event.unicode
                if event.key == pygame.K_F11:
                    toggle_fullscreen(screen)
                    window_size = screen.get_size()
                    input_box = pygame.Rect(window_size[0] // 2 - 200, window_size[1] // 2 - 40, 400, 60)
        screen.fill((15, 20, 30))
        # Titre
        titre = font.render("Entre ton prénom :", True, (255, 255, 255))
        screen.blit(titre, (window_size[0] // 2 - titre.get_width() // 2, window_size[1] // 2 - 140))
        # Info
        info = info_font.render("Appuie sur Entrée pour valider", True, (170, 170, 170))
        screen.blit(info, (window_size[0] // 2 - info.get_width() // 2, window_size[1] // 2 + 50))
        # Box input
        color = color_active if active else color_inactive
        pygame.draw.rect(screen, color, input_box, 3)
        txt_surface = font.render(text, True, (255, 255, 255))
        screen.blit(txt_surface, (input_box.x + 10, input_box.y + 10))
        pygame.display.flip()
        clock.tick(30)
    return text.strip()



# ======== MAIN ========
def main():
    pygame.init()
    pygame.mixer.init()
    screen = pygame.display.set_mode((1280, 720), pygame.RESIZABLE)
    pygame.display.set_caption("Pokémon à la conquête des refs")
    play_intro_video(screen, screen.get_size())
    choix = afficher_menu(screen, screen.get_size())
    afficher_transition(screen, screen.get_size())
    genre = choix_dresseur(screen, screen.get_size())
    prenom = demander_nom_joueur(screen, screen.get_size())   # <------ AJOUT ICI
    print("Personnage choisi :", genre)
    print("Prénom choisi :", prenom)
    # TODO: suite du jeu ici

if __name__ == "__main__":
    main()
