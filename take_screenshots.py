"""
Capture screenshots of all game UI screens for the README.
Run with: python take_screenshots.py
"""
import sys
import time
import tkinter as tk
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from PIL import ImageGrab
import ctypes

OUT = Path(__file__).parent / "docs" / "screenshots"
OUT.mkdir(parents=True, exist_ok=True)

# DPI scale: Tkinter uses logical pixels, ImageGrab uses physical pixels
_SCALE = ctypes.windll.shcore.GetScaleFactorForDevice(0) / 100.0

# ── Theme ──────────────────────────────────────────────────────────────────────
BG       = "#1a1a2e"
ACCENT   = "#c8a951"
INPUT_BG = "#0f0f1a"
PANEL    = "#16213e"
BTN_BG   = "#2a2a4a"
FG       = "#e0e0e0"
DIM      = "#888888"
GREEN    = "#4caf50"
RED      = "#e05050"
BLUE     = "#5b8cdc"

FONT_TITLE = ("Segoe UI", 13, "bold")
FONT_HDR   = ("Segoe UI", 11, "bold")
FONT_BODY  = ("Segoe UI", 10)
FONT_SM    = ("Segoe UI", 9)
FONT_MONO  = ("Consolas", 10)


def grab(win, path):
    win.attributes("-topmost", True)
    win.lift()
    win.focus_force()
    win.update_idletasks()
    win.update()
    time.sleep(0.6)
    lx = win.winfo_rootx()
    ly = win.winfo_rooty()
    lw = win.winfo_width()
    lh = win.winfo_height()
    px, py = int(lx * _SCALE), int(ly * _SCALE)
    pw, ph = int(lw * _SCALE), int(lh * _SCALE)
    img = ImageGrab.grab(bbox=(px, py, px + pw, py + ph))
    img = img.resize((lw * 2, lh * 2), resample=1)
    img.save(path)
    print(f"  {path.name}  ({lw}x{lh})")
    win.destroy()


def _sec(parent, label):
    tk.Label(parent, text=label, font=("Segoe UI", 8, "bold"),
             bg=PANEL, fg=ACCENT).pack(anchor="w", padx=8, pady=(8, 2))
    tk.Frame(parent, bg=ACCENT, height=1).pack(fill="x", padx=8, pady=(0, 4))


def _btn_large(parent, icon, title, subtitle, highlight=False):
    bg = BTN_BG if not highlight else "#2a3a5a"
    f = tk.Frame(parent, bg=bg, cursor="hand2")
    f.pack(fill="x", padx=24, pady=6)
    inner = tk.Frame(f, bg=bg, padx=16, pady=12)
    inner.pack(fill="x")
    tk.Label(inner, text=f"{icon}  {title}", font=FONT_HDR,
             bg=bg, fg=ACCENT if highlight else FG).pack(anchor="w")
    tk.Label(inner, text=subtitle, font=FONT_SM, bg=bg, fg=DIM).pack(anchor="w")
    return f


# ── 01  Main Menu ──────────────────────────────────────────────────────────────
def shot_main_menu(root):
    win = tk.Toplevel(root, bg=BG)
    win.title("D&D AI Dungeon Master")
    win.geometry("460x380+50+50")
    win.resizable(False, False)

    tk.Label(win, text="⚔  D&D AI DUNGEON MASTER", font=FONT_TITLE,
             bg=BG, fg=ACCENT).pack(pady=(28, 4))
    tk.Label(win, text="What would you like to do?", font=FONT_SM,
             bg=BG, fg=DIM).pack(pady=(0, 12))

    _btn_large(win, "⚔", "New Adventure",
               "Create or select a character and start a new session.")
    _btn_large(win, "↑", "Next Adventure",
               "Carry a leveled character into a brand-new story.")
    _btn_large(win, "▶", "Resume Session",
               "Continue from a previously saved session.")

    grab(win, OUT / "01_startup.png")


