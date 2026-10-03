# ♟️ Python Chess Engine

A fully functional chess engine written from scratch in pure Python — no chess libraries, no external dependencies. Comes with both a **command-line interface** and a **modern browser-based UI** powered by a lightweight built-in web server.

---

## 🚀 Features

| Category | Details |
|---|---|
| **Board Representation** | FEN import/export, algebraic notation helpers, full copy-on-write state |
| **Move Generation** | Pseudo-legal + legal move pipeline, castling, en passant, promotions, perft testing |
| **Evaluation** | Material scoring + piece-square tables (Simplified Evaluation Function), middlegame/endgame king tables |
| **Search** | Negamax with alpha-beta pruning, iterative deepening, quiescence search, transposition table (400k entries), MVV-LVA move ordering |
| **Players** | Human (CLI), random bot, greedy (1-ply) bot, full search engine |
| **Web UI** | Interactive chessboard in the browser, engine analysis panel, move history, FEN input |

---

## 🏗️ Architecture

```
chess engine/
│
├── board.py        # Step 1 — Board state, FEN parsing, coordinate helpers
├── moves.py        # Step 2 — Move generation, make_move, legal_moves, perft
├── evaluate.py     # Step 4 — Material + piece-square table evaluation
├── search.py       # Steps 5 & 6 — Negamax, alpha-beta, quiescence, iterative deepening, TT
│
├── play.py         # Step 3 — CLI game loop, human / bot / engine players
├── gui_new.py      # Pygame-based GUI (alternative frontend)
├── server.py       # HTTP backend server (REST API for the web UI)
│
├── web/
│   ├── index.html  # Browser chessboard UI
│   ├── app.js      # Board logic, API calls, move animation
│   ├── pieces.js   # SVG chess piece rendering
│   ├── sound.js    # Move / capture sound effects
│   └── style.css   # UI styling
│
└── test_moves.py   # Move generation tests
```

---

## ⚙️ How It Works

### 1. Board (`board.py`)
- 8×8 grid of characters: uppercase = White (`PNBRQK`), lowercase = Black (`pnbrqk`), `'.'` = empty
- `row 0` = rank 8 (Black's back rank), `row 7` = rank 1 — matches standard FEN order
- Full FEN read/write with castling rights, en passant square, half-move clock

### 2. Move Generation (`moves.py`)
- **Pseudo-legal** moves generated for all piece types including sliders (bishop, rook, queen)
- **Legality filter** — each pseudo-legal move is played on a copy; if the king is left in check it's discarded
- Fully handles castling (checks transit squares) and en passant captures

### 3. Evaluation (`evaluate.py`)
- **Material values**: P=100, N=320, B=330, R=500, Q=900 centipawns
- **Piece-square tables**: knights prefer the centre, rooks like the 7th rank, kings hide in the middlegame and centralise in the endgame
- Score always returned from the **side-to-move's** perspective (positive = better for the mover)

### 4. Search (`search.py`)

```
Negamax + Alpha-Beta
  └── Iterative Deepening (depth 1 → max_depth)
        └── Quiescence Search (at leaf nodes, keep searching captures)
              └── Transposition Table (cache results by position hash)
```

- **Move ordering**: TT best move → MVV-LVA captures → promotions → quiet moves — greatly improves pruning
- **Quiescence search**: solves the horizon problem by extending search on captures and check evasions until the position is quiet
- **Transposition table**: stores `(depth, flag, score, best_move)` per position; cleared when it exceeds 400k entries
- **Forced mate detection**: search terminates early once a forced mate is found

---

## 🖥️ Getting Started

### Prerequisites

- Python 3.9+
- No third-party packages required for the core engine or web UI

```bash
# Optional: for the Pygame GUI only
pip install pygame
```

### Play in the Terminal

```bash
python play.py
```

You'll be asked to choose a side (White/Black) and an opponent:
- `1` — Random bot
- `2` — Greedy bot (1-ply lookahead)
- `3` — Search engine (configurable thinking time)

Moves are entered in **coordinate notation**, e.g. `e2e4`, `g1f3`, `e7e8q` (promotion).  
Type `moves` to see all legal moves, `quit` to exit.

### Play in the Browser

```bash
python server.py
# Open http://localhost:8080 in your browser
```

The server auto-selects an available port (8080–8129) and serves the `web/` UI.

**REST API endpoints:**

| Endpoint | Method | Description |
|---|---|---|
| `/api/state` | POST | Get board state (legal moves, check status) |
| `/api/make_move` | POST | Play a move, get new FEN + game status |
| `/api/engine_move` | POST | Let the engine pick and play a move |
| `/api/analyze` | POST | Run analysis and return eval + PV line |
| `/api/legal_moves` | POST | List all legal moves for a FEN |

All endpoints accept/return JSON. Most take a `"fen"` field in the request body.

### Run Tests

```bash
python test_moves.py     # Move generation correctness
python board.py          # Board self-tests (FEN round-trip, piece lookups)
python evaluate.py       # Evaluation symmetry tests
python search.py         # Mate-in-1, mate-in-2, horizon problem, TT benchmarks
```

---

## 🧠 Search Algorithm Deep Dive

```
find_best_move(board, max_depth=8, time_limit=2.0)
  │
  ├── for depth in 1..max_depth:            ← Iterative Deepening
  │     _search_root(board, depth)
  │       ├── order_moves(board, moves, tt_move)   ← Move Ordering
  │       └── for each move:
  │             negamax(child, depth-1, -β, -α)    ← Alpha-Beta
  │               ├── check TT cache               ← Transposition Table
  │               ├── if depth == 0:
  │               │     quiescence(board, α, β)    ← Quiescence Search
  │               └── update TT cache
  │
  └── return best move from last COMPLETED depth
```

On a modern laptop, the engine typically reaches **depth 6–8** within 2 seconds on a typical middlegame position.

---

## 📋 FEN Examples

```
Starting position:
rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1

After 1.e4 c5 (Sicilian Defence):
rnbqkbnr/pp1ppppp/8/2p5/4P3/8/PPPP1PPP/RNBQKBNR w KQkq c6 0 2

Kiwipete (popular search test position):
r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1
```

---

## 📄 License

MIT — free to use, modify, and distribute.

---

## 🙌 Acknowledgements

- Piece-square tables from the [Simplified Evaluation Function](https://www.chessprogramming.org/Simplified_Evaluation_Function) on the Chess Programming Wiki
- Perft test values from the [CPW Perft Results](https://www.chessprogramming.org/Perft_Results) page
