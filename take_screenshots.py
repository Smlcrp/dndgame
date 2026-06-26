"""
Capture screenshots of the new UI features for the README.
Run with: python take_screenshots.py
"""
import sys
import time
import tkinter as tk
from pathlib import Path

# Make game imports available
sys.path.insert(0, str(Path(__file__).parent))

from PIL import ImageGrab

OUT = Path(__file__).parent / "docs" / "screenshots"
OUT.mkdir(parents=True, exist_ok=True)

BG       = "#1a1a2e"
ACCENT   = "#c8a951"
INPUT_BG = "#0f0f1a"
PANEL    = "#16213e"
BTN_BG   = "#2a2a4a"
FG       = "#e0e0e0"
DIM      = "#888888"
GREEN    = "#4caf50"
RED      = "#e05050"

FONT_HDR  = ("Segoe UI", 11, "bold")
FONT_BODY = ("Segoe UI", 10)
FONT_SM   = ("Segoe UI", 9)


import ctypes as _ctypes
_SCALE = _ctypes.windll.shcore.GetScaleFactorForDevice(0) / 100.0


def grab_widget(widget, path):
    widget.attributes("-topmost", True)
    widget.lift()
    widget.focus_force()
    widget.update_idletasks()
    widget.update()
    time.sleep(0.6)
    lx = widget.winfo_rootx()
    ly = widget.winfo_rooty()
    lw = widget.winfo_width()
    lh = widget.winfo_height()
    # Convert logical → physical pixels for ImageGrab
    px = int(lx * _SCALE)
    py = int(ly * _SCALE)
    pw = int(lw * _SCALE)
    ph = int(lh * _SCALE)
    img = ImageGrab.grab(bbox=(px, py, px + pw, py + ph))
    # Resize to 2× logical size for crisp README display
    out_w = lw * 2
    out_h = lh * 2
    img = img.resize((out_w, out_h), resample=1)
    img.save(path)
    print(f"  saved {path.name}  (output {out_w}x{out_h})")


# ── 1. Sidebar INVENTORY section ───────────────────────────────────────────────
def shot_inventory(root):
    win = tk.Toplevel(root, bg=PANEL)
    win.title("Inventory")
    win.geometry("230x230+50+50")
    win.resizable(False, False)
    win.update()

    def _sec(label):
        tk.Label(win, text=label, font=("Segoe UI", 8, "bold"),
                 bg=PANEL, fg=ACCENT).pack(anchor="w", padx=8, pady=(8, 2))
        tk.Frame(win, bg=ACCENT, height=1).pack(fill="x", padx=8, pady=(0, 4))

    _sec("INVENTORY")

    coin_lbl = tk.Label(win, text="1pp  150gp  3sp", font=FONT_SM, bg=PANEL, fg=FG)
    coin_lbl.pack(anchor="w", padx=10, pady=(0, 2))

    items_frame = tk.Frame(win, bg=PANEL)
    items_frame.pack(fill="x", padx=6, pady=(0, 4))

    for name, bonus in (("+1 Longsword", "+1"), ("Shield of Protection", "+1 AC"), ("Bag of Holding", "")):
        bonus_str = f" {bonus}" if bonus else ""
        tk.Label(items_frame, text=f"✦ {name}{bonus_str}",
                 font=("Segoe UI", 8), bg=PANEL, fg=ACCENT).pack(anchor="w")

    _sec("COMBAT")
    tk.Label(win, text="⚔ Longsword  +5  1d8+3", font=FONT_SM, bg=PANEL, fg=FG).pack(anchor="w", padx=10)
    tk.Label(win, text="⚔ Shortbow   +5  1d6+3", font=FONT_SM, bg=PANEL, fg=FG).pack(anchor="w", padx=10)

    win.update()
    grab_widget(win, OUT / "11_inventory_sidebar.png")
    win.destroy()