# ── 02  Character Select ────────────────────────────────────────────────────────
def shot_character_select(root):
    win = tk.Toplevel(root, bg=BG)
    win.title("D&D AI Dungeon Master")
    win.geometry("460x430+50+50")
    win.resizable(False, False)

    tk.Label(win, text="⚔  SELECT CHARACTER", font=FONT_TITLE,
             bg=BG, fg=ACCENT).pack(pady=(24, 12))
    tk.Label(win, text="Choose a character to play:", font=FONT_SM,
             bg=BG, fg=DIM).pack(anchor="w", padx=30)

    lf = tk.Frame(win, bg=INPUT_BG)
    lf.pack(fill="x", padx=30, pady=6)
    sb = tk.Scrollbar(lf, bg=BG, troughcolor=INPUT_BG)
    sb.pack(side="right", fill="y")
    lb = tk.Listbox(lf, bg=INPUT_BG, fg=FG, font=FONT_BODY,
                    selectbackground=ACCENT, selectforeground="#1a1a2e",
                    relief="flat", bd=0, activestyle="none",
                    exportselection=False, yscrollcommand=sb.set, height=8)
    sb.config(command=lb.yview)
    lb.pack(fill="x", padx=4, pady=4)
    for name in ("Theron Ashvale", "Lyra Moonwhisper", "Dorn Ironforge"):
        lb.insert("end", name)
    lb.select_set(0)

    btn_row = tk.Frame(win, bg=BG)
    btn_row.pack(fill="x", padx=30, pady=8)
    for lbl, side in (("+ New Character", "left"), ("Delete", "left")):
        tk.Button(btn_row, text=lbl, font=FONT_SM, bg=BTN_BG, fg=FG,
                  relief="flat", padx=10, pady=5,
                  activebackground=ACCENT, activeforeground="#1a1a2e"
                  ).pack(side=side, padx=(0, 6))
    tk.Button(btn_row, text="← Back", font=FONT_SM, bg=BTN_BG, fg=FG,
              relief="flat", padx=10, pady=5).pack(side="right")
    tk.Button(btn_row, text="Begin →", font=FONT_SM, bg=ACCENT, fg="#1a1a2e",
              relief="flat", padx=14, pady=5).pack(side="right", padx=(0, 6))

    grab(win, OUT / "02_character_select.png")


# ── 14  Adventure Preset ────────────────────────────────────────────────────────
def shot_preset(root):
    win = tk.Toplevel(root, bg=BG)
    win.title("D&D AI Dungeon Master")
    win.geometry("460x420+50+50")
    win.resizable(False, False)

    tk.Label(win, text="⚔  CHOOSE YOUR ADVENTURE", font=FONT_TITLE,
             bg=BG, fg=ACCENT).pack(pady=(24, 4))
    tk.Label(win, text="How long do you want to play?", font=FONT_SM,
             bg=BG, fg=DIM).pack(pady=(0, 14))

    presets = [
        ("◈", "Epic",     "~5–8 hours",
         "A multi-session campaign.\nSubplots, deep NPCs, slow-burn tension.", False),
        ("◆", "Quest",    "~3–4 hours",
         "A full adventure arc in one sitting.\nHook → 3 acts → climax → resolution.", True),
        ("◇", "One Shot", "~1–2 hours",
         "Quick and compact.\nStarts tense, races to the final confrontation.", False),
    ]
    for icon, title, est, desc, selected in presets:
        bg = "#243050" if selected else BTN_BG
        border = ACCENT if selected else BTN_BG
        f = tk.Frame(win, bg=border, padx=2, pady=2)
        f.pack(fill="x", padx=24, pady=4)
        inner = tk.Frame(f, bg=bg, padx=14, pady=10)
        inner.pack(fill="x")
        header = tk.Frame(inner, bg=bg)
        header.pack(fill="x")
        tk.Label(header, text=f"{icon}  {title}", font=FONT_HDR,
                 bg=bg, fg=ACCENT).pack(side="left")
        tk.Label(header, text=est, font=FONT_SM, bg=bg, fg=DIM).pack(side="right")
        tk.Label(inner, text=desc, font=("Segoe UI", 8), bg=bg,
                 fg=FG, justify="left").pack(anchor="w")

    btn_row = tk.Frame(win, bg=BG)
    btn_row.pack(fill="x", padx=24, pady=(12, 0))
    tk.Button(btn_row, text="← Back", font=FONT_SM, bg=BTN_BG, fg=FG,
              relief="flat", padx=10, pady=5).pack(side="left")
    tk.Button(btn_row, text="Begin Adventure →", font=FONT_SM, bg=ACCENT,
              fg="#1a1a2e", relief="flat", padx=14, pady=5).pack(side="right")

    grab(win, OUT / "14_preset_select.png")


