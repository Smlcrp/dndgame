"""
Animated 3D dice roller window for d4, d6, d8, d10, d12, d20.

Usage:
    DiceRollerWindow(parent, sides=8, value=6, on_confirm=callback)
    DiceRollerWindow(parent, sides=8, value=6, on_confirm=callback, title_override="Damage d8")
"""

import tkinter as tk
import math
import random

PHI = (1 + math.sqrt(5)) / 2

BG     = "#1a1a2e"
PANEL  = "#16213e"
ACCENT = "#c8a951"
FG     = "#e0e0e0"
DIM    = "#888888"

CANVAS_W, CANVAS_H = 240, 240
OX, OY = CANVAS_W // 2, CANVAS_H // 2
FOV    = 3.5
_LIGHT = (0.447, 0.625, 0.894)   # _norm((0.5, 0.7, 1.0))


# ── Math helpers ───────────────────────────────────────────────────────────────

def _norm(v):
    m = math.sqrt(v[0]*v[0] + v[1]*v[1] + v[2]*v[2])
    return (v[0]/m, v[1]/m, v[2]/m)

def _dot(a, b):
    return a[0]*b[0] + a[1]*b[1] + a[2]*b[2]

def _rot_mat(rx, ry):
    cx, sx = math.cos(rx), math.sin(rx)
    cy, sy = math.cos(ry), math.sin(ry)
    return (
        (cy,       0,    sy    ),
        (sx*sy,    cx,  -sx*cy ),
        (-cx*sy,   sx,   cx*cy ),
    )

def _mv(m, v):
    return (
        m[0][0]*v[0] + m[0][1]*v[1] + m[0][2]*v[2],
        m[1][0]*v[0] + m[1][1]*v[1] + m[1][2]*v[2],
        m[2][0]*v[0] + m[2][1]*v[1] + m[2][2]*v[2],
    )

def _project(v, scale):
    x, y, z = v
    f = FOV / max(0.001, FOV - z)
    return (OX + x * f * scale, OY - y * f * scale)

def _face_normal(verts, face):
    n = len(face)
    return _norm(tuple(sum(verts[i][k] for i in face) / n for k in range(3)))

def _target_angles(normal):
    """Find (rx, ry) rotation that orients `normal` to face the camera (+Z)."""
    n   = normal
    ry  = math.atan2(-n[0], n[2])
    sy, cy = math.sin(ry), math.cos(ry)
    npz = -sy * n[0] + cy * n[2]
    rx  = math.atan2(n[1], npz)
    return rx, ry


# ── Die geometries ─────────────────────────────────────────────────────────────

def _d4():
    s2, s6 = math.sqrt(2), math.sqrt(6)
    raw = [
        (0,       0,    1    ),
        ( 2*s2/3, 0,   -1/3  ),
        (-s2/3,   s6/3, -1/3 ),
        (-s2/3,  -s6/3, -1/3 ),
    ]
    v = [_norm(x) for x in raw]
    f = [(0,1,2), (0,2,3), (0,3,1), (1,3,2)]
    return v, f, [1, 2, 3, 4]


def _d6():
    s = 1.0 / math.sqrt(3)
    v = [(a*s, b*s, c*s) for a in (-1,1) for b in (-1,1) for c in (-1,1)]
    # Index: 0(-,-,-) 1(-,-,+) 2(-,+,-) 3(-,+,+) 4(+,-,-) 5(+,-,+) 6(+,+,-) 7(+,+,+)
    f = [
        (4, 5, 7, 6),   # +X  normal (1,0,0)
        (0, 2, 3, 1),   # -X  normal (-1,0,0)
        (2, 6, 7, 3),   # +Y  normal (0,1,0)
        (0, 1, 5, 4),   # -Y  normal (0,-1,0)
        (1, 3, 7, 5),   # +Z  normal (0,0,1)
        (0, 4, 6, 2),   # -Z  normal (0,0,-1)
    ]
    return v, f, [1, 6, 2, 5, 3, 4]   # opposite faces sum to 7


