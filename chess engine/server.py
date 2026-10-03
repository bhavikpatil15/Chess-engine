"""
server.py - High-performance backend web server for Modern Chess Engine Analysis UI.
Zero external dependencies: uses Python standard library http.server and threading.
"""

import json
import os
import socket
import sys
import threading
import time
from http import HTTPStatus
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse

from board import Board, WHITE, BLACK, START_FEN, coords_to_square, square_to_coords, EMPTY
from moves import legal_moves, make_move, parse_move, in_check, game_status, opponent
from search import find_best_move, get_pv_line, MATE

WEB_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "web")


def format_eval(score, side_to_move):
    """Format evaluation centipawns or mate from White's perspective."""
    if abs(score) > MATE - 100:
        moves_to_mate = (MATE - abs(score) + 1) // 2
        # score > 0 means the side_to_move is winning
        winning_side = side_to_move if score > 0 else opponent(side_to_move)
        label = "White" if winning_side == WHITE else "Black"
        return {
            "type": "mate",
            "score": score,
            "white_score": score if side_to_move == WHITE else -score,
            "text": f"M{moves_to_mate}" if winning_side == WHITE else f"-M{moves_to_mate}",
            "desc": f"Mate in {moves_to_mate} ({label})"
        }
    white_score = score if side_to_move == WHITE else -score
    eval_num = white_score / 100.0
    return {
        "type": "cp",
        "score": score,
        "white_score": white_score,
        "text": f"{eval_num:+.2f}",
        "desc": f"{eval_num:+.2f}"
    }


class AnalysisManager:
    """Coordinates search threads and cancellation across requests."""
    def __init__(self):
        self.lock = threading.Lock()
        self.current_id = 0
        self.shared_tt = {}

    def new_token(self):
        with self.lock:
            self.current_id += 1
            return self.current_id

    def is_cancelled(self, token):
        with self.lock:
            return token != self.current_id


manager = AnalysisManager()


class ChessRequestHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=WEB_DIR, **kwargs)

    def end_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Cache-Control", "no-cache, no-store, must-revalidate")
        super().end_headers()

    def do_OPTIONS(self):
        self.send_response(HTTPStatus.NO_CONTENT)
        self.end_headers()

    def _send_json(self, data, status=HTTPStatus.OK):
        body = json.dumps(data).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _read_json(self):
        length = int(self.headers.get("Content-Length", 0))
        if not length:
            return {}
        try:
            return json.loads(self.rfile.read(length).decode("utf-8"))
        except Exception:
            return {}

    def do_POST(self):
        parsed = urlparse(self.path)
        path = parsed.path.rstrip("/")

        if path == "/api/legal_moves":
            self.handle_legal_moves()
        elif path == "/api/make_move":
            self.handle_make_move()
        elif path == "/api/analyze":
            self.handle_analyze()
        elif path == "/api/engine_move":
            self.handle_engine_move()
        elif path == "/api/state":
            self.handle_state()
        else:
            self.send_error(HTTPStatus.NOT_FOUND, "API endpoint not found")

    def handle_state(self):
        payload = self._read_json()
        fen = payload.get("fen", START_FEN)
        try:
            board = Board(fen)
            moves = [str(m) for m in legal_moves(board)]
            checked = in_check(board)
            status = game_status(board)
            king_sq = coords_to_square(*board.find_king(board.side_to_move)) if board.find_king(board.side_to_move) else None
            self._send_json({
                "fen": board.get_fen(),
                "side_to_move": board.side_to_move,
                "in_check": checked,
                "king_square": king_sq if checked else None,
                "status": status,
                "legal_moves": moves
            })
        except Exception as e:
            self._send_json({"error": str(e)}, status=HTTPStatus.BAD_REQUEST)

    def handle_legal_moves(self):
        payload = self._read_json()
        fen = payload.get("fen", START_FEN)
        try:
            board = Board(fen)
            moves = [str(m) for m in legal_moves(board)]
            checked = in_check(board)
            status = game_status(board)
            king_pos = board.find_king(board.side_to_move)
            king_sq = coords_to_square(*king_pos) if (checked and king_pos) else None
            self._send_json({
                "fen": board.get_fen(),
                "side_to_move": board.side_to_move,
                "legal_moves": moves,
                "in_check": checked,
                "check_square": king_sq,
                "status": status
            })
        except Exception as e:
            self._send_json({"error": str(e)}, status=HTTPStatus.BAD_REQUEST)

    def handle_make_move(self):
        payload = self._read_json()
        fen = payload.get("fen", START_FEN)
        move_str = payload.get("move", "").strip().lower()

        try:
            board = Board(fen)
            move = parse_move(board, move_str)
            if move is None and len(move_str) == 4:
                move = parse_move(board, move_str + "q")

            if move is None:
                self._send_json({"error": f"Illegal move: {move_str}"}, status=HTTPStatus.BAD_REQUEST)
                return

            # Capture details before moving
            captured = board.piece_at(coords_to_square(*move.to))
            is_capture_move = captured != EMPTY or (board.piece_at(coords_to_square(*move.frm)).upper() == "P" and move.frm[1] != move.to[1])

            new_board = make_move(board, move)
            checked = in_check(new_board)
            status = game_status(new_board)
            king_pos = new_board.find_king(new_board.side_to_move)
            king_sq = coords_to_square(*king_pos) if (checked and king_pos) else None

            self._send_json({
                "success": True,
                "move": str(move),
                "frm": coords_to_square(*move.frm),
                "to": coords_to_square(*move.to),
                "promotion": move.promotion,
                "is_capture": is_capture_move,
                "new_fen": new_board.get_fen(),
                "side_to_move": new_board.side_to_move,
                "in_check": checked,
                "check_square": king_sq,
                "status": status
            })
        except Exception as e:
            self._send_json({"error": str(e)}, status=HTTPStatus.BAD_REQUEST)

    def handle_analyze(self):
        payload = self._read_json()
        fen = payload.get("fen", START_FEN)
        max_depth = int(payload.get("depth", 6))
        time_limit = float(payload.get("time_limit", 2.0))

        token = manager.new_token()
        try:
            board = Board(fen)
            start_t = time.time()
            res = find_best_move(
                board,
                max_depth=max_depth,
                time_limit=time_limit,
                tt=manager.shared_tt,
                should_stop=lambda: manager.is_cancelled(token)
            )
            elapsed = max(0.001, time.time() - start_t)
            nps = int(res.nodes / elapsed)
            eval_info = format_eval(res.score, board.side_to_move)
            pv = get_pv_line(board, manager.shared_tt, max_plies=8)
            if not pv and res.move:
                pv = [str(res.move)]

            self._send_json({
                "cancelled": manager.is_cancelled(token),
                "best_move": str(res.move) if res.move else None,
                "score": res.score,
                "eval": eval_info,
                "depth": res.depth,
                "max_depth": max_depth,
                "nodes": res.nodes,
                "time_sec": round(elapsed, 3),
                "nps": nps,
                "pv": pv,
                "side_to_move": board.side_to_move
            })
        except Exception as e:
            self._send_json({"error": str(e)}, status=HTTPStatus.BAD_REQUEST)

    def handle_engine_move(self):
        payload = self._read_json()
        fen = payload.get("fen", START_FEN)
        depth = int(payload.get("depth", 6))
        time_limit = float(payload.get("time_limit", 2.0))

        token = manager.new_token()
        try:
            board = Board(fen)
            start_t = time.time()
            res = find_best_move(
                board,
                max_depth=depth,
                time_limit=time_limit,
                tt=manager.shared_tt,
                should_stop=lambda: manager.is_cancelled(token)
            )
            if not res.move:
                self._send_json({"error": "No legal moves available"}, status=HTTPStatus.BAD_REQUEST)
                return

            new_board = make_move(board, res.move)
            elapsed = max(0.001, time.time() - start_t)
            eval_info = format_eval(res.score, board.side_to_move)
            checked = in_check(new_board)
            status = game_status(new_board)
            king_pos = new_board.find_king(new_board.side_to_move)

            self._send_json({
                "move": str(res.move),
                "frm": coords_to_square(*res.move.frm),
                "to": coords_to_square(*res.move.to),
                "promotion": res.move.promotion,
                "new_fen": new_board.get_fen(),
                "eval": eval_info,
                "depth": res.depth,
                "nodes": res.nodes,
                "time_sec": round(elapsed, 3),
                "in_check": checked,
                "check_square": coords_to_square(*king_pos) if (checked and king_pos) else None,
                "status": status
            })
        except Exception as e:
            self._send_json({"error": str(e)}, status=HTTPStatus.BAD_REQUEST)


def find_free_port(start_port=8080):
    for port in range(start_port, start_port + 50):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            if s.connect_ex(("127.0.0.1", port)) != 0:
                return port
    return start_port


def run_server(port=None):
    if port is None:
        port = find_free_port(8080)
    server_address = ("127.0.0.1", port)
    httpd = ThreadingHTTPServer(server_address, ChessRequestHandler)
    print(f"\n========================================================")
    print(f"  Modern Chess Engine Analysis UI Server Running!")
    print(f"  URL: http://localhost:{port}")
    print(f"  Serving files from: {WEB_DIR}")
    print(f"  Press Ctrl+C to stop.")
    print(f"========================================================\n")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down server...")
        httpd.server_close()


if __name__ == "__main__":
    port_arg = int(sys.argv[1]) if len(sys.argv) > 1 else None
    run_server(port_arg)