# ── 06  Main Game Interface ─────────────────────────────────────────────────────
def shot_main_game(root):
    win = tk.Toplevel(root, bg=BG)
    win.title("D&D AI Dungeon Master")
    win.geometry("900x560+50+50")
    win.resizable(False, False)

    # Header
    hdr = tk.Frame(win, bg=PANEL, pady=6)
    hdr.pack(fill="x")
    tk.Label(hdr, text="Theron Ashvale  —  Human Fighter  Lv.5",
             font=FONT_HDR, bg=PANEL, fg=ACCENT).pack(side="left", padx=14)
    tk.Label(hdr, text="The Thornwood  ·  Quest: Act 2",
             font=FONT_SM, bg=PANEL, fg=DIM).pack(side="left", padx=8)
    tk.Button(hdr, text="DEV", font=("Segoe UI", 8), bg=BTN_BG, fg=DIM,
              relief="flat", padx=6).pack(side="right", padx=8)

    content = tk.Frame(win, bg=BG)
    content.pack(fill="both", expand=True)

    # Narration
    narr = tk.Frame(content, bg=INPUT_BG)
    narr.pack(side="left", fill="both", expand=True)
    txt = tk.Text(narr, bg=INPUT_BG, fg=FG, font=FONT_MONO,
                  relief="flat", bd=0, wrap="word", padx=16, pady=14,
                  state="normal", cursor="arrow")
    txt.pack(fill="both", expand=True)
    story = (
        "The Thornwood closes around you as the path narrows. Twisted oaks lean\n"
        "overhead, their branches knitted into a canopy that blots out the sky.\n\n"
        "> I press forward, scanning the treeline for movement.\n\n"
        "Your hand drops to your sword hilt. The forest is unnaturally quiet — no\n"
        "birdsong, no rustling. Then you see it: a flicker of torchlight through\n"
        "the trees ahead, and the low murmur of voices.\n\n"
        "Two figures crouch around a small fire. One wears a tattered tabard\n"
        "bearing the crest of the Silver Star Order — torn, bloodied. He clutches\n"
        "something to his chest. The other is watching the road with a crossbow\n"
        "resting across his knees.\n\n"
        "Give me a Stealth check if you want to get closer without being spotted.\n\n"
        "What do you do?\n"
    )
    txt.insert("1.0", story)
    txt.tag_configure("player", foreground=BLUE)
    txt.tag_add("player", "3.0", "3.end")
    txt.config(state="disabled")

    sb_scroll = tk.Scrollbar(narr, bg=BG, troughcolor=INPUT_BG)
    sb_scroll.pack(side="right", fill="y")

    # Sidebar
    side = tk.Frame(content, bg=PANEL, width=220)
    side.pack(side="right", fill="y")
    side.pack_propagate(False)

    sb_inner = tk.Frame(side, bg=PANEL)
    sb_inner.pack(fill="both", expand=True)

    _sec(sb_inner, "CHARACTER")
    tk.Label(sb_inner, text="Theron Ashvale", font=FONT_SM, bg=PANEL, fg=FG).pack(anchor="w", padx=10)
    tk.Label(sb_inner, text="Human Fighter (Champion)", font=("Segoe UI", 8), bg=PANEL, fg=DIM).pack(anchor="w", padx=10)
    tk.Label(sb_inner, text="Level 5  ·  Soldier", font=("Segoe UI", 8), bg=PANEL, fg=DIM).pack(anchor="w", padx=10, pady=(0, 4))

    _sec(sb_inner, "VITALS")
    tk.Label(sb_inner, text="HP: 47 / 52", font=FONT_HDR, bg=PANEL, fg=GREEN).pack(anchor="w", padx=10)
    hp_bar = tk.Canvas(sb_inner, bg=BTN_BG, height=6, bd=0, highlightthickness=0)
    hp_bar.pack(fill="x", padx=10, pady=(2, 4))
    hp_bar.update()
    hp_bar.create_rectangle(0, 0, int(hp_bar.winfo_width() * 0.9), 6, fill=GREEN, outline="")
    row = tk.Frame(sb_inner, bg=PANEL)
    row.pack(anchor="w", padx=10, pady=(0, 4))
    for lbl in ("AC 17", "Spd 30", "Init +2"):
        tk.Label(row, text=lbl, font=FONT_SM, bg=PANEL, fg=FG).pack(side="left", padx=(0, 10))
    tk.Label(sb_inner, text="Conditions: —", font=FONT_SM, bg=PANEL, fg=DIM).pack(anchor="w", padx=10, pady=(0, 2))
    tk.Label(sb_inner, text="XP: 6500 / 14000  (Lv5→6)", font=("Segoe UI", 8), bg=PANEL, fg=DIM).pack(anchor="w", padx=10, pady=(0, 2))
    xp_bar = tk.Canvas(sb_inner, bg=BTN_BG, height=4, bd=0, highlightthickness=0)
    xp_bar.pack(fill="x", padx=10, pady=(0, 4))
    xp_bar.update()
    xp_bar.create_rectangle(0, 0, int(xp_bar.winfo_width() * 0.46), 4, fill=ACCENT, outline="")

    _sec(sb_inner, "FEATURES")
    for fname, cur, mx in (("Action Surge", "1", "1"), ("Second Wind", "1", "1")):
        fr = tk.Frame(sb_inner, bg=PANEL)
        fr.pack(anchor="w", padx=10, pady=1)
        tk.Label(fr, text=fname, font=FONT_SM, bg=PANEL, fg=FG).pack(side="left")
        tk.Label(fr, text=f" [{cur}/{mx}]", font=FONT_SM, bg=PANEL, fg=ACCENT).pack(side="left")

    _sec(sb_inner, "INVENTORY")
    tk.Label(sb_inner, text="1pp  47gp  3sp", font=FONT_SM, bg=PANEL, fg=FG).pack(anchor="w", padx=10, pady=(0, 2))
    items_f = tk.Frame(sb_inner, bg=PANEL)
    items_f.pack(fill="x", padx=6, pady=(0, 4))
    tk.Label(items_f, text="✦ +1 Longsword +1", font=("Segoe UI", 8), bg=PANEL, fg=ACCENT).pack(anchor="w")

    _sec(sb_inner, "ATTACKS")
    for atk, dmg in (("⚔ +1 Longsword  +8", "1d8+5"), ("⚔ Handaxe  +7", "1d6+4")):
        r = tk.Frame(sb_inner, bg=BTN_BG)
        r.pack(fill="x", padx=8, pady=2)
        tk.Label(r, text=atk, font=FONT_SM, bg=BTN_BG, fg=FG, padx=6, pady=3).pack(side="left")
        tk.Label(r, text=dmg, font=FONT_SM, bg=BTN_BG, fg=DIM).pack(side="right", padx=6)

    # Input bar
    inp = tk.Frame(win, bg=BTN_BG, pady=8)
    inp.pack(fill="x", side="bottom")
    entry = tk.Entry(inp, bg=INPUT_BG, fg=DIM, font=FONT_BODY,
                     relief="flat", bd=0, insertbackground=ACCENT)
    entry.pack(side="left", fill="x", expand=True, padx=(12, 8), ipady=5)
    entry.insert(0, "What do you do?  You can also ask questions.")
    tk.Button(inp, text="Send", font=FONT_SM, bg=ACCENT, fg="#1a1a2e",
              relief="flat", padx=14, pady=5).pack(side="right", padx=8)

    grab(win, OUT / "06_main_game.png")