def _d8():
    v = [(1,0,0), (-1,0,0), (0,1,0), (0,-1,0), (0,0,1), (0,0,-1)]
    # 0:(+X) 1:(-X) 2:(+Y) 3:(-Y) 4:(+Z) 5:(-Z)
    f = [
        (0, 2, 4), (2, 1, 4), (1, 3, 4), (3, 0, 4),  # upper (+Z) hemisphere
        (0, 5, 2), (2, 5, 1), (1, 5, 3), (3, 5, 0),  # lower (-Z) hemisphere
    ]
    return v, f, [1, 2, 3, 4, 8, 7, 6, 5]  # opposite faces sum to 9


def _d10():
    h = 0.309                        # height of upper/lower rings
    r = math.sqrt(1.0 - h * h)
    v = [(0, 0, 1)]                  # top pole (index 0)
    for i in range(5):               # upper ring (indices 1–5)
        a = i * 2 * math.pi / 5
        v.append((r * math.cos(a), r * math.sin(a), h))
    for i in range(5):               # lower ring (indices 6–10), offset 36°
        a = (i + 0.5) * 2 * math.pi / 5
        v.append((r * math.cos(a), r * math.sin(a), -h))
    v.append((0, 0, -1))             # bottom pole (index 11)
    f = []
    for i in range(5):               # upper kites: top → upper_i → lower_i → upper_{i+1}
        f.append((0, 1 + i, 6 + i, 1 + (i + 1) % 5))
    for i in range(5):               # lower kites: bottom → lower_{i+1} → upper_{i+1} → lower_i
        f.append((11, 6 + (i + 1) % 5, 1 + (i + 1) % 5, 6 + i))
    return v, f, [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]


def _order_ring(vertex, ring, ifaces):
    """Order face indices in `ring` around `vertex` by adjacency walking."""
    adj = {fi: [] for fi in ring}
    for fi in ring:
        for fj in ring:
            if fi >= fj:
                continue
            shared = set(ifaces[fi]) & set(ifaces[fj])
            if len(shared) == 2 and vertex in shared:
                adj[fi].append(fj)
                adj[fj].append(fi)
    ordered, prev = [ring[0]], None
    for _ in range(len(ring) - 1):
        curr = ordered[-1]
        nxt  = [f for f in adj[curr] if f != prev]
        if not nxt:
            break
        ordered.append(nxt[0])
        prev = curr
    return ordered


def _d12():
    """Dodecahedron as the dual of the icosahedron."""
    raw_i = [
        (0, 1, PHI), (0, -1, PHI), (0, 1, -PHI), (0, -1, -PHI),
        (1, PHI, 0), (-1, PHI, 0), (1, -PHI, 0), (-1, -PHI, 0),
        (PHI, 0, 1), (-PHI, 0, 1), (PHI, 0, -1), (-PHI, 0, -1),
    ]
    iv = [_norm(x) for x in raw_i]
    ifaces = [
        (0,1,8),(0,8,4),(0,4,5),(0,5,9),(0,9,1),
        (1,8,6),(8,4,10),(4,5,2),(5,9,11),(9,1,7),
        (6,8,10),(10,4,2),(2,5,11),(11,9,7),(7,1,6),
        (3,6,10),(3,10,2),(3,2,11),(3,11,7),(3,7,6),
    ]
    # Dodecahedron vertices = icosa face centroids
    dv = [_norm(tuple(sum(iv[i][k] for i in f) / 3 for k in range(3))) for f in ifaces]
    # Build vertex-to-face map for icosahedron
    v2f = {i: [] for i in range(12)}
    for fi, f in enumerate(ifaces):
        for vi in f:
            v2f[vi].append(fi)
    # Dodecahedron faces = ordered ring of icosa faces around each icosa vertex
    df = [tuple(_order_ring(vi, v2f[vi], ifaces)) for vi in range(12)]
    return dv, df, list(range(1, 13))


