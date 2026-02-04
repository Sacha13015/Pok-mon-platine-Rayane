import pygame
import sys
import os
import cv2
import random

# ----------- Classe pour les étoiles filantes -----------

class Star:
    def __init__(self, w, h):
        self.x = random.randint(0, w)
        self.y = random.randint(0, h // 2)
        self.vx = random.uniform(2, 4)
        self.vy = random.uniform(0.7, 2)
        self.size = random.randint(1, 2)
    def move(self):
        self.x += self.vx
        self.y += self.vy
    def draw(self, screen):
        pygame.draw.circle(screen, (255, 255, 255), (int(self.x), int(self.y)), self.size)

def create_shine_surface(width, height, pos):
    surf = pygame.Surface((width, height), pygame.SRCALPHA)
    for x in range(width):
        alpha = max(0, 110 - abs(x - pos) * 8)
        if alpha > 0:
            pygame.draw.line(surf, (255, 255, 255, alpha), (x, 0), (x, height))
    return surf

def play_intro_video(screen, video_path, audio_path=None):
    if audio_path:
        pygame.mixer.music.load(audio_path)
        pygame.mixer.music.play()
    cap = cv2.VideoCapture(video_path)
    clock = pygame.time.Clock()
    fps = cap.get(cv2.CAP_PROP_FPS) or 30
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        frame = cv2.resize(frame, screen.get_size())
        surf = pygame.surfarray.make_surface(frame.swapaxes(0, 1))
        screen.blit(surf, (0, 0))
        pygame.display.flip()
        clock.tick(fps)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                cap.release()
                pygame.quit()
                sys.exit()
            elif event.type == pygame.KEYDOWN or event.type == pygame.MOUSEBUTTONDOWN:
                cap.release()
                if audio_path:
                    pygame.mixer.music.stop()
                return
    cap.release()
    if audio_path:
        pygame.mixer.music.stop()

def start_menu(screen):
    base_path = os.path.dirname(__file__)
    assets_dir = os.path.join(base_path, "assets")
    sounds_dir = os.path.join(assets_dir, "sounds")
    images_dir = os.path.join(assets_dir, "images")
    videos_dir = os.path.join(assets_dir, "videos")
    video_path = os.path.join(videos_dir, "intro.mp4")
    image_menu_path = os.path.join(images_dir, "image_menu.png")
    sound_validate = os.path.join(sounds_dir, "game-start.mp3")
    sound_move = os.path.join(sounds_dir, "pause-piano.mp3")
    intro_music_path = os.path.join(sounds_dir, "intro.mp3")

    play_intro_video(screen, video_path, intro_music_path)

    menu_items = ["Nouvelle Partie", "Charger une Partie"]
    selected = 0
    pygame.font.init()
    font = pygame.font.SysFont("arial", 54, bold=True)
    try:
        logo = pygame.image.load(image_menu_path).convert_alpha()
        logo = pygame.transform.smoothscale(logo, (700, 210))
    except Exception:
        logo = None

    move_sound = pygame.mixer.Sound(sound_move)
    validate_sound = pygame.mixer.Sound(sound_validate)
    cursor_frames = []
    for i in range(2):
        surf = pygame.Surface((30, 30), pygame.SRCALPHA)
        pygame.draw.polygon(surf, (255, 215, 0, 255), [(0, 15), (30, 0), (30, 30)])
        surf = pygame.transform.rotate(surf, i * 8)
        cursor_frames.append(surf)
    cursor_frame = 0

    stars = [Star(screen.get_width(), screen.get_height()) for _ in range(7)]

    press_font = pygame.font.SysFont("arial", 38, bold=True)
    press_text = press_font.render("Appuyez sur une touche", True, (230, 230, 255))
    press_rect = press_text.get_rect(center=(screen.get_width() // 2, 550))

    running = True
    clock = pygame.time.Clock()
    while running:
        screen.fill((10, 25, 50))
        for star in stars:
            star.move()
            star.draw(screen)
        for star in list(stars):
            if star.x > screen.get_width() or star.y > screen.get_height():
                stars.remove(star)
                stars.append(Star(screen.get_width(), screen.get_height()))

        if logo:
            logo_x = screen.get_width() // 2 - logo.get_width() // 2
            logo_y = 60
            screen.blit(logo, (logo_x, logo_y))
            shine_pos = int((pygame.time.get_ticks() // 8) % (logo.get_width() + 40)) - 20
            shine_surf = create_shine_surface(logo.get_width(), logo.get_height(), shine_pos)
            screen.blit(shine_surf, (logo_x, logo_y), special_flags=pygame.BLEND_RGBA_ADD)

        for idx, item in enumerate(menu_items):
            color = (255, 255, 100) if idx == selected else (230, 230, 255)
            txt = font.render(item, True, color)
            x = screen.get_width() // 2 - txt.get_width() // 2
            y = 320 + idx * 60
            screen.blit(txt, (x, y))
            if idx == selected:
                screen.blit(cursor_frames[cursor_frame // 10], (x - 40, y + 10))
        cursor_frame = (cursor_frame + 1) % 20

        screen.blit(press_text, press_rect)
        pygame.display.flip()
        clock.tick(60)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            elif event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_DOWN, pygame.K_s):
                    if selected < len(menu_items) - 1:
                        selected += 1
                        move_sound.play()
                elif event.key in (pygame.K_UP, pygame.K_z):
                    if selected > 0:
                        selected -= 1
                        move_sound.play()
                elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                    validate_sound.play()
                    pygame.time.wait(250)
                    return selected

    return 0

if __name__ == "__main__":
    pygame.init()
    pygame.mixer.init()
    screen = pygame.display.set_mode((1280, 720), pygame.RESIZABLE)
    pygame.display.set_caption("Pokémon à la conquête des refs")
    start_menu(screen)