# ── 07  Full Sidebar ────────────────────────────────────────────────────────────
def shot_sidebar(root):
    win = tk.Toplevel(root, bg=PANEL)
    win.title("Sidebar")
    win.geometry("230x680+50+50")
    win.resizable(False, False)

    _sec(win, "CHARACTER")
    tk.Label(win, text="Theron Ashvale", font=FONT_SM, bg=PANEL, fg=FG).pack(anchor="w", padx=10)
    tk.Label(win, text="Human Fighter (Champion)", font=("Segoe UI", 8), bg=PANEL, fg=DIM).pack(anchor="w", padx=10)
    tk.Label(win, text="Level 5  ·  Soldier", font=("Segoe UI", 8), bg=PANEL, fg=DIM).pack(anchor="w", padx=10, pady=(0, 2))

    _sec(win, "VITALS")
    tk.Label(win, text="HP: 47 / 52", font=FONT_HDR, bg=PANEL, fg=GREEN).pack(anchor="w", padx=10)
    hp_c = tk.Canvas(win, bg=BTN_BG, height=6, bd=0, highlightthickness=0)
    hp_c.pack(fill="x", padx=10, pady=(2, 4))
    hp_c.update()
    hp_c.create_rectangle(0, 0, int(hp_c.winfo_width() * 0.9), 6, fill=GREEN, outline="")
    row = tk.Frame(win, bg=PANEL)
    row.pack(anchor="w", padx=10, pady=(0, 2))
    for lbl in ("AC 17", "Spd 30", "Init +2"):
        tk.Label(row, text=lbl, font=FONT_SM, bg=PANEL, fg=FG).pack(side="left", padx=(0, 10))
    tk.Label(win, text="XP: 6500 / 14000  (Lv5→6)", font=("Segoe UI", 8), bg=PANEL, fg=DIM).pack(anchor="w", padx=10, pady=(0, 2))

    _sec(win, "ABILITIES")
    ab_f = tk.Frame(win, bg=PANEL)
    ab_f.pack(padx=8, pady=(0, 4))
    for row_data in [("STR\n16\n(+3)", "DEX\n12\n(+1)", "CON\n14\n(+2)"),
                     ("INT\n10\n(+0)", "WIS\n11\n(+0)", "CHA\n10\n(+0)")]:
        r = tk.Frame(ab_f, bg=PANEL)
        r.pack()
        for ab in row_data:
            c = tk.Frame(r, bg=BTN_BG, padx=8, pady=4)
            c.pack(side="left", padx=3, pady=2)
            tk.Label(c, text=ab, font=("Segoe UI", 8), bg=BTN_BG, fg=FG,
                     justify="center").pack()

    _sec(win, "FEATURES")
    for fname, cur, mx in (("Action Surge", "1", "1"), ("Second Wind", "1", "1"),
                            ("Extra Attack", "—", "—")):
        fr = tk.Frame(win, bg=PANEL)
        fr.pack(anchor="w", padx=10, pady=1)
        tk.Label(fr, text=fname, font=FONT_SM, bg=PANEL, fg=FG).pack(side="left")
        if cur != "—":
            tk.Label(fr, text=f" [{cur}/{mx}]", font=FONT_SM, bg=PANEL, fg=ACCENT).pack(side="left")

    _sec(win, "INVENTORY")
    tk.Label(win, text="1pp  47gp  3sp", font=FONT_SM, bg=PANEL, fg=FG).pack(anchor="w", padx=10, pady=(0, 2))
    items_f = tk.Frame(win, bg=PANEL)
    items_f.pack(fill="x", padx=6, pady=(0, 4))
    tk.Label(items_f, text="✦ +1 Longsword +1", font=("Segoe UI", 8), bg=PANEL, fg=ACCENT).pack(anchor="w")
    tk.Label(items_f, text="✦ Shield of Protection +1 AC", font=("Segoe UI", 8), bg=PANEL, fg=ACCENT).pack(anchor="w")

    _sec(win, "ATTACKS")
    for atk, dmg in (("⚔ +1 Longsword  +8", "1d8+5"), ("⚔ Handaxe  +7", "1d6+4")):
        r = tk.Frame(win, bg=BTN_BG)
        r.pack(fill="x", padx=8, pady=2)
        tk.Label(r, text=atk, font=FONT_SM, bg=BTN_BG, fg=FG, padx=6, pady=3).pack(side="left")
        tk.Label(r, text=dmg, font=FONT_SM, bg=BTN_BG, fg=DIM).pack(side="right", padx=6)

    grab(win, OUT / "07_sidebar.png")


