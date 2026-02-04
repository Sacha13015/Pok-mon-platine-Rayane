import pygame
import pytmx
import os

pygame.init()

ASSETS_DIR = os.path.join(os.path.dirname(__file__), "assets")
SON_INTRO = os.path.join(ASSETS_DIR, "sounds", "combatclep.mp3")
LABO_IMG = os.path.join(ASSETS_DIR, "sprite", "Prof otomaï.png")
TMX_CHAMBRE = os.path.join(ASSETS_DIR, "map", "chambre_joueur.tmx")
DIALOGUE_BOX_PATH = os.path.join(ASSETS_DIR, "interfaces", "maps", "frame_map.png")
FONT_PATH = os.path.join(ASSETS_DIR, "fonts", "nds12.ttf")
BIP_PATH = os.path.join(ASSETS_DIR, "sounds", "bip_dialogue.mp3")

DIALOGUE_PROF = [
    "Chaque année, à Marseille, se tient un événement unique au monde...",
    "...La Grande Chasse aux Références et aux Pokémon !",
    "Je suis le Professeur Otomaï, et, avec mon fidèle assistant Goinfrex, nous sommes ravis de t'accueillir pour cette édition exceptionnelle !",
    "Le but ? Devenir le Maître des Pokémon… ET le Maître de la culture Internet !",
    "Au fil de ton aventure, tu devras capturer des Pokémon, mais aussi traquer les références cachées dans chaque recoin du monde : memes, héros de mangas, clins d’œil aux jeux vidéo et bien d’autres surprises !",
    "Mais attention, la concurrence sera rude… Seule une personne avec un QI de 37 pourra atteindre le sommet et remporter le titre suprême !",
    "Alors, es-tu prêt à marquer l’histoire ?",
]
DIALOGUE_MAMAN = [
    "Réveille-toi ! C’est aujourd’hui le grand jour, l’événement que tu attends depuis si longtemps !",
    "N’oublie pas ton sac, et viens vite déjeuner avant de partir… Professeur Otomaï doit t’attendre avec impatience !"
]

