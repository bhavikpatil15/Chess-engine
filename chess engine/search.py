"""
search.py - Steps 5 and 6: Looking ahead, faster and smarter.

Step 5 gave us negamax + alpha-beta. Step 6 adds four upgrades:

1. MOVE ORDERING. Alpha-beta prunes best when good moves are tried first.
   We try the remembered best move, then captures (most valuable victim,
   least valuable attacker first), then promotions, then quiet moves.

2. QUIESCENCE SEARCH. At depth 0 we don't just call evaluate(): if a
   capture is available we keep searching captures until things calm down.
   This fixes the "horizon problem" (e.g. queen takes a defended pawn,
   and the search stops before it sees the recapture).

3. ITERATIVE DEEPENING. Search depth 1, then 2, then 3... until we run
   out of time. The result of each depth feeds move ordering for the next,
   and we always have a best move ready if time runs out.

4. TRANSPOSITION TABLE. Different move orders reach the same position
   ("transpositions"). We remember each searched position's score and best
   move in a dictionary so we never search the same position twice at the
   same depth.

Scores are in centipawns from the side-to-move's point of view.
"""

import random
import time
from collections import namedtuple

from board import EMPTY
from moves import (
    pseudo_legal_moves, legal_moves, make_move,
    in_check, is_square_attacked, opponent,
)
from evaluate import evaluate, VALUES

MATE = 100000          # checkmate score; faster mates score slightly higher
INF = MATE + 1000
EXACT, LOWER, UPPER = 0, 1, 2   # transposition table bound types
TT_MAX = 400_000                # clear the table if it grows beyond this

SearchResult = namedtuple("SearchResult", "move score nodes depth")


class TimeUp(Exception):
    """Raised inside the search when the time limit is reached."""


class Stats:
    def __init__(self, deadline=None, should_stop=None):
        self.nodes = 0
        self.deadline = deadline
        self.should_stop = should_stop


def _tick(stats):
    stats.nodes += 1
    if (stats.nodes & 1023) == 0:
        if stats.deadline is not None and time.time() > stats.deadline:
            raise TimeUp
        if stats.should_stop is not None and stats.should_stop():
            raise TimeUp


# ---------- helpers ----------

def position_key(board):
    """Hashable identity of a position (pieces, side, castling, en passant)."""
    return ("".join("".join(row) for row in board.grid),
            board.side_to_move, board.castling, board.en_passant)


def is_capture(board, move):
    fr, fc = move.frm
    tr, tc = move.to
    if board.grid[tr][tc] != EMPTY:
        return True
    return board.grid[fr][fc] in "Pp" and fc != tc   # en passant


def _move_score(board, move, tt_move):
    if tt_move is not None and move == tt_move:
        return 1_000_000
    score = 0
    if is_capture(board, move):
        victim = board.grid[move.to[0]][move.to[1]]
        victim_value = VALUES[victim.upper()] if victim != EMPTY else 100  # en passant = pawn
        attacker_value = VALUES[board.grid[move.frm[0]][move.frm[1]].upper()]
        score += 10_000 + 10 * victim_value - attacker_value   # MVV-LVA
    if move.promotion:
        score += VALUES[move.promotion.upper()]
    return score


def order_moves(board, moves, tt_move=None):
    return sorted(moves, key=lambda m: _move_score(board, m, tt_move), reverse=True)


# Mate scores depend on distance from the root, so when storing them in the
# table we make them relative to the stored position, and convert back on use.
def _to_tt(score, ply):
    if score > MATE - 1000:
        return score + ply
    if score < -MATE + 1000:
        return score - ply
    return score


def _from_tt(score, ply):
    if score > MATE - 1000:
        return score - ply
    if score < -MATE + 1000:
        return score + ply
    return score


# ---------- quiescence search ----------

