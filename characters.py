import pygame

class AnimatedCharacter(pygame.sprite.Sprite):
    def __init__(self, x, y, spritesheet_path, frame_width=32, frame_height=32):
        super().__init__()
        self.frame_width = frame_width
        self.frame_height = frame_height
        self.direction = 0  # 0=bas, 1=gauche, 2=droite, 3=haut
        self.frame = 0
        self.spritesheet = pygame.image.load(spritesheet_path).convert_alpha()
        self.images = self.load_frames()
        self.image = self.images[self.direction][self.frame]
        # Centrer le personnage par ses pieds (important pour Glitch qui est plus grand)
        self.rect = self.image.get_rect(midbottom=(x, y))
        self.animation_timer = 0

    def load_frames(self):
        images = []
        for direction in range(4):
            frames = []
            for frame in range(4):
                x = frame * self.frame_width
                y = direction * self.frame_height
                if x + self.frame_width <= self.spritesheet.get_width() and y + self.frame_height <= self.spritesheet.get_height():
                    frame_img = self.spritesheet.subsurface((x, y, self.frame_width, self.frame_height))
                    frames.append(frame_img)
            images.append(frames)
        return images

    def update(self, dx=0, dy=0, moving=False):
        if moving:
            self.animation_timer += 1
            if self.animation_timer % 8 == 0:
                self.frame = (self.frame + 1) % 4
        else:
            self.frame = 0
            self.animation_timer = 0
        self.image = self.images[self.direction][self.frame]
        if dx != 0 or dy != 0:
            self.rect.x += dx
            self.rect.y += dy

class Glitch(AnimatedCharacter):
    def __init__(self, x, y):
        super().__init__(
            x, y,
            "assets/sprite/glitch_face2.png",  # Le nouveau fichier bien propre
            frame_width=64, frame_height=96    # Taille exacte d'une frame de Glitch
        )

class Otomai(AnimatedCharacter):
    def __init__(self, x, y):
        super().__init__(
            x, y,
            "assets/sprite/otomaï.png",        # Adapter si Otomaï n'est pas 32x32
            frame_width=32, frame_height=32
        )
