# KBC Tollywood Quiz — PyQt6
# Features:
# - 20 Qs (8 easy, 7 medium, 5 hard) on iconic Tollywood movies
# - 2x2 answer grid with responsive layout & keyboard shortcuts (A-D)
# - 3 lifelines: 50-50, Computer Assist, Extra Life
# - Minimal dark theme, elegant animations (button glow, confetti, shake)
# - Background music loop + correct/wrong SFX (auto-disables if assets missing)
# - Price ladder with current highlight
# - Safe fallbacks if media backends are unavailable
#
# How to run:
#   pip install PyQt6
#   python main.py
#
# Optional assets (put under assets/):
#   assets/bgm.mp3           (looped background track)
#   assets/correct.wav       (SFX)
#   assets/wrong.wav         (SFX)
#
# Build EXE (Windows example):
#   pip install pyinstaller
#   pyinstaller --noconfirm --onefile --windowed \
#     --add-data "assets;assets" main.py
#
# NOTE: If fonts look too small/large, adjust BASE_FONT_SIZE below.

from __future__ import annotations
import sys, os, random, math
from dataclasses import dataclass
from typing import List, Tuple

from PyQt6.QtCore import (
    Qt, QTimer, QEasingCurve, QPoint, QRect, pyqtSignal, QSize
)
from PyQt6.QtGui import (
    QAction, QFont, QIcon, QPalette, QColor, QPainter, QPixmap, QGuiApplication,
    QMovie, QBrush, QFontMetricsF, QShortcut, QKeySequence, QCursor, QGuiApplication
)
from PyQt6.QtWidgets import (
    QApplication, QWidget, QMainWindow, QLabel, QPushButton, QVBoxLayout, QHBoxLayout,
    QGridLayout, QFrame, QMessageBox, QSizePolicy, QSpacerItem, QProgressBar, QGraphicsDropShadowEffect,
    QGraphicsColorizeEffect, QScrollArea
)

# Media (optional): use QMediaPlayer if available; otherwise silent fallback
try:
    from PyQt6.QtMultimedia import QAudioOutput, QSoundEffect, QMediaPlayer
    MULTIMEDIA_AVAILABLE = True
except Exception:
    MULTIMEDIA_AVAILABLE = False

BASE_FONT_SIZE = 16  # adjusts globally with window size

# ----------------------------- Data -----------------------------
@dataclass
class QA:
    q: str
    options: Tuple[str, str, str, str]
    answer_idx: int  # 0..3
    difficulty: str  # "easy" | "medium" | "hard"

