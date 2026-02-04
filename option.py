import pygame

from controller import Controller
from keylistener import KeyListener
from map import Map
from player import Player
from save import Save
from screen import Screen
from sql import SQL
from tool import Tool
from dialogue import Dialogue

class Option:
    def __init__(self, screen: Screen, controller: Controller, map: Map, language: str, save: Save,
                 keylistener: KeyListener, dialogue: Dialogue) -> None:
        self.screen: Screen = screen
        self.controller: Controller = controller
        self.map: Map = map
        self.language: str = language
        self.save: Save = save
        self.sql: SQL = SQL()
        self.player: Player = self.map.player
        self.keylistener: KeyListener = keylistener
        self.dialogue: Dialogue = dialogue

        self.full_backsol: pygame.Surface = pygame.Surface(self.screen.get_size())
        self.image_backsol: pygame.Surface | None = None
        self.initialization: bool = False

        self.backsol_color: tuple[int, int, int] = (4, 18, 18)
        self.backsol: pygame.Surface = pygame.Surface((self.screen.get_size()[0], 80))
        self.backsol.fill(self.backsol_color)

    def update(self) -> None:
        if not self.initialization:
            self.initialization = True
            self.initialize()
        self.draw()
        self.check_end()

    def check_inputs(self) -> None:
        if self.keylistener.key_pressed(self.controller.get_key("action")):
            self.save.save()
            self.keylistener.remove_key(self.controller.get_key("action"))

    def initialize(self) -> None:
        self.image_backsol = self.screen.image_screen()
        self.image_backsol = Tool.blur(self.image_backsol, 2)

    def draw(self) -> None:
        self.player.update_ingame_time()
        self.full_backsol.blit(self.image_backsol, (0, 0))
        self.full_backsol.blit(self.backsol, (0, 0))
        self.full_backsol.blit(self.backsol, (0, self.screen.get_size()[1] - self.backsol.get_height()))
        self.screen.get_display().blit(self.full_backsol, (0, 0))

    def check_end(self) -> None:
        if self.dialogue.active:
            return
        if self.keylistener.key_pressed(self.controller.get_key("quit")):
            self.initialization = False
            self.player.menu_option = False
            self.keylistener.remove_key(self.controller.get_key("quit"))