def _d20():
    raw = [
        (0, 1, PHI), (0, -1, PHI), (0, 1, -PHI), (0, -1, -PHI),
        (1, PHI, 0), (-1, PHI, 0), (1, -PHI, 0), (-1, -PHI, 0),
        (PHI, 0, 1), (-PHI, 0, 1), (PHI, 0, -1), (-PHI, 0, -1),
    ]
    v = [_norm(x) for x in raw]
    f = [
        (0,1,8),(0,8,4),(0,4,5),(0,5,9),(0,9,1),
        (1,8,6),(8,4,10),(4,5,2),(5,9,11),(9,1,7),
        (6,8,10),(10,4,2),(2,5,11),(11,9,7),(7,1,6),
        (3,6,10),(3,10,2),(3,2,11),(3,11,7),(3,7,6),
    ]
    return v, f, [1,20,2,19,3,18,4,17,5,16,6,15,7,14,8,13,9,12,10,11]


_GEO = {4: _d4, 6: _d6, 8: _d8, 10: _d10, 12: _d12, 20: _d20}

_SCALE = {4: 95, 6: 88, 8: 95, 10: 88, 12: 82, 20: 95}

# Each entry: (dark_rgb, bright_rgb)  — face colour interpolated by lighting
_PALETTE = {
    4:  ((0x1a, 0x1a, 0x2e), (0x38, 0x7a, 0xb8)),   # blue
    6:  ((0x1a, 0x1a, 0x2e), (0x2e, 0x8c, 0x3e)),   # green
    8:  ((0x1a, 0x1a, 0x2e), (0xa0, 0x2a, 0x2a)),   # red
    10: ((0x1a, 0x1a, 0x2e), (0x7a, 0x2a, 0x9e)),   # purple
    12: ((0x1a, 0x1a, 0x2e), (0x2a, 0x7a, 0x9e)),   # teal
    20: ((0x1a, 0x1a, 0x2e), (0xc8, 0xa9, 0x51)),   # gold
}


def _face_color(sides, brightness):
    dark, bright = _PALETTE.get(sides, _PALETTE[20])
    r  = min(255, int(dark[0] + brightness * (bright[0] - dark[0])))
    g  = min(255, int(dark[1] + brightness * (bright[1] - dark[1])))
    b  = min(255, int(dark[2] + brightness * (bright[2] - dark[2])))
    er = min(255, int(r * 1.22))
    eg = min(255, int(g * 1.22))
    eb = min(255, int(b * 1.22))
    return f"#{r:02x}{g:02x}{b:02x}", f"#{er:02x}{eg:02x}{eb:02x}"


# ── Animation ─────────────────────────────────────────────────────────────────

def _front_face(rx, ry, normals):
    """Return the index of the face most directly facing the camera at (rx, ry)."""
    mat = _rot_mat(rx, ry)
    rn  = [_mv(mat, n) for n in normals]
    return max(range(len(normals)), key=lambda i: rn[i][2])


def _build_animation(normals, target_fi):
    """Pre-compute 100 eased frames that tumble to land on face `target_fi`.

    Retries the starting-angle draw until the frame[0] orientation shows a
    face that is genuinely different from the target face.
    """
    rng = random.Random(target_fi * 137 + 42)
    rx_t, ry_t = _target_angles(normals[target_fi])
    exp_rx = rng.uniform(2.6, 3.4)
    exp_ry = rng.uniform(2.6, 3.4)

    extra_rx = extra_ry = None
    for _ in range(200):
        ex = rng.uniform(2.1, 3.9)
        ey = rng.uniform(2.1, 3.9)
        rx_s = rx_t - ex * 2 * math.pi
        ry_s = ry_t - ey * 2 * math.pi
        if _front_face(rx_s, ry_s, normals) != target_fi:
            extra_rx, extra_ry = ex, ey
            break

    if extra_rx is None:          # extreme fallback — add a half-turn offset
        extra_rx, extra_ry = 2.5, 2.7

    rx_start = rx_t - extra_rx * 2 * math.pi
    ry_start = ry_t - extra_ry * 2 * math.pi
    total    = 100
    frames   = []
    for i in range(total):
        t      = i / (total - 1)
        ease_x = 1.0 - (1.0 - t) ** exp_rx
        ease_y = 1.0 - (1.0 - t) ** exp_ry
        frames.append((
            rx_start + ease_x * extra_rx * 2 * math.pi,
            ry_start + ease_y * extra_ry * 2 * math.pi,
        ))
    return frames


