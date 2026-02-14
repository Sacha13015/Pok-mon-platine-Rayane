import pygame

class PNJ(pygame.sprite.Sprite):
    def __init__(self, x, y, image_path, patrol_to=None, speed=1):
        super().__init__()
        self.image = pygame.image.load(image_path).convert_alpha()
        self.rect = self.image.get_rect(center=(x, y))
        self.speed = max(1, int(speed))
        self.patrol_origin = pygame.math.Vector2(self.rect.center)
        self.patrol_to = pygame.math.Vector2(patrol_to) if patrol_to else None
        self.patrol_forward = True

    def update(self):
        if not self.patrol_to:
            return
        target = self.patrol_to if self.patrol_forward else self.patrol_origin
        current = pygame.math.Vector2(self.rect.center)
        delta = target - current
        if delta.length() <= self.speed:
            self.rect.center = (int(target.x), int(target.y))
            self.patrol_forward = not self.patrol_forward
            return
        move = delta.normalize() * self.speed
        self.rect.center = (int(current.x + move.x), int(current.y + move.y))
