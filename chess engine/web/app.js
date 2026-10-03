// app.js - Controller for PyChess Studio (Modern Chess Engine Analysis UI)
// Fully wired to the custom Python chess engine backend

const START_FEN = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1";

class ChessApp {
  constructor() {
    this.boardEl = document.getElementById("chessboard");
    this.arrowLine = document.getElementById("engine-arrow-line");

    // Game State
    this.fen = START_FEN;
    this.orientation = "w"; // 'w' or 'b'
    this.mode = "play_white"; // 'play_white', 'play_black', 'analyze'
    this.history = []; // [{ fen, move, san, isCapture, eval }]
    this.historyIndex = 0;
    this.legalMoves = [];
    this.selectedSquare = null;
    this.pendingMove = null;
    this.lastMove = null;
    this.checkSquare = null;
    this.isGameOver = false;

    // Engine settings & telemetry
    this.engineDepth = 6;
    this.engineTime = 2.0;
    this.analysisAbortCtrl = null;
    this.currentAnalysis = null;
    this.isEngineThinking = false;

    // Clocks
    this.playerSeconds = 600;
    this.opponentSeconds = 600;
    this.clockInterval = null;

    this.initDOM();
    this.bindEvents();
    this.loadPosition(START_FEN, true);
    this.startClock();
  }

  initDOM() {
    // Top Snapshot Bar
    this.snapshotEval = document.getElementById("snapshot-eval");
    this.snapshotLead = document.getElementById("snapshot-lead");
    this.snapshotMove = document.getElementById("snapshot-move");
    this.snapshotDepth = document.getElementById("snapshot-depth");
    this.snapshotNodes = document.getElementById("snapshot-nodes");
    this.engineStatusDot = document.getElementById("engine-status-dot");
    this.engineStatusText = document.getElementById("engine-status-text");
    this.headerDepth = document.getElementById("header-depth-indicator");

    // Evaluation Bar
    this.evalBarFill = document.getElementById("eval-bar-fill");
    this.evalBarPill = document.getElementById("eval-bar-pill");

    // Placards & Clocks
    this.playerClock = document.getElementById("player-clock");
    this.opponentClock = document.getElementById("opponent-clock");
    this.playerTurnDot = document.getElementById("player-turn-dot");
    this.playerLabel = document.getElementById("player-color-label");
    this.opponentLabel = document.getElementById("opponent-color-label");

    // Telemetry & Candidates
    this.candBestMove = document.getElementById("cand-best-move");
    this.candBestScore = document.getElementById("cand-best-score");
    this.candPvText = document.getElementById("cand-pv-text");
    this.telemetrySpeed = document.getElementById("telemetry-speed");
    this.telemetryNodes = document.getElementById("telemetry-nodes");
    this.npsLiveBadge = document.getElementById("nps-live-badge");
    this.engineLatencyText = document.getElementById("engine-latency-text");
    this.movesTbody = document.getElementById("moves-tbody");

    // Controls
    this.sliderDepth = document.getElementById("strength-slider");
    this.sliderDepthLabel = document.getElementById("slider-depth-label");
    this.navModePlay = document.getElementById("nav-mode-play");
    this.navModeAnalyze = document.getElementById("nav-mode-analyze");
    this.toggleWhite = document.getElementById("toggle-white");
    this.toggleBlack = document.getElementById("toggle-black");

    // Modals
    this.promoModal = document.getElementById("promo-modal");
    this.fenModal = document.getElementById("fen-modal");
    this.fenInput = document.getElementById("fen-input-text");
  }