def quiescence(board, alpha, beta, ply, stats):
    """Keep searching captures (and check evasions) until the position is quiet."""
    _tick(stats)
    color = board.side_to_move
    enemy = opponent(color)

    checked = in_check(board)
    if checked:
        # Can't "stand pat" while in check: we must look at every evasion.
        candidates = pseudo_legal_moves(board)
        best = -INF
    else:
        stand_pat = evaluate(board)   # option: just stop capturing here
        if stand_pat >= beta:
            return stand_pat
        if stand_pat > alpha:
            alpha = stand_pat
        best = stand_pat
        candidates = [m for m in pseudo_legal_moves(board)
                      if is_capture(board, m) or m.promotion == "q"]

    legal = 0
    for move in order_moves(board, candidates):
        nb = make_move(board, move)
        king = nb.find_king(color)
        if king is not None and is_square_attacked(nb, king[0], king[1], enemy):
            continue
        legal += 1
        score = -quiescence(nb, -beta, -alpha, ply + 1, stats)
        if score > best:
            best = score
        if best > alpha:
            alpha = best
        if alpha >= beta:
            break

    if checked and legal == 0:
        return -MATE + ply       # checkmated
    return best


# ---------- main search ----------

def negamax(board, depth, alpha, beta, ply, stats, tt):
    if depth <= 0:
        return quiescence(board, alpha, beta, ply, stats)
    _tick(stats)

    alpha_orig = alpha
    key = position_key(board) if tt is not None else None
    tt_move = None

    if tt is not None:
        entry = tt.get(key)
        if entry is not None:
            e_depth, e_flag, e_score, tt_move = entry
            if e_depth >= depth:
                e_score = _from_tt(e_score, ply)
                if e_flag == EXACT:
                    return e_score
                if e_flag == LOWER:
                    alpha = max(alpha, e_score)
                else:
                    beta = min(beta, e_score)
                if alpha >= beta:
                    return e_score

    color = board.side_to_move
    enemy = opponent(color)
    best, best_move, legal = -INF, None, 0

    for move in order_moves(board, pseudo_legal_moves(board), tt_move):
        nb = make_move(board, move)
        king = nb.find_king(color)
        if king is not None and is_square_attacked(nb, king[0], king[1], enemy):
            continue    # illegal: leaves our king in check
        legal += 1
        score = -negamax(nb, depth - 1, -beta, -alpha, ply + 1, stats, tt)
        if score > best:
            best, best_move = score, move
        if best > alpha:
            alpha = best
        if alpha >= beta:
            break       # cutoff

    if legal == 0:
        return -MATE + ply if in_check(board) else 0   # mate or stalemate

    if tt is not None:
        flag = UPPER if best <= alpha_orig else (LOWER if best >= beta else EXACT)
        if len(tt) > TT_MAX:
            tt.clear()
        old = tt.get(key)
        if old is None or depth >= old[0]:
            tt[key] = (depth, flag, _to_tt(best, ply), best_move if flag != UPPER else None)
    return best


def _search_root(board, depth, stats, tt, first_move):
    moves = legal_moves(board)
    random.shuffle(moves)   # variety between equally good moves
    moves = order_moves(board, moves, first_move)

    best_move, alpha = None, -INF
    for move in moves:
        score = -negamax(make_move(board, move), depth - 1, -INF, -alpha, 1, stats, tt)
        if score > alpha or best_move is None:
            best_move, alpha = move, score
    return best_move, alpha


def get_pv_line(board, tt, max_plies=8):
    """Reconstruct the principal variation (predicted best line) from the transposition table."""
    if tt is None:
        return []
    pv = []
    curr = board.copy()
    seen = set()
    for _ in range(max_plies):
        key = position_key(curr)
        if key in seen:
            break
        seen.add(key)
        entry = tt.get(key)
        if entry is None or entry[3] is None:
            break
        move = entry[3]
        if move not in legal_moves(curr):
            break
        pv.append(str(move))
        curr = make_move(curr, move)
    return pv


