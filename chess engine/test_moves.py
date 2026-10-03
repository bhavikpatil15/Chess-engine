"""
test_moves.py - Verifies move generation using perft.

Perft counts every position reachable in N moves. The correct numbers for
well-known test positions are published, so if ours match, move generation
is almost certainly right (castling, en passant, promotion and pins included).
"""

import time
from board import Board
from moves import perft, legal_moves, game_status

# (name, FEN, [expected counts for depth 1, 2, 3, ...])
TESTS = [
    ("Start position",
     "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
     [20, 400, 8902]),
    ("Kiwipete (castling, pins, captures)",
     "r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1",
     [48, 2039, 97862]),
    ("Endgame (en passant, discovered checks)",
     "8/2p5/3p4/KP5r/1R3p1k/8/4P1P1/8 w - - 0 1",
     [14, 191, 2812, 43238]),
    ("Promotions and castling rights",
     "r3k2r/Pppp1ppp/1b3nbN/nP6/BBP1P3/q4N2/Pp1P2PP/R2Q1RK1 w kq - 0 1",
     [6, 264, 9467]),
    ("Mixed middlegame",
     "rnbq1k1r/pp1Pbppp/2p5/8/2B5/8/PPP1NnPP/RNBQK2R w KQ - 1 8",
     [44, 1486, 62379]),
]

if __name__ == "__main__":
    all_ok = True
    for name, fen, expected in TESTS:
        print(name)
        board = Board(fen)
        for depth, want in enumerate(expected, start=1):
            t = time.time()
            got = perft(board, depth)
            ok = got == want
            all_ok &= ok
            print(f"  depth {depth}: {got:>7} (expected {want:>7})  "
                  f"{'OK' if ok else 'MISMATCH'}  [{time.time() - t:.1f}s]")

    # Game status checks
    assert game_status(Board("rnb1kbnr/pppp1ppp/8/4p3/6Pq/5P2/PPPPP2P/RNBQKBNR w KQkq - 1 3")) == "checkmate"
    assert game_status(Board("7k/5Q2/6K1/8/8/8/8/8 b - - 0 1")) == "stalemate"
    assert game_status(Board()) == "ongoing"
    print("\nGame status checks OK")

    print("\nALL PASSED" if all_ok else "\nSOME TESTS FAILED")
