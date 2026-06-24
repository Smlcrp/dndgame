import tkinter as tk
import random
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from dice import roll

BG       = "#1a1a2e"
PANEL    = "#16213e"
ACCENT   = "#c8a951"
INPUT_BG = "#0f0f1a"
BTN_BG   = "#2a2a4a"
FG       = "#e0e0e0"
DIM      = "#888888"

FONT_HDR = ("Segoe UI", 11, "bold")
FONT_SM  = ("Segoe UI",  9)
FONT_NUM = ("Consolas", 15, "bold")

CS = 84          # canvas size
CX = CS // 2
CY = CS // 2
R  = 32          # die shape radius

DICE = [4, 6, 8, 10, 12, 20]

ANIM_FRAMES = [50]*10 + [80, 110, 150, 200, 260, 330]

PIP_GRIDS = {
    1: [(0, 0)],
    2: [(-1, -1), (1, 1)],
    3: [(-1, -1), (0, 0), (1, 1)],
    4: [(-1, -1), (1, -1), (-1, 1), (1, 1)],
    5: [(-1, -1), (1, -1), (0, 0), (-1, 1), (1, 1)],
    6: [(-1, -1), (1, -1), (-1, 0), (1, 0), (-1, 1), (1, 1)],
}


def _die_points(sides):
    pts = []
    if sides == 6:
        return [CX-R, CY-R, CX+R, CY-R, CX+R, CY+R, CX-R, CY+R]
    elif sides == 8:
        return [CX, CY-R, CX+R, CY, CX, CY+R, CX-R, CY]
    else:
        n = {4: 3, 10: 5, 12: 6}[sides]
        start = -math.pi / 2
        for i in range(n):
            a = start + 2 * math.pi * i / n
            pts += [CX + R * math.cos(a), CY + R * math.sin(a)]
        return pts


class DiceRollerWindow:

    def __init__(self, parent=None):
        if parent is None:
            self.win = tk.Tk()
            self.win.title("Dice Roller")
        else:
            self.win = tk.Toplevel(parent)
            self.win.title("Dice Roller")
        self.win.configure(bg=BG)
        self.win.resizable(False, False)
        self._slots = []
        self._build()
        if parent:
            self.win.transient(parent)

    def _build(self):
        tk.Frame(self.win, bg=ACCENT, height=3).pack(fill="x")
        tk.Label(self.win, text="DICE ROLLER", font=FONT_HDR,
                 bg=PANEL, fg=ACCENT, pady=8).pack(fill="x")

        row = tk.Frame(self.win, bg=BG, padx=10, pady=10)
        row.pack()

        for sides in DICE:
            col = tk.Frame(row, bg=BG, padx=6)
            col.pack(side="left")

            tk.Label(col, text=f"d{sides}", font=("Segoe UI", 10, "bold"),
                     bg=BG, fg=ACCENT).pack()

            canvas = tk.Canvas(col, width=CS, height=CS,
                               bg=BG, highlightthickness=0)
            canvas.pack()

            result_var = tk.StringVar(value="—")
            tk.Label(col, textvariable=result_var, font=FONT_NUM,
                     bg=BG, fg=FG, width=4).pack(pady=2)

            slot = {"sides": sides, "canvas": canvas,
                    "result_var": result_var, "rolling": False}
            self._slots.append(slot)
            self._draw(slot, None, False)

            btn = tk.Button(col, text="Roll", font=FONT_SM,
                            bg=BTN_BG, fg=FG, relief="flat", bd=0,
                            padx=10, pady=4,
                            activebackground=ACCENT, activeforeground="#1a1a2e",
                            command=lambda s=slot: self._start(s))
            btn.pack(pady=(2, 0))
            slot["btn"] = btn

        tk.Frame(self.win, bg=BTN_BG, height=1).pack(fill="x", padx=16, pady=(6, 0))
        tk.Button(self.win, text="Roll All", font=("Segoe UI", 10),
                  bg=BTN_BG, fg=ACCENT, relief="flat", bd=0,
                  padx=20, pady=6,
                  activebackground=ACCENT, activeforeground="#1a1a2e",
                  command=self._roll_all).pack(pady=(4, 12))

    def _start(self, slot):
        if slot["rolling"]:
            return
        slot["rolling"] = True
        slot["btn"].config(state="disabled")
        actual = roll(slot["sides"])
        slot["result_var"].set("...")
        self._animate(slot, actual, 0)

    def _animate(self, slot, actual, frame):
        if frame < len(ANIM_FRAMES):
            fake = random.randint(1, slot["sides"])
            self._draw(slot, fake, True)
            self.win.after(ANIM_FRAMES[frame],
                           lambda: self._animate(slot, actual, frame + 1))
        else:
            self._draw(slot, actual, False)
            slot["result_var"].set(str(actual))
            slot["rolling"] = False
            slot["btn"].config(state="normal")

    def _draw(self, slot, value, animating):
        c     = slot["canvas"]
        sides = slot["sides"]
        c.delete("all")

        if animating:
            fill, outline, fg = INPUT_BG, DIM, DIM
        elif value is None:
            fill, outline, fg = BTN_BG, DIM, DIM
        else:
            fill, outline, fg = "#1e1e3a", ACCENT, ACCENT

        if sides == 20:
            c.create_oval(CX - R, CY - R, CX + R, CY + R,
                          fill=fill, outline=outline, width=2)
        else:
            pts = _die_points(sides)
            c.create_polygon(pts, fill=fill, outline=outline, width=2)

        if sides == 6 and value and not animating:
            self._draw_pips(c, value)
        elif value is not None:
            c.create_text(CX, CY, text=str(value),
                          font=("Consolas", 16, "bold"), fill=fg)
        else:
            c.create_text(CX, CY, text="—", font=("Consolas", 13), fill=DIM)

    def _draw_pips(self, canvas, value):
        gap = R * 0.55
        pr  = 4
        for ox, oy in PIP_GRIDS.get(value, []):
            px, py = CX + ox * gap, CY + oy * gap
            canvas.create_oval(px - pr, py - pr, px + pr, py + pr,
                               fill=ACCENT, outline="")

    def _roll_all(self):
        for s in self._slots:
            self._start(s)

    def run(self):
        self.win.mainloop()


if __name__ == "__main__":
    DiceRollerWindow().run()
