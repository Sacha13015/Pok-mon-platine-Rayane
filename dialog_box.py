import pygame

def show_dialog_box_overlay(screen, dialogue, vitesse=45):
    font = pygame.font.Font(None, 36)
    if isinstance(dialogue, str):
        lines = dialogue.split('\n')
    else:
        lines = dialogue

    current_line = 0
    clock = pygame.time.Clock()
    running = True

    while running:
        text_displayed = ""
        lettre_index = 0
        full_line = lines[current_line]
        displaying_line = True

        while displaying_line:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    exit()
                elif (event.type == pygame.KEYDOWN and (
                        event.key == pygame.K_RETURN or event.key == pygame.K_SPACE)) or event.type == pygame.MOUSEBUTTONDOWN:
                    if lettre_index < len(full_line):
                        lettre_index = len(full_line)
                        text_displayed = full_line
                    else:
                        displaying_line = False

            if lettre_index < len(full_line):
                lettre_index += 1
                text_displayed = full_line[:lettre_index]

            pygame.draw.rect(screen, (0, 0, 0), (60, screen.get_height() - 140, screen.get_width() - 120, 110), border_radius=16)
            pygame.draw.rect(screen, (50, 150, 255), (60, screen.get_height() - 140, screen.get_width() - 120, 110), 3, border_radius=16)
            rendered_text = font.render(text_displayed, True, (255, 255, 255))
            screen.blit(rendered_text, (80, screen.get_height() - 120))

            pygame.display.flip()
            clock.tick(vitesse)
            if lettre_index == len(full_line):
                clock.tick(15)
        current_line += 1
        if current_line >= len(lines):
            running = False
