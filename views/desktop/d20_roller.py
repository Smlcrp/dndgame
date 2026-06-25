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

FACE_NORMALS = []
for _f in FACES:
    _cx = sum(VERTS[i][0] for i in _f) / 3
    _cy = sum(VERTS[i][1] for i in _f) / 3
    _cz = sum(VERTS[i][2] for i in _f) / 3
    FACE_NORMALS.append(_norm((_cx, _cy, _cz)))

LIGHT = _norm((0.5, 0.7, 1.0))

FACE_NUMBERS = [1,20,2,19,3,18,4,17,5,16,6,15,7,14,8,13,9,12,10,11]


def _face_target_angles(face_idx):
    n  = FACE_NORMALS[face_idx]
    ry = math.atan2(-n[0], n[2])
    sy, cy = math.sin(ry), math.cos(ry)
    npz = -sy * n[0] + cy * n[2]
    rx  = math.atan2(n[1], npz)
    return rx, ry


def _angle_diff(a, b):
    d = (b - a) % (2 * math.pi)
    if d > math.pi:
        d -= 2 * math.pi
    return d


def _front_face_d20(rx, ry):
    """Return the face index most directly facing the camera at (rx, ry).
    Inlines the rotation to avoid a forward-reference to _rot_mat."""
    cx, sx = math.cos(rx), math.sin(rx)
    cy, sy = math.cos(ry), math.sin(ry)
    m = ((cy, 0, sy), (sx*sy, cx, -sx*cy), (-cx*sy, sx, cx*cy))
    def _z(n):
        return m[2][0]*n[0] + m[2][1]*n[1] + m[2][2]*n[2]
    return max(range(len(FACE_NORMALS)), key=lambda i: _z(FACE_NORMALS[i]))


def _generate_animation(face_idx, seed):
    rng    = random.Random(seed)
    rx_t, ry_t = _face_target_angles(face_idx)
    exp_rx = rng.uniform(2.6, 3.4)
    exp_ry = rng.uniform(2.6, 3.4)

    extra_rx = extra_ry = None
    for _ in range(200):
        ex = rng.uniform(2.1, 3.9)
        ey = rng.uniform(2.1, 3.9)
        rx_s = rx_t - ex * 2 * math.pi
        ry_s = ry_t - ey * 2 * math.pi
        if _front_face_d20(rx_s, ry_s) != face_idx:
            extra_rx, extra_ry = ex, ey
            break

    if extra_rx is None:
        extra_rx, extra_ry = 2.5, 2.7

    rx_start = rx_t - extra_rx * 2 * math.pi
    ry_start = ry_t - extra_ry * 2 * math.pi
    total = 100
    frames = []
    for i in range(total):
        t      = i / (total - 1)
        ease_x = 1.0 - (1.0 - t) ** exp_rx
        ease_y = 1.0 - (1.0 - t) ** exp_ry
        frames.append((
            rx_start + ease_x * extra_rx * 2 * math.pi,
            ry_start + ease_y * extra_ry * 2 * math.pi,
        ))
    return frames


ANIMATIONS = {
    n: _generate_animation(FACE_NUMBERS.index(n), seed=n * 137 + 42)
    for n in range(1, 21)
}

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
    def __init__(self, parent, d20_value, on_confirm):
        self._val        = d20_value
        self._on_confirm = on_confirm
        self._rolling    = False
        self._done       = False
        self._rz         = 0.0
        self._rx, self._ry = ANIMATIONS[d20_value][0]

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
        self._play_frame(0)

    def _play_frame(self, i):
        frames = ANIMATIONS[self._val]
        if i < len(frames):
            self._rx, self._ry = frames[i]
            self._redraw()
            self.win.after(35, lambda: self._play_frame(i + 1))
        else:
            self._land()

    def _land(self):
        self._done    = True
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
        visible.sort()

        for _depth, fi, face, normal in visible:
            pts = []
            projected_face = []
            for vi in face:
                px, py = _project(rv[vi])
                pts += [px, py]
                projected_face.append((px, py))

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

            if normal[2] > 0.15:
                fx = sum(p[0] for p in projected_face) / 3
                fy = sum(p[1] for p in projected_face) / 3
                fsize = max(8, int(normal[2] * 16))
                num   = str(FACE_NUMBERS[fi])
                font  = ("Consolas", fsize, "bold")
                c.create_text(fx + 1, fy + 1, text=num, font=font, fill="#dddddd")
                c.create_text(fx,     fy,     text=num, font=font, fill="#000000")

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
    root.geometry("1x1+0+0")
    D20RollerWindow(root, d20_value=_r.randint(1, 20), on_confirm=root.destroy)
    root.mainloop()