  bindEvents() {
    // Mode toggles
    this.navModePlay.addEventListener("click", () => this.setMode("play_white"));
    this.navModeAnalyze.addEventListener("click", () => this.setMode("analyze"));

    this.toggleWhite.addEventListener("click", () => this.setMode("play_white"));
    this.toggleBlack.addEventListener("click", () => this.setMode("play_black"));

    // Sliders
    this.sliderDepth.addEventListener("input", (e) => {
      this.engineDepth = parseInt(e.target.value);
      const labels = {
        1: "Depth 1 (Novice)",
        2: "Depth 2 (Novice)",
        3: "Depth 3 (Casual)",
        4: "Depth 4 (Intermediate)",
        5: "Depth 5 (Club)",
        6: "Depth 6 (Expert)",
        7: "Depth 7 (Master)",
        8: "Depth 8 (Grandmaster)",
        9: "Depth 9 (Engine Max)",
        10: "Depth 10 (Deep Calculation)"
      };
      this.sliderDepthLabel.textContent = labels[this.engineDepth] || `Depth ${this.engineDepth}`;
      this.headerDepth.textContent = `Depth: ${this.engineDepth} ply`;
      this.triggerAnalysis();
    });

    // Under-Board Dock Controls
    document.getElementById("btn-takeback").addEventListener("click", () => this.takeback());
    document.getElementById("btn-suggest").addEventListener("click", () => this.triggerAnalysis());
    document.getElementById("btn-flip").addEventListener("click", () => this.flipBoard());
    document.getElementById("btn-new-game").addEventListener("click", () => this.newGame());
    document.getElementById("btn-copy-fen").addEventListener("click", () => this.copyFen());

    // Navigation buttons
    document.getElementById("btn-step-start").addEventListener("click", () => this.goToMove(0));
    document.getElementById("btn-step-prev").addEventListener("click", () => this.goToMove(this.historyIndex - 1));
    document.getElementById("btn-step-next").addEventListener("click", () => this.goToMove(this.historyIndex + 1));
    document.getElementById("btn-step-end").addEventListener("click", () => this.goToMove(this.history.length));

    // Sound toggle
    document.getElementById("btn-sound-toggle").addEventListener("click", () => {
      chessSound.muted = !chessSound.muted;
      const icon = document.querySelector("#btn-sound-toggle span");
      icon.textContent = chessSound.muted ? "volume_off" : "volume_up";
    });

    // FEN Dialog
    document.getElementById("btn-fen-dialog").addEventListener("click", () => this.openFenModal());
    document.getElementById("btn-fen-close-modal").addEventListener("click", () => this.closeFenModal());
    document.getElementById("btn-fen-copy-clip").addEventListener("click", () => {
      navigator.clipboard.writeText(this.fen);
      const btn = document.getElementById("btn-fen-copy-clip");
      const orig = btn.textContent;
      btn.textContent = "Copied!";
      setTimeout(() => (btn.textContent = orig), 1500);
    });
    document.getElementById("btn-fen-load-pos").addEventListener("click", () => {
      const val = this.fenInput.value.trim();
      if (val) {
        this.loadPosition(val, true);
        this.closeFenModal();
      }
    });

    // Promotion Dialog buttons
    document.querySelectorAll(".promo-choice").forEach((btn) => {
      btn.addEventListener("click", () => {
        const piece = btn.dataset.piece;
        this.closePromoModal();
        if (this.pendingMove) {
          this.executeMove(this.pendingMove.frm, this.pendingMove.to, piece);
          this.pendingMove = null;
        }
      });
    });

    // Keyboard shortcuts
    window.addEventListener("keydown", (e) => {
      if (document.activeElement.tagName === "INPUT") return;
      if (e.key === "ArrowLeft") this.goToMove(this.historyIndex - 1);
      if (e.key === "ArrowRight") this.goToMove(this.historyIndex + 1);
      if (e.key === "f") this.flipBoard();
      if (e.key === "u") this.takeback();
    });
  }