# ── 09  Combat narration ────────────────────────────────────────────────────────
def shot_combat(root):
    win = tk.Toplevel(root, bg=BG)
    win.title("D&D AI Dungeon Master")
    win.geometry("900x560+50+50")
    win.resizable(False, False)

    hdr = tk.Frame(win, bg=PANEL, pady=6)
    hdr.pack(fill="x")
    tk.Label(hdr, text="Theron Ashvale  —  Human Fighter  Lv.5",
             font=FONT_HDR, bg=PANEL, fg=ACCENT).pack(side="left", padx=14)
    tk.Label(hdr, text="The Thornwood  ·  ⚔ COMBAT",
             font=FONT_SM, bg=PANEL, fg=RED).pack(side="left", padx=8)

    content = tk.Frame(win, bg=BG)
    content.pack(fill="both", expand=True)

    narr = tk.Frame(content, bg=INPUT_BG)
    narr.pack(side="left", fill="both", expand=True)
    txt = tk.Text(narr, bg=INPUT_BG, fg=FG, font=FONT_MONO,
                  relief="flat", bd=0, wrap="word", padx=16, pady=14,
                  state="normal", cursor="arrow")
    txt.pack(fill="both", expand=True)
    story = (
        "⚔  Combat begins!\n\n"
        "Initiative order:\n"
        "  1. Theron Ashvale (rolled 14 + 2 = 16)\n"
        "  2. Hobgoblin Captain (rolled 11 + 2 = 13)\n"
        "  3. Goblin Scout A (rolled 5 + 2 = 7)\n"
        "  4. Goblin Scout B (rolled 3 + 2 = 5)\n\n"
        "The Hobgoblin Captain spins toward you, barking a command to the\n"
        "goblins. He levels his blade — pitted iron, but held with the\n"
        "confidence of someone who has used it before.\n\n"
        "It is Theron's turn!  What do you do?\n"
    )
    txt.insert("1.0", story)
    txt.config(state="disabled")

    # Sidebar
    side = tk.Frame(content, bg=PANEL, width=220)
    side.pack(side="right", fill="y")
    side.pack_propagate(False)

    _sec(side, "VITALS")
    tk.Label(side, text="HP: 47 / 52", font=FONT_HDR, bg=PANEL, fg=GREEN).pack(anchor="w", padx=10)
    hp_c = tk.Canvas(side, bg=BTN_BG, height=6, bd=0, highlightthickness=0)
    hp_c.pack(fill="x", padx=10, pady=(2, 4))
    hp_c.update()
    hp_c.create_rectangle(0, 0, int(hp_c.winfo_width() * 0.9), 6, fill=GREEN, outline="")
    row = tk.Frame(side, bg=PANEL)
    row.pack(anchor="w", padx=10, pady=(0, 4))
    for lbl in ("AC 18", "Spd 30"):
        tk.Label(row, text=lbl, font=FONT_SM, bg=PANEL, fg=FG).pack(side="left", padx=(0, 10))

    _sec(side, "ATTACKS")
    for atk, dmg in (("⚔ +1 Longsword  +8", "1d8+5"), ("⚔ Handaxe  +7", "1d6+4")):
        r = tk.Frame(side, bg=ACCENT)
        r.pack(fill="x", padx=8, pady=2)
        tk.Label(r, text=atk, font=FONT_SM, bg=ACCENT, fg="#1a1a2e", padx=6, pady=4).pack(side="left")
        tk.Label(r, text=dmg, font=FONT_SM, bg=ACCENT, fg="#1a1a2e").pack(side="right", padx=6)

    _sec(side, "COMBAT")
    combatants = [("▶ Theron Ashvale", "47/52", GREEN, True),
                  ("  Hobgoblin Captain", "39/39", FG, False),
                  ("  Goblin Scout A", "7/7", FG, False),
                  ("  Goblin Scout B", "7/7", FG, False)]
    for name, hp, col, active in combatants:
        cr = tk.Frame(side, bg=PANEL)
        cr.pack(fill="x", padx=10, pady=1)
        tk.Label(cr, text=name, font=FONT_SM, bg=PANEL,
                 fg=ACCENT if active else FG).pack(side="left")
        tk.Label(cr, text=hp, font=FONT_SM, bg=PANEL, fg=col).pack(side="right")

    # Input row with ⚔ Actions button
    inp = tk.Frame(win, bg=BTN_BG, pady=8)
    inp.pack(fill="x", side="bottom")
    tk.Button(inp, text="⚔ Actions", font=FONT_SM, bg=BTN_BG, fg=ACCENT,
              relief="flat", padx=10, pady=5).pack(side="left", padx=(8, 4))
    entry = tk.Entry(inp, bg=INPUT_BG, fg=DIM, font=FONT_BODY,
                     relief="flat", bd=0, insertbackground=ACCENT)
    entry.pack(side="left", fill="x", expand=True, padx=4, ipady=5)
    entry.insert(0, "Describe your action...")
    tk.Button(inp, text="✦ Spells", font=FONT_SM, bg=BTN_BG, fg=BLUE,
              relief="flat", padx=10, pady=5).pack(side="right", padx=(4, 4))
    tk.Button(inp, text="→", font=FONT_SM, bg=ACCENT, fg="#1a1a2e",
              relief="flat", padx=10, pady=5).pack(side="right", padx=(0, 8))

    grab(win, OUT / "09_combat.png")


