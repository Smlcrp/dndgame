import tkinter as tk
import math
import random

PHI = (1 + math.sqrt(5)) / 2

BG     = "#1a1a2e"
PANEL  = "#16213e"
ACCENT = "#c8a951"
BTN_BG = "#2a2a4a"
FG     = "#e0e0e0"
DIM    = "#888888"

# Icosahedron vertices on the unit sphere
_RAW = [
    (0, 1, PHI), (0, -1, PHI), (0, 1, -PHI), (0, -1, -PHI),
    (1, PHI, 0), (-1, PHI, 0), (1, -PHI, 0), (-1, -PHI, 0),
    (PHI, 0, 1), (-PHI, 0, 1), (PHI, 0, -1), (-PHI, 0, -1),
]

def _mag(v):    return math.sqrt(v[0]**2 + v[1]**2 + v[2]**2)
def _norm(v):   m = _mag(v); return (v[0]/m, v[1]/m, v[2]/m)
def _dot(a, b): return a[0]*b[0] + a[1]*b[1] + a[2]*b[2]

VERTS = [_norm(v) for v in _RAW]

FACES = [
    (0,1,8),(0,8,4),(0,4,5),(0,5,9),(0,9,1),
    (1,8,6),(8,4,10),(4,5,2),(5,9,11),(9,1,7),
    (6,8,10),(10,4,2),(2,5,11),(11,9,7),(7,1,6),
    (3,6,10),(3,10,2),(3,2,11),(3,11,7),(3,7,6),
]

# Face normals as outward centroid direction (correct for a convex body at origin)
FACE_NORMALS = []
for _f in FACES:
    _cx = sum(VERTS[i][0] for i in _f) / 3
    _cy = sum(VERTS[i][1] for i in _f) / 3
    _cz = sum(VERTS[i][2] for i in _f) / 3
    FACE_NORMALS.append(_norm((_cx, _cy, _cz)))

LIGHT = _norm((0.5, 0.7, 1.0))

CANVAS_W = 300
CANVAS_H = 300
OX = CANVAS_W // 2
OY = CANVAS_H // 2
SCALE = 110
FOV   = 4.0


def _rot_mat(rx, ry, rz):
    cx, sx = math.cos(rx), math.sin(rx)
    cy, sy = math.cos(ry), math.sin(ry)
    cz, sz = math.cos(rz), math.sin(rz)
    return [
        [cy*cz,             -cy*sz,              sy    ],
        [sx*sy*cz + cx*sz,  -sx*sy*sz + cx*cz,  -sx*cy],
        [-cx*sy*cz + sx*sz,  cx*sy*sz + sx*cz,   cx*cy ],
    ]


def _mv(m, v):
    return (
        m[0][0]*v[0] + m[0][1]*v[1] + m[0][2]*v[2],
        m[1][0]*v[0] + m[1][1]*v[1] + m[1][2]*v[2],
        m[2][0]*v[0] + m[2][1]*v[1] + m[2][2]*v[2],
    )


def _project(v):
    x, y, z = v
    f = FOV / (FOV - z)
    return (OX + x * f * SCALE, OY - y * f * SCALE)


