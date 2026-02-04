import pygame
from collections import deque


class Player(pygame.sprite.Sprite):
    def __init__(self, x, y, genre="red_m"):
        super().__init__()
        self.frame_width = 25
        self.frame_height = 32
        self.direction = 0  # 0=down,1=left,2=right,3=up
        self.frame = 0

        self.walk_speed = 2
        self.run_speed = 3

        self.spritesheet = pygame.image.load(
            f"assets/sprite/hero_01_{genre}_walk.png"
        ).convert_alpha()

        self.images = self.load_frames()
        self.image = self.images[self.direction][self.frame]
        self.rect = self.image.get_rect(topleft=(x, y))

        self.animation_timer = 0
        self.map = None
        self.current_layer = 2

        # ✅ Historique positions pour le follower
        self.history = deque(maxlen=240)  # plus long = plus fluide
        self.history.appendleft((self.rect.x, self.rect.y))

    def load_frames(self):
        images = []
        for direction in range(4):
            frames = []
            for frame in range(4):
                sx = frame * self.frame_width
                sy = direction * self.frame_height
                if (
                    sx + self.frame_width <= self.spritesheet.get_width()
                    and sy + self.frame_height <= self.spritesheet.get_height()
                ):
                    frame_img = self.spritesheet.subsurface(
                        (sx, sy, self.frame_width, self.frame_height)
                    )
                    frames.append(frame_img)
            images.append(frames)
        return images

    def try_move(self, dx, dy):
        if self.map:
            future_rect = self.rect.move(dx, dy)
            if self.map.is_collision(future_rect.centerx, future_rect.centery):
                return False
            if hasattr(self.map, "npcs") and pygame.sprite.spritecollideany(self, self.map.npcs):
                return False
            self.rect = future_rect
            return True
        else:
            self.rect = self.rect.move(dx, dy)
            return True

    def update(self):
        keys = pygame.key.get_pressed()
        dx, dy = 0, 0
        moved = False

        speed = self.walk_speed
        if keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT]:
            speed = self.run_speed

        if keys[pygame.K_UP] or keys[pygame.K_z]:
            self.direction = 3
            dy = -speed
        elif keys[pygame.K_DOWN] or keys[pygame.K_s]:
            self.direction = 0
            dy = speed
        elif keys[pygame.K_LEFT] or keys[pygame.K_q]:
            self.direction = 1
            dx = -speed
        elif keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            self.direction = 2
            dx = speed

        if dx != 0 or dy != 0:
            moved = self.try_move(dx, dy)

        else:
            self.frame = 0
            self.animation_timer = 0

        self.image = self.images[self.direction][self.frame]
c