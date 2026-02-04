import os
import pygame

class Tool:
    @staticmethod
    def split_image(spritesheet: pygame.Surface, x: int, y: int, width: int, height: int) -> pygame.Surface:
        """
        Split the image from the spritesheet
        """
        return spritesheet.subsurface(pygame.Rect(x, y, width, height))

    @staticmethod
    def blur(backsol: pygame.Surface, param: int) -> pygame.Surface:
        """
        Blur the backsol of the screen
        """
        for i in range(param):
            backsol = pygame.transform.smoothscale(
                backsol, (backsol.get_width() // 2, backsol.get_height() // 2)
            )
            backsol = pygame.transform.smoothscale(
                backsol, (backsol.get_width() * 2, backsol.get_height() * 2)
            )
        return backsol

    @staticmethod
    def create_text(text: str, size: int, color: tuple[int, int, int], font: str = "Roboto-Light", bold: bool = False) -> pygame.Surface:
        """
        Create the text surface from the text
        """
        font_obj = pygame.font.Font(f"../../assets/fonts/{font}.ttf", size)
        if bold:
            font_obj.set_bold(True)
        return font_obj.render(text, True, color)

    @staticmethod
    def add_text_to_surface(surface: pygame.Surface, text: pygame.Surface, x: int, y: int) -> None:
        """
        Add the text to the surface
        """
        surface.blit(text, (x, y))