class D20RollerWindow:
    """
    Pop-up 3D d20 roller.

    d20_value  — the pre-computed actual roll (1-20); animation lands here.
    on_confirm — called with no args after the user clicks Confirm.
    """

    def __init__(self, parent, d20_value, on_confirm):
        self._val        = d20_value
        self._on_confirm = on_confirm
        self._rolling    = False
        self._done       = False
        self._rx         = 0.30
        self._ry         = 0.55
        self._rz         = 0.0
        self._vx         = 0.0
        self._vy         = 0.0
        self._frame      = 0
        self._phase      = "idle"

        self.win = tk.Toplevel(parent)
        self.win.title("Roll d20")
        self.win.configure(bg=BG)
        self.win.resizable(False, False)
        self.win.transient(parent)
        self.win.grab_set()
        self._build()
        self._redraw()

    def _build(self):
        tk.Frame(self.win, bg=ACCENT, height=3).pack(fill="x")
        tk.Label(self.win, text="ROLL D20", font=("Segoe UI", 11, "bold"),
                 bg=PANEL, fg=ACCENT, pady=8).pack(fill="x")

        self._canvas = tk.Canvas(self.win, width=CANVAS_W, height=CANVAS_H,
                                 bg=BG, highlightthickness=0, cursor="hand2")
        self._canvas.pack(padx=20, pady=(12, 0))
        self._canvas.bind("<Button-1>", self._click)

        self._hint = tk.Label(self.win, text="Click the die to roll",
                              font=("Segoe UI", 10), bg=BG, fg=DIM)
        self._hint.pack(pady=(6, 0))

        self._num_label = tk.Label(self.win, text="",
                                   font=("Consolas", 46, "bold"), bg=BG, fg=ACCENT)
        self._num_label.pack()

        self._confirm_btn = tk.Button(
            self.win, text="Confirm", font=("Segoe UI", 10),
            bg=ACCENT, fg="#1a1a2e", relief="flat", bd=0,
            padx=20, pady=6, state="disabled",
            activebackground="#e0c060", activeforeground="#1a1a2e",
            command=self._confirm)
        self._confirm_btn.pack(pady=(4, 16))

    def _click(self, _):
        if self._rolling or self._done:
            return
        self._rolling = True
        self._hint.config(text="Rolling…")
        self._vx    = random.uniform(0.06, 0.11)
        self._vy    = random.uniform(0.09, 0.14)
        self._frame = 0
        self._phase = "fast"
        self._tick()

    def _tick(self):
        self._frame += 1

        if self._phase == "fast" and self._frame > 38:
            self._phase = "slow"
            self._frame = 0

        if self._phase == "slow":
            self._vx *= 0.87
            self._vy *= 0.87
            if max(abs(self._vx), abs(self._vy)) < 0.003:
                self._land()
                return

        self._rx += self._vx
        self._ry += self._vy
        self._redraw()
        self.win.after(30, self._tick)

    def _land(self):
        self._done = True
        self._rolling = False
        self._redraw()
        self._hint.config(text="")
        self._num_label.config(text=str(self._val))
        self._confirm_btn.config(state="normal")

    def _redraw(self):
        c = self._canvas
        c.delete("all")

        mat = _rot_mat(self._rx, self._ry, self._rz)
        rv  = [_mv(mat, v) for v in VERTS]
        rn  = [_mv(mat, n) for n in FACE_NORMALS]

        visible = []
        for i, face in enumerate(FACES):
            if rn[i][2] <= 0:
                continue
            depth = sum(rv[j][2] for j in face) / 3
            visible.append((depth, i, face, rn[i]))
        visible.sort()  # back → front

        for _depth, _fi, face, normal in visible:
            pts = []
            for vi in face:
                px, py = _project(rv[vi])
                pts += [px, py]

            b = max(0.1, _dot(normal, LIGHT))
            r  = min(255, int(0x1a + b * (0xc8 - 0x1a)))
            g  = min(255, int(0x1a + b * (0xa9 - 0x1a)))
            bl = min(255, int(0x2e + b * (0x51 - 0x2e)))
            fill = f"#{r:02x}{g:02x}{bl:02x}"
            er   = min(255, int(r  * 1.18))
            eg   = min(255, int(g  * 1.18))
            ebl  = min(255, int(bl * 1.18))
            edge = f"#{er:02x}{eg:02x}{ebl:02x}"
            c.create_polygon(pts, fill=fill, outline=edge, width=1)

        if self._done:
            c.create_text(OX, OY, text=str(self._val),
                          font=("Consolas", 54, "bold"), fill="#000000")

    def _confirm(self):
        self.win.destroy()
        self._on_confirm()


if __name__ == "__main__":
    import random as _r
    root = tk.Tk()
    root.configure(bg=BG)
    root.withdraw()
    D20RollerWindow(root, d20_value=_r.randint(1, 20), on_confirm=root.destroy)
    root.mainloop()