def find_best_move(board, max_depth=4, time_limit=None, tt=None, should_stop=None):
    """
    Iterative deepening: search depth 1, 2, ... up to max_depth, stopping
    early if time_limit (seconds) runs out or should_stop() returns True.
    Returns a SearchResult with the best move from the last COMPLETED depth.
    """
    start = time.time()
    stats = Stats(start + time_limit if time_limit else None, should_stop)

    moves = legal_moves(board)
    if not moves:
        return SearchResult(None, 0, 0, 0)

    best_move, best_score, reached = moves[0], 0, 0
    for depth in range(1, max_depth + 1):
        if should_stop is not None and should_stop():
            break
        # Each depth takes several times longer than the last, so don't
        # start one we are unlikely to finish.
        if time_limit and depth > 1 and time.time() - start > time_limit * 0.4:
            break
        try:
            move, score = _search_root(board, depth, stats, tt, best_move)
        except TimeUp:
            break
        best_move, best_score, reached = move, score, depth
        if abs(score) > MATE - 100:
            break   # forced mate found; no point searching deeper
    return SearchResult(best_move, best_score, stats.nodes, reached)


def make_engine(max_depth=8, time_limit=2.0, verbose=True):
    """Build a player function (board -> Move). It keeps its table between moves."""
    tt = {}

    def engine(board):
        start = time.time()
        result = find_best_move(board, max_depth, time_limit, tt)
        if verbose:
            score = result.score
            if abs(score) > MATE - 100:
                n = (MATE - abs(score) + 1) // 2
                shown = f"mate in {n}" if score > 0 else f"getting mated in {n}"
            else:
                shown = f"{score / 100:+.2f}"
            print(f"  [engine: depth {result.depth}, eval {shown}, "
                  f"{result.nodes} nodes, {time.time() - start:.1f}s]")
        return result.move
    return engine


# ---------- quick self-test ----------

if __name__ == "__main__":
    from board import Board

    def best(fen, depth, **kw):
        return find_best_move(Board(fen), depth, **kw)

    # Mate in 1 (back rank): Ra8#
    r = best("6k1/5ppp/8/8/8/8/5PPP/R5K1 w - - 0 1", 2, tt={})
    print("Back-rank mate:", r.move, r.score)
    assert str(r.move) == "a1a8" and r.score == MATE - 1

    # Scholar's mate: Qxf7#
    r = best("r1bqkb1r/pppp1ppp/2n2n2/4p2Q/2B1P3/8/PPPP1PPP/RNB1K1NR w KQkq - 4 4", 2, tt={})
    print("Scholar's mate:", r.move, r.score)
    assert str(r.move) == "h5f7" and r.score == MATE - 1

    # Mate in 2 (two rooks): Ra7 (or Rb7) then Rb8# / Ra8#
    r = best("7k/8/8/8/8/8/R7/1R4K1 w - - 0 1", 4, tt={})
    print("Mate in 2:", r.move, r.score)
    assert r.score == MATE - 3

    # Horizon problem: even at depth 1, quiescence sees the recapture
    # and refuses to play Qxd5 (the d5 pawn is defended).
    poisoned = "rnbqkb1r/ppp2ppp/4pn2/3p4/3P4/2N2Q2/PPP1PPPP/R1B1KBNR w KQkq - 0 4"
    r = best(poisoned, 1, tt={})
    print("Poisoned pawn at depth 1, engine plays:", r.move)
    assert str(r.move) != "f3d5"

    # Effect of the transposition table on a busy middlegame position
    kiwi = "r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1"
    for label, table in (("without table", None), ("with table   ", {})):
        t = time.time()
        r = best(kiwi, 4, tt=table)
        print(f"Depth 4 {label}: {r.nodes:>7} nodes, {time.time() - t:.1f}s, best {r.move}")

    # Time-limited iterative deepening
    t = time.time()
    r = best(kiwi, 12, time_limit=2.0, tt={})
    print(f"2-second limit: reached depth {r.depth}, took {time.time() - t:.1f}s, best {r.move}")
    assert time.time() - t < 3.5

    print("All search tests passed.")
