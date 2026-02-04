import sys
import os
import random
import time

# Toujours travailler depuis le dossier du fichier
os.chdir(os.path.dirname(__file__))

import pygame
import cv2

from menu_pause_ds import PauseMenuDS
from select_character_3d import start_character_selection
from intro_otomaï import cinematique_otomai
from dialog_box import show_dialog_box_overlay
from game import Game

from characters import Glitch, Otomai

from intro_tv_dbz import play_intro_tv_dbz


# ----------------------------
# PATHS / CONSTANTES
# ----------------------------
ASSETS_PATH = os.path.join(os.path.dirname(__file__), "assets")
IMAGES_PATH = os.path.join(ASSETS_PATH, "images")
SOUNDS_PATH = os.path.join(ASSETS_PATH, "sounds")
VIDEOS_PATH = os.path.join(ASSETS_PATH, "videos")
DRESSEUR_PATH = os.path.join(IMAGES_PATH, "dresseurs")
TRANSITIONS_PATH = os.path.join(IMAGES_PATH, "transitions")

MENU_IMAGE = os.path.join(IMAGES_PATH, "image_menu.png")  # (gardée si jamais fallback)
MENU_VIDEO = os.path.join(VIDEOS_PATH, "Animation_de_menu_de_jeu_en_boucle.mp4")  # ✅ ton menu vidéo
VIDEO_INTRO = os.path.join(VIDEOS_PATH, "intro.mp4")

AUDIO_INTRO = os.path.join(SOUNDS_PATH, "intro_audio.mp3")
MUSIQUE_MENU = os.path.join(SOUNDS_PATH, "Enter_the_galaxy.mp3")
SON_DEPLACEMENT_MENU = os.path.join(SOUNDS_PATH, "pause-piano.mp3")

# ✅ Son pour le choix starter (tu peux changer)
SON_SELECT_STARTER = os.path.join(SOUNDS_PATH, "select_sound-121244.mp3")

DRESSEUR_GARCON = os.path.join(DRESSEUR_PATH, "dresseur_garcon.png")
DRESSEUR_FILLE = os.path.join(DRESSEUR_PATH, "dresseur_fille.png")

WINDOW_WIDTH, WINDOW_HEIGHT = 1280, 720


