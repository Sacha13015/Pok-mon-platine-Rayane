import os
import pygame

class Screen:
    """
    Screen class to manage the screen
    """
    def __init__(self) -> None:
        self.display: pygame.Surface = pygame.display.set_mode((1280, 720))
        pygame.display.set_caption("Pokémon")
        pygame.display.set_icon(
            pygame.image.load(
                os.path.join(
                    os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
                    "assets", "app", "logo_projet_pokemon.png"
                )
            )
        )
        self.clock: pygame.time.Clock = pygame.time.Clock()
        self.framerate: int = 144
        self.deltatime: float = 0.0
        self.imagescreen: pygame.Surface = self.display.copy()

    def update(self) -> None:
        pygame.display.flip()
        self.clock.tick(self.framerate)
        self.imagescreen = self.display.copy()
        self.display.fill((0, 0, 0))
        self.deltatime = self.clock.get_time()

    def get_delta_time(self) -> float:
        return self.deltatime

    def get_size(self) -> tuple[int, int]:
        return self.display.get_size()

    def get_display(self) -> pygame.Surface:
        return self.display

    def image_screen(self):
        return self.imagescreen