# ── 10  Combat Sidebar ──────────────────────────────────────────────────────────
def shot_combat_sidebar(root):
    win = tk.Toplevel(root, bg=PANEL)
    win.title("Combat Sidebar")
    win.geometry("230x580+50+50")
    win.resizable(False, False)

    _sec(win, "VITALS")
    tk.Label(win, text="HP: 47 / 52", font=FONT_HDR, bg=PANEL, fg=GREEN).pack(anchor="w", padx=10)
    hp_c = tk.Canvas(win, bg=BTN_BG, height=6, bd=0, highlightthickness=0)
    hp_c.pack(fill="x", padx=10, pady=(2, 4))
    hp_c.update()
    hp_c.create_rectangle(0, 0, int(hp_c.winfo_width() * 0.9), 6, fill=GREEN, outline="")
    row = tk.Frame(win, bg=PANEL)
    row.pack(anchor="w", padx=10, pady=(0, 4))
    for lbl in ("AC 18", "Spd 30", "Init +2"):
        tk.Label(row, text=lbl, font=FONT_SM, bg=PANEL, fg=FG).pack(side="left", padx=(0, 10))

    _sec(win, "FEATURES")
    for fname, val in (("Action Surge", "[1/1]"), ("Second Wind", "[1/1]")):
        fr = tk.Frame(win, bg=PANEL)
        fr.pack(anchor="w", padx=10, pady=1)
        tk.Label(fr, text=fname, font=FONT_SM, bg=PANEL, fg=FG).pack(side="left")
        tk.Label(fr, text=f" {val}", font=FONT_SM, bg=PANEL, fg=ACCENT).pack(side="left")

    _sec(win, "INVENTORY")
    tk.Label(win, text="47gp", font=FONT_SM, bg=PANEL, fg=FG).pack(anchor="w", padx=10, pady=(0, 2))
    tk.Label(win, text="✦ +1 Longsword +1", font=("Segoe UI", 8), bg=PANEL, fg=ACCENT).pack(anchor="w", padx=10)

    _sec(win, "ATTACKS")
    for atk, dmg in (("⚔ +1 Longsword  +8", "1d8+5"), ("⚔ Handaxe  +7", "1d6+4")):
        r = tk.Frame(win, bg=ACCENT)
        r.pack(fill="x", padx=8, pady=2)
        tk.Label(r, text=atk, font=FONT_SM, bg=ACCENT, fg="#1a1a2e", padx=6, pady=4).pack(side="left")
        tk.Label(r, text=dmg, font=FONT_SM, bg=ACCENT, fg="#1a1a2e").pack(side="right", padx=6)

    _sec(win, "COMBAT")
    combatants = [("▶ Theron Ashvale", "47/52", GREEN, True),
                  ("  Hobgoblin Captain", "39/39", FG, False),
                  ("  Goblin Scout A", "7/7", FG, False),
                  ("  Goblin Scout B", "7/7", FG, False)]
    for name, hp, col, active in combatants:
        cr = tk.Frame(win, bg=PANEL)
        cr.pack(fill="x", padx=10, pady=1)
        tk.Label(cr, text=name, font=FONT_SM, bg=PANEL,
                 fg=ACCENT if active else FG).pack(side="left")
        tk.Label(cr, text=hp, font=FONT_SM, bg=PANEL, fg=col).pack(side="right")

    tk.Button(win, text="Save & Quit", font=FONT_SM, bg=BTN_BG, fg=FG,
              relief="flat", pady=5).pack(fill="x", padx=8, pady=8)

    grab(win, OUT / "10_combat_sidebar.png")