# ----------------------------
# OUTILS VIDEO
# ----------------------------
def play_intro_video(screen, video_path, audio_path=None):
    """Joue une vidéo (intro) avec possibilité de skip ECHAP."""
    if audio_path:
        pygame.mixer.music.load(audio_path)
        pygame.mixer.music.play()

    cap = cv2.VideoCapture(video_path)
    fps = cap.get(cv2.CAP_PROP_FPS) or 30

    start_time = time.time()
    frame_idx = 0
    skip = False
    font = pygame.font.SysFont("Arial", 36)

    while cap.isOpened():
        target_time = frame_idx / fps
        now = time.time() - start_time
        if now < target_time:
            time.sleep(target_time - now)

        ret, frame = cap.read()
        if not ret:
            break

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                cap.release()
                if audio_path:
                    pygame.mixer.music.stop()
                return
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                skip = True
                break

        if skip:
            break

        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        frame = cv2.resize(frame, screen.get_size())
        surf = pygame.surfarray.make_surface(frame.swapaxes(0, 1))

        screen.blit(surf, (0, 0))
        txt = font.render("Appuie sur [ECHAP] pour passer", True, (255, 255, 0))
        screen.blit(
            txt,
            (screen.get_width() // 2 - txt.get_width() // 2, screen.get_height() - 80),
        )
        pygame.display.update()
        frame_idx += 1

    cap.release()
    if audio_path:
        pygame.mixer.music.stop()


# ----------------------------
# MENU PRINCIPAL (VIDEO LOOP)
# ----------------------------
def afficher_menu(screen):
    """
    Menu principal avec vidéo en boucle en fond.
    - UP/DOWN pour naviguer
    - ENTER/SPACE pour valider
    - ECHAP pour quitter
    Retour: index sélectionné (0/1) ou None si quitter
    """
    font = pygame.font.SysFont("Arial", 48)
    options = ["Nouvelle Partie", "Charger la Partie"]
    selected = 0
    menu_running = True

    # Musique + SFX
    pygame.mixer.music.load(MUSIQUE_MENU)
    pygame.mixer.music.play(-1)
    son_deplacement = pygame.mixer.Sound(SON_DEPLACEMENT_MENU)

    # Ouvrir la vidéo
    cap = cv2.VideoCapture(MENU_VIDEO)

    # Fallback si vidéo introuvable / illisible
    use_fallback_image = False
    fallback_surf = None
    if not cap.isOpened():
        use_fallback_image = True
        try:
            fallback_surf = pygame.image.load(MENU_IMAGE).convert()
            fallback_surf = pygame.transform.smoothscale(fallback_surf, screen.get_size())
            print("[MENU] Vidéo introuvable/illisible -> fallback image_menu.png")
        except Exception as e:
            print("[MENU] Vidéo ET image indisponibles:", e)

    # Timing vidéo
    fps = 30
    if not use_fallback_image:
        vid_fps = cap.get(cv2.CAP_PROP_FPS)
        if vid_fps and vid_fps > 1:
            fps = vid_fps
    frame_delay_ms = int(1000 / fps)

    last_frame_time = pygame.time.get_ticks()
    current_surf = fallback_surf

    while menu_running:
        # Events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                if not use_fallback_image:
                    cap.release()
                pygame.mixer.music.stop()
                return None

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_UP:
                    selected = (selected - 1) % len(options)
                    son_deplacement.play()

                elif event.key == pygame.K_DOWN:
                    selected = (selected + 1) % len(options)
                    son_deplacement.play()

                elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                    menu_running = False

                elif event.key == pygame.K_ESCAPE:
                    if not use_fallback_image:
                        cap.release()
                    pygame.mixer.music.stop()
                    return None

        # Avancer la vidéo
        now = pygame.time.get_ticks()
        if not use_fallback_image and (current_surf is None or now - last_frame_time >= frame_delay_ms):
            last_frame_time = now
            ret, frame = cap.read()
            if not ret:
                cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                ret, frame = cap.read()

            if ret:
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                frame = cv2.resize(frame, screen.get_size())
                current_surf = pygame.surfarray.make_surface(frame.swapaxes(0, 1))

        # Render fond
        if current_surf:
            screen.blit(current_surf, (0, 0))
        else:
            screen.fill((0, 0, 0))

        # Overlay lisibilité
        overlay = pygame.Surface(screen.get_size(), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 70))
        screen.blit(overlay, (0, 0))

        # Options
        for i, option in enumerate(options):
            color = (255, 255, 0) if i == selected else (255, 255, 255)
            txt = font.render(option, True, color)
            y = screen.get_height() // 2 + i * 80 + 100
            screen.blit(txt, ((screen.get_width() - txt.get_width()) // 2, y))

        pygame.display.update()
        pygame.time.delay(1)  # évite CPU 100%

    if not use_fallback_image:
        cap.release()
    pygame.mixer.music.stop()
    return selected


# ----------------------------
# TRANSITION
# ----------------------------
def afficher_transition(screen):
    transitions = [
        os.path.join(TRANSITIONS_PATH, f)
        for f in os.listdir(TRANSITIONS_PATH)
        if f.lower().endswith((".png", ".jpg", ".jpeg"))
    ]
    if not transitions:
        return
    img = pygame.image.load(random.choice(transitions)).convert()
    img = pygame.transform.smoothscale(img, screen.get_size())
    screen.blit(img, (0, 0))
    pygame.display.update()
    pygame.time.wait(1200)


# ----------------------------
# CHOIX DRESSEUR
# ----------------------------
def choix_dresseur(screen):
    font = pygame.font.SysFont("Arial", 40)
    selected = 0

    dresseur_garcon = pygame.image.load(DRESSEUR_GARCON).convert_alpha()
    dresseur_fille = pygame.image.load(DRESSEUR_FILLE).convert_alpha()

    son_deplacement = pygame.mixer.Sound(SON_DEPLACEMENT_MENU)
    running = True

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return None

            if event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_LEFT, pygame.K_RIGHT):
                    selected = 1 - selected
                    son_deplacement.play()
                elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                    running = False
                elif event.key == pygame.K_ESCAPE:
                    return None

        screen.fill((30, 30, 40))
        w, h = screen.get_size()

        img_size = int(h * 0.82)
        angle_garcon = -10
        angle_fille = 10

        garcon_scaled = pygame.transform.smoothscale(dresseur_garcon, (img_size, img_size))
        garcon_rotated = pygame.transform.rotate(garcon_scaled, angle_garcon)

        fille_scaled = pygame.transform.smoothscale(dresseur_fille, (img_size, img_size))
        fille_rotated = pygame.transform.rotate(fille_scaled, angle_fille)

        if selected == 0:
            garcon_rotated.set_alpha(255)
            fille_rotated.set_alpha(80)
        else:
            garcon_rotated.set_alpha(80)
            fille_rotated.set_alpha(255)

        x_margin = 70
        garcon_x = x_margin
        garcon_y = (h - garcon_rotated.get_height()) // 2

        fille_x = w - x_margin - fille_rotated.get_width()
        fille_y = (h - fille_rotated.get_height()) // 2

        screen.blit(garcon_rotated, (garcon_x, garcon_y))
        screen.blit(fille_rotated, (fille_x, fille_y))

        trait_color = (200, 200, 230)
        trait_x = w // 2
        pygame.draw.line(screen, trait_color, (trait_x, 60), (trait_x, h - 60), 7)

        txt_garcon = font.render("Garçon", True, (255, 255, 255) if selected == 0 else (160, 160, 160))
        txt_fille = font.render("Fille", True, (255, 255, 255) if selected == 1 else (160, 160, 160))

        screen.blit(
            txt_garcon,
            (garcon_x + garcon_rotated.get_width() // 2 - txt_garcon.get_width() // 2, h - 80),
        )
        screen.blit(
            txt_fille,
            (fille_x + fille_rotated.get_width() // 2 - txt_fille.get_width() // 2, h - 80),
        )

        pygame.display.update()

    return selected


# ----------------------------
# HANDLER STARTER (✅ intégré)
# ----------------------------
def make_starter_choice_handler(screen, clock):
    """
    Retourne une fonction que Game pourra appeler quand le joueur interagit avec la table.
    La fonction attend un focus_rect EN COORDONNÉES ÉCRAN (camera déjà appliquée).
    """
    def _handler(focus_rect_screen: pygame.Rect):
        base_frame = screen.copy()
        scene = StarterChoiceScene(
            screen=screen,
            clock=clock,
            base_frame=base_frame,
            focus_rect=focus_rect_screen,
            duration_ms=700,
            zoom_scale=1.7,
            select_sound_path=SON_SELECT_STARTER if os.path.exists(SON_SELECT_STARTER) else None,
        )
        result = scene.run()
        if result.chosen:
            return result.starter_id
        return None

    return _handler


# ----------------------------
# MAIN
# ----------------------------
def main():
    pygame.init()
    pygame.mixer.init()

    # Plein écran (comme ton code)
    screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
    pygame.display.set_caption("Pokémon à la conquête des refs")

    clock = pygame.time.Clock()  # ✅ AJOUT (utile pour la scene starter)

    # 1) Intro vidéo
    play_intro_video(screen, VIDEO_INTRO, AUDIO_INTRO)

    # 2) Menu principal (vidéo en boucle)
    menu_selected = afficher_menu(screen)
    if menu_selected is None:
        pygame.quit()
        sys.exit()

    # 3) Transition image
    afficher_transition(screen)

    # 4) Choix garçon/fille
    genre = choix_dresseur(screen)
    if genre is None:
        pygame.quit()
        sys.exit()

    # 5) Sélection personnage + prénom
    personnage, prenom = start_character_selection()
    if personnage is None or prenom is None:
        pygame.quit()
        sys.exit()

    print("Genre choisi :", "red_m" if genre == 0 else "white_f")
    print("Prénom choisi :", prenom)
    print("Personnage sélectionné :", personnage)

    # ✅ INTRO TV DBZ (AU BON MOMENT : APRÈS PRÉNOM)
    play_intro_tv_dbz(screen)

    # ❌ On ne lance plus Otomaï ici : le jeu doit reprendre direct en chambre.
    # (Otomaï se fera plus tard quand tu iras au labo via la map / event)
    # cinematique_otomai(screen)

    # 6) Début du jeu → chambre du joueur
    genre_str = "red_m" if genre == 0 else "white_f"
    game = Game(
        screen,
        genre_str,
        prenom,
        personnage,
        map_name="chambre_joueur",
        spawn_name="Player",
    )

    # ✅ BRANCHE le handler starter au Game (sans casser ton code)
    # Game pourra appeler: game.starter_choice_handler(focus_rect_screen)
    game.run()


if __name__ == "__main__":
    main()