  setMode(mode) {
    this.mode = mode;
    if (mode === "play_white") {
      this.orientation = "w";
      this.navModePlay.className = "px-3 py-1 rounded transition-colors bg-surface-container-high text-primary font-semibold text-[13px]";
      this.navModeAnalyze.className = "text-[13px] px-3 py-1 rounded transition-colors text-on-surface-variant hover:text-on-surface font-semibold";
      this.toggleWhite.className = "flex items-center justify-center gap-2 py-1.5 rounded-lg bg-surface-container text-primary font-semibold text-[13px] transition-all shadow-sm";
      this.toggleBlack.className = "flex items-center justify-center gap-2 py-1.5 rounded-lg text-on-surface-variant hover:text-on-surface font-semibold text-[13px] transition-all";
      this.playerLabel.textContent = "White · Grandmaster Session";
      this.opponentLabel.textContent = "Black · Engine";
    } else if (mode === "play_black") {
      this.orientation = "b";
      this.navModePlay.className = "px-3 py-1 rounded transition-colors bg-surface-container-high text-primary font-semibold text-[13px]";
      this.navModeAnalyze.className = "text-[13px] px-3 py-1 rounded transition-colors text-on-surface-variant hover:text-on-surface font-semibold";
      this.toggleWhite.className = "flex items-center justify-center gap-2 py-1.5 rounded-lg text-on-surface-variant hover:text-on-surface font-semibold text-[13px] transition-all";
      this.toggleBlack.className = "flex items-center justify-center gap-2 py-1.5 rounded-lg bg-surface-container text-primary font-semibold text-[13px] transition-all shadow-sm";
      this.playerLabel.textContent = "Black · Grandmaster Session";
      this.opponentLabel.textContent = "White · Engine";
    } else {
      this.navModePlay.className = "text-[13px] px-3 py-1 rounded transition-colors text-on-surface-variant hover:text-on-surface font-semibold";
      this.navModeAnalyze.className = "px-3 py-1 rounded transition-colors bg-surface-container-high text-primary font-semibold text-[13px]";
      this.playerLabel.textContent = "Analysis Board (Both Sides)";
      this.opponentLabel.textContent = "Continuous Evaluation Active";
    }

    this.renderBoard();
    this.triggerAnalysis();
    this.checkEngineTurn();
  }

  flipBoard() {
    this.orientation = this.orientation === "w" ? "b" : "w";
    this.renderBoard();
    this.updateArrow();
  }

  newGame() {
    this.history = [];
    this.historyIndex = 0;
    this.lastMove = null;
    this.playerSeconds = 600;
    this.opponentSeconds = 600;
    this.loadPosition(START_FEN, true);
  }

  takeback() {
    if (this.history.length === 0) return;
    if (this.mode.startsWith("play_")) {
      this.history.pop();
      if (this.history.length > 0) this.history.pop();
    } else {
      this.history.pop();
    }
    const last = this.history[this.history.length - 1];
    this.loadPosition(last ? last.fen : START_FEN, false);
    this.historyIndex = this.history.length;
    this.lastMove = last ? last.move : null;
    this.updateMoveList();
  }

  goToMove(idx) {
    if (idx < 0 || idx > this.history.length) return;
    this.historyIndex = idx;
    const targetFen = idx === 0 ? START_FEN : this.history[idx - 1].fen;
    this.lastMove = idx === 0 ? null : this.history[idx - 1].move;
    this.loadPosition(targetFen, false);
    this.updateMoveList();
  }

  copyFen() {
    navigator.clipboard.writeText(this.fen);
    const btn = document.getElementById("btn-copy-fen");
    btn.classList.add("text-primary");
    setTimeout(() => btn.classList.remove("text-primary"), 1200);
  }

  startClock() {
    if (this.clockInterval) clearInterval(this.clockInterval);
    this.clockInterval = setInterval(() => {
      if (this.isGameOver) return;
      const side = this.fen.split(" ")[1];
      const isPlayerTurn =
        (this.mode === "play_white" && side === "w") ||
        (this.mode === "play_black" && side === "b");

      if (isPlayerTurn) {
        this.playerSeconds = Math.max(0, this.playerSeconds - 1);
        this.playerClock.textContent = this.formatClock(this.playerSeconds);
      } else if (this.mode.startsWith("play_")) {
        this.opponentSeconds = Math.max(0, this.opponentSeconds - 1);
        this.opponentClock.textContent = this.formatClock(this.opponentSeconds);
      }
    }, 1000);
  }

  formatClock(secs) {
    const m = Math.floor(secs / 60);
    const s = secs % 60;
    return `${m.toString().padStart(2, "0")}:${s.toString().padStart(2, "0")}`;
  }

