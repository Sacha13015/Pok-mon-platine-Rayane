import pygame


class KeyListener:
    """
    KeyListener class to manage the keys
    """
    def __init__(self) -> None:
        self.keys: list[int] = []

    def add_key(self, key: int) -> None:
        """Ajoute une touche si non présente."""
        if key not in self.keys:
            self.keys.append(key)

    def remove_key(self, key: int) -> None:
        """Supprime une touche si présente."""
        if key in self.keys:
            self.keys.remove(key)

    def key_pressed(self, key: int) -> bool:
        """Renvoie True si la touche est pressée."""
        return key in self.keys

    def clear(self) -> None:
        """Vide la liste des touches."""
        self.keys.clear()

    def handle_event(self, event) -> None:
        """Gère l'ajout et la suppression des touches selon l'événement pygame."""
        if event.type == pygame.KEYDOWN:
            self.add_key(event.key)
        elif event.type == pygame.KEYUP:
            self.remove_key(event.key)
