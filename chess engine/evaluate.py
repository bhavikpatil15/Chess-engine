"""
evaluate.py - Step 4: Evaluation function.

evaluate(board) returns a score in "centipawns" (100 = one pawn) from the
point of view of the SIDE TO MOVE: positive means the player to move is
better, negative means worse. This convention makes the search in step 5
(negamax) much simpler.

The score has two parts:
  1. Material: pawn 100, knight 320, bishop 330, rook 500, queen 900.
  2. Piece-square tables: a small bonus/penalty depending on WHERE a piece
     stands (knights love the centre, rooks like the 7th rank, kings should
     hide early on and come out in the endgame).

The tables are the well-known "Simplified Evaluation Function" values,
written from White's point of view with the top row = rank 8, which matches
our board.grid layout. For Black pieces we mirror the row.
"""

from board import EMPTY, WHITE, BLACK

VALUES = {"P": 100, "N": 320, "B": 330, "R": 500, "Q": 900, "K": 0}

PAWN = [
     0,  0,  0,  0,  0,  0,  0,  0,
    50, 50, 50, 50, 50, 50, 50, 50,
    10, 10, 20, 30, 30, 20, 10, 10,
     5,  5, 10, 25, 25, 10,  5,  5,
     0,  0,  0, 20, 20,  0,  0,  0,
     5, -5,-10,  0,  0,-10, -5,  5,
     5, 10, 10,-20,-20, 10, 10,  5,
     0,  0,  0,  0,  0,  0,  0,  0,
]

KNIGHT = [
   -50,-40,-30,-30,-30,-30,-40,-50,
   -40,-20,  0,  0,  0,  0,-20,-40,
   -30,  0, 10, 15, 15, 10,  0,-30,
   -30,  5, 15, 20, 20, 15,  5,-30,
   -30,  0, 15, 20, 20, 15,  0,-30,
   -30,  5, 10, 15, 15, 10,  5,-30,
   -40,-20,  0,  5,  5,  0,-20,-40,
   -50,-40,-30,-30,-30,-30,-40,-50,
]

BISHOP = [
   -20,-10,-10,-10,-10,-10,-10,-20,
   -10,  0,  0,  0,  0,  0,  0,-10,
   -10,  0,  5, 10, 10,  5,  0,-10,
   -10,  5,  5, 10, 10,  5,  5,-10,
   -10,  0, 10, 10, 10, 10,  0,-10,
   -10, 10, 10, 10, 10, 10, 10,-10,
   -10,  5,  0,  0,  0,  0,  5,-10,
   -20,-10,-10,-10,-10,-10,-10,-20,
]

ROOK = [
     0,  0,  0,  0,  0,  0,  0,  0,
     5, 10, 10, 10, 10, 10, 10,  5,
    -5,  0,  0,  0,  0,  0,  0, -5,
    -5,  0,  0,  0,  0,  0,  0, -5,
    -5,  0,  0,  0,  0,  0,  0, -5,
    -5,  0,  0,  0,  0,  0,  0, -5,
    -5,  0,  0,  0,  0,  0,  0, -5,
     0,  0,  0,  5,  5,  0,  0,  0,
]

QUEEN = [
   -20,-10,-10, -5, -5,-10,-10,-20,
   -10,  0,  0,  0,  0,  0,  0,-10,
   -10,  0,  5,  5,  5,  5,  0,-10,
    -5,  0,  5,  5,  5,  5,  0, -5,
     0,  0,  5,  5,  5,  5,  0, -5,
   -10,  5,  5,  5,  5,  5,  0,-10,
   -10,  0,  5,  0,  0,  0,  0,-10,
   -20,-10,-10, -5, -5,-10,-10,-20,
]

KING_MIDDLEGAME = [
   -30,-40,-40,-50,-50,-40,-40,-30,
   -30,-40,-40,-50,-50,-40,-40,-30,
   -30,-40,-40,-50,-50,-40,-40,-30,
   -30,-40,-40,-50,-50,-40,-40,-30,
   -20,-30,-30,-40,-40,-30,-30,-20,
   -10,-20,-20,-20,-20,-20,-20,-10,
    20, 20,  0,  0,  0,  0, 20, 20,
    20, 30, 10,  0,  0, 10, 30, 20,
]

