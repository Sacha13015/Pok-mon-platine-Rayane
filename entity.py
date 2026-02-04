import os
import pygame

from screen import Screen
from tool import Tool

class Entity(pygame.sprite.Sprite):
    """
    Entity class to manage the entities
    """
    def __init__(self, screen: Screen, x: int, y: int, spritesheet: str) -> None:
        super().__init__()
        self.screen: Screen = screen

        spritesheet_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
            "assets", "sprite", f"{spritesheet}_walk.png"
        )
        self.spritesheet = pygame.image.load(spritesheet_path).convert_alpha()

        self.image: pygame.Surface = Tool.split_image(self.spritesheet, 0, 0, 24, 32)
        self.position: pygame.math.Vector2 = pygame.math.Vector2(x, y)
        self.rect: pygame.Rect = self.image.get_rect()
        self.all_images: dict[str, list[pygame.Surface]] = self.get_all_images(self.spritesheet)
        self.index_image: int = 0
        self.image_part: int = 0
        self.reset_animation: bool = False
        self.hitbox: pygame.Rect = pygame.Rect(0, 0, 16, 16)

        self.step: int = 0
        self.animation_walk: bool = False
        self.direction: str = "down"

        # On désactive les références à get_delta_time()
        self.animtion_step_time: float = 0.0
        self.action_animation: int = 16

        self.speed: int = 1

        self.stairs_walk: int = 0
        self.stairs_direction: str = "down"

    def update(self) -> None:
        self.animation_sprite()
        self.move()
        self.rect.center = self.position
        self.hitbox.midbottom = self.rect.midbottom
        self.image = self.all_images[self.direction][self.index_image]

    def move_left(self) -> None:
        self.animation_walk = True
        self.direction = "left"

    def move_right(self) -> None:
        self.animation_walk = True
        self.direction = "right"

    def move_up(self) -> None:
        self.animation_walk = True
        self.direction = "up"

    def move_down(self) -> None:
        self.animation_walk = True
        self.direction = "down"

    def animation_sprite(self) -> None:
        if int(self.step // 8) + self.image_part >= 4:
            self.image_part = 0
            self.reset_animation = True
        self.index_image = int(self.step // 8) + self.image_part

    def move(self) -> None:
        if self.animation_walk:
            # ANIMATION SIMPLIFIÉE, on ne prend plus en compte le temps
            if self.step < 16:
                self.step += self.speed
                if self.direction == "left":
                    self.position.x -= self.speed
                elif self.direction == "right":
                    self.position.x += self.speed
                elif self.direction == "up":
                    self.position.y -= self.speed
                elif self.direction == "down":
                    self.position.y += self.speed
                if self.stairs_walk > 0:
                    self.stairs_walk -= 1
                    self.move_stairs()
            else:
                self.step = 0
                self.animation_walk = False
                if self.reset_animation:
                    self.reset_animation = False
                else:
                    self.image_part = 2 if self.image_part == 0 else 0

    def align_hitbox(self) -> None:
        if self.is_aligned():
            return
        self.position.x += 16
        self.rect.center = self.position
        self.hitbox.midbottom = self.rect.midbottom
        while self.hitbox.x % 16 != 0:
            self.rect.x -= 1
            self.hitbox.midbottom = self.rect.midbottom
        while self.hitbox.y % 16 != 0:
            self.rect.y -= 1
            self.hitbox.midbottom = self.rect.midbottom
        self.position = pygame.math.Vector2(self.rect.center)

    def is_aligned(self) -> bool:
        return self.hitbox.x % 16 == 0 and self.hitbox.y % 16 == 0

    def get_all_images(self, spritesheet: pygame.Surface) -> dict[str, list[pygame.Surface]]:
        all_images = {"down": [], "left": [], "right": [], "up": []}
        width: int = spritesheet.get_width() // 4
        height: int = spritesheet.get_height() // 4

        for i in range(4):
            for j, key in enumerate(all_images.keys()):
                all_images[key].append(Tool.split_image(spritesheet, i * width, j * height, 24, 32))
        return all_images

    def set_position(self, x: int, y: int) -> None:
        self.position = pygame.math.Vector2(x, y)
        self.rect.center = self.position
        self.hitbox.midbottom = self.rect.midbottom

    def move_stairs(self):
        # Correction : déplacement sur les escaliers selon stairs_direction
        if self.stairs_direction == "up":
            self.position.y -= self.speed
        elif self.stairs_direction == "down":
            self.position.y += self.speed
        elif self.stairs_direction == "left":
            self.position.x -= self.speed
        elif self.stairs_direction == "right":
            self.position.x += self.speed