# ── 15  Level-Up: Features step ─────────────────────────────────────────────────
def shot_level_up(root):
    win = tk.Toplevel(root, bg=BG)
    win.title("Level Up!")
    win.geometry("430x480+50+50")
    win.resizable(False, False)

    body = tk.Frame(win, bg=BG, padx=20, pady=16)
    body.pack(fill="both", expand=True)

    tk.Label(body, text="🎉  Level 6!", font=("Segoe UI", 14, "bold"),
             bg=BG, fg=ACCENT).pack(anchor="w", pady=(0, 4))
    tk.Label(body, text="Theron Ashvale  —  Human Fighter",
             font=FONT_SM, bg=BG, fg=DIM).pack(anchor="w", pady=(0, 12))

    tk.Label(body, text="New Features Gained", font=FONT_HDR,
             bg=BG, fg=FG).pack(anchor="w", pady=(0, 8))

    features = [
        ("Extra Attack (2)",
         "You can attack three times instead of twice when you take the Attack action."),
        ("Ability Score Improvement",
         "Your ability scores can be improved or you may take a feat. (Next step)"),
    ]
    for fname, fdesc in features:
        ff = tk.Frame(body, bg=BTN_BG)
        ff.pack(fill="x", pady=4)
        tk.Label(ff, text=fname, font=("Segoe UI", 9, "bold"),
                 bg=BTN_BG, fg=ACCENT, padx=10, pady=4).pack(anchor="w")
        tk.Label(ff, text=fdesc, font=("Segoe UI", 8), bg=BTN_BG, fg=FG,
                 padx=10, wraplength=370, justify="left").pack(anchor="w", pady=(0, 6))

    tk.Label(body, text="", bg=BG).pack()

    tk.Label(body, text="HP Roll — d10 + CON modifier",
             font=FONT_HDR, bg=BG, fg=FG).pack(anchor="w", pady=(4, 6))

    roll_f = tk.Frame(body, bg=BG)
    roll_f.pack(anchor="w")
    tk.Label(roll_f, text="Rolled: ", font=FONT_SM, bg=BG, fg=DIM).pack(side="left")
    tk.Label(roll_f, text="8", font=("Segoe UI", 18, "bold"),
             bg=BG, fg=ACCENT).pack(side="left")
    tk.Label(roll_f, text=" + 2 (CON)  =  ", font=FONT_SM, bg=BG, fg=DIM).pack(side="left")
    tk.Label(roll_f, text="+10 HP", font=("Segoe UI", 12, "bold"),
             bg=BG, fg=GREEN).pack(side="left")

    btn_row = tk.Frame(body, bg=BG)
    btn_row.pack(fill="x", pady=(16, 0))
    tk.Button(btn_row, text="Roll HP Die", font=FONT_SM, bg=BTN_BG, fg=FG,
              relief="flat", padx=14, pady=6).pack(side="left")
    tk.Button(btn_row, text="Take Average (+6)", font=FONT_SM, bg=BTN_BG, fg=DIM,
              relief="flat", padx=14, pady=6).pack(side="left", padx=8)
    tk.Button(btn_row, text="Next →", font=FONT_SM, bg=ACCENT, fg="#1a1a2e",
              relief="flat", padx=14, pady=6).pack(side="right")

    grab(win, OUT / "15_level_up.png")