KING_ENDGAME = [
   -50,-40,-30,-20,-20,-30,-40,-50,
   -30,-20,-10,  0,  0,-10,-20,-30,
   -30,-10, 20, 30, 30, 20,-10,-30,
   -30,-10, 30, 40, 40, 30,-10,-30,
   -30,-10, 30, 40, 40, 30,-10,-30,
   -30,-10, 20, 30, 30, 20,-10,-30,
   -30,-30,  0,  0,  0,  0,-30,-30,
   -50,-30,-30,-30,-30,-30,-30,-50,
]

TABLES = {"P": PAWN, "N": KNIGHT, "B": BISHOP, "R": ROOK, "Q": QUEEN}


def is_endgame(board):
    """
    Endgame if no side that still has a queen also has a rook or
    more than one minor piece. (So: no queens at all counts as endgame.)
    """
    for color in (WHITE, BLACK):
        queens = rooks = minors = 0
        for _, _, piece in board.pieces(color):
            kind = piece.upper()
            if kind == "Q":
                queens += 1
            elif kind == "R":
                rooks += 1
            elif kind in "NB":
                minors += 1
        if queens and (rooks or minors > 1):
            return False
    return True


def evaluate(board):
    """Score the position, from the side-to-move's point of view."""
    endgame = is_endgame(board)
    king_table = KING_ENDGAME if endgame else KING_MIDDLEGAME
    score = 0  # from White's point of view while we add things up

    for row in range(8):
        for col in range(8):
            piece = board.grid[row][col]
            if piece == EMPTY:
                continue
            kind = piece.upper()
            table = king_table if kind == "K" else TABLES[kind]
            if piece.isupper():
                score += VALUES[kind] + table[row * 8 + col]
            else:
                score -= VALUES[kind] + table[(7 - row) * 8 + col]

    return score if board.side_to_move == WHITE else -score


# ---------- quick self-test ----------

def _mirror_fen(fen):
    """Swap colours and flip the board vertically (for symmetry testing)."""
    placement, side, castling, ep, half, full = fen.split()
    ranks = [r.swapcase() for r in reversed(placement.split("/"))]
    side = "b" if side == "w" else "w"
    castling = "".join(sorted(castling.swapcase(), key=lambda c: "KQkq".find(c))) if castling != "-" else "-"
    if ep != "-":
        ep = ep[0] + str(9 - int(ep[1]))
    return f"{'/'.join(ranks)} {side} {castling} {ep} {half} {full}"


if __name__ == "__main__":
    from board import Board, START_FEN

    # Start position is perfectly balanced
    assert evaluate(Board()) == 0

    # Remove Black's queen: White (to move) should be ahead by about a queen
    no_black_queen = Board("rnb1kbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1")
    print("White up a queen:", evaluate(no_black_queen))
    assert evaluate(no_black_queen) > 800

    # Same position, but Black to move: score flips sign (side-to-move view)
    no_black_queen.side_to_move = BLACK
    assert evaluate(no_black_queen) < -800

    # Centralised knight beats a rim knight
    centre = Board("4k3/8/8/8/3N4/8/8/4K3 w - - 0 1")
    rim = Board("4k3/8/8/8/8/8/8/N3K3 w - - 0 1")
    print("Knight on d4:", evaluate(centre), "| knight on a1:", evaluate(rim))
    assert evaluate(centre) > evaluate(rim)

    # Symmetry: mirroring colours must give the same score
    for fen in [
        START_FEN,
        "r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1",
        "8/2p5/3p4/KP5r/1R3p1k/8/4P1P1/8 w - - 0 1",
        "r3k2r/Pppp1ppp/1b3nbN/nP6/BBP1P3/q4N2/Pp1P2PP/R2Q1RK1 w kq - 0 1",
    ]:
        assert evaluate(Board(fen)) == evaluate(Board(_mirror_fen(fen))), fen

    print("All evaluation tests passed.")
