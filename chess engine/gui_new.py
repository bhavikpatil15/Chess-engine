"""
gui.py - Play against the engine, or use it as an analysis board.

Run:  python gui.py

PLAY mode  ("New game: White / Black"): you move, the engine replies.
ANALYSIS mode ("Analysis board"): you move BOTH sides. After every move the
engine analyses the position in the background and draws an arrow for the
best move, with the evaluation (from White's point of view, + = White better).

Click a piece, then click a highlighted square to move.
"Undo" takes back moves, "Flip" turns the board around.
"Think time" is how long the engine thinks (per move in play mode, per
position in analysis mode - try 5-10 seconds for analysis).
"""

import queue
import threading
import time
import tkinter as tk

from board import Board, WHITE, BLACK, color_of, EMPTY
from moves import legal_moves, make_move, in_check
from search import find_best_move, MATE
from play import game_result

SQUARE = 72
LIGHT, DARK = "#f0d9b5", "#b58863"
LAST_MOVE = "#ced26b"
SELECTED = "#f6f669"
CHECK = "#e8736b"
ARROW = "#2f6fdb"

# Solid glyphs for both colours; white pieces get a black outline drawn behind.
# The \ufe0e forces text (not emoji) rendering for the pawn on some systems.
GLYPHS = {"K": "\u265a", "Q": "\u265b", "R": "\u265c",
          "B": "\u265d", "N": "\u265e", "P": "\u265f\ufe0e"}
FONT = ("Segoe UI Symbol", int(SQUARE * 0.62))


def eval_text(board, result):
    """Describe a SearchResult from White's point of view, e.g. '+0.35'."""
    score = result.score
    if abs(score) > MATE - 100:
        n = (MATE - abs(score) + 1) // 2
        winner_is_mover = score > 0
        mover_is_white = board.side_to_move == WHITE
        winner = "White" if winner_is_mover == mover_is_white else "Black"
        return f"mate for {winner} in {n}"
    white_score = score if board.side_to_move == WHITE else -score
    return f"{white_score / 100:+.2f}"


