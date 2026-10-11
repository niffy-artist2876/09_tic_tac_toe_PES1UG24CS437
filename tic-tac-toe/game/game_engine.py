"""
GameEngine: owns the board, turn state, round-end logic, and the
match-level scoreboard.

You (the player) always play X and click to move. The computer always
plays O and moves automatically after a short pause, using a simple
random-move AI (see game/ai.py) - this is given infrastructure, not
something you need to build.

Controls:
    R      restart the current round (scoreboard is kept)
    M      reset the whole match (scoreboard is cleared)
    X / O  choose which symbol starts - takes effect on the next round
"""

from game.rules import find_winning_line, is_board_full
from game.renderer import board_pos_to_cell
from game.ai import choose_move

HUMAN_SYMBOL = 'X'
COMPUTER_SYMBOL = 'O'
COMPUTER_DELAY_MS = 450   # pause before the computer moves, so it reads as a turn


class GameEngine:
    def __init__(self):
        self.now = 0                 # current time in ms, updated every frame by update()
        self.starting_player = 'X'   # who moves first in the next round
        self.reset_match()

    def reset_match(self):
        """Clear the scoreboard and start a fresh round."""
        self.scores = {'X': 0, 'O': 0, 'draw': 0}
        self.new_round()

    def new_round(self):
        """Start a new round, keeping the scoreboard."""
        self.board = [[None] * 3 for _ in range(3)]
        self.current_player = self.starting_player
        self.round_over = False
        self.winner = None     # 'X', 'O', or None (meaning draw, only valid when round_over)
        self.win_line = None   # the 3 winning cells, once someone has won
        self.ended_at = None   # time the round ended (drives the win animation)
        self.placed_at = {}    # (row, col) -> time the mark was placed (drives its animation)
        self.computer_move_at = None
        self._schedule_computer_turn()   # if O starts, the computer moves first

    def update(self, now):
        """Advance the clock; makes the computer's move once its pause is over."""
        self.now = now
        if self.computer_move_at is not None and now >= self.computer_move_at:
            self.computer_move_at = None
            self._take_computer_turn()

    def handle_click(self, pos):
        if self.round_over:
            return   # round has ended - ignore clicks until a new round starts
        if self.current_player != HUMAN_SYMBOL:
            return   # not your turn - the computer is about to move
        cell = board_pos_to_cell(pos)
        if cell is None:
            return
        row, col = cell
        if self.board[row][col] is not None:
            return   # cell already taken - reject the move, board and turn stay unchanged
        self._place(row, col)
        self._schedule_computer_turn()

    def _place(self, row, col):
        self.board[row][col] = self.current_player
        self.placed_at[(row, col)] = self.now
        self.check_round_end()
        self.current_player = 'O' if self.current_player == 'X' else 'X'

    def _schedule_computer_turn(self):
        if not self.round_over and self.current_player == COMPUTER_SYMBOL:
            self.computer_move_at = self.now + COMPUTER_DELAY_MS

    def _take_computer_turn(self):
        if self.round_over or self.current_player != COMPUTER_SYMBOL:
            return
        move = choose_move(self.board)
        if move is None:
            return
        self._place(*move)

    def handle_keydown(self, key):
        import pygame
        if key == pygame.K_r:
            self.new_round()
        elif key == pygame.K_m:
            self.reset_match()
        elif key == pygame.K_x:
            self.starting_player = 'X'
        elif key == pygame.K_o:
            self.starting_player = 'O'

    def check_round_end(self):
        # A win takes priority over a full board, so check for a winner first
        result = find_winning_line(self.board)
        if result:
            self.winner, self.win_line = result
            self.round_over = True
            self.ended_at = self.now
            self.scores[self.winner] += 1
        elif is_board_full(self.board):
            self.round_over = True
            self.winner = None
            self.ended_at = self.now
            self.scores['draw'] += 1

    def _status(self):
        from game import renderer
        if self.round_over:
            if self.winner == HUMAN_SYMBOL:
                return "You win!  Press R for next round", renderer.COLOR_X
            if self.winner == COMPUTER_SYMBOL:
                return "Computer wins.  Press R for next round", renderer.COLOR_O
            return "Draw!  Press R for next round", renderer.COLOR_TEXT
        if self.current_player == HUMAN_SYMBOL:
            return "Your turn", renderer.COLOR_X
        return "Computer is thinking...", renderer.COLOR_O

    def draw(self, surface, fonts, mouse_pos=None):
        from game import renderer
        renderer.draw_background(surface)

        active = None if self.round_over else self.current_player
        renderer.draw_scoreboard(surface, fonts, self.scores, active)
        renderer.draw_status(surface, fonts, *self._status())

        # preview your mark on the empty cell under the mouse, only when it's your move
        hover_cell = None
        if mouse_pos is not None and not self.round_over and self.current_player == HUMAN_SYMBOL:
            cell = board_pos_to_cell(mouse_pos)
            if cell is not None and self.board[cell[0]][cell[1]] is None:
                hover_cell = cell

        renderer.draw_board(surface, self.board, self.now, self.placed_at,
                            hover_cell=hover_cell, hover_symbol=HUMAN_SYMBOL,
                            win_line=self.win_line, ended_at=self.ended_at)
        renderer.draw_hints(surface, fonts, self.starting_player)