# ── 2. Level-Up: ASI / Feat step ───────────────────────────────────────────────
def shot_feat_picker(root):
    win = tk.Toplevel(root, bg=BG)
    win.title("Level Up — Ability Score Improvement or Feat")
    win.geometry("430x490+50+50")
    win.resizable(False, False)
    win.update()

    FEATS = {
        "Alert":              "+5 initiative; can't be surprised; no advantage vs you for hidden attackers.",
        "Great Weapon Master":"On crit or kill, bonus action attack; take -5 to hit for +10 damage.",
        "Lucky":              "3 luck points per long rest; reroll attack/ability/save or force reroll of attack against you.",
        "Mobile":             "+10 ft speed; Dash ignores difficult terrain; no opportunity attacks from creatures you attack.",
        "Resilient":          "+1 to chosen ability; gain proficiency in that ability's saving throw.",
        "Sentinel":           "Opportunity attacks reduce speed to 0; can opportunity attack even when target Disengages.",
        "Sharpshooter":       "Ignore long range and half/three-quarter cover; -5 attack for +10 damage.",
        "Tough":              "HP max increases by 2 per level (applied immediately, retroactive).",
        "War Caster":         "Advantage on Concentration saves; somatic components with hands full; spell as opportunity attack.",
        "Weapon Master":      "+1 STR or DEX; gain proficiency with 4 weapons of your choice.",
    }
    feat_names = sorted(FEATS.keys())

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

    desc_lbl = tk.Label(body, text=FEATS["Sentinel"],
                        font=("Segoe UI", 8), bg=BG, fg=DIM,
                        wraplength=380, justify="left")
    desc_lbl.pack(anchor="w", pady=(6, 4))

    tk.Label(body, text="", font=FONT_SM, bg=BG, fg=RED).pack(anchor="w")

    btn = tk.Button(body, text="Confirm →", font=FONT_SM,
                    bg=BTN_BG, fg=FG, relief="flat", padx=16, pady=6,
                    activebackground=ACCENT, activeforeground="#1a1a2e")
    btn.pack(side="right", pady=(8, 0))

    win.update()
    time.sleep(0.1)
    grab_widget(win, OUT / "12_feat_picker.png")
    win.destroy()


# ── 3. Level-Up: Spell Learning step ──────────────────────────────────────────
def shot_spell_picker(root):
    win = tk.Toplevel(root, bg=BG)
    win.title("Level Up — Spellcasting")
    win.geometry("430x460+50+50")
    win.resizable(False, False)
    win.update()

    body = tk.Frame(win, bg=BG, padx=20, pady=16)
    body.pack(fill="both", expand=True)

    tk.Label(body, text="Spellcasting",
             font=FONT_HDR, bg=BG, fg=ACCENT).pack(anchor="w", pady=(0, 4))

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

    spells = [
        "[Cantrip] Minor Illusion",
        "[Lv2] Blur",
        "[Lv2] Hold Person",
        "[Lv2] Mirror Image",
        "[Lv2] Misty Step",
        "[Lv3] Counterspell",
        "[Lv3] Fireball",
        "[Lv3] Haste",
    ]
    for s in spells:
        spell_lb.insert("end", s)
    spell_lb.select_set(6)   # Fireball highlighted

    tk.Label(body, text="", font=FONT_SM, bg=BG, fg=RED).pack(anchor="w")

    btn = tk.Button(body, text="Confirm →", font=FONT_SM,
                    bg=BTN_BG, fg=FG, relief="flat", padx=16, pady=6,
                    activebackground=ACCENT, activeforeground="#1a1a2e")
    btn.pack(side="right", pady=(8, 0))

    win.update()
    time.sleep(0.1)
    grab_widget(win, OUT / "13_spell_picker.png")
    win.destroy()


# ── Run all ────────────────────────────────────────────────────────────────────
root = tk.Tk()
root.withdraw()

print("Taking screenshots...")
shot_inventory(root)
shot_feat_picker(root)
shot_spell_picker(root)

root.destroy()
print("Done.")