# 20 questions: 8 easy, 7 medium, 5 hard
QUESTIONS: List[QA] = [
    # Easy (1-8)
    QA("In which movie did Mahesh Babu play the character 'Pokiri'?",
       ("Athadu", "Pokiri", "Okkadu", "Businessman"), 1, "easy"),
    QA("Which actor is known as 'Megastar' in Tollywood?",
       ("Chiranjeevi", "Balakrishna", "Nagarjuna", "Pawan Kalyan"), 0, "easy"),
    QA("The song 'Butta Bomma' is from which movie?",
       ("Ala Vaikunthapurramuloo", "DJ", "Sarrainodu", "Race Gurram"), 0, "easy"),
    QA("Who played the role of Baahubali in the Baahubali series?",
       ("Rana Daggubati", "Prabhas", "NTR Jr.", "Allu Arjun"), 1, "easy"),
    QA("In 'Arjun Reddy', who played the lead role?",
       ("Vijay Deverakonda", "Nani", "Sharwanand", "Varun Tej"), 0, "easy"),
    QA("'Pushpa: The Rise' stars which actor as Pushpa Raj?",
       ("Mahesh Babu", "Allu Arjun", "Ram Charan", "NTR Jr."), 1, "easy"),
    QA("The movie 'Magadheera' was directed by?",
       ("S. S. Rajamouli", "Trivikram", "Puri Jagannadh", "Sukumar"), 0, "easy"),
    QA("Which movie popularly uses the chant 'Jai Balayya'?",
       ("Simha", "Legend", "Akhanda", "Gautamiputra Satakarni"), 2, "easy"),

    # Medium (9-15)
    QA("In 'Srimanthudu', Mahesh Babu's character name is?",
       ("Harsha", "Ramesh", "Gopi", "Surya"), 0, "medium"),
    QA("Which Tollywood movie was a major sleeper hit and praised in 2023 for its rural drama?",
       ("RRR", "Dasara", "Balagam", "Karthikeya 2"), 2, "medium"),
    QA("'Eega' features which actor as the main villain?",
        ("Kichcha Sudeep", "Jagapathi Babu", "Sonu Sood", "Suman"), 0, "medium"),
    QA("Who composed the music for 'RRR'?",
       ("Devi Sri Prasad", "M. M. Keeravani", "Thaman S", "Anirudh"), 1, "medium"),
    QA("In 'Temper', which actor played the antagonist Daya's foil?",
       ("Prakash Raj", "Sonu Sood", "Posani", "Ajay"), 1, "medium"),
    QA("'Legend' is a film of which actor?",
       ("Chiranjeevi", "Nandamuri Balakrishna", "Venkatesh", "Ravi Teja"), 1, "medium"),
    QA("In 'Sye', students clash using which sport?",
       ("Cricket", "Football", "Rugby", "Kabaddi"), 2, "medium"),

    # Hard (16-20)
    QA("In which year was the classic 'Mayabazar' released?",
       ("1955", "1957", "1960", "1962"), 1, "hard"),
    QA("Who portrayed 'Kattappa' in Baahubali?",
       ("Sathyaraj", "Nassar", "Prabhakar", "Subbaraju"), 0, "hard"),
    QA("Which was among the earliest Telugu films to win National Award (Feature Film category) recognition?",
       ("Shankarabharanam", "Maa Bhoomi", "Pathala Bhairavi", "Bhuvan Shome"), 1, "hard"),
    QA("Who directed the classic 'Sankarabharanam'?",
       ("K. Viswanath", "Bapu", "K. Raghavendra Rao", "Dasari Narayana Rao"), 0, "hard"),
    QA("Which movie features the Brahmanandam character 'Galeejam'?",
       ("Ready", "Dhee", "King", "Race Gurram"), 1, "hard"),
]

PRICE_LADDER = [
    1000, 2000, 3000, 5000, 10000,
    20000, 40000, 80000, 160000, 320000,
    640000, 1250000, 2500000, 5000000, 10000000,
    20000000, 30000000, 40000000, 50000000, 100000000
]

SAFE_LEVELS = {4, 9, 14}  # after Q5, Q10, Q15 (0-indexed) — optional checkpoints

# ----------------------------- UI Helpers -----------------------------
DARK_BG = QColor("#0B132B")
DARK_CARD = QColor("#1C2541")
ACCENT = QColor("#F0C419")  # gold
TEXT = QColor("#EAEAEA")
WRONG = QColor("#D9534F")
RIGHT = QColor("#4CAF50")
NEUTRAL = QColor("#3A506B")

class ConfettiLayer(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.setStyleSheet("background: transparent;")
        self.particles: List[Tuple[float, float, float, float, str]] = []
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_particles)

    def start(self, bursts: int = 40):
        self.particles.clear()
        w, h = self.width(), self.height()
        emojis = ["🎉", "✨", "🎊", "🥳", "💥"]
        for _ in range(bursts):
            x = random.uniform(0, w)
            y = -random.uniform(0, 120)
            vy = random.uniform(2.0, 5.0)
            vx = random.uniform(-1.5, 1.5)
            ch = random.choice(emojis)
            self.particles.append([x, y, vx, vy, ch])
        self.timer.start(16)
        self.show()

    def update_particles(self):
        w, h = self.width(), self.height()
        alive = []
        for p in self.particles:
            p[0] += p[2]
            p[1] += p[3]
            p[2] *= 0.99
            if p[1] < h + 40:
                alive.append(p)
        self.particles = alive
        if not self.particles:
            self.timer.stop()
            self.hide()
        self.update()

    def paintEvent(self, e):
        painter = QPainter(self)
        painter.setRenderHints(QPainter.RenderHint.Antialiasing | QPainter.RenderHint.TextAntialiasing)
        font = painter.font()
        font.setPointSize(int(self.height() * 0.04))
        painter.setFont(font)
        for x, y, _, _, ch in self.particles:
            painter.drawText(QPoint(int(x), int(y)), ch)