# ── Window class ───────────────────────────────────────────────────────────────

class DiceRollerWindow:
    """
    Animated 3D die roller Toplevel window.

    Parameters
    ----------
    parent        : tk widget — transient parent
    sides         : int — 4, 6, 8, 10, 12, or 20
    value         : int — pre-determined result (1..sides)
    on_confirm    : callable — called with no args when player clicks Confirm
    title_override: str | None — replaces the default "ROLL Dn" header
    """

    def __init__(self, parent, sides, value, on_confirm, title_override=None):
        if sides not in _GEO:
            raise ValueError(f"Unsupported die: d{sides}")
        self._sides      = sides
        self._val        = value
        self._on_confirm = on_confirm
        self._rolling    = False
        self._done       = False

        verts, faces, nums = _GEO[sides]()
        self._verts   = verts
        self._faces   = faces
        self._nums    = nums
        self._normals = [_face_normal(verts, f) for f in faces]
        self._scale   = _SCALE.get(sides, 90)

        # Find the face that shows `value` and build its animation
        try:
            target_fi = nums.index(value)
        except ValueError:
            target_fi = 0
        self._anim = _build_animation(self._normals, target_fi)
        self._rx, self._ry = self._anim[0]

        title = title_override or f"ROLL D{sides}"

        self.win = tk.Toplevel(parent)
        self.win.title(f"Roll d{sides}")
        self.win.configure(bg=BG)
        self.win.resizable(False, False)
        self.win.transient(parent)
        self.win.grab_set()
        self._build(title)
        self._redraw()

    def _build(self, title):
        tk.Frame(self.win, bg=ACCENT, height=3).pack(fill="x")
        tk.Label(self.win, text=title,
                 font=("Segoe UI", 11, "bold"),
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
            self.win, text="Confirm",
            font=("Segoe UI", 10), bg=ACCENT, fg="#1a1a2e",
            relief="flat", bd=0, padx=20, pady=6, state="disabled",
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
        if i < len(self._anim):
            self._rx, self._ry = self._anim[i]
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

        mat = _rot_mat(self._rx, self._ry)
        rv  = [_mv(mat, v) for v in self._verts]
        rn  = [_mv(mat, n) for n in self._normals]

        visible = []
        for i, face in enumerate(self._faces):
            if rn[i][2] <= 0:
                continue
            depth = sum(rv[j][2] for j in face) / len(face)
            visible.append((depth, i, face, rn[i]))
        visible.sort()

        for _depth, fi, face, normal in visible:
            pts, projected = [], []
            for vi in face:
                px, py = _project(rv[vi], self._scale)
                pts += [px, py]
                projected.append((px, py))

            brightness = max(0.12, _dot(normal, _LIGHT))
            fill, edge = _face_color(self._sides, brightness)
            c.create_polygon(pts, fill=fill, outline=edge, width=1)

            if normal[2] > 0.15:
                fx = sum(p[0] for p in projected) / len(projected)
                fy = sum(p[1] for p in projected) / len(projected)
                fsize = max(7, int(normal[2] * 15))
                num   = str(self._nums[fi])
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
    import sys
    sides = int(sys.argv[1]) if len(sys.argv) > 1 else 6
    val   = int(sys.argv[2]) if len(sys.argv) > 2 else random.randint(1, sides)
    root = tk.Tk()
    root.configure(bg=BG)
    root.geometry("1x1+0+0")
    DiceRollerWindow(root, sides, val, on_confirm=root.destroy)
    root.mainloop()
