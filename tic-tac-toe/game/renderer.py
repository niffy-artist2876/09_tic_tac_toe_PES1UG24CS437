"""
renderer: all pygame drawing lives here, kept separate from game logic.

Layout is defined in logical units (a 440x620 window). Everything is drawn
SCALE times larger onto the canvas and smoothly scaled down to the window,
which gives anti-aliased edges and keeps the game sharp when enlarged.
"""

import pygame

WIDTH, HEIGHT = 440, 620
WINDOW_SIZE = (WIDTH, HEIGHT)

SCALE = 2
CANVAS_SIZE = (WIDTH * SCALE, HEIGHT * SCALE)

BOARD_SIZE = 360
CELL_SIZE = BOARD_SIZE // 3
BOARD_LEFT = (WIDTH - BOARD_SIZE) // 2
BOARD_TOP = 166

# "Dark modern" palette
COLOR_BG = (30, 30, 46)
COLOR_CARD = (42, 42, 60)
COLOR_GRID = (58, 58, 80)
COLOR_TEXT = (230, 230, 240)
COLOR_MUTED = (138, 138, 163)
COLOR_X = (255, 107, 107)
COLOR_O = (78, 205, 196)

MARK_STROKE = 10
X_HALF = 32         # half the width of an X
O_RADIUS = 34
MARK_ANIM_MS = 220  # how long a new mark takes to draw in
WIN_ANIM_MS = 350   # how long the winning strike-through takes


# --- helpers -----------------------------------------------------------------

def _s(v):
    """Logical units -> canvas pixels."""
    return int(round(v * SCALE))


def _sp(point):
    return (_s(point[0]), _s(point[1]))


def _srect(x, y, w, h):
    return pygame.Rect(_s(x), _s(y), _s(w), _s(h))


def _lerp_color(a, b, t):
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


def _ease_out(p):
    p = max(0.0, min(1.0, p))
    return 1 - (1 - p) ** 3


def _round_line(surface, color, a, b, width):
    """Thick line with rounded ends (a, b in logical units).

    Drawn as a polygon because pygame.draw.line makes thick diagonal lines
    noticeably thinner than horizontal ones.
    """
    (x1, y1), (x2, y2) = a, b
    length = ((x2 - x1) ** 2 + (y2 - y1) ** 2) ** 0.5
    half = width / 2
    if length > 0:
        # offset perpendicular to the line, half the width on each side
        nx, ny = -(y2 - y1) / length * half, (x2 - x1) / length * half
        corners = [(x1 + nx, y1 + ny), (x2 + nx, y2 + ny), (x2 - nx, y2 - ny), (x1 - nx, y1 - ny)]
        pygame.draw.polygon(surface, color, [_sp(p) for p in corners])
    for end in (a, b):
        pygame.draw.circle(surface, color, _sp(end), _s(half))


def _blit_centered(surface, text_surf, center):
    surface.blit(text_surf, text_surf.get_rect(center=_sp(center)))


def symbol_color(symbol):
    return COLOR_X if symbol == 'X' else COLOR_O


def load_fonts():
    def font(size, bold=False):
        return pygame.font.SysFont("segoeui,helveticaneue,arial", _s(size), bold=bold)
    return {
        'label': font(12, bold=True),
        'score': font(30, bold=True),
        'status': font(17, bold=True),
        'hint': font(14),
    }


# --- board geometry ----------------------------------------------------------

def board_pos_to_cell(pos):
    x, y = pos
    x -= BOARD_LEFT
    y -= BOARD_TOP
    if not (0 <= x < BOARD_SIZE and 0 <= y < BOARD_SIZE):
        return None
    col = x // CELL_SIZE
    row = y // CELL_SIZE
    return int(row), int(col)


def cell_center(row, col):
    return (BOARD_LEFT + col * CELL_SIZE + CELL_SIZE / 2,
            BOARD_TOP + row * CELL_SIZE + CELL_SIZE / 2)


# --- drawing -----------------------------------------------------------------

def draw_background(surface):
    surface.fill(COLOR_BG)


def draw_scoreboard(surface, fonts, scores, active_symbol):
    """Three cards: you (X), draws, computer (O). The player to move is outlined."""
    cards = [("YOU  ·  X", 'X', COLOR_X), ("DRAWS", 'draw', COLOR_MUTED), ("CPU  ·  O", 'O', COLOR_O)]
    card_w, card_h, gap, top = 124, 72, 14, 20
    left = (WIDTH - (3 * card_w + 2 * gap)) / 2
    for i, (label, key, color) in enumerate(cards):
        x = left + i * (card_w + gap)
        rect = _srect(x, top, card_w, card_h)
        pygame.draw.rect(surface, COLOR_CARD, rect, border_radius=_s(14))
        if key == active_symbol:
            pygame.draw.rect(surface, color, rect, width=_s(2), border_radius=_s(14))
        _blit_centered(surface, fonts['label'].render(label, True, color), (x + card_w / 2, top + 18))
        _blit_centered(surface, fonts['score'].render(str(scores[key]), True, COLOR_TEXT),
                       (x + card_w / 2, top + 47))


