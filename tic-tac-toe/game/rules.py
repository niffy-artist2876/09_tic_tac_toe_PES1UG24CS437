"""
rules: win/draw detection for a 3x3 board.

board is a 3x3 list of lists, each cell is None, 'X', or 'O'.
"""

# All 8 winning lines as (row, col) cells: 3 rows, 3 columns, 2 diagonals.
# Each line's cells are listed end to end, so the first and last cells are
# the two ends of the line (used to draw the winning strike-through).
LINES = (
    [[(r, 0), (r, 1), (r, 2)] for r in range(3)]
    + [[(0, c), (1, c), (2, c)] for c in range(3)]
    + [[(0, 0), (1, 1), (2, 2)], [(0, 2), (1, 1), (2, 0)]]
)


def find_winning_line(board):
    """Return (symbol, cells) for the winning line, or None if nobody has won."""
    for cells in LINES:
        a, b, c = (board[r][col] for r, col in cells)
        if a is not None and a == b == c:
            return a, cells
    return None


def check_winner(board):
    result = find_winning_line(board)
    return result[0] if result else None


def is_board_full(board):
    return all(cell is not None for row in board for cell in row)
