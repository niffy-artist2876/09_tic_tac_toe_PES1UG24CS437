"""
Tic-Tac-Toe (Lab Starter)

Run with:  python3 main.py

Click a cell to place your symbol.
"""

import pygame

from game.game_engine import GameEngine
from game.renderer import WINDOW_SIZE, CANVAS_SIZE, COLOR_BG, load_fonts


def fit_rect(window_size):
    """Largest rect with the game's aspect ratio, centered in the window."""
    win_w, win_h = window_size
    scale = min(win_w / WINDOW_SIZE[0], win_h / WINDOW_SIZE[1])
    rect = pygame.Rect(0, 0, int(WINDOW_SIZE[0] * scale), int(WINDOW_SIZE[1] * scale))
    rect.center = (win_w // 2, win_h // 2)
    return rect, scale


def to_game_coords(pos, rect, scale):
    """Window coordinates -> the game's logical coordinates (None if outside the game area)."""
    if not rect.collidepoint(pos):
        return None
    return ((pos[0] - rect.x) / scale, (pos[1] - rect.y) / scale)


def main():
    pygame.init()
    screen = pygame.display.set_mode(WINDOW_SIZE, pygame.RESIZABLE)
    pygame.display.set_caption("Tic-Tac-Toe")
    clock = pygame.time.Clock()
    fonts = load_fonts()

    # The game draws onto a fixed-size, high-resolution canvas, which is then
    # smoothly scaled to fit the (resizable) window.
    canvas = pygame.Surface(CANVAS_SIZE)

    engine = GameEngine()
    running = True
    while running:
        screen = pygame.display.get_surface()
        rect, scale = fit_rect(screen.get_size())
        engine.update(pygame.time.get_ticks())

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                pos = to_game_coords(event.pos, rect, scale)
                if pos is not None:
                    engine.handle_click(pos)
            elif event.type == pygame.KEYDOWN:
                engine.handle_keydown(event.key)

        engine.draw(canvas, fonts, to_game_coords(pygame.mouse.get_pos(), rect, scale))

        screen.fill(COLOR_BG)
        screen.blit(pygame.transform.smoothscale(canvas, rect.size), rect)
        pygame.display.flip()
        clock.tick(60)

    pygame.quit()


if __name__ == "__main__":
    main()