class DialogueBox:
    def __init__(self, image_path, font_path, screen, box_rect, padding_x=40, padding_y=38):
        self.image = pygame.image.load(image_path).convert_alpha()
        self.font = pygame.font.Font(font_path, 36)
        self.screen = screen
        self.box_rect = box_rect
        self.padding_x = padding_x
        self.padding_y = padding_y

    def blit_box(self):
        box_img = pygame.transform.smoothscale(self.image, (self.box_rect[2], self.box_rect[3]))
        self.screen.blit(box_img, (self.box_rect[0], self.box_rect[1]))

    def wrap_text(self, text, max_width, max_lines):
        words = text.split(" ")
        lines = []
        cur = ""
        for word in words:
            test = cur + word + " "
            if self.font.size(test)[0] > max_width:
                lines.append(cur)
                cur = word + " "
                if len(lines) >= max_lines:
                    break
            else:
                cur = test
        if len(lines) < max_lines:
            lines.append(cur)
        if len(lines) == max_lines and len(words) > 0:
            lines[-1] = lines[-1].rstrip() + "…"
        return lines

    def show(self, text, nom=None, speed=48, bip_sound=None, allow_skip=False):
        x, y, w, h = self.box_rect
        max_width = w - 2 * self.padding_x
        max_lines = int((h - self.padding_y*1.1) // (self.font.get_height() + 8))
        lines = self.wrap_text(text, max_width, max_lines)
        idx = 0
        running = True
        clock = pygame.time.Clock()
        last = pygame.time.get_ticks()
        finished = False

        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit(); exit()
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_s and allow_skip:
                        return "skip"
                    if not finished:
                        idx = sum(len(line) for line in lines)
                        finished = True
                    else:
                        if bip_sound: bip_sound.play()
                        return

            now = pygame.time.get_ticks()
            if idx < sum(len(line) for line in lines) and not finished and now - last > 1000 // speed:
                idx += 1
                last = now

            self.blit_box()
            if nom:
                nom_font = pygame.font.Font(FONT_PATH, 24)
                nom_surface = nom_font.render(nom, True, (30,30,30))
                self.screen.blit(nom_surface, (x + self.padding_x, y + 7))
            line_idx = 0
            letters = idx
            for line in lines:
                to_draw = line[:letters]
                txt = self.font.render(to_draw, True, (30,30,30))
                self.screen.blit(txt, (x + self.padding_x, y + self.padding_y + line_idx * (self.font.get_height()+8)))
                letters -= len(line)
                if letters <= 0:
                    break
                line_idx += 1

            # Ajout du texte "Appuie sur S pour passer" si skip possible
            if allow_skip:
                font_small = pygame.font.Font(FONT_PATH, 24)
                txt_skip = font_small.render("Appuie sur S pour passer", True, (150, 30, 30))
                self.screen.blit(txt_skip, (x + w - txt_skip.get_width() - 28, y + h - txt_skip.get_height() - 18))

            pygame.display.flip()
            clock.tick(60)

def render_chambre_tmx(screen_size):
    tmx_data = pytmx.load_pygame(TMX_CHAMBRE)
    width = tmx_data.width * tmx_data.tilewidth
    height = tmx_data.height * tmx_data.tileheight
    surface = pygame.Surface((width, height))
    for layer in tmx_data.visible_layers:
        if isinstance(layer, pytmx.TiledTileLayer):
            for x, y, gid in layer:
                tile = tmx_data.get_tile_image_by_gid(gid)
                if tile:
                    surface.blit(tile, (x * tmx_data.tilewidth, y * tmx_data.tileheight))
    surface = pygame.transform.smoothscale(surface, screen_size)
    return surface

def fade_in(screen, surface, duration=1.2):
    fade = pygame.Surface(screen.get_size(), pygame.SRCALPHA)
    for alpha in range(255, -1, -15):
        screen.blit(surface, (0, 0))
        fade.set_alpha(alpha)
        fade.fill((0, 0, 0))
        screen.blit(fade, (0, 0))
        pygame.display.flip()
        pygame.time.delay(int(duration * 1000 / 18))

def fade_out(screen, surface, duration=1.2):
    fade = pygame.Surface(screen.get_size(), pygame.SRCALPHA)
    for alpha in range(0, 256, 15):
        screen.blit(surface, (0, 0))
        fade.set_alpha(alpha)
        fade.fill((0, 0, 0))
        screen.blit(fade, (0, 0))
        pygame.display.flip()
        pygame.time.delay(int(duration * 1000 / 18))

def cinematique_otomai(screen):
    screen_size = screen.get_size()
    labo_img_orig = pygame.image.load(LABO_IMG).convert_alpha()
    bg_width = int(screen_size[0] * 1.75)
    bg_height = screen_size[1]
    labo_img = pygame.transform.smoothscale(labo_img_orig, (bg_width, bg_height))
    chambre_img = render_chambre_tmx(screen_size)

    box_rect = (
        int(screen_size[0]*0.05),
        int(screen_size[1]*0.68),
        int(screen_size[0]*0.90),
        int(screen_size[1]*0.28)
    )
    dialogue_box = DialogueBox(
        image_path=DIALOGUE_BOX_PATH,
        font_path=FONT_PATH,
        screen=screen,
        box_rect=box_rect,
        padding_x=46,
        padding_y=46
    )

    bip_sound = pygame.mixer.Sound(BIP_PATH)

    # FONDU D'INTRO
    screen.fill((0, 0, 0))
    pygame.display.flip()
    pygame.time.wait(700)
    fade_in(screen, labo_img, duration=1.3)

    pygame.mixer.music.load(SON_INTRO)
    pygame.mixer.music.set_volume(0.65)
    pygame.mixer.music.play(-1)

    total_frames = len(DIALOGUE_PROF) * 140
    max_scroll = bg_width - screen_size[0]
    dialogue_index = 0
    frame_count = 0
    running = True

    skip_entire_dialogue = False
    while running and dialogue_index < len(DIALOGUE_PROF):
        scroll_x = int(max_scroll * frame_count / total_frames)
        screen.blit(labo_img, (-scroll_x, 0))
        phrase = DIALOGUE_PROF[dialogue_index]
        res = dialogue_box.show(phrase, nom="Prof. Otomaï", speed=42, bip_sound=bip_sound, allow_skip=True)
        if res == "skip":
            skip_entire_dialogue = True
            break
        dialogue_index += 1
        frame_count += 140

    fade_out(screen, labo_img, duration=1.0)
    pygame.mixer.music.stop()
    fade_in(screen, chambre_img, duration=1.2)

    if not skip_entire_dialogue:
        for phrase in DIALOGUE_MAMAN:
            screen.blit(chambre_img, (0, 0))
            dialogue_box.show(phrase, nom="Maman", speed=42, bip_sound=bip_sound, allow_skip=True)
    else:
        screen.blit(chambre_img, (0, 0))
        pygame.display.flip()
        pygame.time.wait(700)
    return