  async loadPosition(fen, resetHistory = false) {
    this.fen = fen;
    if (resetHistory) {
      this.history = [];
      this.historyIndex = 0;
      this.lastMove = null;
    }

    try {
      const res = await fetch("/api/legal_moves", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ fen })
      });
      const data = await res.json();
      if (data.error) {
        alert("Invalid FEN: " + data.error);
        return;
      }
      this.legalMoves = data.legal_moves || [];
      this.checkSquare = data.check_square;
      this.isGameOver = data.status !== "ongoing";

      this.updateStatus(data);
      this.renderBoard();
      this.triggerAnalysis();
      this.checkEngineTurn();
    } catch (err) {
      console.error("Legal moves fetch error", err);
    }
  }

  updateStatus(data) {
    const side = data.side_to_move === "w" ? "White" : "Black";
    const isPlayerTurn =
      (this.mode === "play_white" && data.side_to_move === "w") ||
      (this.mode === "play_black" && data.side_to_move === "b");

    if (this.playerTurnDot) {
      this.playerTurnDot.style.opacity = isPlayerTurn ? "1" : "0.2";
    }

    if (data.status === "checkmate") {
      const winner = data.side_to_move === "w" ? "Black" : "White";
      this.engineStatusText.textContent = `Checkmate! ${winner} wins`;
      this.engineStatusDot.className = "w-2 h-2 rounded-full bg-red-500";
      chessSound.playGameEnd();
    } else if (data.status === "stalemate") {
      this.engineStatusText.textContent = "Draw by Stalemate";
      this.engineStatusDot.className = "w-2 h-2 rounded-full bg-amber-400";
      chessSound.playGameEnd();
    } else if (data.in_check) {
      this.engineStatusText.textContent = `Check! (${side})`;
      this.engineStatusDot.className = "w-2 h-2 rounded-full bg-red-500 animate-pulse";
      chessSound.playCheck();
    } else {
      this.engineStatusText.textContent = "Engine Ready";
      this.engineStatusDot.className = "w-2 h-2 rounded-full bg-emerald-400";
    }
  }

  // ---------- Board Grid Rendering ----------

  renderBoard() {
    this.boardEl.innerHTML = "";
    const ranks = this.fen.split(" ")[0].split("/");
    const grid = [];

    for (let r = 0; r < 8; r++) {
      const row = [];
      for (const ch of ranks[r]) {
        if (ch >= "1" && ch <= "8") {
          for (let i = 0; i < parseInt(ch); i++) row.push(".");
        } else {
          row.push(ch);
        }
      }
      grid.push(row);
    }

    const rowOrder = this.orientation === "w" ? [0,1,2,3,4,5,6,7] : [7,6,5,4,3,2,1,0];
    const colOrder = this.orientation === "w" ? [0,1,2,3,4,5,6,7] : [7,6,5,4,3,2,1,0];

    for (const r of rowOrder) {
      for (const c of colOrder) {
        const sqName = "abcdefgh"[c] + (8 - r);
        const isLight = (r + c) % 2 === 0;

        const sqEl = document.createElement("div");
        sqEl.className = `relative flex items-center justify-center select-none transition-colors ${
          isLight ? "bg-[#efe8dd]" : "bg-[#2a303e]"
        }`;
        sqEl.dataset.sq = sqName;

        // Last move highlight (amber tint)
        if (this.lastMove && (this.lastMove.startsWith(sqName) || this.lastMove.slice(2, 4) === sqName)) {
          sqEl.classList.add("!bg-primary/25");
        }

        // Selected square highlight
        if (this.selectedSquare === sqName) {
          sqEl.classList.add("!bg-primary/40");
        }

        // Check highlight
        if (this.checkSquare === sqName) {
          sqEl.classList.add("square-check");
        }

        // Coordinate Labels
        if (this.orientation === "w") {
          if (c === 0) {
            sqEl.innerHTML += `<span class="absolute top-1 left-1.5 font-mono-notation text-[10px] ${
              isLight ? "text-[#2a303e]/40" : "text-[#d4c4b0]/40"
            } font-semibold">${8 - r}</span>`;
          }
          if (r === 7) {
            sqEl.innerHTML += `<span class="absolute bottom-1 right-1.5 font-mono-notation text-[10px] ${
              isLight ? "text-[#2a303e]/40" : "text-[#d4c4b0]/40"
            } font-semibold">${"abcdefgh"[c]}</span>`;
          }
        } else {
          if (c === 7) {
            sqEl.innerHTML += `<span class="absolute top-1 left-1.5 font-mono-notation text-[10px] ${
              isLight ? "text-[#2a303e]/40" : "text-[#d4c4b0]/40"
            } font-semibold">${8 - r}</span>`;
          }
          if (r === 0) {
            sqEl.innerHTML += `<span class="absolute bottom-1 right-1.5 font-mono-notation text-[10px] ${
              isLight ? "text-[#2a303e]/40" : "text-[#d4c4b0]/40"
            } font-semibold">${"abcdefgh"[c]}</span>`;
          }
        }

        // Piece
        const pieceChar = grid[r][c];
        if (pieceChar !== ".") {
          const pieceEl = document.createElement("div");
          pieceEl.className = "piece-img flex items-center justify-center";
          pieceEl.innerHTML = PIECE_SVGS[pieceChar] || "";
          pieceEl.setAttribute("draggable", "true");
          this.bindPieceDrag(pieceEl, sqName);
          sqEl.appendChild(pieceEl);
        }

        // Move hint dot / capture ring
        if (this.selectedSquare) {
          const matching = this.legalMoves.filter(
            (m) => m.startsWith(this.selectedSquare) && m.slice(2, 4) === sqName
          );
          if (matching.length > 0) {
            const isCapture = pieceChar !== "." || (matching[0].length === 4 && this.isEnPassant(this.selectedSquare, sqName));
            if (isCapture) {
              const ring = document.createElement("div");
              ring.className = "square-hint-ring";
              sqEl.appendChild(ring);
            } else {
              const dot = document.createElement("div");
              dot.className = "square-hint-dot";
              sqEl.appendChild(dot);
            }
          }
        }

        // Event listeners
        sqEl.addEventListener("click", () => this.onSquareClick(sqName));
        sqEl.addEventListener("dragover", (e) => e.preventDefault());
        sqEl.addEventListener("drop", (e) => {
          e.preventDefault();
          const fromSq = e.dataTransfer.getData("text/plain");
          if (fromSq && fromSq !== sqName) {
            this.handleMoveAttempt(fromSq, sqName);
          }
        });

        this.boardEl.appendChild(sqEl);
      }
    }
  }

  isEnPassant(from, to) {
    const ep = this.fen.split(" ")[3];
    return ep === to;
  }

  bindPieceDrag(pieceEl, square) {
    pieceEl.addEventListener("dragstart", (e) => {
      e.dataTransfer.setData("text/plain", square);
      this.selectedSquare = square;
      this.renderBoard();
    });
  }

  onSquareClick(sq) {
    if (this.isGameOver) return;
    const side = this.fen.split(" ")[1];

    if (this.selectedSquare) {
      if (this.selectedSquare === sq) {
        this.selectedSquare = null;
        this.renderBoard();
        return;
      }

      const match = this.legalMoves.filter(
        (m) => m.startsWith(this.selectedSquare) && m.slice(2, 4) === sq
      );
      if (match.length > 0) {
        this.handleMoveAttempt(this.selectedSquare, sq);
        return;
      }
    }

    // Select piece
    const ranks = this.fen.split(" ")[0].split("/");
    const col = sq.charCodeAt(0) - 97;
    const row = 8 - parseInt(sq[1]);
    let count = 0;
    let clickedPiece = ".";
    for (const ch of ranks[row]) {
      if (ch >= "1" && ch <= "8") {
        count += parseInt(ch);
        if (count > col) break;
      } else {
        if (count === col) {
          clickedPiece = ch;
          break;
        }
        count++;
      }
    }

    const isWhite = clickedPiece === clickedPiece.toUpperCase() && clickedPiece !== ".";
    const isMover = (side === "w" && isWhite) || (side === "b" && !isWhite && clickedPiece !== ".");

    if (isMover) {
      this.selectedSquare = sq;
    } else {
      this.selectedSquare = null;
    }
    this.renderBoard();
  }

  handleMoveAttempt(from, to) {
    const matching = this.legalMoves.filter((m) => m.startsWith(from) && m.slice(2, 4) === to);
    if (matching.length === 0) {
      this.selectedSquare = null;
      this.renderBoard();
      return;
    }

    if (matching.some((m) => m.length === 5)) {
      this.pendingMove = { frm: from, to: to };
      this.openPromoModal(this.fen.split(" ")[1]);
      return;
    }

    this.executeMove(from, to);
  }

  async executeMove(from, to, promo = null) {
    const moveStr = from + to + (promo || "");
    this.selectedSquare = null;

    try {
      const res = await fetch("/api/make_move", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ fen: this.fen, move: moveStr })
      });
      const data = await res.json();
      if (data.error) {
        console.error(data.error);
        return;
      }

      if (data.is_capture) {
        chessSound.playCapture();
      } else {
        chessSound.playMove();
      }

      this.lastMove = moveStr;
      this.history.push({
        fen: data.new_fen,
        move: moveStr,
        isCapture: data.is_capture
      });
      this.historyIndex = this.history.length;

      this.loadPosition(data.new_fen, false);
      this.updateMoveList();
    } catch (err) {
      console.error("Execute move failed", err);
    }
  }

  async checkEngineTurn() {
    if (this.isGameOver) return;
    const side = this.fen.split(" ")[1];
    const isBotTurn =
      (this.mode === "play_white" && side === "b") ||
      (this.mode === "play_black" && side === "w");

    if (!isBotTurn) return;

    this.isEngineThinking = true;
    this.engineStatusDot.className = "w-2 h-2 rounded-full bg-primary animate-pulse";
    this.engineStatusText.textContent = "Engine is thinking...";

    try {
      const res = await fetch("/api/engine_move", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          fen: this.fen,
          depth: this.engineDepth,
          time_limit: this.engineTime
        })
      });
      const data = await res.json();
      if (data.move) {
        this.lastMove = data.move;
        this.history.push({
          fen: data.new_fen,
          move: data.move
        });
        this.historyIndex = this.history.length;
        chessSound.playMove();
        this.loadPosition(data.new_fen, false);
        this.updateMoveList();
      }
    } catch (err) {
      console.error("Engine move error", err);
    } finally {
      this.isEngineThinking = false;
    }
  }

  // ---------- Engine Analysis & Arrow ----------

  async triggerAnalysis() {
    if (this.analysisAbortCtrl) {
      this.analysisAbortCtrl.abort();
    }
    this.analysisAbortCtrl = new AbortController();

    this.engineStatusDot.className = "w-2 h-2 rounded-full bg-primary animate-pulse";

    try {
      const res = await fetch("/api/analyze", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          fen: this.fen,
          depth: this.engineDepth,
          time_limit: this.engineTime
        }),
        signal: this.analysisAbortCtrl.signal
      });
      const data = await res.json();
      if (data.cancelled) return;

      this.currentAnalysis = data;
      this.updateAnalysisUI(data);
      this.updateArrow();

      this.engineStatusDot.className = "w-2 h-2 rounded-full bg-emerald-400";
    } catch (err) {
      if (err.name !== "AbortError") console.error("Analysis error", err);
    }
  }

  updateAnalysisUI(data) {
    if (!data.eval) return;

    const evalObj = data.eval;
    const scoreText = evalObj.text;

    // Snapshot Bar
    this.snapshotEval.textContent = scoreText;
    if (evalObj.white_score > 50) {
      this.snapshotLead.textContent = "White leads";
    } else if (evalObj.white_score < -50) {
      this.snapshotLead.textContent = "Black leads";
    } else {
      this.snapshotLead.textContent = "Equal Position";
    }

    if (data.best_move) {
      this.snapshotMove.textContent = `1. ${data.best_move.slice(0,2)}–${data.best_move.slice(2,4)}`;
    }
    this.snapshotDepth.textContent = `Best Move · Depth ${data.depth}`;
    this.snapshotNodes.textContent = `${(data.nodes || 0).toLocaleString()} nodes`;

    // Eval Bar (Height calculation)
    let pct = 50;
    if (evalObj.type === "mate") {
      pct = evalObj.white_score > 0 ? 100 : 0;
    } else {
      const cp = evalObj.white_score;
      pct = 50 + (cp / (Math.abs(cp) + 400)) * 50;
      pct = Math.max(4, Math.min(96, pct));
    }
    this.evalBarFill.style.height = `${pct}%`;
    this.evalBarPill.textContent = scoreText;

    // Candidate Lines Card
    if (data.best_move) {
      this.candBestMove.textContent = `1. ${data.best_move.slice(0,2)}–${data.best_move.slice(2,4)}`;
    }
    this.candBestScore.textContent = scoreText;
    if (data.pv && data.pv.length > 0) {
      this.candPvText.textContent = data.pv.join(" ");
    }

    // Telemetry Card
    this.telemetrySpeed.textContent = `${Math.round((data.nps || 0) / 1000)}k nps`;
    this.telemetryNodes.textContent = (data.nodes || 0).toLocaleString();
    this.npsLiveBadge.textContent = `${(data.nodes || 0).toLocaleString()} nodes · ${data.time_sec}s`;
    this.engineLatencyText.textContent = `Search time: ${data.time_sec}s · Zero errors`;
  }

  updateArrow() {
    if (!this.currentAnalysis || !this.currentAnalysis.best_move) {
      this.arrowLine.setAttribute("opacity", "0");
      return;
    }

    const move = this.currentAnalysis.best_move;
    const fromSq = move.slice(0, 2);
    const toSq = move.slice(2, 4);

    const fromCoords = this.squareToPixel(fromSq);
    const toCoords = this.squareToPixel(toSq);

    this.arrowLine.setAttribute("x1", fromCoords.x);
    this.arrowLine.setAttribute("y1", fromCoords.y);
    this.arrowLine.setAttribute("x2", toCoords.x);
    this.arrowLine.setAttribute("y2", toCoords.y);
    this.arrowLine.setAttribute("opacity", "1");
  }

  squareToPixel(sq) {
    const col = sq.charCodeAt(0) - 97;
    const row = 8 - parseInt(sq[1]);
    const sqSize = 560 / 8; // 70px

    const r = this.orientation === "w" ? row : 7 - row;
    const c = this.orientation === "w" ? col : 7 - col;

    return {
      x: c * sqSize + sqSize / 2,
      y: r * sqSize + sqSize / 2
    };
  }

  // ---------- Move Table ----------

  updateMoveList() {
    this.movesTbody.innerHTML = "";
    for (let i = 0; i < this.history.length; i += 2) {
      const moveNum = Math.floor(i / 2) + 1;
      const whiteMove = this.history[i];
      const blackMove = this.history[i + 1];

      const tr = document.createElement("tr");
      tr.className = "border-b border-[#2d3139]/20 hover:bg-surface-container-high/40 transition-colors";

      tr.innerHTML = `
        <td class="py-1 px-2 text-on-surface-variant font-semibold w-10">${moveNum}.</td>
        <td class="py-1 px-2 cursor-pointer hover:text-primary ${this.historyIndex === i + 1 ? "text-primary font-bold" : "text-on-surface"}" data-step="${i + 1}">
          ${whiteMove.move}
        </td>
        <td class="py-1 px-2 cursor-pointer hover:text-primary ${blackMove && this.historyIndex === i + 2 ? "text-primary font-bold" : "text-on-surface"}" data-step="${i + 2}">
          ${blackMove ? blackMove.move : ""}
        </td>
      `;

      tr.querySelectorAll("td[data-step]").forEach((td) => {
        td.addEventListener("click", () => {
          const step = parseInt(td.dataset.step);
          if (!isNaN(step)) this.goToMove(step);
        });
      });

      this.movesTbody.appendChild(tr);
    }

    const logContainer = document.getElementById("moves-log-container");
    if (logContainer) logContainer.scrollTop = logContainer.scrollHeight;
  }

  // ---------- Modals ----------

  openPromoModal(color) {
    const choices = this.promoModal.querySelectorAll(".promo-choice");
    choices.forEach((btn) => {
      const pieceKey = color === "w" ? btn.dataset.piece.toUpperCase() : btn.dataset.piece.toLowerCase();
      btn.innerHTML = PIECE_SVGS[pieceKey] || "";
    });
    this.promoModal.classList.remove("hidden");
    this.promoModal.classList.add("flex");
  }

  closePromoModal() {
    this.promoModal.classList.add("hidden");
    this.promoModal.classList.remove("flex");
  }

  openFenModal() {
    this.fenInput.value = this.fen;
    this.fenModal.classList.remove("hidden");
    this.fenModal.classList.add("flex");
  }

  closeFenModal() {
    this.fenModal.classList.add("hidden");
    this.fenModal.classList.remove("flex");
  }
}

// Bootstrap
window.addEventListener("DOMContentLoaded", () => {
  window.chessApp = new ChessApp();
});