# ── Feat + Spell pickers (unchanged from before) ───────────────────────────────
def shot_feat_picker(root):
    FEATS = {
        "Alert":              "+5 initiative; can't be surprised; no advantage vs you for hidden attackers.",
        "Great Weapon Master":"On crit or kill, bonus action attack; take -5 to hit for +10 damage.",
        "Lucky":              "3 luck points per long rest; reroll attack/ability/save or force reroll.",
        "Mobile":             "+10 ft speed; Dash ignores difficult terrain; no opp. attacks from creatures you attack.",
        "Resilient":          "+1 to chosen ability; gain proficiency in that ability's saving throw.",
        "Sentinel":           "Opportunity attacks reduce speed to 0; can opp. attack even when target Disengages.",
        "Sharpshooter":       "Ignore long range and half/three-quarter cover; -5 attack for +10 damage.",
        "Tough":              "HP max increases by 2 per level (applied immediately, retroactive).",
        "War Caster":         "Advantage on Concentration saves; somatic components with hands full.",
        "Weapon Master":      "+1 STR or DEX; gain proficiency with 4 weapons of your choice.",
    }
    feat_names = sorted(FEATS.keys())

    win = tk.Toplevel(root, bg=BG)
    win.title("Level Up — Ability Score Improvement or Feat")
    win.geometry("430x490+50+50")
    win.resizable(False, False)

    body = tk.Frame(win, bg=BG, padx=20, pady=16)
    body.pack(fill="both", expand=True)

    tk.Label(body, text="Ability Score Improvement or Feat",
             font=FONT_HDR, bg=BG, fg=ACCENT).pack(anchor="w", pady=(0, 8))

    mode_var = tk.StringVar(value="feat")
    for val, lbl in (("plus2", "+2 to one ability"), ("plus1each", "+1 to two abilities"), ("feat", "Take a Feat")):
        tk.Radiobutton(body, text=lbl, variable=mode_var, value=val,
                       bg=BG, fg=FG, selectcolor=BTN_BG, activebackground=BG,
                       font=FONT_SM).pack(anchor="w")

    tk.Frame(body, bg=BG, height=6).pack()

    lf = tk.Frame(body, bg=INPUT_BG)
    lf.pack(fill="x")
    sb = tk.Scrollbar(lf, bg=BG, troughcolor=INPUT_BG)
    sb.pack(side="right", fill="y")
    lb = tk.Listbox(lf, bg=INPUT_BG, fg=FG, font=FONT_SM,
                    selectbackground=ACCENT, selectforeground="#1a1a2e",
                    relief="flat", bd=0, activestyle="none",
                    exportselection=False, yscrollcommand=sb.set, height=8)
    sb.config(command=lb.yview)
    lb.pack(fill="x", padx=4, pady=4)
    for fn in feat_names:
        lb.insert("end", fn)
    lb.select_set(feat_names.index("Sentinel"))

    tk.Label(body, text=FEATS["Sentinel"],
             font=("Segoe UI", 8), bg=BG, fg=DIM,
             wraplength=380, justify="left").pack(anchor="w", pady=(6, 4))

    tk.Label(body, text="", font=FONT_SM, bg=BG, fg=RED).pack(anchor="w")

    tk.Button(body, text="Confirm →", font=FONT_SM,
              bg=BTN_BG, fg=FG, relief="flat", padx=16, pady=6,
              activebackground=ACCENT, activeforeground="#1a1a2e").pack(side="right", pady=(8, 0))

    grab(win, OUT / "12_feat_picker.png")


def shot_spell_picker(root):
    win = tk.Toplevel(root, bg=BG)
    win.title("Level Up — Spellcasting")
    win.geometry("430x460+50+50")
    win.resizable(False, False)

    body = tk.Frame(win, bg=BG, padx=20, pady=16)
    body.pack(fill="both", expand=True)

    tk.Label(body, text="Spellcasting", font=FONT_HDR, bg=BG, fg=ACCENT).pack(anchor="w", pady=(0, 4))
    tk.Label(body, text="Your spell slots:", font=FONT_SM, bg=BG, fg=DIM).pack(anchor="w", pady=(0, 2))
    for line in ("Level 1: 4 slots", "Level 2: 3 slots", "Level 3: 2 slots"):
        tk.Label(body, text=f"  {line}", font=FONT_SM, bg=BG, fg=FG).pack(anchor="w")
    tk.Label(body, text="", bg=BG).pack()
    tk.Label(body, text="Choose up to 1 spell to learn:",
             font=FONT_SM, bg=BG, fg=DIM).pack(anchor="w", pady=(0, 4))

    lf2 = tk.Frame(body, bg=INPUT_BG)
    lf2.pack(fill="both", expand=True)
    sb2 = tk.Scrollbar(lf2, bg=BG, troughcolor=INPUT_BG)
    sb2.pack(side="right", fill="y")
    spell_lb = tk.Listbox(lf2, bg=INPUT_BG, fg=FG, font=FONT_SM,
                          selectbackground=ACCENT, selectforeground="#1a1a2e",
                          relief="flat", bd=0, activestyle="none",
                          exportselection=False, selectmode="multiple",
                          yscrollcommand=sb2.set, height=7)
    sb2.config(command=spell_lb.yview)
    spell_lb.pack(fill="both", expand=True, padx=4, pady=4)
    for s in ("[Cantrip] Minor Illusion", "[Lv2] Blur", "[Lv2] Hold Person",
              "[Lv2] Mirror Image", "[Lv2] Misty Step",
              "[Lv3] Counterspell", "[Lv3] Fireball", "[Lv3] Haste"):
        spell_lb.insert("end", s)
    spell_lb.select_set(6)

    tk.Label(body, text="", font=FONT_SM, bg=BG, fg=RED).pack(anchor="w")
    tk.Button(body, text="Confirm →", font=FONT_SM,
              bg=BTN_BG, fg=FG, relief="flat", padx=16, pady=6,
              activebackground=ACCENT, activeforeground="#1a1a2e").pack(side="right", pady=(8, 0))

    grab(win, OUT / "13_spell_picker.png")


# ── Run ────────────────────────────────────────────────────────────────────────
root = tk.Tk()
root.geometry("1x1+0+0")

print("Taking screenshots...")
shot_main_menu(root)
shot_character_select(root)
shot_preset(root)
shot_main_game(root)
shot_sidebar(root)
shot_combat(root)
shot_combat_sidebar(root)
shot_level_up(root)
shot_feat_picker(root)
shot_spell_picker(root)

root.destroy()
print("Done.")
