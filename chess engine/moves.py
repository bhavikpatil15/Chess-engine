"""
moves.py - Step 2: Move generation.

Pipeline
--------
1. pseudo_legal_moves(board): every move that obeys piece movement rules,
   ignoring whether our own king ends up in check.
2. make_move(board, move): returns a NEW board with the move played.
3. legal_moves(board): pseudo-legal moves minus those that leave our king
   attacked. This is the function the rest of the engine will use.

Coordinates are (row, col) as in board.py: row 0 = rank 8, col 0 = file a.
"""

from board import (
    Board, EMPTY, WHITE, BLACK,
    color_of, coords_to_square, square_to_coords,
)

KNIGHT_OFFSETS = [(-2, -1), (-2, 1), (-1, -2), (-1, 2), (1, -2), (1, 2), (2, -1), (2, 1)]
KING_OFFSETS = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]
BISHOP_DIRS = [(-1, -1), (-1, 1), (1, -1), (1, 1)]
ROOK_DIRS = [(-1, 0), (1, 0), (0, -1), (0, 1)]


def opponent(color):
    return BLACK if color == WHITE else WHITE


class Move:
    """A move from one square to another. `promotion` is 'q', 'r', 'b', 'n' or None."""
    __slots__ = ("frm", "to", "promotion")

    def __init__(self, frm, to, promotion=None):
        self.frm = frm
        self.to = to
        self.promotion = promotion

    def __str__(self):
        text = coords_to_square(*self.frm) + coords_to_square(*self.to)
        return text + (self.promotion or "")

    __repr__ = __str__

    def __eq__(self, other):
        return (self.frm, self.to, self.promotion) == (other.frm, other.to, other.promotion)

    def __hash__(self):
        return hash((self.frm, self.to, self.promotion))


# ---------- attack detection ----------

def is_square_attacked(board, row, col, by_color):
    """Is (row, col) attacked by any piece of `by_color`?"""
    grid = board.grid
    white = by_color == WHITE

    # Pawns: a white pawn attacks diagonally "up" (towards row 0), so it
    # would be standing one row below the target square. Black is mirrored.
    pawn = "P" if white else "p"
    pr = row + 1 if white else row - 1
    if 0 <= pr < 8:
        for dc in (-1, 1):
            c = col + dc
            if 0 <= c < 8 and grid[pr][c] == pawn:
                return True

    knight = "N" if white else "n"
    for dr, dc in KNIGHT_OFFSETS:
        r, c = row + dr, col + dc
        if 0 <= r < 8 and 0 <= c < 8 and grid[r][c] == knight:
            return True

    king = "K" if white else "k"
    for dr, dc in KING_OFFSETS:
        r, c = row + dr, col + dc
        if 0 <= r < 8 and 0 <= c < 8 and grid[r][c] == king:
            return True

    bishop, rook, queen = ("B", "R", "Q") if white else ("b", "r", "q")
    for directions, slider in ((BISHOP_DIRS, bishop), (ROOK_DIRS, rook)):
        for dr, dc in directions:
            r, c = row + dr, col + dc
            while 0 <= r < 8 and 0 <= c < 8:
                piece = grid[r][c]
                if piece != EMPTY:
                    if piece == slider or piece == queen:
                        return True
                    break
                r += dr
                c += dc
    return False


def in_check(board, color=None):
    color = color or board.side_to_move
    king = board.find_king(color)
    return king is not None and is_square_attacked(board, king[0], king[1], opponent(color))


# ---------- pseudo-legal generation ----------

def _add_pawn_move(moves, frm, to, promo_row):
    if to[0] == promo_row:
        for p in "qrbn":
            moves.append(Move(frm, to, p))
    else:
        moves.append(Move(frm, to))


def _pawn_moves(board, row, col, color, moves):
    grid = board.grid
    white = color == WHITE
    step = -1 if white else 1
    start_row = 6 if white else 1
    promo_row = 0 if white else 7
    nr = row + step
    if not (0 <= nr < 8):
        return

    # Pushes
    if grid[nr][col] == EMPTY:
        _add_pawn_move(moves, (row, col), (nr, col), promo_row)
        if row == start_row and grid[nr + step][col] == EMPTY:
            moves.append(Move((row, col), (nr + step, col)))

    # Captures (including en passant)
    ep = square_to_coords(board.en_passant) if board.en_passant else None
    for dc in (-1, 1):
        nc = col + dc
        if not (0 <= nc < 8):
            continue
        target = grid[nr][nc]
        if target != EMPTY and color_of(target) != color:
            _add_pawn_move(moves, (row, col), (nr, nc), promo_row)
        elif target == EMPTY and ep == (nr, nc):
            moves.append(Move((row, col), (nr, nc)))


def _step_moves(board, row, col, color, offsets, moves):
    """Knights and kings: jump to a fixed set of squares."""
    grid = board.grid
    for dr, dc in offsets:
        r, c = row + dr, col + dc
        if 0 <= r < 8 and 0 <= c < 8:
            target = grid[r][c]
            if target == EMPTY or color_of(target) != color:
                moves.append(Move((row, col), (r, c)))