def draw_status(surface, fonts, text, color):
    """A pill-shaped badge under the scoreboard."""
    text_surf = fonts['status'].render(text, True, color)
    pill = text_surf.get_rect(center=_sp((WIDTH / 2, 124))).inflate(_s(32), _s(14))
    pygame.draw.rect(surface, _lerp_color(color, COLOR_BG, 0.82), pill, border_radius=pill.height // 2)
    surface.blit(text_surf, text_surf.get_rect(center=pill.center))


def _draw_x(surface, center, color, progress):
    """Two strokes drawn in one after the other."""
    cx, cy = center
    strokes = [((cx - X_HALF, cy - X_HALF), (cx + X_HALF, cy + X_HALF)),
               ((cx + X_HALF, cy - X_HALF), (cx - X_HALF, cy + X_HALF))]
    for i, (start, end) in enumerate(strokes):
        p = _ease_out(progress * 2 - i)
        if p <= 0:
            continue
        tip = (start[0] + (end[0] - start[0]) * p, start[1] + (end[1] - start[1]) * p)
        _round_line(surface, color, start, tip, MARK_STROKE)


def _draw_o(surface, center, color, progress):
    """A ring that grows into place."""
    radius = O_RADIUS * (0.5 + 0.5 * _ease_out(progress))
    pygame.draw.circle(surface, color, _sp(center), _s(radius), _s(MARK_STROKE))


def _draw_mark(surface, symbol, center, color, progress):
    if symbol == 'X':
        _draw_x(surface, center, color, progress)
    else:
        _draw_o(surface, center, color, progress)


def draw_board(surface, board, now, placed_at, hover_cell=None, hover_symbol=None,
               win_line=None, ended_at=None):
    # card behind the board
    pad = 14
    card = _srect(BOARD_LEFT - pad, BOARD_TOP - pad, BOARD_SIZE + 2 * pad, BOARD_SIZE + 2 * pad)
    pygame.draw.rect(surface, COLOR_CARD, card, border_radius=_s(20))

    # grid lines, inset from the edges
    inset = 16
    for i in range(1, 3):
        x = BOARD_LEFT + i * CELL_SIZE
        y = BOARD_TOP + i * CELL_SIZE
        _round_line(surface, COLOR_GRID, (x, BOARD_TOP + inset), (x, BOARD_TOP + BOARD_SIZE - inset), 4)
        _round_line(surface, COLOR_GRID, (BOARD_LEFT + inset, y), (BOARD_LEFT + BOARD_SIZE - inset, y), 4)

    # faint preview of your mark under the mouse
    if hover_cell is not None:
        color = _lerp_color(symbol_color(hover_symbol), COLOR_CARD, 0.78)
        _draw_mark(surface, hover_symbol, cell_center(*hover_cell), color, 1.0)

    # after a win, non-winning marks fade back so the winning line stands out
    win_cells = set(win_line) if win_line else set()
    win_progress = _ease_out((now - ended_at) / WIN_ANIM_MS) if win_line else 0.0

    for r in range(3):
        for c in range(3):
            symbol = board[r][c]
            if symbol is None:
                continue
            color = symbol_color(symbol)
            if win_line and (r, c) not in win_cells:
                color = _lerp_color(color, COLOR_CARD, 0.65 * win_progress)
            progress = (now - placed_at.get((r, c), now - MARK_ANIM_MS)) / MARK_ANIM_MS
            _draw_mark(surface, symbol, cell_center(r, c), color, progress)

    # strike-through on the winning line, growing from one end to the other
    if win_line and win_progress > 0:
        (x1, y1), (x2, y2) = cell_center(*win_line[0]), cell_center(*win_line[-1])
        # extend a little past the outer cell centers
        ext = 0.18
        start = (x1 - (x2 - x1) * ext, y1 - (y2 - y1) * ext)
        end = (x2 + (x2 - x1) * ext, y2 + (y2 - y1) * ext)
        tip = (start[0] + (end[0] - start[0]) * win_progress, start[1] + (end[1] - start[1]) * win_progress)
        _round_line(surface, COLOR_TEXT, start, tip, 7)


def _draw_segments(surface, font, segments, center):
    """Draw differently-colored text pieces side by side, centered as one line."""
    surfs = [font.render(text, True, color) for text, color in segments]
    total = sum(s.get_width() for s in surfs)
    x = _s(center[0]) - total // 2
    for s in surfs:
        surface.blit(s, s.get_rect(midleft=(x, _s(center[1]))))
        x += s.get_width()


def draw_hints(surface, fonts, starting_player):
    font = fonts['hint']
    _draw_segments(surface, font, [
        ("R", COLOR_TEXT), ("  new round        ", COLOR_MUTED),
        ("M", COLOR_TEXT), ("  reset match", COLOR_MUTED),
    ], (WIDTH / 2, 566))
    _draw_segments(surface, font, [
        ("X", COLOR_X), (" / ", COLOR_MUTED), ("O", COLOR_O),
        ("  choose who starts next round:  ", COLOR_MUTED),
        (starting_player, symbol_color(starting_player)),
    ], (WIDTH / 2, 592))
