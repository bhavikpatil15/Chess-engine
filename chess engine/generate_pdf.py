"""
generate_pdf.py - Generates a complete, beautiful PDF guide:
"The Secret Life of a Chess Engine: Explained for a 6-Year-Old"
Each file has its own detailed, kid-friendly story-section.
Built with pure Python standard library (no third-party dependencies).
"""

import sys
import os

class SimplePDF:
    def __init__(self, filename="Chess_Engine_Explained_Simply.pdf"):
        self.filename = filename
        self.pages = []  # list of byte streams for each page
        self.page_width = 595.28  # A4
        self.page_height = 841.89
        self.margin_x = 48
        self.margin_top = 54
        self.margin_bottom = 50
        self.content_w = self.page_width - (2 * self.margin_x)

        # Current page stream and Y cursor
        self.current_stream = []
        self.cursor_y = self.page_height - self.margin_top

    def new_page(self):
        if self.current_stream:
            self.pages.append("".join(self.current_stream))
        self.current_stream = []
        self.cursor_y = self.page_height - self.margin_top
        # Subtle top decorative line
        self.draw_rect(self.margin_x, self.page_height - 30, self.content_w, 2, fill=(0.0, 0.85, 0.95))

    def ensure_space(self, needed_height):
        if self.cursor_y - needed_height < self.margin_bottom:
            self.new_page()

    def draw_rect(self, x, y, w, h, fill=None, stroke=None, stroke_width=1):
        cmds = []
        if stroke:
            cmds.append(f"{stroke_width} w {stroke[0]:.2f} {stroke[1]:.2f} {stroke[2]:.2f} RG ")
        if fill:
            cmds.append(f"{fill[0]:.2f} {fill[1]:.2f} {fill[2]:.2f} rg ")
        cmds.append(f"{x:.2f} {y:.2f} {w:.2f} {h:.2f} re ")
        if fill and stroke:
            cmds.append("B\n")
        elif fill:
            cmds.append("f\n")
        elif stroke:
            cmds.append("S\n")
        self.current_stream.append("".join(cmds))

    def draw_banner(self, title, subtitle=None):
        self.ensure_space(90)
        h = 70 if subtitle else 50
        y = self.cursor_y - h
        # Dark navy background card with bright cyan border
        self.draw_rect(self.margin_x, y, self.content_w, h, fill=(0.08, 0.11, 0.18), stroke=(0.0, 0.75, 0.9), stroke_width=1.5)
        # Left accent pill
        self.draw_rect(self.margin_x, y, 6, h, fill=(0.0, 0.85, 0.95))

        self.add_text(title, self.margin_x + 18, y + h - 26, font="F2", size=18, color=(1.0, 1.0, 1.0))
        if subtitle:
            self.add_text(subtitle, self.margin_x + 18, y + 16, font="F3", size=11, color=(0.7, 0.8, 0.9))
        self.cursor_y = y - 16

    def draw_section_header(self, file_name, friendly_title, icon="*"):
        self.ensure_space(55)
        h = 36
        y = self.cursor_y - h
        # Card header fill
        self.draw_rect(self.margin_x, y, self.content_w, h, fill=(0.12, 0.16, 0.24), stroke=(0.2, 0.25, 0.35), stroke_width=1)
        # Left color bar
        self.draw_rect(self.margin_x, y, 5, h, fill=(0.0, 0.85, 0.85))

        self.add_text(f"{icon}  {file_name}", self.margin_x + 14, y + 21, font="F2", size=12, color=(0.0, 0.9, 1.0))
        self.add_text(f"— {friendly_title}", self.margin_x + 14, y + 8, font="F2", size=10, color=(1.0, 1.0, 1.0))
        self.cursor_y = y - 12

    def add_text(self, text, x, y, font="F1", size=10, color=(0.15, 0.18, 0.24)):
        # Sanitize unicode characters for standard Type1 PDF fonts
        sanitized = (text
            .replace("—", "--")
            .replace("–", "-")
            .replace("“", '"')
            .replace("”", '"')
            .replace("’", "'")
            .replace("‘", "'")
            .replace("•", "*")
            .replace("…", "...")
        )
        # Escape parenthesis and backslashes for PDF string literal
        escaped = sanitized.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
        cmd = f"BT /{font} {size} Tf {color[0]:.2f} {color[1]:.2f} {color[2]:.2f} rg 1 0 0 1 {x:.2f} {y:.2f} Tm ({escaped}) Tj ET\n"
        self.current_stream.append(cmd)

    def wrap_words(self, text, max_chars):
        words = text.split(" ")
        lines = []
        cur = []
        cur_len = 0
        for w in words:
            if cur_len + len(w) + 1 <= max_chars:
                cur.append(w)
                cur_len += len(w) + 1
            else:
                if cur:
                    lines.append(" ".join(cur))
                cur = [w]
                cur_len = len(w)
        if cur:
            lines.append(" ".join(cur))
        return lines

    def add_paragraph(self, text, font="F1", size=9.5, color=(0.18, 0.20, 0.25), line_height=14, indent=0):
        # Rough estimation: characters that fit in content_w
        # font size 9.5 -> ~5.2 pt per char -> ~92 chars per line
        max_chars = int((self.content_w - indent) / (size * 0.52))
        lines = self.wrap_words(text, max_chars)
        needed = len(lines) * line_height + 4
        self.ensure_space(needed)

        for line in lines:
            self.add_text(line, self.margin_x + indent, self.cursor_y - size, font=font, size=size, color=color)
            self.cursor_y -= line_height
        self.cursor_y -= 4

    def add_bullet(self, bold_prefix, text, icon="*"):
        full_text = f"{bold_prefix} {text}"
        max_chars = int((self.content_w - 20) / (9.5 * 0.52))
        lines = self.wrap_words(full_text, max_chars)
        needed = len(lines) * 14 + 6
        self.ensure_space(needed)

        # Bullet symbol
        self.add_text(icon, self.margin_x + 6, self.cursor_y - 9.5, font="F2", size=10, color=(0.0, 0.7, 0.85))

        for idx, line in enumerate(lines):
            # Print first line with highlight if possible or regular
            font = "F2" if (idx == 0 and len(lines) == 1) else "F1"
            self.add_text(line, self.margin_x + 20, self.cursor_y - 9.5, font="F1", size=9.5, color=(0.18, 0.20, 0.25))
            self.cursor_y -= 14
        self.cursor_y -= 3

    def add_callout(self, title, text, bg_color=(0.95, 0.97, 1.0), border_color=(0.6, 0.8, 0.95)):
        max_chars = int((self.content_w - 28) / (9.2 * 0.52))
        lines = self.wrap_words(text, max_chars)
        box_h = 24 + len(lines) * 13.5
        self.ensure_space(box_h + 8)

        y = self.cursor_y - box_h
        self.draw_rect(self.margin_x, y, self.content_w, box_h, fill=bg_color, stroke=border_color, stroke_width=1)
        self.draw_rect(self.margin_x, y, 4, box_h, fill=(0.1, 0.6, 0.9))

        self.add_text(title, self.margin_x + 14, y + box_h - 15, font="F2", size=10, color=(0.05, 0.35, 0.65))
        cy = y + box_h - 29
        for line in lines:
            self.add_text(line, self.margin_x + 14, cy, font="F3", size=9, color=(0.15, 0.25, 0.35))
            cy -= 13.5
        self.cursor_y = y - 12

    def save(self):
        if self.current_stream:
            self.pages.append("".join(self.current_stream))

        total_pages = len(self.pages)
        # Add footers to all pages
        for idx in range(total_pages):
            pg_num = idx + 1
            footer_text = f"The Secret Life of a Chess Engine  |  Page {pg_num} of {total_pages}"
            footer_stream = []
            footer_stream.append(
                f"0.85 0.88 0.92 RG 1 w {self.margin_x:.2f} 32.00 {self.content_w:.2f} 0.00 re S\n"
            )
            escaped = footer_text.replace("(", "\\(").replace(")", "\\)")
            footer_stream.append(
                f"BT /F3 8.5 Tf 0.5 0.55 0.62 rg 1 0 0 1 {self.margin_x:.2f} 20.00 Tm ({escaped}) Tj ET\n"
            )
            self.pages[idx] = self.pages[idx] + "".join(footer_stream)

        # Build PDF objects
        objects = []
        # 1: Catalog
        objects.append("<< /Type /Catalog /Pages 2 0 R >>")
        # 2: Pages container (placeholder, will fill kids)
        kids_refs = [f"{3 + i * 2} 0 R" for i in range(total_pages)]
        pages_obj = f"<< /Type /Pages /Kids [{' '.join(kids_refs)}] /Count {total_pages} >>"
        objects.append(pages_obj)

        # For each page:
        # Page object at index 3 + i*2
        # Content stream object at index 4 + i*2
        # Fonts at the end
        font_f1_idx = 3 + total_pages * 2
        font_f2_idx = font_f1_idx + 1
        font_f3_idx = font_f1_idx + 2

        for i, page_str in enumerate(self.pages):
            content_obj_idx = 4 + i * 2
            page_obj = (
                f"<< /Type /Page /Parent 2 0 R "
                f"/MediaBox [0 0 {self.page_width:.2f} {self.page_height:.2f}] "
                f"/Contents {content_obj_idx} 0 R "
                f"/Resources << /Font << /F1 {font_f1_idx} 0 R /F2 {font_f2_idx} 0 R /F3 {font_f3_idx} 0 R >> >> >>"
            )
            objects.append(page_obj)
            stream_bytes = page_str.encode("latin-1")
            stream_obj = f"<< /Length {len(stream_bytes)} >>\nstream\n{page_str}\nendstream"
            objects.append(stream_obj)

        # Standard built-in Type1 Fonts
        objects.append("<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica /Encoding /WinAnsiEncoding >>")
        objects.append("<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica-Bold /Encoding /WinAnsiEncoding >>")
        objects.append("<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica-Oblique /Encoding /WinAnsiEncoding >>")

        # Assemble PDF file with cross-reference table
        output = [b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n"]
        offsets = [0]

        for i, obj in enumerate(objects, start=1):
            offset = sum(len(x) for x in output)
            offsets.append(offset)
            if isinstance(obj, str):
                chunk = f"{i} 0 obj\n{obj}\nendobj\n".encode("latin-1")
            else:
                chunk = f"{i} 0 obj\n".encode("latin-1") + obj + b"\nendobj\n"
            output.append(chunk)

        xref_offset = sum(len(x) for x in output)
        xref_str = f"xref\n0 {len(objects) + 1}\n0000000000 65535 f \n"
        for off in offsets[1:]:
            xref_str += f"{off:010d} 00000 n \n"
        trailer = (
            f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\n"
            f"startxref\n{xref_offset}\n%%EOF\n"
        )

        output.append(xref_str.encode("latin-1"))
        output.append(trailer.encode("latin-1"))

        with open(self.filename, "wb") as f:
            f.write(b"".join(output))

        print(f"Successfully generated: {self.filename} ({len(b''.join(output))} bytes, {total_pages} pages)")


def build_chess_guide():
    doc = SimplePDF("Chess_Engine_Explained_Simply.pdf")

    # ================= PAGE 1 =================
    doc.new_page()
    doc.draw_banner(
        "THE SECRET LIFE OF A CHESS ENGINE",
        "A Friendly Adventure Guide for Curious Kids (and Grown-Ups!)"
    )

    doc.add_paragraph(
        "Imagine you have a magical wooden toy box filled with 32 little carved kings, queens, knights, "
        "and pawns. When you play chess with your friend, your eyes see the board and your hand moves the pieces. "
        "But how can a computer, which has no eyes, no hands, and no brain, play chess against you and win?"
    )

    doc.add_paragraph(
        "Inside this computer folder is a team of tiny digital superheroes. Each file in your project has one "
        "special superpower. None of them can play chess alone, but when they work together like best friends in "
        "a school project, they become a master chess player that thinks faster than lightning!"
    )

    doc.add_callout(
        "MEET THE SUPERHERO TEAM AT A GLANCE:",
        "1. board.py: The Toybox (holds every piece in its exact square)\n"
        "2. moves.py: The Strict Referee (knows all legal chess rules)\n"
        "3. test_moves.py: The Superhero Exam (tests the referee's eyesight)\n"
        "4. evaluate.py: The Wise Judge (uses a golden scale to see who is winning)\n"
        "5. search.py: The Crystal Ball (looks 5 moves into the future)\n"
        "6. play.py: The Terminal Arcade (lets you play in the black terminal box)\n"
        "7. gui_new.py: The Desktop Game Window (the classic desktop app)\n"
        "8. server.py: The Superfast Telephone Wire (connects brain to website)\n"
        "9. web/: The Glass Castle (the shiny, modern web browser interface)"
    )

    # SECTION 1: board.py
    doc.draw_section_header("board.py", "The Toybox & The Magical Grid", icon="[1]")
    doc.add_paragraph(
        "What is it? Imagine an egg carton with 64 tiny holes: 8 rows tall and 8 columns wide. "
        "This file is the toybox where the chess board lives."
    )
    doc.add_bullet("Capital Letters vs Little Letters:", "White pieces get tall capital hats (P for Pawn, N for Knight, B, R, Q, K). Black pieces wear lowercase shoes (p, n, b, r, q, k). An empty square is just a little dot ('.').")
    doc.add_bullet("The Secret Address System (FEN):", "If you want to save your game and pack your toys away, board.py writes a magical secret code called a FEN string. It describes all 64 squares in a single short line of text, like a secret recipe!")
    doc.add_bullet("Fast Clones (The Copy Power):", "Whenever the computer wants to guess a move, it makes a twin-copy of the toybox so your real game never gets messed up.")

    # ================= PAGE 2 =================
    doc.new_page()

    # SECTION 2: moves.py
    doc.draw_section_header("moves.py", "The Strict Referee With The Golden Whistle", icon="[2]")
    doc.add_paragraph(
        "If a pawn suddenly tried to fly backwards across the whole board like a dragon, the referee blows its "
        "whistle: TWEET! 'Not allowed!' moves.py knows every single rule invented in chess over the last 1,500 years."
    )
    doc.add_bullet("Two-Step Move Verification:", "First, it asks 'Can this piece physically walk there?' (Pseudo-legal). Then it asks the life-or-death question: 'Does this move leave our King in danger?' If our King would get captured, the referee throws the move in the trash!")
    doc.add_bullet("Special Magic Moves:", "Moves.py knows the trickiest rules in chess history:")
    doc.add_paragraph("   - Castling: The King jumps two squares sideways and the Rook hops over him to build a fortress.", indent=10)
    doc.add_paragraph("   - En Passant: The ghost pawn capture where a pawn takes an enemy pawn that ran past it.", indent=10)
    doc.add_paragraph("   - Pawn Promotion: When a humble pawn reaches the far edge, it transforms into a Queen!", indent=10)
    doc.add_bullet("Check & Checkmate Detector:", "It checks whether the King is under attack (Check!) or trapped with zero escape moves (Checkmate - game over!).")

    # SECTION 3: test_moves.py
    doc.draw_section_header("test_moves.py", "The Superhero Exam & Obstacle Course", icon="[3]")
    doc.add_paragraph(
        "How do we know our Referee (moves.py) didn't forget a rule or fall asleep? "
        "test_moves.py is a rigorous obstacle course called 'Perft' (Performance Test)."
    )
    doc.add_bullet("The Exact Leaf Counter:", "Computers around the world have calculated the exact number of possible moves in chess. From the start position, in 1 move there are exactly 20 possibilities. In 2 moves, 400. In 3 moves, exactly 8,902!")
    doc.add_bullet("Kiwipete Jungle:", "A famous messy puzzle position with pins, discovered attacks, and double pawn pushes. test_moves.py verifies all 97,862 paths in 0.4 seconds. If even ONE pawn move was wrong, it sounds an alarm!")

    # ================= PAGE 3 =================
    doc.new_page()

    # SECTION 4: evaluate.py
    doc.draw_section_header("evaluate.py", "The Wise Judge With The Golden Scales", icon="[4]")
    doc.add_paragraph(
        "When the computer looks at a board, it cannot say 'this position looks pretty.' It needs a score! "
        "evaluate.py is the wise judge holding a giant balance scale. It gives a score in 'centipawns' "
        "(100 centipawns = 1 healthy pawn)."
    )
    doc.add_bullet("Piece Pocket Money:", "Pawn = 100 points, Knight = 320, Bishop = 330, Rook = 500, Queen = 900. The King is priceless (100,000 points)!")
    doc.add_bullet("Square Preference Tables:", "Pieces hate sitting in corners! Knights in the center attack 8 squares, but on the edge they only attack 2. evaluate.py gives bonus points for pieces standing on golden squares.")
    doc.add_bullet("King Bedtime vs King Hero:", "In the opening, the King must stay tucked in bed behind pawns. But when almost all enemy pieces are gone (the endgame), the King bravely marches out to help win the game!")

    # SECTION 5: search.py
    doc.draw_section_header("search.py", "The Crystal Ball & The Time Machine", icon="[5]")
    doc.add_paragraph(
        "This is the heart and brain of the whole engine! While you are taking your turn, search.py "
        "is jumping into a time machine to explore hundreds of thousands of possible futures."
    )
    doc.add_bullet("The Tree of Possibilities (Negamax):", "I play this, then you might play that, then I play this... It builds a giant tree of choices and assumes you will always pick your best move, so it picks the path that keeps it safe.")
    doc.add_bullet("Alpha-Beta Pruning (Ignoring Bad Branches):", "If the computer sees that path A loses its Queen for nothing, it stops looking down path A immediately! This saves millions of wasted calculations.")
    doc.add_bullet("The Quiescence Calmer:", "Have you ever made a trade where you take a piece, but forget that their friend takes you right back? Quiescence search keeps calculating until all captures stop, avoiding blind traps!")
    doc.add_bullet("Transposition Table (The Photographic Memory):", "If two different move orders lead to the exact same position, search.py remembers the answer in its memory diary so it never solves the same puzzle twice.")

    # ================= PAGE 4 =================
    doc.new_page()

    # SECTION 6: play.py
    doc.draw_section_header("play.py", "The Retro Arcade In The Terminal", icon="[6]")
    doc.add_paragraph(
        "Before we built fancy web pages, play.py was how human players challenged the computer. "
        "It prints the 64 squares out of plain keyboard letters inside your black terminal screen!"
    )
    doc.add_bullet("Three Bot Personalities:", "")
    doc.add_paragraph("   - Bot 1 (The Toddler): Picks any legal move completely at random.", indent=10)
    doc.add_paragraph("   - Bot 2 (The Greedy Goblin): Grabs whichever piece has the highest point value right now, even if it walks into a trap!", indent=10)
    doc.add_paragraph("   - Bot 3 (The Grandmaster): Wakes up search.py to look several steps ahead with deep calculation.", indent=10)

    # SECTION 7: gui_new.py
    doc.draw_section_header("gui_new.py", "The Desktop Window On Your Screen", icon="[7]")
    doc.add_paragraph(
        "gui_new.py is a classic desktop computer window built with Tkinter (Python's built-in paintbrush). "
        "It draws colored tiles, listens for mouse clicks on pieces, and displays a blue arrow showing the best move."
    )
    doc.add_bullet("Background Brain Worker (Threading):", "When the engine thinks, it runs in a quiet background room so your mouse doesn't freeze. You can click 'Undo' or 'Flip' anytime!")

    # SECTION 8: server.py
    doc.draw_section_header("server.py", "The High-Speed Telephone Operator", icon="[8]")
    doc.add_paragraph(
        "Your web browser (Chrome or Safari) cannot talk to Python directly. They speak different languages! "
        "server.py acts as the friendly telephone operator standing between the two."
    )
    doc.add_bullet("Order Taker (HTTP API):", "When you drag a piece in your browser, the browser whispers: 'Hey server, I want to move e2 to e4!' server.py checks with moves.py, runs search.py, and replies in milliseconds: 'Move accepted! The engine thinks White is ahead by +0.35.'")
    doc.add_bullet("Stop-Watch & Cancellation:", "If you make a new move while the engine is still thinking, server.py taps search.py on the shoulder: 'Stop! The player made a new move, start thinking about this one instead!'")

    # ================= PAGE 5 =================
    doc.new_page()

    # SECTION 9: web/
    doc.draw_banner("THE MODERN WEB KINGDOM (web/ folder)", "PyChess Studio — Your Exact Stitch Design")

    doc.add_paragraph(
        "Inside the web/ folder lives the exact interface you crafted in Stitch: 'PyChess Studio - Midnight Retro'. "
        "It features the Walnut & Bone chessboard, floating frosted capsule bar, player placards, and retro gold telemetry!"
    )

    doc.draw_section_header("index.html", "The PyChess Studio Stage & Layout", icon="[A]")
    doc.add_paragraph(
        "index.html implements your exact 12-column Stitch layout: the Top Snapshot capsule with '+1.4 White leads', "
        "Opponent & Player placards with live game clocks, the 560x560 board flanked by the precision eval bar, "
        "the under-board dock controls (Takeback, Suggest Move, Flip, New Game), Candidate Lines, and Engine Telemetry."
    )

    doc.draw_section_header("style.css & Tailwind", "Your Exact Colors & Typography", icon="[B]")
    doc.add_paragraph(
        "Directly uses your Stitch design tokens and Google Web Fonts:"
    )
    doc.add_bullet("Exact Palette:", "Deep charcoal base (#0c0e12), surface workpanes (#1a1c20), crisp borders (#2d3139), and warm retro amber-gold (#e5a93c / #ffc665).")
    doc.add_bullet("Walnut & Bone Board:", "Alabaster light squares (#efe8dd) and cool slate-dark squares (#2a303e) for maximum piece clarity.")
    doc.add_bullet("Fonts:", "Plus Jakarta Sans for bold headlines, Inter for crisp UI labels, and monospaced telemetry for clocks and depths.")

    doc.draw_section_header("pieces.js", "The Beautiful Handcrafted Wooden Toys", icon="[C]")
    doc.add_paragraph(
        "Instead of blurry photos downloaded from the internet that might break offline, pieces.js contains "
        "crisp vector math instructions (SVGs) for all 12 chess pieces. They stay razor-sharp whether viewed "
        "on a giant 4K television or a tiny phone screen!"
    )

    # ================= PAGE 6 =================
    doc.new_page()

    doc.draw_section_header("sound.js", "The Orchestra & Sound Effects", icon="[D]")
    doc.add_paragraph(
        "sound.js uses your computer's built-in sound synthesizer chip (Web Audio API) to play real audio "
        "without needing any mp3 audio files!"
    )
    doc.add_bullet("The Wooden Tock:", "A quick, satisfying wooden snap when you set a piece on an empty square.")
    doc.add_bullet("The Capture Thud:", "A deep, energetic bass thud when you capture an enemy piece.")
    doc.add_bullet("The Check Chime:", "A two-tone alert chime warning you that the King is in danger!")
    doc.add_bullet("The Victory Fanfare:", "A cheerful four-note musical chord when someone wins by checkmate.")

    doc.draw_section_header("app.js", "The Master Puppeteer (Client Brain)", icon="[E]")
    doc.add_paragraph(
        "app.js is the conductor of the orchestra in your browser. It connects the mouse, the board, "
        "the sounds, and the server into one smooth experience."
    )
    doc.add_bullet("Mouse & Touch Handling:", "Lets you drag pieces smoothly with your finger/mouse or click-to-move.")
    doc.add_bullet("Arrow Painter:", "Uses a transparent digital glass canvas overlay to draw a bright neon cyan arrow pointing to the engine's favorite move.")
    doc.add_bullet("Move Memory Table:", "Keeps track of every move played (1. e4 e5 2. Nf3...). You can click any move in the past to travel backwards in time!")

    # Grand Harmony Summary
    doc.draw_section_header("Summary", "The Grand Symphony: What Happens In 1 Second", icon="[*]")
    doc.add_callout(
        "WHEN YOU MOVE A PAWN FROM e2 TO e4:",
        "1. Your mouse drops the pawn on e4 -> app.js hears the click.\n"
        "2. sound.js plays a crisp wooden 'tock' sound.\n"
        "3. app.js sends a message to server.py across the local wire.\n"
        "4. server.py tells moves.py: 'Is this legal?' -> moves.py says YES!\n"
        "5. board.py moves the pawn on the internal grid.\n"
        "6. search.py wakes up, evaluates 50,000 futures in evaluate.py.\n"
        "7. server.py sends the answer back to app.js.\n"
        "8. style.css smoothly moves the Eval Bar, and app.js paints the best-move arrow!\n"
        "All of that happens in less than half a second!"
    )

    doc.save()

if __name__ == "__main__":
    build_chess_guide()