def _sliding_moves(board, row, col, color, directions, moves):
    """Bishops, rooks, queens: slide until blocked."""
    grid = board.grid
    for dr, dc in directions:
        r, c = row + dr, col + dc
        while 0 <= r < 8 and 0 <= c < 8:
            target = grid[r][c]
            if target == EMPTY:
                moves.append(Move((row, col), (r, c)))
            else:
                if color_of(target) != color:
                    moves.append(Move((row, col), (r, c)))
                break
            r += dr
            c += dc


def _castling_moves(board, color, moves):
    white = color == WHITE
    row = 7 if white else 0
    grid = board.grid
    if grid[row][4] != ("K" if white else "k"):
        return
    enemy = opponent(color)
    rook = "R" if white else "r"
    k_flag, q_flag = ("K", "Q") if white else ("k", "q")

    # Kingside: f and g empty; e, f, g not attacked
    if (k_flag in board.castling and grid[row][7] == rook
            and grid[row][5] == EMPTY and grid[row][6] == EMPTY
            and not any(is_square_attacked(board, row, c, enemy) for c in (4, 5, 6))):
        moves.append(Move((row, 4), (row, 6)))

    # Queenside: b, c, d empty; e, d, c not attacked (b may be attacked)
    if (q_flag in board.castling and grid[row][0] == rook
            and grid[row][1] == EMPTY and grid[row][2] == EMPTY and grid[row][3] == EMPTY
            and not any(is_square_attacked(board, row, c, enemy) for c in (4, 3, 2))):
        moves.append(Move((row, 4), (row, 2)))


def pseudo_legal_moves(board):
    color = board.side_to_move
    moves = []
    for row, col, piece in board.pieces(color):
        kind = piece.upper()
        if kind == "P":
            _pawn_moves(board, row, col, color, moves)
        elif kind == "N":
            _step_moves(board, row, col, color, KNIGHT_OFFSETS, moves)
        elif kind == "K":
            _step_moves(board, row, col, color, KING_OFFSETS, moves)
            _castling_moves(board, color, moves)
        elif kind == "B":
            _sliding_moves(board, row, col, color, BISHOP_DIRS, moves)
        elif kind == "R":
            _sliding_moves(board, row, col, color, ROOK_DIRS, moves)
        elif kind == "Q":
            _sliding_moves(board, row, col, color, BISHOP_DIRS + ROOK_DIRS, moves)
    return moves


# ---------- playing a move ----------

def make_move(board, move):
    """Return a new Board with `move` played. The original is untouched."""
    new = board.copy()
    g = new.grid
    (fr, fc), (tr, tc) = move.frm, move.to
    piece = g[fr][fc]
    color = color_of(piece)
    kind = piece.upper()
    captured = g[tr][tc]

    g[fr][fc] = EMPTY
    g[tr][tc] = piece

    # En passant: pawn moved diagonally onto an empty square.
    # The captured pawn sits beside us, on the row we started from.
    if kind == "P" and fc != tc and captured == EMPTY:
        g[fr][tc] = EMPTY
        captured = "p"  # just marks "something was captured" for the clock

    # Promotion
    if move.promotion:
        g[tr][tc] = move.promotion.upper() if color == WHITE else move.promotion.lower()

    # Castling: also move the rook
    if kind == "K" and abs(tc - fc) == 2:
        if tc > fc:
            g[fr][5], g[fr][7] = g[fr][7], EMPTY
        else:
            g[fr][3], g[fr][0] = g[fr][0], EMPTY

    # Castling rights
    rights = set(board.castling) - {"-"}
    if kind == "K":
        rights -= {"K", "Q"} if color == WHITE else {"k", "q"}
    for corner, flag in (((7, 0), "Q"), ((7, 7), "K"), ((0, 0), "q"), ((0, 7), "k")):
        if move.frm == corner or move.to == corner:  # rook moved or was captured
            rights.discard(flag)
    new.castling = "".join(f for f in "KQkq" if f in rights) or "-"

    # En passant target square (only after a double pawn push)
    new.en_passant = None
    if kind == "P" and abs(tr - fr) == 2:
        new.en_passant = coords_to_square((fr + tr) // 2, fc)

    # Clocks and turn
    new.halfmove_clock = 0 if (kind == "P" or captured != EMPTY) else board.halfmove_clock + 1
    if color == BLACK:
        new.fullmove_number += 1
    new.side_to_move = opponent(color)
    return new


# ---------- legal moves ----------

def legal_moves(board):
    """All fully legal moves for the side to move."""
    color = board.side_to_move
    enemy = opponent(color)
    legal = []
    for move in pseudo_legal_moves(board):
        nb = make_move(board, move)
        king = nb.find_king(color)
        if king is None or not is_square_attacked(nb, king[0], king[1], enemy):
            legal.append(move)
    return legal


def parse_move(board, text):
    """Turn user text like 'e2e4' or 'e7e8q' into a legal Move, or None."""
    text = text.strip().lower()
    for move in legal_moves(board):
        if str(move) == text:
            return move
    return None


def game_status(board):
    """'checkmate', 'stalemate', or 'ongoing' (draw-by-rule checks come later)."""
    if legal_moves(board):
        return "ongoing"
    return "checkmate" if in_check(board) else "stalemate"


# ---------- perft: the standard test for move generators ----------

def perft(board, depth):
    """Count all leaf positions reachable in exactly `depth` plies."""
    if depth == 0:
        return 1
    moves = legal_moves(board)
    if depth == 1:
        return len(moves)
    return sum(perft(make_move(board, m), depth - 1) for m in moves)