class ChessGUI:
    def __init__(self, root):
        self.root = root
        root.title("Chess Engine")
        root.resizable(False, False)

        # --- controls ---
        bar1 = tk.Frame(root)
        bar1.pack(fill="x", padx=6, pady=(6, 0))
        tk.Button(bar1, text="New game: White", command=lambda: self.start_game(WHITE)).pack(side="left")
        tk.Button(bar1, text="New game: Black", command=lambda: self.start_game(BLACK)).pack(side="left", padx=4)
        tk.Button(bar1, text="Analysis board", command=self.start_analysis).pack(side="left")

        bar2 = tk.Frame(root)
        bar2.pack(fill="x", padx=6, pady=6)
        tk.Button(bar2, text="Undo", command=self.undo).pack(side="left")
        tk.Button(bar2, text="Flip", command=self.flip).pack(side="left", padx=4)
        tk.Label(bar2, text="Think time (s):").pack(side="left", padx=(12, 2))
        self.seconds = tk.Spinbox(bar2, from_=0.5, to=60, increment=0.5, width=5)
        self.seconds.delete(0, "end")
        self.seconds.insert(0, "2")
        self.seconds.pack(side="left")

        # --- board ---
        self.canvas = tk.Canvas(root, width=8 * SQUARE, height=8 * SQUARE, highlightthickness=0)
        self.canvas.pack()
        self.canvas.bind("<Button-1>", self.on_click)

        # --- status line ---
        self.status = tk.StringVar()
        tk.Label(root, textvariable=self.status, anchor="w", justify="left",
                 font=("Arial", 11), wraplength=8 * SQUARE - 16).pack(fill="x", padx=8, pady=6)

        self.results = queue.Queue()
        self.epoch = 0           # bumped whenever pending engine work becomes stale
        self.poll_job = None
        self.view = WHITE        # which side is at the bottom of the screen
        self.start_game(WHITE)

    # ---------- setting up games ----------

    def _reset(self, human_color):
        self.epoch += 1
        if self.poll_job:
            self.root.after_cancel(self.poll_job)
            self.poll_job = None
        self.board = Board()
        self.human = human_color
        self.tt = {}
        self.selected = None
        self.targets = set()
        self.last_move = None
        self.history = []        # list of (board, last_move) for undo
        self.thinking = False    # play mode: engine is choosing its reply
        self.analysing = False   # analysis mode: engine is analysing
        self.suggestion = None   # latest SearchResult in analysis mode
        self.engine_note = ""
        self.over = False
        self.legal = []

    def start_game(self, human_color):
        self.mode = "play"
        self._reset(human_color)
        self.view = human_color
        self.refresh()
        if self.board.side_to_move != self.human:
            self.engine_turn()

    def start_analysis(self):
        self.mode = "analysis"
        self._reset(WHITE)
        self.refresh()
        self.begin_analysis()

    def flip(self):
        self.view = BLACK if self.view == WHITE else WHITE
        self.draw()

    # ---------- state and status ----------

    def refresh(self):
        """Recompute legal moves, game state and status text, then redraw."""
        result = game_result(self.board)
        if self.mode == "analysis":
            self.human = self.board.side_to_move     # you play whoever is to move
        self.over = bool(result)

        if result:
            self.legal = []
            self.status.set(result)
        else:
            my_turn = self.mode == "analysis" or self.board.side_to_move == self.human
            self.legal = legal_moves(self.board) if my_turn else []
            check = "Check! " if in_check(self.board) else ""
            if self.mode == "analysis":
                side = "White" if self.board.side_to_move == WHITE else "Black"
                self.status.set(f"{check}{side} to move.   {self.analysis_line()}")
            elif self.thinking:
                self.status.set("Engine is thinking...")
            else:
                note = self.engine_note + "   " if self.engine_note else ""
                self.status.set(f"{note}{check}Your move.")
        self.draw()

    def analysis_line(self):
        if self.suggestion is None or self.suggestion.move is None:
            return "Analysing..." if self.analysing else ""
        r = self.suggestion
        tail = "  (analysing...)" if self.analysing else "  (done)"
        return f"Best: {r.move}   eval {eval_text(self.board, r)}, depth {r.depth}{tail}"

    # ---------- moves, undo ----------

    def do_move(self, move):
        self.history.append((self.board, self.last_move))
        self.board = make_move(self.board, move)
        self.last_move = move
        self.selected = None
        self.targets = set()

        if self.mode == "analysis":
            self.epoch += 1            # old analysis is now out of date
            self.suggestion = None
            self.analysing = False
            self.refresh()
            self.begin_analysis()
        else:
            self.refresh()
            if not self.over and self.board.side_to_move != self.human:
                self.engine_turn()

    def undo(self):
        if not self.history:
            return
        self.epoch += 1
        self.thinking = False
        self.analysing = False
        self.board, self.last_move = self.history.pop()
        if self.mode == "play":
            # take back until it is the human's turn again
            while self.board.side_to_move != self.human and self.history:
                self.board, self.last_move = self.history.pop()
        self.selected, self.targets, self.suggestion = None, set(), None
        self.engine_note = ""
        self.refresh()
        if self.mode == "analysis":
            self.begin_analysis()
        elif not self.over and self.board.side_to_move != self.human:
            self.engine_turn()

    # ---------- engine work (background threads) ----------

    def _seconds(self, default):
        try:
            return max(0.5, float(self.seconds.get()))
        except ValueError:
            return default

    def ensure_polling(self):
        if self.poll_job is None:
            self.poll_job = self.root.after(100, self.poll)

    def engine_turn(self):
        """Play mode: the engine chooses and plays a move."""
        self.thinking = True
        self.refresh()
        seconds = self._seconds(2.0)
        gid, board, tt = self.epoch, self.board.copy(), self.tt

        def work():
            result = find_best_move(board, 8, seconds, tt, should_stop=lambda: gid != self.epoch)
            self.results.put(("move", gid, result))

        threading.Thread(target=work, daemon=True).start()
        self.ensure_polling()

    def begin_analysis(self):
        """Analysis mode: search deeper and deeper, reporting after each depth."""
        if self.over:
            return
        self.suggestion = None
        self.analysing = True
        seconds = self._seconds(5.0)
        gid, board, tt = self.epoch, self.board.copy(), self.tt

        def work():
            deadline = time.time() + seconds
            stop = lambda: gid != self.epoch
            for depth in range(1, 40):
                remaining = deadline - time.time()
                if remaining <= 0.05 or stop():
                    break
                r = find_best_move(board, depth, remaining, tt, should_stop=stop)
                if r.depth < depth:        # ran out of time / cancelled mid-depth
                    break
                self.results.put(("analysis", gid, r))
                if abs(r.score) > MATE - 100:
                    break                  # forced mate found
            self.results.put(("done", gid, None))

        threading.Thread(target=work, daemon=True).start()
        self.refresh()
        self.ensure_polling()

    def poll(self):
        """Runs on the GUI thread every 100 ms to collect results from the engine thread."""
        self.poll_job = None
        try:
            while True:
                kind, gid, payload = self.results.get_nowait()
                if gid != self.epoch:
                    continue                     # stale result from an abandoned position
                if kind == "move":
                    self.thinking = False
                    self.engine_note = (f"Engine played {payload.move} "
                                        f"(eval {eval_text(self.board, payload)}, depth {payload.depth}).")
                    self.do_move(payload.move)
                elif kind == "analysis":
                    self.suggestion = payload
                    self.refresh()
                elif kind == "done":
                    self.analysing = False
                    self.refresh()
        except queue.Empty:
            pass
        if (self.thinking or self.analysing) and self.poll_job is None:
            self.poll_job = self.root.after(100, self.poll)

    # ---------- input ----------

    def to_board(self, r, c):
        """Screen square -> board square (the view flips when Black is at the bottom)."""
        return (7 - r, 7 - c) if self.view == BLACK else (r, c)

    def to_screen(self, row, col):
        return (7 - row, 7 - col) if self.view == BLACK else (row, col)

    def on_click(self, event):
        if self.over:
            return
        if self.mode == "play" and (self.thinking or self.board.side_to_move != self.human):
            return
        c, r = event.x // SQUARE, event.y // SQUARE
        if not (0 <= r < 8 and 0 <= c < 8):
            return
        square = self.to_board(r, c)

        if self.selected and square in self.targets:
            options = [m for m in self.legal if m.frm == self.selected and m.to == square]
            move = options[0]
            if len(options) > 1:                       # promotion: ask which piece
                piece = self.ask_promotion()
                move = next(m for m in options if m.promotion == piece)
            self.do_move(move)
            return

        piece = self.board.grid[square[0]][square[1]]
        if piece != EMPTY and color_of(piece) == self.human:
            self.selected = square
            self.targets = {m.to for m in self.legal if m.frm == square}
        else:
            self.selected, self.targets = None, set()
        self.draw()

    def ask_promotion(self):
        win = tk.Toplevel(self.root)
        win.title("Promote to")
        win.transient(self.root)
        choice = tk.StringVar(value="q")
        for label, code in (("Queen", "q"), ("Rook", "r"), ("Bishop", "b"), ("Knight", "n")):
            tk.Button(win, text=label, width=8,
                      command=lambda c=code: (choice.set(c), win.destroy())).pack(side="left", padx=4, pady=8)
        win.grab_set()
        self.root.wait_window(win)
        return choice.get()

    # ---------- drawing ----------

    def draw(self):
        cv = self.canvas
        cv.delete("all")
        check_sq = None
        if in_check(self.board):
            check_sq = self.board.find_king(self.board.side_to_move)

        for r in range(8):
            for c in range(8):
                row, col = self.to_board(r, c)
                x, y = c * SQUARE, r * SQUARE
                color = LIGHT if (row + col) % 2 == 0 else DARK
                if self.last_move and (row, col) in (self.last_move.frm, self.last_move.to):
                    color = LAST_MOVE
                if self.selected == (row, col):
                    color = SELECTED
                if check_sq == (row, col):
                    color = CHECK
                cv.create_rectangle(x, y, x + SQUARE, y + SQUARE, fill=color, outline=color)

                # coordinate labels in the corners
                label_color = DARK if (row + col) % 2 == 0 else LIGHT
                if c == 0:
                    cv.create_text(x + 3, y + 3, text=str(8 - row), anchor="nw",
                                   fill=label_color, font=("Arial", 9, "bold"))
                if r == 7:
                    cv.create_text(x + SQUARE - 3, y + SQUARE - 3, text="abcdefgh"[col], anchor="se",
                                   fill=label_color, font=("Arial", 9, "bold"))

                piece = self.board.grid[row][col]
                if piece != EMPTY:
                    self.draw_piece(piece, x + SQUARE / 2, y + SQUARE / 2)

                if (row, col) in self.targets:
                    if piece == EMPTY:
                        rad = SQUARE * 0.12
                        cv.create_oval(x + SQUARE / 2 - rad, y + SQUARE / 2 - rad,
                                       x + SQUARE / 2 + rad, y + SQUARE / 2 + rad,
                                       fill="#6a8f4e", outline="")
                    else:
                        cv.create_rectangle(x + 3, y + 3, x + SQUARE - 3, y + SQUARE - 3,
                                            outline="#6a8f4e", width=4)

        self.draw_suggestion()

    def draw_suggestion(self):
        """Analysis mode: arrow for the engine's best move."""
        if self.mode != "analysis" or self.over or self.suggestion is None or self.suggestion.move is None:
            return
        move = self.suggestion.move
        r1, c1 = self.to_screen(*move.frm)
        r2, c2 = self.to_screen(*move.to)
        self.canvas.create_line(
            c1 * SQUARE + SQUARE / 2, r1 * SQUARE + SQUARE / 2,
            c2 * SQUARE + SQUARE / 2, r2 * SQUARE + SQUARE / 2,
            fill=ARROW, width=9, arrow=tk.LAST, arrowshape=(20, 24, 10), capstyle=tk.ROUND,
        )

    def draw_piece(self, piece, cx, cy):
        glyph = GLYPHS[piece.upper()]
        if piece.isupper():   # white: black outline behind a white glyph
            for dx, dy in ((-1, -1), (-1, 1), (1, -1), (1, 1), (0, -1), (0, 1), (-1, 0), (1, 0)):
                self.canvas.create_text(cx + dx * 1.5, cy + dy * 1.5, text=glyph, font=FONT, fill="black")
            self.canvas.create_text(cx, cy, text=glyph, font=FONT, fill="white")
        else:
            self.canvas.create_text(cx, cy, text=glyph, font=FONT, fill="black")


if __name__ == "__main__":
    root = tk.Tk()
    ChessGUI(root)
    root.mainloop()