class GlowButton(QPushButton):
    def __init__(self, text: str):
        super().__init__(text)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.setMinimumHeight(56)
        self.setStyleSheet(self.base_stylesheet(NEUTRAL))
        # Shadow
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(24)
        shadow.setColor(QColor(0, 0, 0, 140))
        shadow.setOffset(0, 6)
        self.setGraphicsEffect(shadow)

    def base_stylesheet(self, bg: QColor) -> str:
        return f"""
            QPushButton {{
                background-color: {bg.name()};
                color: {TEXT.name()};
                border: 2px solid #2E4372;
                border-radius: 14px;
                padding: 14px 18px;
                font-weight: 600;
            }}
            QPushButton:hover {{
                filter: brightness(1.06);
                border-color: {ACCENT.name()};
            }}
            QPushButton:disabled {{
                background-color: #2B3A55;
                color: #9BAEC8;
            }}
        """

    def set_bg(self, color: QColor):
        self.setStyleSheet(self.base_stylesheet(color))

class Tag(QLabel):
    def __init__(self, text: str, bg: QColor = NEUTRAL):
        super().__init__(text)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setStyleSheet(f"background:{bg.name()};color:{TEXT.name()};padding:6px 10px;border-radius:10px;font-weight:600;")

# ----------------------------- Main Window -----------------------------
class KBCWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("KBC — Tollywood Edition")
        self.resize(1100, 720)
        self.setMinimumSize(900, 620)
        self.setPalette(self._palette())
        self.extra_life_available = True
        self.lifelines = {
            "5050": True,
            "assist": True,
            "extra": True,
        }
        self.current_index = 0
        self.total_amount = 0
        self.safe_amount = 0

        # Media
        self.bgm_player = None
        self.sfx_correct = None
        self.sfx_wrong = None
        self._setup_media()

        # Central Layout
        central = QWidget()
        self.setCentralWidget(central)
        root = QHBoxLayout(central)
        root.setContentsMargins(16, 16, 16, 16)
        root.setSpacing(16)

        # Left: Price ladder
        self.ladder = QVBoxLayout()
        self.ladder.setSpacing(6)
        self.ladder_box = QFrame()
        self.ladder_box.setStyleSheet(f"background:{DARK_CARD.name()}; border-radius:16px;")
        ladder_wrap = QVBoxLayout(self.ladder_box)
        ladder_wrap.setContentsMargins(12, 12, 12, 12)
        ladder_wrap.addWidget(QLabel("Prize Ladder"))
        self.ladder_area = QVBoxLayout()
        ladder_wrap.addLayout(self.ladder_area)
        ladder_spacer = QSpacerItem(10, 10, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)
        ladder_wrap.addItem(ladder_spacer)
        self._build_ladder()

        # Center: Question + Answers
        center_box = QFrame()
        center_box.setStyleSheet(f"background:{DARK_CARD.name()}; border-radius:16px;")
        center = QVBoxLayout(center_box)
        center.setContentsMargins(16, 16, 16, 16)
        center.setSpacing(12)

        self.difficulty_tag = Tag("Easy", bg=RIGHT)
        self.amount_tag = Tag("₹0", bg=ACCENT)

        header = QHBoxLayout()
        header.addWidget(self.difficulty_tag)
        header.addStretch(1)
        header.addWidget(self.amount_tag)

        self.question_label = QLabel()
        self.question_label.setWordWrap(True)
        self.question_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.question_label.setStyleSheet(f"color:{TEXT.name()}; font-weight:700;")

        self.grid = QGridLayout()
        self.grid.setHorizontalSpacing(12)
        self.grid.setVerticalSpacing(12)

        self.btnA = GlowButton("A")
        self.btnB = GlowButton("B")
        self.btnC = GlowButton("C")
        self.btnD = GlowButton("D")
        for i, b in enumerate([self.btnA, self.btnB, self.btnC, self.btnD]):
            b.clicked.connect(lambda _=False, idx=i: self.select_option(idx))

        self.grid.addWidget(self.btnA, 0, 0)
        self.grid.addWidget(self.btnB, 0, 1)
        self.grid.addWidget(self.btnC, 1, 0)
        self.grid.addWidget(self.btnD, 1, 1)

        # Lifelines
        life_box = QHBoxLayout()
        life_box.setSpacing(8)
        self.life_5050 = GlowButton("50-50")
        self.life_5050.clicked.connect(self.use_5050)
        self.life_assist = GlowButton("Computer Assist")
        self.life_assist.clicked.connect(self.use_assist)
        self.life_extra = GlowButton("Extra Life")
        self.life_extra.clicked.connect(self.use_extra)
        for b in (self.life_5050, self.life_assist, self.life_extra):
            b.setMinimumHeight(44)
        life_box.addWidget(self.life_5050)
        life_box.addWidget(self.life_assist)
        life_box.addWidget(self.life_extra)

        center.addLayout(header)
        center.addWidget(self.question_label)
        center.addLayout(self.grid)
        center.addSpacing(8)
        center.addLayout(life_box)

        # Right: Status/Info
        right_box = QFrame()
        right_box.setStyleSheet(f"background:{DARK_CARD.name()}; border-radius:16px;")
        right = QVBoxLayout(right_box)
        right.setContentsMargins(12, 12, 12, 12)
        self.info_label = QLabel("Welcome to KBC — Tollywood Edition!\nAnswer wisely.")
        self.info_label.setWordWrap(True)
        self.info_label.setStyleSheet(f"color:{TEXT.name()};")
        right.addWidget(self.info_label)
        right.addStretch(1)

        root.addWidget(self.ladder_box, 1)
        root.addWidget(center_box, 2)
        root.addWidget(right_box, 1)

        # Confetti overlay
        self.confetti = ConfettiLayer(self)
        self.confetti.setGeometry(self.rect())
        self.confetti.hide()

        # Keyboard shortcuts
        QShortcut(QKeySequence("A"), self, activated=lambda: self.select_option(0))
        QShortcut(QKeySequence("B"), self, activated=lambda: self.select_option(1))
        QShortcut(QKeySequence("C"), self, activated=lambda: self.select_option(2))
        QShortcut(QKeySequence("D"), self, activated=lambda: self.select_option(3))

        self.load_question(0)

    # -------------- Media --------------
    def _setup_media(self):
        if not MULTIMEDIA_AVAILABLE:
            return
        assets = os.path.join(os.path.dirname(__file__), "assets")
        bgm = os.path.join(assets, "bgm.mp3")
        self.bgm_player = QMediaPlayer()
        if os.path.exists(bgm):
            try:
                from PyQt6.QtCore import QUrl
                self.audio_out = QAudioOutput()
                self.bgm_player.setAudioOutput(self.audio_out)
                self.bgm_player.setSource(QUrl.fromLocalFile(bgm))
                self.audio_out.setVolume(0.35)
                self.bgm_player.play()
                # loop timer
                self.loop_timer = QTimer(self)
                self.loop_timer.timeout.connect(lambda: self.bgm_player.play())
                self.loop_timer.start(60_000)  # naive loop; adjust to your track length
            except Exception:
                self.bgm_player = None
        # SFX
        assets = os.path.join(os.path.dirname(__file__), "assets")
        correct = os.path.join(assets, "correct.wav")
        wrong = os.path.join(assets, "wrong.wav")
        if os.path.exists(correct):
            self.sfx_correct = QSoundEffect()
            from PyQt6.QtCore import QUrl
            self.sfx_correct.setSource(QUrl.fromLocalFile(correct))
            self.sfx_correct.setVolume(0.8)
        if os.path.exists(wrong):
            self.sfx_wrong = QSoundEffect()
            from PyQt6.QtCore import QUrl
            self.sfx_wrong.setSource(QUrl.fromLocalFile(wrong))
            self.sfx_wrong.setVolume(0.8)

    # -------------- Ladder --------------
    def _build_ladder(self):
        # Clear
        while self.ladder_area.count():
            item = self.ladder_area.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()
        self.ladder_labels: List[QLabel] = []
        for i, amt in enumerate(reversed(PRICE_LADDER)):
            idx = len(PRICE_LADDER) - 1 - i
            lab = QLabel(f"{idx+1:02d}. ₹{amt:,}")
            lab.setStyleSheet(f"color:{TEXT.name()}; padding:4px 6px; border-radius:8px;")
            self.ladder_area.addWidget(lab)
            self.ladder_labels.append(lab)
        self._highlight_ladder(0)

    def _highlight_ladder(self, q_index: int):
        # Reset all
        total = len(PRICE_LADDER)
        for i, lab in enumerate(self.ladder_labels):
            lab.setStyleSheet(f"color:{TEXT.name()}; padding:4px 6px; border-radius:8px;")
        # Highlight current
        ri = total - 1 - q_index
        if 0 <= ri < len(self.ladder_labels):
            self.ladder_labels[ri].setStyleSheet(
                f"color:{DARK_BG.name()}; background:{ACCENT.name()}; padding:4px 6px; border-radius:8px; font-weight:700;"
            )

    # -------------- Core --------------
    def load_question(self, idx: int):
        self.current_index = idx
        qa = QUESTIONS[idx]
        self.question_label.setText(f"Q{idx+1}. {qa.q}")
        self.btnA.setText(f"A) {qa.options[0]}")
        self.btnB.setText(f"B) {qa.options[1]}")
        self.btnC.setText(f"C) {qa.options[2]}")
        self.btnD.setText(f"D) {qa.options[3]}")
        for b in (self.btnA, self.btnB, self.btnC, self.btnD):
            b.setEnabled(True)
            b.set_bg(NEUTRAL)
        # lifeline buttons reflect availability
        self.life_5050.setEnabled(self.lifelines["5050"]) 
        self.life_assist.setEnabled(self.lifelines["assist"]) 
        self.life_extra.setEnabled(self.lifelines["extra"]) 
        # difficulty tag
        diff = qa.difficulty.capitalize()
        color = RIGHT if qa.difficulty == "easy" else (ACCENT if qa.difficulty == "medium" else WRONG)
        self.difficulty_tag.setText(diff)
        self.difficulty_tag.setStyleSheet(f"background:{color.name()};color:{DARK_BG.name()};padding:6px 10px;border-radius:10px;font-weight:800;")
        # amount tag
        self.amount_tag.setText(f"₹{self.total_amount:,}")
        self._highlight_ladder(idx)
        self.info_label.setText("Choose your answer or use a lifeline.")

    def select_option(self, idx: int):
        # Ignore if disabled
        buttons = [self.btnA, self.btnB, self.btnC, self.btnD]
        if not buttons[idx].isEnabled():
            return
        qa = QUESTIONS[self.current_index]
        for b in buttons:
            b.setEnabled(False)
        is_correct = (idx == qa.answer_idx)
        if is_correct:
            buttons[idx].set_bg(RIGHT)
            self._play_correct()
            self._confetti()
            self.total_amount += PRICE_LADDER[self.current_index]
            self.amount_tag.setText(f"₹{self.total_amount:,}")
            if self.current_index in SAFE_LEVELS:
                self.safe_amount = self.total_amount
            QTimer.singleShot(1200, self._next)
        else:
            buttons[idx].set_bg(WRONG)
            buttons[qa.answer_idx].set_bg(RIGHT)
            self._play_wrong()
            if self.lifelines["extra"] is False and self.extra_life_available is False:
                # consumed already, fall through
                pass
            if self.lifelines["extra"] is False and self.extra_life_available is True:
                # shouldn't happen; flag safety
                pass
            # Extra life logic
            if self.lifelines["extra"] is False:
                # already used earlier, no protection now
                self._end_game(False)
            else:
                # consume extra life if available
                if self.extra_life_available:
                    self.extra_life_available = False
                    self.lifelines["extra"] = False
                    self.life_extra.setEnabled(False)
                    self.info_label.setText("Extra Life consumed! You may continue.")
                    QTimer.singleShot(1200, self._next)
                else:
                    self._end_game(False)

    def _next(self):
        if self.current_index + 1 >= len(QUESTIONS):
            self._end_game(True)
            return
        self.load_question(self.current_index + 1)

    def _end_game(self, completed: bool):
        msg = QMessageBox(self)
        msg.setWindowTitle("Game Over")
        if completed:
            msg.setText(f"🏆 Congratulations! You completed all questions!\nTotal Winnings: ₹{self.total_amount:,}")
        else:
            fallback = max(self.safe_amount, 0)
            msg.setText(f"❌ Wrong Answer!\nYou take home: ₹{fallback:,}")
            self.total_amount = fallback
        msg.setStandardButtons(QMessageBox.StandardButton.Ok)
        msg.exec()
        self.close()

    # -------------- Lifelines --------------
    def use_5050(self):
        if not self.lifelines["5050"]:
            return
        qa = QUESTIONS[self.current_index]
        wrongs = [i for i in range(4) if i != qa.answer_idx]
        remove = random.sample(wrongs, 2)
        buttons = [self.btnA, self.btnB, self.btnC, self.btnD]
        for i in remove:
            buttons[i].setEnabled(False)
            buttons[i].setText("—")
        self.lifelines["5050"] = False
        self.life_5050.setEnabled(False)
        self.info_label.setText("50-50 used: Two wrong options removed.")

    def use_assist(self):
        if not self.lifelines["assist"]:
            return
        qa = QUESTIONS[self.current_index]
        # Weighted suggestion: easier → higher certainty
        base = {"easy": 0.75, "medium": 0.6, "hard": 0.5}[qa.difficulty]
        probs = [ (1-base)/3 ] * 4
        probs[qa.answer_idx] = base
        # Convert to percentage-like and pick suggestion index
        suggestion = max(range(4), key=lambda i: probs[i] + random.uniform(0, 0.05))
        letters = ['A','B','C','D']
        pct = int(probs[suggestion]*100)
        self.info_label.setText(f"Computer suggests: Option {letters[suggestion]} (~{pct}%).")
        # Subtle flash on suggested button
        self._flash_button(suggestion, ACCENT)
        self.lifelines["assist"] = False
        self.life_assist.setEnabled(False)

    def use_extra(self):
        if not self.lifelines["extra"]:
            return
        self.extra_life_available = True
        self.lifelines["extra"] = True  # mark as armed; will be consumed on wrong
        self.life_extra.setEnabled(False)
        self.info_label.setText("Extra Life armed: one wrong answer will be forgiven.")

    # -------------- Effects --------------
    def _flash_button(self, idx: int, color: QColor):
        btn = [self.btnA, self.btnB, self.btnC, self.btnD][idx]
        original = NEUTRAL
        def seq(step=0):
            btn.set_bg(color if step % 2 == 0 else original)
            if step < 5:
                QTimer.singleShot(160, lambda: seq(step+1))
            else:
                btn.set_bg(original)
        seq(0)

    def _confetti(self):
        self.confetti.setGeometry(self.rect())
        self.confetti.start(50)

    def _play_correct(self):
        if MULTIMEDIA_AVAILABLE and self.sfx_correct:
            self.sfx_correct.play()

    def _play_wrong(self):
        if MULTIMEDIA_AVAILABLE and self.sfx_wrong:
            self.sfx_wrong.play()

    # -------------- Theming --------------
    def _palette(self):
        pal = QPalette()
        pal.setColor(QPalette.ColorRole.Window, DARK_BG)
        pal.setColor(QPalette.ColorRole.Base, DARK_BG)
        pal.setColor(QPalette.ColorRole.Button, DARK_CARD)
        pal.setColor(QPalette.ColorRole.Text, TEXT)
        pal.setColor(QPalette.ColorRole.WindowText, TEXT)
        return pal

    def resizeEvent(self, e):
        super().resizeEvent(e)
        self.confetti.setGeometry(self.rect())
        # responsive font scaling
        w = self.width()
        h = self.height()
        scale = max(0.8, min(1.6, (w*h)/(1100*720)))
        qf = self.question_label.font()
        qf.setPointSize(int(BASE_FONT_SIZE*1.2*scale))
        self.question_label.setFont(qf)
        for b in [self.btnA, self.btnB, self.btnC, self.btnD, self.life_5050, self.life_assist, self.life_extra]:
            f = b.font()
            f.setPointSize(int(BASE_FONT_SIZE*scale))
            b.setFont(f)

# ----------------------------- App Entry -----------------------------
if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setApplicationName("KBC Tollywood Quiz")

    win = KBCWindow()
    win.show()
    sys.exit(app.exec())
