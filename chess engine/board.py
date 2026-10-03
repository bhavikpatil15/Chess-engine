"""
board.py - Step 1: Board representation for our chess engine.

Conventions
-----------
- grid[row][col]: row 0 = rank 8 (Black's back rank), row 7 = rank 1.
- col 0 = file 'a', col 7 = file 'h'.
- White pieces are UPPERCASE (P N B R Q K), Black pieces are lowercase.
- Empty squares are '.'.
- Squares are written in algebraic form ("e4"), and converted to
  (row, col) with the helpers below.
"""

START_FEN = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"

EMPTY = "."
WHITE, BLACK = "w", "b"
VALID_PIECES = "PNBRQKpnbrqk"


# ---------- helpers ----------

def square_to_coords(square):
    """'e4' -> (4, 4). Raises ValueError for bad squares."""
    if len(square) != 2 or square[0] not in "abcdefgh" or square[1] not in "12345678":
        raise ValueError(f"Invalid square: {square!r}")
    col = ord(square[0]) - ord("a")
    row = 8 - int(square[1])
    return row, col


def coords_to_square(row, col):
    """(4, 4) -> 'e4'."""
    if not (0 <= row < 8 and 0 <= col < 8):
        raise ValueError(f"Coordinates out of range: {(row, col)}")
    return "abcdefgh"[col] + str(8 - row)


def color_of(piece):
    """Return WHITE, BLACK, or None for an empty square."""
    if piece == EMPTY:
        return None
    return WHITE if piece.isupper() else BLACK


# ---------- the board ----------

class Board:
    def __init__(self, fen=START_FEN):
        self.set_fen(fen)

    # --- FEN in / out ---

    def set_fen(self, fen):
        """Load a position from a FEN string."""
        parts = fen.split()
        if len(parts) != 6:
            raise ValueError("FEN must have 6 fields")
        placement, side, castling, ep, half, full = parts

        ranks = placement.split("/")
        if len(ranks) != 8:
            raise ValueError("FEN placement must have 8 ranks")

        grid = []
        for rank in ranks:
            row = []
            for ch in rank:
                if ch.isdigit():
                    row.extend([EMPTY] * int(ch))
                elif ch in VALID_PIECES:
                    row.append(ch)
                else:
                    raise ValueError(f"Bad character in FEN: {ch!r}")
            if len(row) != 8:
                raise ValueError(f"Rank {rank!r} does not add up to 8 squares")
            grid.append(row)

        if side not in (WHITE, BLACK):
            raise ValueError("Side to move must be 'w' or 'b'")

        self.grid = grid
        self.side_to_move = side
        self.castling = castling              # e.g. "KQkq" or "-"
        self.en_passant = None if ep == "-" else ep
        self.halfmove_clock = int(half)
        self.fullmove_number = int(full)

    def get_fen(self):
        """Return the current position as a FEN string."""
        ranks = []
        for row in self.grid:
            s, empty = "", 0
            for piece in row:
                if piece == EMPTY:
                    empty += 1
                else:
                    if empty:
                        s += str(empty)
                        empty = 0
                    s += piece
            if empty:
                s += str(empty)
            ranks.append(s)
        return (
            f"{'/'.join(ranks)} {self.side_to_move} {self.castling} "
            f"{self.en_passant or '-'} {self.halfmove_clock} {self.fullmove_number}"
        )

    # --- access ---

    def piece_at(self, square):
        row, col = square_to_coords(square)
        return self.grid[row][col]

    def set_piece(self, square, piece):
        if piece != EMPTY and piece not in VALID_PIECES:
            raise ValueError(f"Invalid piece: {piece!r}")
        row, col = square_to_coords(square)
        self.grid[row][col] = piece

    def pieces(self, color):
        """Yield (row, col, piece) for every piece of the given color."""
        for row in range(8):
            for col in range(8):
                piece = self.grid[row][col]
                if piece != EMPTY and color_of(piece) == color:
                    yield row, col, piece

    def find_king(self, color):
        """Return (row, col) of the king, or None if missing."""
        target = "K" if color == WHITE else "k"
        for row in range(8):
            for col in range(8):
                if self.grid[row][col] == target:
                    return row, col
        return None

    def copy(self):
        """Independent copy (used constantly by move generation and search)."""
        new = Board.__new__(Board)
        new.grid = [row[:] for row in self.grid]
        new.side_to_move = self.side_to_move
        new.castling = self.castling
        new.en_passant = self.en_passant
        new.halfmove_clock = self.halfmove_clock
        new.fullmove_number = self.fullmove_number
        return new

    # --- display ---

    def __str__(self):
        lines = []
        for row in range(8):
            lines.append(f"{8 - row}  " + " ".join(self.grid[row]))
        lines.append("")
        lines.append("   a b c d e f g h")
        return "\n".join(lines)


# ---------- quick self-test ----------

if __name__ == "__main__":
    b = Board()
    print(b)
    print()
    print("Side to move:", b.side_to_move)
    print("FEN:", b.get_fen())

    # FEN round trip
    assert b.get_fen() == START_FEN

    # Piece lookups
    assert b.piece_at("e1") == "K"
    assert b.piece_at("d8") == "q"
    assert b.piece_at("e4") == EMPTY
    assert b.find_king(WHITE) == (7, 4)
    assert b.find_king(BLACK) == (0, 4)

    # Coordinate helpers
    assert square_to_coords("a8") == (0, 0)
    assert square_to_coords("h1") == (7, 7)
    assert coords_to_square(4, 4) == "e4"

    # Counting pieces
    assert len(list(b.pieces(WHITE))) == 16
    assert len(list(b.pieces(BLACK))) == 16

    # Custom position (after 1.e4 c5)
    b2 = Board("rnbqkbnr/pp1ppppp/8/2p5/4P3/8/PPPP1PPP/RNBQKBNR w KQkq c6 0 2")
    assert b2.piece_at("e4") == "P"
    assert b2.piece_at("c5") == "p"
    assert b2.en_passant == "c6"
    assert b2.get_fen() == "rnbqkbnr/pp1ppppp/8/2p5/4P3/8/PPPP1PPP/RNBQKBNR w KQkq c6 0 2"

    # Copy is independent
    c = b.copy()
    c.set_piece("e2", EMPTY)
    assert b.piece_at("e2") == "P"

    print("\nAll tests passed.")
