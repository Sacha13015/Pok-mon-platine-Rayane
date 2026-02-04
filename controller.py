import pygame

class Controller:
    def __init__(self):
        # Tu peux initialiser ici des variables si besoin
        pass

    def handle_event(self, event, player):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_LEFT:
                player.move_left()
            elif event.key == pygame.K_RIGHT:
                player.move_right()
            elif event.key == pygame.K_UP:
                player.move_up()
            elif event.key == pygame.K_DOWN:
                player.move_down()
            elif event.key == pygame.K_LSHIFT:
                player.speed = 2  # Par exemple vitesse accélérée
            elif event.key == pygame.K_b:
                player.switch_bike()
            elif event.key == pygame.K_ESCAPE:
                player.menu_option = True

        elif event.type == pygame.KEYUP:
            if event.key == pygame.K_LSHIFT:
                player.speed = 1  # Vitesse normale quand relâche shift

    def get_key(self, action: str) -> int:
        keymap = {
            "left": pygame.K_LEFT,
            "right": pygame.K_RIGHT,
            "up": pygame.K_UP,
            "down": pygame.K_DOWN,
            "bike": pygame.K_b,
            "quit": pygame.K_ESCAPE,
        }
        return keymap.get(action, 0)
