"""
play.py - Step 3: A playable game.

Run:  python play.py

A "player" is just a function that takes a Board and returns a Move
(or None to quit). That means the human, the random bot, and later our
real engine are all interchangeable.
"""

import random
from board import Board, WHITE, BLACK
from moves import legal_moves, make_move, parse_move, in_check, opponent
from evaluate import evaluate
from search import make_engine


# ---------- players ----------

def random_bot(board):
    """Picks any legal move at random."""
    return random.choice(legal_moves(board))


def greedy_bot(board):
    """
    Looks exactly one move ahead: plays whichever legal move leaves the
    best evaluation for itself. Takes checkmate when it sees it.
    It can't see replies, so it happily walks into recaptures.
    """
    moves = legal_moves(board)
    random.shuffle(moves)  # so equal moves aren't always picked in the same order
    best_move, best_score = None, -10**9
    for move in moves:
        nb = make_move(board, move)
        if not legal_moves(nb):
            score = 100000 if in_check(nb) else 0  # mate / stalemate
        else:
            score = -evaluate(nb)  # evaluate() is from the opponent's view
        if score > best_score:
            best_move, best_score = move, score
    return best_move


def human_player(board):
    """Asks the user for a move in text form, e.g. e2e4 or e7e8q."""
    while True:
        text = input("Your move (e.g. e2e4 | 'moves' | 'quit'): ").strip().lower()
        if text in ("quit", "q", "exit"):
            return None
        if text == "moves":
            print(" ".join(str(m) for m in legal_moves(board)))
            continue
        move = parse_move(board, text)
        if move is None and len(text) == 4:
            move = parse_move(board, text + "q")  # promotion defaults to queen
        if move:
            return move
        print("That's not a legal move. Type 'moves' to see the legal ones.")


# ---------- display ----------

def show(board, perspective=WHITE):
    """Print the board from the given side's point of view."""
    white = perspective == WHITE
    rows = range(8) if white else range(7, -1, -1)
    cols = range(8) if white else range(7, -1, -1)
    for r in rows:
        print(f"{8 - r}  " + " ".join(board.grid[r][c] for c in cols))
    print("\n   " + " ".join("abcdefgh" if white else "hgfedcba"))


# ---------- game loop ----------

def game_result(board):
    """Return a result string if the game is over, else None."""
    if not legal_moves(board):
        if in_check(board):
            winner = "White" if opponent(board.side_to_move) == WHITE else "Black"
            return f"Checkmate! {winner} wins."
        return "Stalemate. It's a draw."
    if board.halfmove_clock >= 100:
        return "Draw by the 50-move rule."
    return None


def play(white_player, black_player, perspective=WHITE, verbose=True, max_plies=1000):
    """Play one game. Returns the result string."""
    board = Board()
    players = {WHITE: white_player, BLACK: black_player}

    for _ in range(max_plies):
        if verbose:
            print()
            show(board, perspective)
            print()

        result = game_result(board)
        if result:
            if verbose:
                print(result)
            return result

        if verbose and in_check(board):
            print("Check!")

        mover = board.side_to_move
        move = players[mover](board)
        if move is None:
            if verbose:
                print("Game abandoned.")
            return "Abandoned"

        if verbose:
            print(f"{'White' if mover == WHITE else 'Black'} plays {move}")
        board = make_move(board, move)

    return "Stopped (too many moves)"


if __name__ == "__main__":
    choice = ""
    while choice not in ("w", "b"):
        choice = input("Play as White or Black? (w/b): ").strip().lower()

    level = ""
    while level not in ("1", "2", "3"):
        level = input("Opponent: 1 = random bot, 2 = greedy bot, 3 = search engine: ").strip()

    if level == "1":
        bot = random_bot
    elif level == "2":
        bot = greedy_bot
    else:
        seconds = 0
        while seconds <= 0:
            text = input("Thinking time per move in seconds (e.g. 2): ").strip()
            try:
                seconds = float(text)
            except ValueError:
                seconds = 0
        bot = make_engine(max_depth=8, time_limit=seconds)

    if choice == "w":
        play(human_player, bot, perspective=WHITE)
    else:
        play(bot, human_player, perspective=BLACK)
