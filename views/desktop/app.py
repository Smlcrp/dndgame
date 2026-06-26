import sys
import threading
import tkinter as tk
from tkinter import messagebox, ttk
from pathlib import Path

_root = Path(__file__).parent.parent.parent
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))

from models.character import load_character, save_character, list_characters, modifier, proficiency_bonus, reset_to_level1
import models.game_state as gs
import models.combat as cb
import models.dm as dm_module
import models.dice as dice
from controllers.game_controller import (
    setup_combat as gc_setup_combat,
    process_skill_check,
    process_enemy_turn,
    process_death_save,
    process_xp_award,
    start_adventure,
    advance_beat as gc_advance_beat,
    process_spell_cast,
    get_available_combat_spells,
    SKILL_ABILITIES,
)
from models.progression import is_asi_level, get_subclass_trigger
from views.desktop.d20_roller import D20RollerWindow
from views.desktop.dice_roller import DiceRollerWindow

# ── Theme ──────────────────────────────────────────────────────────────────────
BG       = "#1a1a2e"
PANEL    = "#16213e"
ACCENT   = "#c8a951"
INPUT_BG = "#0f0f1a"
BTN_BG   = "#2a2a4a"
FG       = "#e0e0e0"
DIM      = "#888888"
GREEN    = "#4caf50"
YELLOW   = "#e0c050"
RED      = "#e05050"
BLUE     = "#5b8cdc"

FONT_TITLE = ("Segoe UI", 13, "bold")
FONT_HDR   = ("Segoe UI", 11, "bold")
FONT_BODY  = ("Segoe UI", 10)
FONT_SM    = ("Segoe UI",  9)
FONT_MONO  = ("Consolas", 10)

ABILITY_KEYS = [
    ("STR", "strength"), ("DEX", "dexterity"), ("CON", "constitution"),
    ("INT", "intelligence"), ("WIS", "wisdom"), ("CHA", "charisma"),
]
SKILL_ABILITY = {
    "Acrobatics":"dexterity","Animal Handling":"wisdom","Arcana":"intelligence",
    "Athletics":"strength","Deception":"charisma","History":"intelligence",
    "Insight":"wisdom","Intimidation":"charisma","Investigation":"intelligence",
    "Medicine":"wisdom","Nature":"intelligence","Perception":"wisdom",
    "Performance":"charisma","Persuasion":"charisma","Religion":"intelligence",
    "Sleight of Hand":"dexterity","Stealth":"dexterity","Survival":"wisdom",
}


class _Tooltip:
    def __init__(self, widget, text_fn):
        self._text_fn = text_fn
        self._win     = None
        widget.bind("<Enter>",   self._show)
        widget.bind("<Leave>",   self._hide)
        widget.bind("<Destroy>", self._hide)

    def _show(self, event):
        if self._win:
            return
        w = event.widget
        x = w.winfo_rootx() + 4
        y = w.winfo_rooty() + w.winfo_height() + 4
        self._win = tk.Toplevel()
        self._win.wm_overrideredirect(True)
        self._win.attributes("-topmost", True)
        self._win.geometry(f"+{x}+{y}")
        tk.Label(self._win, text=self._text_fn(),
                 bg=BTN_BG, fg=FG, font=FONT_SM,
                 padx=10, pady=5, relief="flat", justify="left").pack()

    def _hide(self, event=None):
        if self._win:
            try:
                self._win.destroy()
            except Exception:
                pass
            self._win = None


class GameApp:

    def __init__(self, root):
        self.root    = root
        self.char    = None
        self.session = None
        self.dm      = None
        self.state   = "STARTUP"   # EXPLORING | COMBAT | DEAD

        root.title("D&D AI Dungeon Master")
        root.configure(bg=BG)
        root.geometry("1340x780")
        root.minsize(900, 600)

        self._build_ui()
        root.after(150, self._startup_dialog)

    # ── UI construction ────────────────────────────────────────────────────────

    def _build_ui(self):
        hdr = tk.Frame(self.root, bg=PANEL, pady=6)
        hdr.pack(fill="x")
        tk.Frame(hdr, bg=ACCENT, width=4).pack(side="left", fill="y")
        self._loc_var  = tk.StringVar(value="D&D AI Dungeon Master")
        self._char_var = tk.StringVar(value="")
        tk.Label(hdr, textvariable=self._char_var, font=FONT_TITLE,
                 bg=PANEL, fg=ACCENT, padx=12).pack(side="left")
        tk.Label(hdr, textvariable=self._loc_var, font=FONT_BODY,
                 bg=PANEL, fg=DIM, padx=8).pack(side="left")
        tk.Button(hdr, text="DEV", font=("Segoe UI", 8, "bold"),
                  bg=BTN_BG, fg=DIM, relief="flat", bd=0, padx=8, pady=2,
                  activebackground=ACCENT, activeforeground="#1a1a2e",
                  command=self._open_dev_panel).pack(side="right", padx=8)

        main = tk.Frame(self.root, bg=BG)
        main.pack(fill="both", expand=True)

        nf = tk.Frame(main, bg=BG)
        nf.pack(side="left", fill="both", expand=True, padx=(8,4), pady=6)
        self._narration = tk.Text(
            nf, bg=INPUT_BG, fg=FG, font=FONT_MONO, relief="flat", bd=0,
            wrap="word", padx=14, pady=10, state="disabled", cursor="arrow")
        sb = tk.Scrollbar(nf, command=self._narration.yview, bg=BG,
                          troughcolor=INPUT_BG)
        self._narration.config(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")
        self._narration.pack(fill="both", expand=True)

        self._narration.tag_config("dm",     foreground=FG)
        self._narration.tag_config("player", foreground=ACCENT)
        self._narration.tag_config("system", foreground=BLUE)
        self._narration.tag_config("hit",    foreground=GREEN)
        self._narration.tag_config("miss",   foreground=DIM)
        self._narration.tag_config("danger", foreground=RED)
        self._narration.tag_config("header", foreground=ACCENT,
                                   font=("Consolas", 10, "bold"))

        # ── Scrollable sidebar ──────────────────────────────────────────────────
        sf = tk.Frame(main, bg=PANEL, width=320)
        sf.pack(side="right", fill="y", padx=(4,8), pady=6)
        sf.pack_propagate(False)

        # Tab bar
        _tab_bar = tk.Frame(sf, bg=PANEL, height=32)
        _tab_bar.pack(fill="x")
        _tab_bar.pack_propagate(False)
        self._sb_tab_char  = tk.Button(
            _tab_bar, text="CHARACTER", font=("Segoe UI", 8, "bold"),
            bg=ACCENT, fg="#1a1a2e", relief="flat", bd=0, padx=10,
            activebackground=ACCENT, activeforeground="#1a1a2e",
            command=lambda: self._switch_sidebar_tab("character"))
        self._sb_tab_char.pack(side="left", fill="y")
        self._sb_tab_party = tk.Button(
            _tab_bar, text="PARTY", font=("Segoe UI", 8, "bold"),
            bg=BTN_BG, fg=DIM, relief="flat", bd=0, padx=10,
            activebackground=ACCENT, activeforeground="#1a1a2e",
            command=lambda: self._switch_sidebar_tab("party"))
        self._sb_tab_party.pack(side="left", fill="y")
        self._sb_active_tab = "character"

        # CHARACTER panel (scrollable)
        self._char_panel = tk.Frame(sf, bg=PANEL)
        self._char_panel.pack(fill="both", expand=True)

        _sb_bar = tk.Scrollbar(self._char_panel, orient="vertical",
                               bg=PANEL, troughcolor=INPUT_BG)
        _sb_bar.pack(side="right", fill="y")
        _sb_cv = tk.Canvas(self._char_panel, bg=PANEL, highlightthickness=0,
                           yscrollcommand=_sb_bar.set)
        _sb_cv.pack(side="left", fill="both", expand=True)
        _sb_bar.config(command=_sb_cv.yview)
        self._sb_inner = tk.Frame(_sb_cv, bg=PANEL)
        _win_id = _sb_cv.create_window((0, 0), window=self._sb_inner, anchor="nw")
        self._sb_inner.bind(
            "<Configure>",
            lambda e: _sb_cv.configure(scrollregion=_sb_cv.bbox("all")))
        _sb_cv.bind(
            "<Configure>",
            lambda e: _sb_cv.itemconfig(_win_id, width=e.width))

        # PARTY panel (scrollable, hidden initially)
        self._party_panel = tk.Frame(sf, bg=PANEL)
        _pb_bar = tk.Scrollbar(self._party_panel, orient="vertical",
                               bg=PANEL, troughcolor=INPUT_BG)
        _pb_bar.pack(side="right", fill="y")
        _pb_cv = tk.Canvas(self._party_panel, bg=PANEL, highlightthickness=0,
                           yscrollcommand=_pb_bar.set)
        _pb_cv.pack(side="left", fill="both", expand=True)
        _pb_bar.config(command=_pb_cv.yview)
        self._party_inner = tk.Frame(_pb_cv, bg=PANEL)
        _pw_id = _pb_cv.create_window((0, 0), window=self._party_inner, anchor="nw")
        self._party_inner.bind(
            "<Configure>",
            lambda e: _pb_cv.configure(scrollregion=_pb_cv.bbox("all")))
        _pb_cv.bind(
            "<Configure>",
            lambda e: _pb_cv.itemconfig(_pw_id, width=e.width))

        sf.bind_all("<MouseWheel>",
                    lambda e: (_sb_cv if self._sb_active_tab == "character" else _pb_cv)
                    .yview_scroll(int(-1*(e.delta/120)), "units"))

        def _sec(text):
            tk.Label(self._sb_inner, text=text, font=("Segoe UI", 8, "bold"),
                     bg=PANEL, fg=ACCENT).pack(anchor="w", padx=10, pady=(10,0))
            tk.Frame(self._sb_inner, bg=BTN_BG, height=1).pack(
                fill="x", padx=10, pady=(2,4))

        # CHARACTER INFO
        _sec("CHARACTER")
        self._char_info_label = tk.Label(
            self._sb_inner, text="—", font=FONT_SM, bg=PANEL, fg=FG,
            anchor="w", justify="left", wraplength=285)
        self._char_info_label.pack(anchor="w", padx=10, pady=(0,4))

        # VITALS
        _sec("VITALS")
        self._hp_label = tk.Label(self._sb_inner, text="HP: —",
                                  font=FONT_BODY, bg=PANEL, fg=FG)
        self._hp_label.pack(anchor="w", padx=10)
        self._hp_bar_canvas = tk.Canvas(self._sb_inner, bg=PANEL, height=8,
                                        highlightthickness=0)
        self._hp_bar_canvas.pack(fill="x", padx=10, pady=2)
        vrow = tk.Frame(self._sb_inner, bg=PANEL)
        vrow.pack(anchor="w", padx=10, pady=(0,2), fill="x")
        self._ac_label   = tk.Label(vrow, text="AC —",   font=FONT_SM, bg=PANEL, fg=DIM)
        self._ac_label.pack(side="left")
        tk.Label(vrow, text="  |  ", font=FONT_SM, bg=PANEL, fg=BTN_BG).pack(side="left")
        self._spd_label  = tk.Label(vrow, text="Spd —",  font=FONT_SM, bg=PANEL, fg=DIM)
        self._spd_label.pack(side="left")
        tk.Label(vrow, text="  |  ", font=FONT_SM, bg=PANEL, fg=BTN_BG).pack(side="left")
        self._init_label = tk.Label(vrow, text="Init —", font=FONT_SM, bg=PANEL, fg=DIM)
        self._init_label.pack(side="left")
        self._cond_label = tk.Label(
            self._sb_inner, text="Conditions: —", font=FONT_SM,
            bg=PANEL, fg=DIM, wraplength=285, justify="left")
        self._cond_label.pack(anchor="w", padx=10, pady=(0,2))

        # Inspiration toggle
        self._insp_btn = tk.Button(
            self._sb_inner, text="✦  Inspiration",
            font=FONT_SM, relief="flat", bd=0, padx=8, pady=3,
            bg=BTN_BG, fg=DIM,
            activebackground=ACCENT, activeforeground="#1a1a2e",
            command=self._toggle_inspiration)
        self._insp_btn.pack(anchor="w", padx=10, pady=(0,4))

        # XP bar
        self._xp_label = tk.Label(
            self._sb_inner, text="XP: —", font=FONT_SM, bg=PANEL, fg=DIM)
        self._xp_label.pack(anchor="w", padx=10)
        self._xp_bar_canvas = tk.Canvas(
            self._sb_inner, bg=PANEL, height=6, highlightthickness=0)
        self._xp_bar_canvas.pack(fill="x", padx=10, pady=(2,6))

        # ABILITIES
        _sec("ABILITIES")
        ab_grid = tk.Frame(self._sb_inner, bg=PANEL)
        ab_grid.pack(anchor="w", padx=8, pady=2)
        self._ab_labels = {}
        for i, (abbr, key) in enumerate(ABILITY_KEYS):
            col, row_i = i % 3, i // 3
            cell = tk.Frame(ab_grid, bg=BTN_BG, padx=6, pady=4, width=88)
            cell.grid(row=row_i, column=col, padx=3, pady=3)
            cell.grid_propagate(False)
            tk.Label(cell, text=abbr, font=("Segoe UI",7,"bold"),
                     bg=BTN_BG, fg=DIM).pack()
            lbl = tk.Label(cell, text="—", font=("Segoe UI",10,"bold"),
                           bg=BTN_BG, fg=FG)
            lbl.pack()
            self._ab_labels[key] = lbl

        # SAVING THROWS
        _sec("SAVING THROWS")
        self._save_frame = tk.Frame(self._sb_inner, bg=PANEL)
        self._save_frame.pack(anchor="w", padx=10, pady=(0,4), fill="x")

        # PROFICIENT SKILLS
        _sec("SKILLS")
        self._skills_frame = tk.Frame(self._sb_inner, bg=PANEL)
        self._skills_frame.pack(anchor="w", padx=10, pady=(0,4), fill="x")

        # SPELLCASTING (compact: DC / ATK / slot counts — only populated for casters)
        _sec("SPELLCASTING")
        self._spells_frame = tk.Frame(self._sb_inner, bg=PANEL)
        self._spells_frame.pack(fill="x", padx=6, pady=(0,4))

        # ACTIONS (weapons + spells-as-actions + standard actions)
        _sec("ACTIONS")
        self._attacks_frame = tk.Frame(self._sb_inner, bg=PANEL)
        self._attacks_frame.pack(fill="x", padx=6, pady=(0,4))

        # BONUS ACTIONS
        _sec("BONUS ACTIONS")
        self._bonus_frame = tk.Frame(self._sb_inner, bg=PANEL)
        self._bonus_frame.pack(fill="x", padx=6, pady=(0,4))

        # FEATURES (non-BA charge tracking: Arcane Recovery etc.)
        _sec("FEATURES")
        self._features_frame = tk.Frame(self._sb_inner, bg=PANEL)
        self._features_frame.pack(fill="x", padx=6, pady=(0,4))

        # COMBAT ORDER
        _sec("COMBAT")
        self._combat_frame = tk.Frame(self._sb_inner, bg=PANEL)
        self._combat_frame.pack(fill="x", padx=6)

        # REST
        _sec("REST")
        rest_row = tk.Frame(self._sb_inner, bg=PANEL)
        rest_row.pack(fill="x", padx=6, pady=(0,8))
        tk.Button(rest_row, text="Short Rest", font=FONT_SM,
                  bg=BTN_BG, fg=FG, relief="flat", bd=0, padx=8, pady=5,
                  activebackground=ACCENT, activeforeground="#1a1a2e",
                  command=self._show_short_rest_dialog).pack(
                      side="left", fill="x", expand=True, padx=(0,3))
        tk.Button(rest_row, text="Long Rest", font=FONT_SM,
                  bg=BTN_BG, fg=FG, relief="flat", bd=0, padx=8, pady=5,
                  activebackground=BLUE, activeforeground=FG,
                  command=self._do_long_rest).pack(
                      side="left", fill="x", expand=True, padx=(3,0))

        # Save & Quit
        tk.Frame(self._sb_inner, bg=BTN_BG, height=1).pack(
            fill="x", padx=10, pady=(4,4))
        tk.Button(self._sb_inner, text="Save & Quit", font=FONT_SM,
                  bg=BTN_BG, fg=FG, relief="flat", bd=0, padx=8, pady=4,
                  activebackground=ACCENT, activeforeground="#1a1a2e",
                  command=self._save_and_quit).pack(
                      padx=10, pady=(0,12), fill="x")

        inp = tk.Frame(self.root, bg=PANEL, pady=6)
        inp.pack(fill="x", side="bottom")
        tk.Frame(inp, bg=ACCENT, height=2).pack(fill="x")
        self._input_frame = tk.Frame(inp, bg=PANEL)
        self._input_frame.pack(fill="x", padx=8, pady=6)
        self._build_explore_input()

        self._story_mode_label = tk.Label(
            hdr, text="  ◆ STORY MODE  ",
            font=("Segoe UI", 8, "bold"),
            bg=ACCENT, fg="#1a1a2e", padx=6, pady=2)

        self.root.bind_all("<F4>", self._open_dev_panel)
        self._dev_panel   = None
        self._story_mode  = False

    def _build_explore_input(self):
        for w in self._input_frame.winfo_children():
            w.destroy()
        self._input_var = tk.StringVar()
        tk.Label(self._input_frame, text=">", font=FONT_BODY, bg=PANEL,
                 fg=ACCENT).pack(side="left", padx=(4,2))
        self._input_entry = tk.Entry(
            self._input_frame, textvariable=self._input_var,
            bg=INPUT_BG, fg=FG, font=FONT_BODY, insertbackground=FG,
            relief="flat", bd=4)
        self._input_entry.pack(side="left", fill="x", expand=True, padx=4)
        self._input_entry.bind("<Return>", lambda e: self._send_action())
        tk.Button(self._input_frame, text="Send", font=FONT_SM, bg=BTN_BG,
                  fg=FG, relief="flat", bd=0, padx=10, pady=4,
                  activebackground=ACCENT, activeforeground="#1a1a2e",
                  command=self._send_action).pack(side="left", padx=4)
        self._input_entry.focus_set()

    _RANGED_WEAPONS = {
        "shortbow", "longbow", "hand crossbow", "light crossbow",
        "heavy crossbow", "sling", "dart", "blowgun", "net",
        "throwing hammer", "handaxe (thrown)", "javelin",
    }
    _COMBAT_FEATURES = {
        "Second Wind":      "Bonus action — regain 1d10 + level HP",
        "Action Surge":     "Take one additional action this turn",
        "Rage":             "Bonus action — enter a rage",
        "Wild Shape":       "Bonus action — transform into a beast",
        "Ki Points":        "Spend for Flurry of Blows / Patient Defense / Step of the Wind",
        "Bardic Inspiration": "Bonus action — grant an ally an inspiration die",
        "Channel Divinity": "Turn Undead or domain effect",
        "Lay on Hands":     "Action — heal from your HP pool",
        "Sorcery Points":   "Spend to create spell slots or power Metamagic",
    }

    def _is_ranged_weapon(self, name):
        n = name.lower()
        return n in self._RANGED_WEAPONS or "bow" in n or "crossbow" in n

    def _get_attack_options(self):
        import re as _re
        import sys as _sys
        from pathlib import Path as _Path
        _cb = _Path(__file__).parent / "character_builder"
        if str(_cb) not in _sys.path:
            _sys.path.insert(0, str(_cb))
        from dnd_data import WEAPONS as WPN_DATA

        attacks = self.char.get("attacks", []) if self.char else []
        options = []
        light_melee = []

        for atk in attacks:
            name     = atk["name"]
            bonus    = atk.get("attack_bonus", 0)
            damage   = atk.get("damage", "—")
            dmg_type = atk.get("damage_type", "")

            wpn   = WPN_DATA.get(name, {})
            props = wpn.get("props", [])
            cat   = wpn.get("cat", "")

            is_melee  = "Ranged" not in cat and not any("ammunition" in p for p in props)
            has_light = "light" in props
            has_reach = "reach" in props

            # Parse versatile damage die (e.g. "versatile (1d10)")
            vers_dmg = None
            for p in props:
                if p.startswith("versatile"):
                    m = _re.search(r'\((.+?)\)', p)
                    if m:
                        die = m.group(1)
                        mod = (_re.search(r'([+-]\d+)$', damage) or type('', (), {'group': lambda s, x: ''})()).group(1) if _re.search(r'([+-]\d+)$', damage) else ""
                        vers_dmg = die + mod

            # Parse thrown range (e.g. "thrown (20/60)")
            thrown_range = None
            for p in props:
                if p.startswith("thrown"):
                    m = _re.search(r'\((.+?)\)', p)
                    if m:
                        thrown_range = m.group(1)

            # Parse ammo range for ranged weapons
            ammo_range = None
            for p in props:
                if p.startswith("ammunition"):
                    m = _re.search(r'\((.+?)\)', p)
                    if m:
                        ammo_range = m.group(1)

            reach_note = " · reach 10ft" if has_reach else ""

            # Primary option
            if vers_dmg:
                label = f"{name} (one-handed){reach_note}"
            elif ammo_range:
                label = f"{name} · range {ammo_range} ft"
            else:
                label = f"{name}{reach_note}"

            options.append({
                "label": label, "weapon": name, "bonus": bonus,
                "damage": damage, "dmg_type": dmg_type,
                "mode": "ranged" if ammo_range else "melee",
            })

            # Versatile two-handed option
            if vers_dmg:
                options.append({
                    "label": f"{name} (two-handed){reach_note}",
                    "weapon": name, "bonus": bonus,
                    "damage": vers_dmg, "dmg_type": dmg_type,
                    "mode": "melee_2h", "damage_override": vers_dmg,
                })

            # Thrown option (melee weapons that can be thrown)
            if thrown_range and is_melee:
                options.append({
                    "label": f"{name} (thrown · {thrown_range} ft)",
                    "weapon": name, "bonus": bonus,
                    "damage": damage, "dmg_type": dmg_type,
                    "mode": "thrown",
                })

            if has_light and is_melee:
                light_melee.append(atk)

        # Dual wielding: 2+ light melee weapons → off-hand bonus action
        if len(light_melee) >= 2:
            import re as _re2
            off      = light_melee[1]
            off_name = off["name"]
            off_dmg  = off.get("damage", "—")
            off_type = off.get("damage_type", "")
            # PHB: no ability modifier on off-hand damage
            die_m = _re2.match(r'(\d*d\d+)', off_dmg)
            off_dmg_no_mod = die_m.group(1) if die_m else off_dmg
            options.append({
                "label": f"{off_name} (off-hand · bonus action)",
                "weapon": off_name,
                "bonus": off.get("attack_bonus", 0),
                "damage": off_dmg_no_mod, "dmg_type": off_type,
                "mode": "offhand", "damage_override": off_dmg_no_mod,
                "note": "No ability modifier to damage (PHB two-weapon fighting rule)",
            })

        return options

    def _find_weapon_in_text(self, text):
        options = self._get_attack_options()
        text_lower = text.lower()

        # First pass: mode-specific matches (more specific wins)
        for opt in options:
            if opt["weapon"].lower() not in text_lower:
                continue
            mode = opt.get("mode", "melee")
            if mode == "melee_2h" and any(
                    kw in text_lower for kw in ["two-handed", "two handed", "both hands", "two hand"]):
                return opt
            if mode == "thrown" and any(
                    kw in text_lower for kw in ["throw", "thrown", "hurl", "toss", "fling"]):
                return opt
            if mode == "offhand" and any(
                    kw in text_lower for kw in ["off-hand", "off hand", "offhand", "bonus action", "second attack"]):
                return opt

        # Second pass: default (melee or ranged)
        for opt in options:
            if opt["weapon"].lower() in text_lower and opt.get("mode") in ("melee", "ranged"):
                return opt

        return None

    def _build_combat_input(self):
        for w in self._input_frame.winfo_children():
            w.destroy()

        row = tk.Frame(self._input_frame, bg=PANEL)
        row.pack(fill="x", padx=6, pady=(4, 4))

        self._combat_entry = tk.Entry(
            row, bg=INPUT_BG, fg=FG, font=FONT_BODY,
            relief="flat", insertbackground=FG)
        self._combat_entry.pack(side="left", fill="x", expand=True, padx=(0, 6), ipady=5)
        self._combat_entry.bind("<Return>", lambda e: self._send_combat_action())
        self._combat_entry.focus_set()

        tk.Button(row, text="→", font=FONT_HDR,
                  bg=ACCENT, fg="#1a1a2e", relief="flat", bd=0, padx=12, pady=3,
                  activebackground="#e0c060", activeforeground="#1a1a2e",
                  command=self._send_combat_action).pack(side="right")

    # ── Action reference panel ────────────────────────────────────────────────

    def _tooltip_show(self, event, text):
        self._tooltip_hide()
        tw = tk.Toplevel(self.root)
        tw.overrideredirect(True)
        tw.attributes("-topmost", True)
        tk.Label(tw, text=text, font=FONT_SM, bg="#2a2a1a", fg=ACCENT,
                 relief="flat", bd=0, padx=8, pady=4).pack()
        tw.update_idletasks()
        x = event.x_root + 14
        y = event.y_root + 14
        tw.geometry(f"+{x}+{y}")
        self._active_tooltip = tw

    def _tooltip_hide(self, _event=None):
        tw = getattr(self, "_active_tooltip", None)
        if tw:
            try:
                tw.destroy()
            except Exception:
                pass
        self._active_tooltip = None

    def _open_action_panel(self):
        INCAPACITATING = {"Stunned", "Paralyzed", "Incapacitated", "Unconscious"}
        player_comb    = next((c for c in self.session.get("initiative_order", [])
                               if c.get("is_player")), None)
        p_conds        = set(player_comb.get("conditions", []) if player_comb
                             else self.session.get("conditions", []))
        action_blocked = bool(INCAPACITATING & p_conds)
        blocked_reason = f"Condition: {', '.join(INCAPACITATING & p_conds)}" if action_blocked else ""

        d = tk.Toplevel(self.root)
        d.title("Available Actions")
        d.configure(bg=BG)
        d.resizable(False, False)

        pad_x = 16

        def section(label):
            tk.Frame(d, bg=ACCENT, height=1).pack(fill="x", padx=pad_x, pady=(10, 0))
            tk.Label(d, text=label, font=FONT_SM, bg=BG, fg=ACCENT).pack(
                anchor="w", padx=pad_x, pady=(2, 4))

        def row(text, available, reason=""):
            fg_col = FG if available else DIM
            lbl = tk.Label(d, text=text, font=FONT_BODY, bg=BG, fg=fg_col,
                           cursor="arrow", anchor="w", justify="left")
            lbl.pack(fill="x", padx=pad_x + 8, pady=1)
            if not available and reason:
                lbl.bind("<Enter>", lambda e, r=reason: self._tooltip_show(e, r))
                lbl.bind("<Leave>", self._tooltip_hide)

        # ── ACTIONS ──────────────────────────────────────────────────────────
        section("⚔  ACTIONS")

        attack_opts = self._get_attack_options()
        main_attacks = [o for o in attack_opts if o.get("mode") != "offhand"]
        if main_attacks:
            for opt in main_attacks:
                text = f"  ⚔  {opt['label']}  {opt['bonus']:+d} · {opt['damage']} {opt['dmg_type']}"
                row(text, available=not action_blocked,
                    reason=blocked_reason or "")
        else:
            row("  ⚔  No weapons equipped", available=False, reason="Equip a weapon in the character sheet")

        tk.Label(d, text="  ─── Standard Actions ───", font=FONT_SM,
                 bg=BG, fg=DIM).pack(anchor="w", padx=pad_x + 8, pady=(4, 0))
        for std in ("Dash", "Dodge", "Disengage", "Hide"):
            row(f"  ↳  {std}", available=not action_blocked, reason=blocked_reason)

        # ── BONUS ACTIONS ─────────────────────────────────────────────────────
        section("★  BONUS ACTIONS")

        offhand = [o for o in attack_opts if o.get("mode") == "offhand"]
        for opt in offhand:
            text = f"  ⚔  {opt['label']}  {opt['bonus']:+d} · {opt['damage']} {opt['dmg_type']}"
            row(text, available=not action_blocked, reason=blocked_reason)

        uses = self.char.get("feature_uses", {}) if self.char else {}
        bonus_features = {k: v for k, v in uses.items() if k in self._BONUS_ACTION_FEATURES}
        if bonus_features:
            for fname, data in bonus_features.items():
                cur = data.get("current", 0)
                mx  = data.get("max", 1)
                avail = cur > 0
                text  = f"  ★  {fname}  ({cur}/{mx})"
                row(text, available=avail,
                    reason=f"No charges remaining — {cur}/{mx}")
        else:
            row("  No bonus actions available", available=False, reason="")

        tk.Label(d, text="  Describe your action in the text bar below.",
                 font=FONT_SM, bg=BG, fg=DIM).pack(anchor="w", padx=pad_x, pady=(10, 12))

        d.update_idletasks()
        x = self.root.winfo_x() + (self.root.winfo_width()  - d.winfo_width())  // 2
        y = self.root.winfo_y() + (self.root.winfo_height() - d.winfo_height()) // 2
        d.geometry(f"+{x}+{y}")
        d.bind("<Escape>", lambda _e: d.destroy())

    # ── Client-side fallback action parsing ───────────────────────────────────

    def _parse_action_from_text(self, text):
        option = self._find_weapon_in_text(text)
        if option and option.get("mode") != "offhand":
            return {"type": "action_taken", "action": "attack",
                    "weapon": option["weapon"], "mode": option.get("mode"),
                    "damage_override": option.get("damage_override")}
        from models.spells import SPELLS
        text_lower = text.lower()
        for name in SPELLS:
            if name.lower() in text_lower:
                available = get_available_combat_spells(self.char)
                if any(a["name"] == name for a in available):
                    return {"type": "action_taken", "action": "spell",
                            "spell": name, "slot": None}
        feature = self._detect_feature_in_text(text)
        if feature and feature not in self._BONUS_ACTION_FEATURES:
            return {"type": "action_taken", "action": "feature", "feature": feature}
        for std in ("dodge", "dash", "disengage", "hide"):
            if std in text_lower:
                return {"type": "action_taken", "action": std}
        return None

    def _parse_bonus_from_text(self, text):
        option = self._find_weapon_in_text(text)
        if option and option.get("mode") == "offhand":
            return {"type": "bonus_action_taken", "action": "attack",
                    "weapon": option["weapon"],
                    "damage_override": option.get("damage_override")}
        feature = self._detect_feature_in_text(text)
        if feature and feature in self._BONUS_ACTION_FEATURES:
            return {"type": "bonus_action_taken", "action": "feature", "feature": feature}
        return None

    # Bonus-action features that don't consume the attack action
    _BONUS_ACTION_FEATURES = {
        "Rage", "Second Wind", "Wild Shape", "Bardic Inspiration",
        "Ki Points", "Channel Divinity",
    }

    def _detect_feature_in_text(self, text):
        text_lower = text.lower()
        uses = self.char.get("feature_uses", {}) if self.char else {}
        for name in uses:
            if name.lower() in text_lower:
                return name
        return None

    def _apply_combat_feature(self, name):
        uses = self.char.get("feature_uses", {})
        if name not in uses:
            return False
        data = uses[name]
        if data["current"] <= 0:
            self._display(
                f"  {name}: no charges remaining ({data['current']}/{data['max']}).\n\n",
                "danger")
            return False
        data["current"] -= 1
        self._display(
            f"  {name} activated! ({data['current']}/{data['max']} remaining)\n\n",
            "system")
        self._refresh_features()
        return True

    def _send_combat_action(self):
        if not getattr(self, "_combat_entry", None):
            return
        action = self._combat_entry.get().strip()
        if not action:
            return
        self._combat_entry.delete(0, "end")
        self._set_input_enabled(False)
        self._display(f"  You: {action}\n\n", "player")
        self._combat_last_action = action

        def _end_turn():
            cb.end_turn(self.session)
            self.root.after(300, self._next_turn)

        def _on_dm_result(result):
            events    = result.get("events", [])
            action_ev = next((e for e in events if e["type"] == "action_taken"), None)
            bonus_ev  = next((e for e in events if e["type"] == "bonus_action_taken"), None)

            # Client-side fallback if DM didn't emit tags
            if not action_ev:
                action_ev = self._parse_action_from_text(action)
            if not bonus_ev:
                bonus_ev = self._parse_bonus_from_text(action)

            # Apply bonus action feature first (if any)
            if bonus_ev and bonus_ev.get("action") == "feature":
                self._apply_combat_feature(bonus_ev["feature"])

            if not action_ev:
                _end_turn()
                return

            act = action_ev.get("action", "")

            if act == "attack":
                weapon   = action_ev.get("weapon", "")
                mode     = action_ev.get("mode")
                dmg_ovr  = action_ev.get("damage_override")
                opts     = self._get_attack_options()
                mode_map = {"twohanded": "melee_2h", "thrown": "thrown", "ranged": "ranged"}
                mapped   = mode_map.get(mode, mode)
                opt = next((o for o in opts
                            if o["weapon"].lower() == weapon.lower()
                            and (mapped is None or o.get("mode") == mapped)), None)
                if opt is None:
                    opt = next((o for o in opts
                                if o["weapon"].lower() == weapon.lower()), None)
                if opt:
                    dmg_ovr = dmg_ovr or opt.get("damage_override")
                    lbl     = opt["label"]
                else:
                    lbl = weapon
                self._do_player_attack(weapon, damage_override=dmg_ovr,
                                       label=lbl, skip_dm_call=False)

            elif act == "spell":
                from models.spells import SPELLS
                spell_name = action_ev.get("spell", "")
                spell_data = SPELLS.get(spell_name)
                if not spell_data:
                    _end_turn()
                    return
                slot = action_ev.get("slot")
                if slot is None and spell_data["level"] > 0:
                    sc_slots = self.char.get("spellcasting", {}).get("slots", {})
                    for lvl in sorted(sc_slots.keys(), key=int):
                        if int(lvl) >= spell_data["level"]:
                            av = sc_slots[lvl]
                            if av.get("total", 0) - av.get("used", 0) > 0:
                                slot = int(lvl)
                                break
                if slot is None:
                    slot = spell_data["level"]
                living = [c for c in self.session["initiative_order"]
                          if not c["is_player"] and c["hp"] > 0]
                target = living[0]["name"] if living else ""
                self._do_player_spell(spell_name, spell_data, slot, target, skip_dm_call=False)

            elif act == "feature":
                feat_ok = self._apply_combat_feature(action_ev.get("feature", ""))
                if feat_ok:
                    _end_turn()
                else:
                    self._build_combat_input()

            elif act in ("dodge", "dash", "disengage", "hide"):
                _end_turn()

            else:
                _end_turn()

        self._dm_call(action, on_action=_on_dm_result)

    # ── Startup ────────────────────────────────────────────────────────────────

    def _startup_dialog(self):
        d = tk.Toplevel(self.root)
        d.title("D&D AI Dungeon Master")
        d.configure(bg=BG)
        d.grab_set()
        d.resizable(False, False)
        self.root.update_idletasks()
        rx = self.root.winfo_x() + self.root.winfo_width()  // 2 - 220
        ry = self.root.winfo_y() + self.root.winfo_height() // 2 - 200
        d.geometry(f"440x400+{rx}+{ry}")

        tk.Frame(d, bg=ACCENT, height=4).pack(fill="x")
        self._dlg_title = tk.Label(d, text="  ⚔  D&D AI DUNGEON MASTER",
                                   font=FONT_HDR, bg=PANEL, fg=ACCENT, pady=8)
        self._dlg_title.pack(fill="x")

        self._dlg_body = tk.Frame(d, bg=BG, padx=24, pady=16)
        self._dlg_body.pack(fill="both", expand=True)

        self._dlg_err = tk.Label(d, text="", font=FONT_SM, bg=BG, fg=RED)
        self._dlg_err.pack(pady=(0, 6))

        self._show_mode_page(d)

    def _clear_body(self):
        for w in self._dlg_body.winfo_children():
            w.destroy()
        self._dlg_err.config(text="")

    def _btn_large(self, parent, text, sub, command):
        f        = tk.Frame(parent, bg=BTN_BG, padx=12, pady=10, cursor="hand2")
        f.pack(fill="x", pady=6)
        lbl_main = tk.Label(f, text=text, font=FONT_HDR, bg=BTN_BG, fg=ACCENT)
        lbl_main.pack(anchor="w")
        lbl_sub  = tk.Label(f, text=sub,  font=FONT_SM,  bg=BTN_BG, fg=DIM)
        lbl_sub.pack(anchor="w")

        def on_enter(_):
            f.config(bg=ACCENT)
            lbl_main.config(bg=ACCENT, fg="#1a1a2e")
            lbl_sub.config(bg=ACCENT,  fg="#1a1a2e")

        def on_leave(_):
            f.config(bg=BTN_BG)
            lbl_main.config(bg=BTN_BG, fg=ACCENT)
            lbl_sub.config(bg=BTN_BG,  fg=DIM)

        for w in (f, lbl_main, lbl_sub):
            w.bind("<Button-1>", lambda e: command())
            w.bind("<Enter>",    on_enter)
            w.bind("<Leave>",    on_leave)
        return f

    # ── Page 1: Mode selection ─────────────────────────────────────────────────

    def _show_mode_page(self, d):
        self._clear_body()
        self._dlg_title.config(text="  ⚔  D&D AI DUNGEON MASTER")

        tk.Label(self._dlg_body, text="What would you like to do?",
                 font=FONT_BODY, bg=BG, fg=DIM).pack(anchor="w", pady=(0, 12))

        self._btn_large(self._dlg_body,
                        "⚔  New Adventure",
                        "Select a character and start fresh at Level 1.",
                        lambda: self._show_character_page(d))

        self._btn_large(self._dlg_body,
                        "↗  Next Adventure",
                        "Continue a leveled character into a brand-new story.",
                        lambda: self._show_next_adventure_page(d))

        self._btn_large(self._dlg_body,
                        "↩  Resume Session",
                        "Continue from a previously saved session.",
                        lambda: self._show_resume_page(d))

    # ── Page 2a: Character selection ───────────────────────────────────────────

    def _show_character_page(self, d):
        self._clear_body()
        self._dlg_title.config(text="  ⚔  SELECT CHARACTER")

        tk.Label(self._dlg_body, text="Choose a character to play:",
                 font=FONT_SM, bg=BG, fg=DIM).pack(anchor="w", pady=(0, 4))

        lf = tk.Frame(self._dlg_body, bg=INPUT_BG)
        lf.pack(fill="both", expand=True)
        sb = tk.Scrollbar(lf, bg=BG, troughcolor=INPUT_BG)
        sb.pack(side="right", fill="y")
        char_lb = tk.Listbox(lf, bg=INPUT_BG, fg=FG, font=FONT_BODY,
                             selectbackground=ACCENT, selectforeground="#1a1a2e",
                             relief="flat", bd=0, activestyle="none",
                             exportselection=False,
                             yscrollcommand=sb.set, height=7)
        sb.config(command=char_lb.yview)
        char_lb.pack(fill="both", expand=True, padx=4, pady=4)

        def _populate(select_last=False):
            chars = list_characters()
            char_lb.delete(0, "end")
            for c in chars:
                char_lb.insert("end", c)
            if chars:
                idx = len(chars) - 1 if select_last else 0
                char_lb.select_set(idx)
                char_lb.see(idx)

        _populate()

        btn_row = tk.Frame(self._dlg_body, bg=BG)
        btn_row.pack(fill="x", pady=(8, 0))

        def new_char():
            import subprocess
            builder = Path(__file__).parent / "character_builder" / "character_builder_app.py"
            def _run():
                subprocess.run([sys.executable, str(builder)],
                               cwd=str(builder.parent))
                self._dlg_body.after(0, lambda: _populate(select_last=True))
            threading.Thread(target=_run, daemon=True).start()

        def delete_char():
            sel = char_lb.curselection()
            if not sel:
                self._dlg_err.config(text="Select a character to delete.")
                return
            name = char_lb.get(sel[0])
            if not messagebox.askyesno("Delete Character",
                                       f"Permanently delete '{name}'?",
                                       parent=d):
                return
            char_file = _root / "data" / "characters" / f"{name}.json"
            if char_file.exists():
                char_file.unlink()
            _populate()

        def begin():
            sel = char_lb.curselection()
            if not sel:
                self._dlg_err.config(text="Select a character first.")
                return
            char_name = char_lb.get(sel[0])
            try:
                self.char = load_character(char_name)
            except Exception as e:
                self._dlg_err.config(text=f"Could not load character: {e}")
                return
            has_progress = self.char.get("level", 1) > 1 or self.char.get("experience", 0) > 0
            if has_progress:
                level = self.char.get("level", 1)
                cls   = self.char.get("class", "")
                xp    = self.char.get("experience", 0)
                if not messagebox.askyesno(
                    "Overwrite Progress?",
                    f"{char_name} has saved progress (Lv {level} {cls}, {xp} XP).\n\n"
                    f"Starting a New Adventure will permanently delete this progress.\n\n"
                    f"Proceed?",
                    parent=d,
                ):
                    return
            reset_to_level1(self.char)
            save_character(self.char)
            self._launch_new_adventure(d)

        tk.Button(btn_row, text="+ New Character", font=FONT_SM, bg=BTN_BG,
                  fg=ACCENT, relief="flat", bd=0, padx=8, pady=5,
                  activebackground=ACCENT, activeforeground="#1a1a2e",
                  command=new_char).pack(side="left", padx=(0, 4))
        tk.Button(btn_row, text="Delete", font=FONT_SM, bg=BTN_BG, fg=RED,
                  relief="flat", bd=0, padx=8, pady=5,
                  activebackground="#5a1e1e", activeforeground=FG,
                  command=delete_char).pack(side="left")
        tk.Button(btn_row, text="← Back", font=FONT_SM, bg=BTN_BG, fg=DIM,
                  relief="flat", bd=0, padx=8, pady=5,
                  activebackground=BTN_BG, activeforeground=FG,
                  command=lambda: self._show_mode_page(d)).pack(side="right", padx=(4, 0))
        tk.Button(btn_row, text="Begin →", font=FONT_SM, bg=ACCENT, fg="#1a1a2e",
                  relief="flat", bd=0, padx=12, pady=5,
                  activebackground="#e0c060", activeforeground="#1a1a2e",
                  command=begin).pack(side="right")

    def _launch_new_adventure(self, d):
        try:
            self.dm = dm_module.from_config()
        except Exception as e:
            self._dlg_err.config(text=f"DM config error: {e}")
            return
        char_name = self.char["name"]
        self.session = gs.empty_session(character_name=char_name,
                                        session_name=char_name)
        gs.init_hp(self.session, self.char)
        start_adventure(self.session, self.char)
        d.destroy()
        self._start_adventure(new=True)

    # ── Page 2c: Next Adventure (leveled characters only) ─────────────────────

    def _show_next_adventure_page(self, d):
        self._clear_body()
        self._dlg_title.config(text="  ↗  NEXT ADVENTURE")

        # Load every character and keep only those with stored progress
        chars = []
        for name in list_characters():
            try:
                c = load_character(name)
                if c.get("level", 1) > 1 or c.get("experience", 0) > 0:
                    chars.append(c)
            except Exception:
                pass

        if not chars:
            tk.Label(self._dlg_body,
                     text="No characters with saved progress yet.",
                     font=FONT_BODY, bg=BG, fg=DIM).pack(pady=(20, 6))
            tk.Label(self._dlg_body,
                     text="Play a New Adventure first to earn XP and level up.",
                     font=FONT_SM, bg=BG, fg=DIM).pack()
            tk.Button(self._dlg_body, text="← Back", font=FONT_SM, bg=BTN_BG,
                      fg=DIM, relief="flat", bd=0, padx=8, pady=5,
                      activebackground=BTN_BG, activeforeground=FG,
                      command=lambda: self._show_mode_page(d)).pack(pady=12)
            return

        tk.Label(self._dlg_body, text="Choose a character to carry forward:",
                 font=FONT_SM, bg=BG, fg=DIM).pack(anchor="w", pady=(0, 4))

        lf = tk.Frame(self._dlg_body, bg=INPUT_BG)
        lf.pack(fill="both", expand=True)
        sb = tk.Scrollbar(lf, bg=BG, troughcolor=INPUT_BG)
        sb.pack(side="right", fill="y")
        char_lb = tk.Listbox(lf, bg=INPUT_BG, fg=FG, font=FONT_BODY,
                             selectbackground=ACCENT, selectforeground="#1a1a2e",
                             relief="flat", bd=0, activestyle="none",
                             exportselection=False,
                             yscrollcommand=sb.set, height=7)
        sb.config(command=char_lb.yview)
        char_lb.pack(fill="both", expand=True, padx=4, pady=4)

        for c in chars:
            level = c.get("level", 1)
            cls   = c.get("class", "")
            xp    = c.get("experience", 0)
            char_lb.insert("end", f"{c['name']}  ·  Lv {level} {cls}  ({xp} XP)")
        char_lb.select_set(0)

        btn_row = tk.Frame(self._dlg_body, bg=BG)
        btn_row.pack(fill="x", pady=(8, 0))

        def begin():
            sel = char_lb.curselection()
            if not sel:
                self._dlg_err.config(text="Select a character first.")
                return
            self.char = chars[sel[0]]
            self._launch_new_adventure(d)

        tk.Button(btn_row, text="← Back", font=FONT_SM, bg=BTN_BG, fg=DIM,
                  relief="flat", bd=0, padx=8, pady=5,
                  activebackground=BTN_BG, activeforeground=FG,
                  command=lambda: self._show_mode_page(d)).pack(side="left")
        tk.Button(btn_row, text="Begin →", font=FONT_SM, bg=ACCENT, fg="#1a1a2e",
                  relief="flat", bd=0, padx=12, pady=5,
                  activebackground="#e0c060", activeforeground="#1a1a2e",
                  command=begin).pack(side="right")

    # ── Page 2b: Resume session ────────────────────────────────────────────────

    def _show_resume_page(self, d):
        self._clear_body()
        self._dlg_title.config(text="  ↩  RESUME SESSION")

        sessions = gs.list_sessions()

        if not sessions:
            tk.Label(self._dlg_body, text="No saved sessions found.",
                     font=FONT_BODY, bg=BG, fg=DIM).pack(pady=20)
            tk.Button(self._dlg_body, text="← Back", font=FONT_SM, bg=BTN_BG,
                      fg=DIM, relief="flat", bd=0, padx=8, pady=5,
                      command=lambda: self._show_mode_page(d)).pack()
            return

        tk.Label(self._dlg_body, text="Choose a session to resume:",
                 font=FONT_SM, bg=BG, fg=DIM).pack(anchor="w", pady=(0, 4))

        lf = tk.Frame(self._dlg_body, bg=INPUT_BG)
        lf.pack(fill="both", expand=True)
        sb = tk.Scrollbar(lf, bg=BG, troughcolor=INPUT_BG)
        sb.pack(side="right", fill="y")
        ses_lb = tk.Listbox(lf, bg=INPUT_BG, fg=FG, font=FONT_BODY,
                            selectbackground=ACCENT, selectforeground="#1a1a2e",
                            relief="flat", bd=0, activestyle="none",
                            exportselection=False,
                            yscrollcommand=sb.set, height=7)
        sb.config(command=ses_lb.yview)
        ses_lb.pack(fill="both", expand=True, padx=4, pady=4)
        for s in sessions:
            ses_lb.insert("end", s)
        ses_lb.select_set(0)

        btn_row = tk.Frame(self._dlg_body, bg=BG)
        btn_row.pack(fill="x", pady=(8, 0))

        def resume():
            sel = ses_lb.curselection()
            if not sel:
                self._dlg_err.config(text="Select a session first.")
                return
            sname = ses_lb.get(sel[0])
            try:
                self.session = gs.load_session(sname)
            except Exception as e:
                self._dlg_err.config(text=f"Could not load session: {e}")
                return
            char_name = self.session.get("character_name", "")
            try:
                self.char = load_character(char_name)
            except Exception as e:
                self._dlg_err.config(text=f"Could not load character '{char_name}': {e}")
                return
            try:
                self.dm = dm_module.from_config()
            except Exception as e:
                self._dlg_err.config(text=f"DM config error: {e}")
                return
            d.destroy()
            self._start_adventure(new=False)

        tk.Button(btn_row, text="← Back", font=FONT_SM, bg=BTN_BG, fg=DIM,
                  relief="flat", bd=0, padx=8, pady=5,
                  activebackground=BTN_BG, activeforeground=FG,
                  command=lambda: self._show_mode_page(d)).pack(side="right", padx=(4, 0))
        tk.Button(btn_row, text="Resume →", font=FONT_SM, bg=ACCENT, fg="#1a1a2e",
                  relief="flat", bd=0, padx=12, pady=5,
                  activebackground="#e0c060", activeforeground="#1a1a2e",
                  command=resume).pack(side="right")

    def _start_adventure(self, new=True):
        self._char_var.set(
            f"{self.char.get('name','')}  —  "
            f"{self.char.get('race','')} {self.char.get('class','')} "
            f"Lv.{self.char.get('level',1)}")
        self._loc_var.set(self.session.get("location", "Unknown"))
        self._update_sidebar()
        self.state = "COMBAT" if self.session.get("in_combat") else "EXPLORING"

        if not new and self.session.get("history"):
            if self.session.get("in_combat"):
                self._display("── Resuming — combat in progress ──\n\n", "header")
                for entry in self.session["history"][-3:]:
                    tag = "player" if entry["role"] == "player" else "dm"
                    prefix = "> " if tag == "player" else ""
                    self._display(prefix + entry["text"] + "\n\n", tag)
                self._next_turn()
            else:
                self._display("── Resuming session ──\n\n", "header")
                for entry in self.session["history"][-6:]:
                    tag = "player" if entry["role"] == "player" else "dm"
                    prefix = "> " if tag == "player" else ""
                    self._display(prefix + entry["text"] + "\n\n", tag)
                self._set_input_enabled(True)
        else:
            self._display("── Adventure begins ──\n\n", "header")
            self._set_input_enabled(False)
            self._dm_call("Begin the adventure. Set the opening scene.")

    # ── Action flow ────────────────────────────────────────────────────────────

    def _send_action(self):
        if self.state != "EXPLORING":
            return
        action = self._input_var.get().strip()
        if not action:
            return
        self._input_var.set("")
        self._set_input_enabled(False)
        self._display(f"> {action}\n\n", "player")
        self._dm_call(action)

    def _dm_call(self, action, on_complete=None, on_action=None):
        self._display("DM is thinking...\n", "system")
        def _thread():
            try:
                result = self.dm.respond(self.session, self.char, action)
                self.root.after(0, lambda: self._handle_dm_response(result, on_complete, on_action))
            except Exception as e:
                msg = str(e) or repr(e)
                self.root.after(0, lambda: self._handle_dm_error(msg, on_complete, on_action))
        threading.Thread(target=_thread, daemon=True).start()

    def _handle_dm_response(self, result, on_complete=None, on_action=None):
        self._erase_last_line()
        self._display(result["narration"] + "\n\n", "dm")
        self._loc_var.set(self.session.get("location", self.session.get("scene", "")[:40]))

        if on_complete:
            on_complete()
            return

        if on_action:
            on_action(result)
            return

        if self._story_mode:
            self._set_input_enabled(True)
            return

        pending_xp  = 0
        beat_done   = False
        climax_done = False
        show_break  = False

        for ev in result["events"]:
            if ev["type"] == "combat_start":
                self._start_combat(ev["enemies"])
                return
            elif ev["type"] == "skill_check":
                self._handle_skill_check(ev["skill"], ev["dc"])
                return
            elif ev["type"] == "companion_join":
                self._handle_companion_join(ev["name"])
            elif ev["type"] == "scene_change":
                self._on_scene_change(ev["location"])
            elif ev["type"] == "xp_award":
                pending_xp += ev["amount"]
            elif ev["type"] == "beat_complete":
                adv = self.session.get("adventure") or {}
                player_turns   = sum(1 for h in self.session.get("history", [])
                                     if h.get("role") == "player")
                turns_this_act = player_turns - adv.get("beat_turn_start", 0)
                # Require at least 4 player exchanges per act before beat can advance
                if turns_this_act >= 4:
                    beat_done = True
            elif ev["type"] == "climax_reached":
                climax_done = True
            elif ev["type"] == "break_suggested":
                show_break = True

        if climax_done:
            self._display("── The final confrontation is at hand ──\n\n", "header")
            adv = self.session.get("adventure") or {}
            if adv.get("current_beat", 0) < 4:
                adv["current_beat"] = 4
                pending_xp += adv.get("climax_xp", 0)

        if beat_done:
            # Beat XP replaces any [XP] the DM also emitted in this same response
            pending_xp = 0
            beat_xp = self._advance_beat()
            pending_xp += beat_xp
            # Record which player turn this beat completed on
            adv = self.session.get("adventure") or {}
            adv["beat_turn_start"] = sum(1 for h in self.session.get("history", [])
                                         if h.get("role") == "player")

        if show_break:
            self._show_break_point()

        if pending_xp:
            self._award_xp(pending_xp)
            return

        self._set_input_enabled(True)

    def _ask_starting_location(self, on_confirm):
        """Modal dialog that asks the player where their story begins, then calls on_confirm(location)."""
        d = tk.Toplevel(self.root)
        d.title("Story Mode")
        d.resizable(False, False)
        d.configure(bg=BG)
        d.grab_set()

        tk.Label(d, text="Where does your story begin?",
                 font=FONT_BODY, bg=BG, fg=ACCENT).pack(padx=20, pady=(18, 12))

        loc_var = tk.StringVar()
        entry = tk.Entry(d, textvariable=loc_var, font=FONT_BODY,
                         bg=INPUT_BG, fg=FG, insertbackground=FG,
                         relief="flat", bd=0)
        entry.pack(fill="x", padx=20, pady=(0, 14), ipady=6)
        entry.focus_set()

        err_lbl = tk.Label(d, text="", font=FONT_SM, bg=BG, fg="#cc4444")
        err_lbl.pack()

        def _confirm():
            loc = loc_var.get().strip()
            if not loc:
                err_lbl.config(text="Enter a starting location.")
                return
            d.destroy()
            on_confirm(loc)

        tk.Button(d, text="Begin Story", font=FONT_SM,
                  bg=ACCENT, fg="#1a1a2e", relief="flat", bd=0,
                  padx=14, pady=6, activebackground=FG,
                  command=_confirm).pack(pady=(0, 18))

        entry.bind("<Return>", lambda _e: _confirm())

        d.update_idletasks()
        x = self.root.winfo_x() + (self.root.winfo_width()  - d.winfo_width())  // 2
        y = self.root.winfo_y() + (self.root.winfo_height() - d.winfo_height()) // 2
        d.geometry(f"+{x}+{y}")

    def _enter_story_mode(self, location):
        self._story_mode = True
        self._story_mode_label.pack(side="right", padx=(0, 4))
        self._set_input_enabled(False)
        self._display("── Story Mode ──\n\n", "header")
        opening = (
            f"Story Mode begins. Set the opening scene: the character finds themselves at "
            f"{location}. "
            "Describe this location vividly — sights, sounds, smells, the people or atmosphere "
            "present. Make it feel alive and specific to where they are. "
            "End with the character taking stock of their surroundings, ready to act. "
            "Do not emit any [COMBAT:], [CHECK:], or [XP:] tags yet. "
            "This is a purely narrative opening scene."
        )
        self._dm_call(opening)

    def _exit_story_mode(self):
        self._story_mode = False
        try:
            self._story_mode_label.pack_forget()
        except Exception:
            pass
        self._display("── Story Mode ended ──\n\n", "header")
        self._set_input_enabled(True)

    def _advance_beat(self):
        """Advance the adventure beat and display a transition message. Returns XP earned."""
        xp = gc_advance_beat(self.session)
        adv  = self.session.get("adventure", {})
        beat = adv.get("current_beat", 0)
        if beat <= 3:
            self._display(f"── Act {beat} begins ──\n\n", "header")
        elif beat == 4:
            self._display("── The story reaches its climax ──\n\n", "header")
        return xp

    def _show_break_point(self):
        """Embed a break-point banner in the narration suggesting a good save point."""
        self._narration.config(state="normal")
        self._narration.insert("end",
            "─" * 52 + "\n"
            "  Good stopping point — this is a natural break\n"
            "  in the story. Save & Quit when ready, or keep\n"
            "  going if you want to push on.\n"
            + "─" * 52 + "\n\n",
            "system")
        self._narration.see("end")
        self._narration.config(state="disabled")

    def _handle_dm_error(self, msg, on_complete=None, on_action=None):
        self._erase_last_line()
        self._display(f"[DM Error: {msg}]\n\n", "danger")
        if on_complete:
            on_complete()
        elif on_action:
            self._build_combat_input()
        else:
            self._set_input_enabled(True)

    # ── Combat ─────────────────────────────────────────────────────────────────

    def _start_combat(self, enemy_specs):
        self._display("── Combat begins! ──\n\n", "header")
        dex_mod   = modifier(self.char["abilities"].get("dexterity", 10))
        init_roll = dice.initiative(dex_mod)

        self._display(f"Roll for initiative!  (modifier {init_roll['modifier']:+d})\n\n", "system")

        def _after_init():
            result = gc_setup_combat(self.session, self.char, enemy_specs,
                                     d20_initiative=init_roll["total"])
            # Add active companions to initiative order
            from models.character import modifier as _cmod
            for comp in self.session.get("companions", []):
                if comp.get("status") == "dead":
                    continue
                dex_mod  = _cmod(comp["abilities"].get("dexterity", 10))
                init_val = dice.initiative(dex_mod)["total"]
                self.session["initiative_order"].append({
                    "name":       comp["name"],
                    "initiative": init_val,
                    "hp":         comp["hp"]["current"],
                    "max_hp":     comp["hp"]["max"],
                    "ac":         comp["ac"],
                    "is_player":  False,
                    "is_companion": True,
                    "conditions": [],
                })
            # Re-sort initiative order
            self.session["initiative_order"].sort(
                key=lambda c: c["initiative"], reverse=True)
            self.state = "COMBAT"
            self._update_sidebar()
            self._display("Initiative order:\n", "system")
            order_lines = "\n".join(
                f"  {c['initiative']:2d}  {c['name']}"
                + (" [you]" if c["is_player"] else "")
                + (" [companion]" if c.get("is_companion") else "")
                for c in self.session["initiative_order"])
            self._display(order_lines + "\n\n", "system")
            self._next_turn()

        self._show_roll_button("Initiative", init_roll["roll"], _after_init)

    def _next_turn(self):
        self._update_sidebar()
        current = gs.current_combatant(self.session)
        if not current:
            self._end_combat(victory=True)
            return
        if not gs.enemies_alive(self.session):
            self._end_combat(victory=True)
            return

        if current["is_player"]:
            if self.session["current_hp"] <= 0:
                if self.session.get("stable"):
                    self._display("  You are stabilized — waiting for aid.\n\n", "system")
                    cb.end_turn(self.session)
                    self.root.after(800, self._next_turn)
                else:
                    self._handle_death_saves()
                return
            self._display(f"── Round {self.session['round']} — Your turn ──\n\n", "header")
            self._build_combat_input()
        elif current.get("is_companion"):
            self.root.after(800, self._do_companion_turn)
        else:
            self.root.after(800, self._do_enemy_turn)

    def _do_player_attack(self, weapon_name, damage_override=None, label=None, skip_dm_call=False):
        living_enemies = [c for c in self.session["initiative_order"]
                          if not c["is_player"] and c["hp"] > 0]
        if not living_enemies:
            self._end_combat(victory=True)
            return
        target = living_enemies[0]["name"]

        weapon = next((a for a in self.char.get("attacks", [])
                       if a["name"].lower() == weapon_name.lower()), None)
        if not weapon:
            self._display(f"  Weapon '{weapon_name}' not found.\n\n", "danger")
            return

        attack_bonus = weapon.get("attack_bonus", 0)
        pre_roll     = dice.d20_check(modifier=attack_bonus)
        display_name = label or weapon_name

        self._display(f"── Attacking {target} with {display_name} ──\n"
                      f"  Attack bonus: {attack_bonus:+d}\n\n", "header")
        self._build_explore_input()

        def _advance_turn():
            if not gs.enemies_alive(self.session):
                self.root.after(300, lambda: self._end_combat(victory=True))
            else:
                self.root.after(300, lambda: (cb.end_turn(self.session), self._next_turn()))

        def _resolve_damage(pre_dmg):
            """Called after damage dice are animated — apply damage and call DM."""
            result = cb.player_attack(self.session, self.char, weapon_name, target,
                                      d20_override=pre_roll["kept"],
                                      damage_override=damage_override,
                                      pre_damage=pre_dmg)
            dmg = result["damage"]["total"]
            self._display(f"  Damage: {dmg} — {target} HP: {result['new_hp']}\n\n", "hit")
            if result.get("killed"):
                self._display(f"  ☠  {target} has fallen!\n\n", "danger")
            if skip_dm_call:
                _advance_turn()
            else:
                prefix  = "CRITICAL HIT! " if result.get("critical") else ""
                outcome = (f"{prefix}The attack hits for {dmg} damage. "
                           f"{target} HP: {result['new_hp']}."
                           + (f" {target} has been defeated!" if result.get("killed") else ""))
                self._dm_call(
                    f"[COMBAT RESULT — narrate this outcome dramatically in 2-3 sentences] "
                    f"{outcome}",
                    on_complete=_advance_turn)

        def _after_roll():
            target_entry = next((c for c in self.session["initiative_order"]
                                 if c["name"] == target), None)
            target_ac = target_entry["ac"] if target_entry else 10
            is_crit   = pre_roll["kept"] == 20
            is_nat1   = pre_roll["kept"] == 1
            will_hit  = is_crit or (not is_nat1 and pre_roll["total"] >= target_ac)

            hit_word = "CRITICAL HIT!" if is_crit else "HIT!" if will_hit else "MISS"
            self._display(
                f"  Roll: {pre_roll['kept']} {attack_bonus:+d} = {pre_roll['total']}"
                f" vs AC {target_ac} — {hit_word}\n\n",
                "hit" if will_hit else "miss")

            if not will_hit:
                if skip_dm_call:
                    _advance_turn()
                else:
                    self._dm_call(
                        f"[COMBAT RESULT — narrate this outcome dramatically in 1-2 sentences] "
                        f"The attack with {display_name} misses {target}.",
                        on_complete=_advance_turn)
                return

            actual_notation = damage_override or weapon["damage"]
            pre_dmg = (dice.critical_damage(actual_notation) if is_crit
                       else dice.damage(actual_notation))
            self._show_damage_button(actual_notation, pre_dmg, is_crit,
                                     on_done=lambda: _resolve_damage(pre_dmg))

        self._show_roll_button(f"d20 ({display_name})", pre_roll["kept"], _after_roll)

    # ── Spell combat ───────────────────────────────────────────────────────────

    def _open_spell_picker(self):
        from models.spells import spell_damage_notation
        living = [c for c in self.session["initiative_order"]
                  if not c["is_player"] and c["hp"] > 0]
        if not living:
            return
        target_name = living[0]["name"]
        available   = get_available_combat_spells(self.char)
        if not available:
            self._display("  No combat spells available.\n\n", "system")
            return

        d = tk.Toplevel(self.root)
        d.title("Cast a Spell")
        d.configure(bg=BG)
        d.resizable(False, False)
        d.grab_set()

        tk.Label(d, text=f"Cast a Spell  →  {target_name}",
                 font=FONT_HDR, bg=BG, fg=ACCENT).pack(padx=16, pady=(12, 4), anchor="w")

        lf = tk.Frame(d, bg=BG)
        lf.pack(fill="both", expand=True, padx=12, pady=(0, 4))
        sb = tk.Scrollbar(lf, orient="vertical", bg=PANEL, troughcolor=INPUT_BG)
        sb.pack(side="right", fill="y")
        lb = tk.Listbox(lf, bg=INPUT_BG, fg=FG, font=FONT_SM,
                        selectbackground=BTN_BG, selectforeground=ACCENT,
                        relief="flat", bd=0, exportselection=False,
                        yscrollcommand=sb.set, width=54,
                        height=min(16, len(available) + len({s["level"] for s in available}) + 1))
        lb.pack(side="left", fill="both", expand=True)
        sb.config(command=lb.yview)

        ICON = {"attack": "⚔", "save": "⊕", "auto": "★"}
        spell_map = {}
        cur_level = -1
        idx = 0
        for entry in available:
            if entry["level"] != cur_level:
                header = "CANTRIPS" if entry["level"] == 0 else f"LEVEL {entry['level']}"
                lb.insert("end", f"   — {header} —")
                lb.itemconfig(idx, fg=ACCENT, selectbackground=BG, selectforeground=ACCENT)
                spell_map[idx] = None
                idx += 1
                cur_level = entry["level"]
            sp        = entry["spell"]
            plvl      = self.char.get("level", 1)
            note      = spell_damage_notation(entry["name"], sp, entry["level"] or 1, plvl)
            dmg_str   = f"  {note} {sp['damage_type']}" if note not in ("0","","—") else ""
            slots_str = f"  [{entry['available_slots']} slots]" if entry["level"] > 0 else ""
            icon      = ICON.get(sp["delivery"], "·")
            lb.insert("end", f"   {icon}  {entry['name']:<26}{dmg_str}{slots_str}")
            spell_map[idx] = entry
            idx += 1

        slot_frame = tk.Frame(d, bg=BG)
        slot_frame.pack(fill="x", padx=12, pady=(0, 2))
        slot_var    = tk.IntVar(value=0)
        selected    = [None]

        def _rebuild_slots(entry):
            for w in slot_frame.winfo_children():
                w.destroy()
            if not entry or entry["level"] == 0:
                return
            tk.Label(slot_frame, text="Slot level:", font=FONT_SM,
                     bg=BG, fg=DIM).pack(side="left", padx=(0, 6))
            sc_slots = self.char.get("spellcasting", {}).get("slots", {})
            for lvl in entry.get("slot_options", []):
                avail = sc_slots.get(str(lvl), {})
                cnt   = avail.get("total", 0) - avail.get("used", 0)
                tk.Button(slot_frame, text=f"{lvl}  ({cnt})", font=FONT_SM,
                          bg=BTN_BG, fg=FG, relief="flat", bd=0, padx=8, pady=3,
                          activebackground=ACCENT, activeforeground="#1a1a2e",
                          command=lambda l=lvl: slot_var.set(l)).pack(side="left", padx=2)
            if entry.get("slot_options"):
                slot_var.set(entry["slot_options"][0])

        err = tk.Label(d, text="", font=FONT_SM, bg=BG, fg=RED)
        err.pack()

        def _on_select(_evt=None):
            sel = lb.curselection()
            if not sel:
                return
            entry = spell_map.get(sel[0])
            selected[0] = entry
            _rebuild_slots(entry)
            err.config(text="")
        lb.bind("<<ListboxSelect>>", _on_select)

        br = tk.Frame(d, bg=BG)
        br.pack(fill="x", padx=12, pady=(4, 14))

        def _cast():
            entry = selected[0]
            if not entry:
                err.config(text="Select a spell first.")
                return
            lvl = slot_var.get() if entry["level"] > 0 else 0
            if entry["level"] > 0 and lvl < entry["level"]:
                err.config(text="Select a slot level.")
                return
            d.destroy()
            self._do_player_spell(entry["name"], entry["spell"], lvl, target_name)

        tk.Button(br, text="Cast", font=FONT_SM,
                  bg=ACCENT, fg="#1a1a2e", relief="flat", bd=0,
                  padx=14, pady=6, activebackground=FG,
                  command=_cast).pack(side="left")
        tk.Button(br, text="Cancel", font=FONT_SM,
                  bg=BTN_BG, fg=DIM, relief="flat", bd=0, padx=14, pady=6,
                  command=d.destroy).pack(side="left", padx=8)

        d.update_idletasks()
        x = self.root.winfo_x() + (self.root.winfo_width()  - d.winfo_width())  // 2
        y = self.root.winfo_y() + (self.root.winfo_height() - d.winfo_height()) // 2
        d.geometry(f"+{x}+{y}")

    def _do_player_spell(self, spell_name, spell_data, slot_level, target_name, skip_dm_call=False):
        import re as _re
        from models.character import use_spell_slot
        from models.spells import spell_damage_notation

        level = spell_data.get("level", 0)
        if level > 0:
            try:
                use_spell_slot(self.char, slot_level)
            except ValueError as e:
                self._display(f"  {e}\n\n", "danger")
                self._set_input_enabled(True)
                return

        delivery     = spell_data.get("delivery", "auto")
        player_level = self.char.get("level", 1)
        dmg_note     = spell_damage_notation(spell_name, spell_data, slot_level, player_level)
        has_damage   = dmg_note not in ("0", "", "—")
        sc           = self.char.get("spellcasting", {})
        atk_bonus    = sc.get("attack_bonus", 0)
        save_dc      = sc.get("spell_save_dc", 8)
        slot_str     = f" (slot {slot_level})" if level > 0 else ""

        self._display(f"── Casting {spell_name}{slot_str} → {target_name} ──\n\n", "header")
        self._build_explore_input()
        self._update_sidebar()

        def _advance_turn():
            if not gs.enemies_alive(self.session):
                self.root.after(300, lambda: self._end_combat(victory=True))
            else:
                self.root.after(300, lambda: (cb.end_turn(self.session), self._next_turn()))

        if delivery == "attack":
            pre_roll = dice.d20_check(modifier=atk_bonus)

            def _resolve_spell_damage(pre_dmg):
                result = process_spell_cast(self.session, self.char, spell_name,
                                            target_name, slot_level,
                                            d20_override=pre_roll["kept"], pre_damage=pre_dmg)
                dmg = (result.get("damage") or {}).get("total", 0)
                self._display(f"  Damage: {dmg} {spell_data['damage_type']} — "
                              f"{target_name} HP: {result['new_hp']}\n\n", "hit")
                if result.get("killed"):
                    self._display(f"  ☠  {target_name} has fallen!\n\n", "danger")
                if spell_data.get("on_hit_effect"):
                    self._display(f"  {spell_data['on_hit_effect']}\n\n", "system")
                if skip_dm_call:
                    _advance_turn()
                else:
                    crit_tag = "CRITICAL HIT! " if result.get("critical") else ""
                    self._dm_call(
                        f"[COMBAT RESULT — narrate this outcome dramatically in 2-3 sentences] "
                        f"{crit_tag}{spell_name} hits {target_name} for {dmg} "
                        f"{spell_data['damage_type']} damage. {target_name} HP: {result['new_hp']}."
                        + (" {target_name} has been defeated!" if result.get("killed") else ""),
                        on_complete=_advance_turn)

            def _after_spell_roll():
                target_c  = next((c for c in self.session["initiative_order"]
                                  if c["name"] == target_name), None)
                target_ac = target_c["ac"] if target_c else 10
                total     = pre_roll["kept"] + atk_bonus
                nat20     = pre_roll["kept"] == 20
                nat1      = pre_roll["kept"] == 1
                hit       = nat20 or (not nat1 and total >= target_ac)

                if not hit:
                    self._display(f"  Miss — {pre_roll['kept']} + {atk_bonus:+d} = "
                                  f"{total} vs AC {target_ac}\n\n", "danger")
                    if skip_dm_call:
                        _advance_turn()
                    else:
                        self._dm_call(
                            f"[COMBAT RESULT — narrate this outcome dramatically in 1-2 sentences] "
                            f"{spell_name} misses {target_name}.",
                            on_complete=_advance_turn)
                    return

                crit = nat20
                self._display(f"  {'CRIT! ' if crit else ''}Hit — {pre_roll['kept']} + "
                              f"{atk_bonus:+d} = {total} vs AC {target_ac}\n\n", "hit")

                if has_damage:
                    m = _re.match(r'(\d*)d(\d+)', dmg_note)
                    if m and int(m.group(2)) in {4, 6, 8, 10, 12, 20}:
                        pre_dmg = (dice.critical_damage(dmg_note) if crit
                                   else dice.damage(dmg_note))
                        self._show_damage_button(dmg_note, pre_dmg, crit,
                                                 lambda: _resolve_spell_damage(pre_dmg))
                        return
                pre_dmg = dice.critical_damage(dmg_note) if crit else dice.damage(dmg_note)
                _resolve_spell_damage(pre_dmg)

            self._show_roll_button(f"{spell_name} {atk_bonus:+d}", pre_roll["kept"],
                                   _after_spell_roll)

        elif delivery == "save":
            result = process_spell_cast(self.session, self.char, spell_name,
                                        target_name, slot_level)
            save_ab  = (spell_data.get("save_ability") or "").upper()
            saved_s  = "saved (half damage)" if result["saved"] else "failed the save"
            dmg      = result.get("damage") or {}
            dmg_tot  = dmg.get("total", 0)

            self._display(f"  {target_name} {save_ab} save vs DC {save_dc}: "
                          f"{result['save_roll']} — {saved_s}\n", "system")
            if has_damage:
                self._display(f"  Damage: {dmg_tot} {spell_data['damage_type']} — "
                              f"{target_name} HP: {result['new_hp']}\n\n", "hit")
            else:
                self._display("\n", "system")
            if result.get("killed"):
                self._display(f"  ☠  {target_name} has fallen!\n\n", "danger")
            if not result["saved"] and spell_data.get("on_hit_effect"):
                self._display(f"  {spell_data['on_hit_effect']}\n\n", "system")

            if skip_dm_call:
                _advance_turn()
            else:
                dm_verb = "resisted" if result["saved"] else "failed to resist"
                self._dm_call(
                    f"[COMBAT RESULT — narrate this outcome dramatically in 2-3 sentences] "
                    f"{spell_name}: {target_name} {dm_verb}."
                    + (f" {dmg_tot} {spell_data['damage_type']} damage."
                       f" {target_name} HP: {result['new_hp']}." if dmg_tot else "")
                    + (" {target_name} has been defeated!" if result.get("killed") else ""),
                    on_complete=_advance_turn)

        else:  # auto
            result  = process_spell_cast(self.session, self.char, spell_name,
                                         target_name, slot_level)
            dmg     = result.get("damage") or {}
            dmg_tot = dmg.get("total", 0)
            if dmg_tot:
                if spell_name == "Magic Missile":
                    n = dmg.get("missiles", 3)
                    self._display(f"  {n} missiles — {dmg_tot} force damage — "
                                  f"{target_name} HP: {result['new_hp']}\n\n", "hit")
                else:
                    self._display(f"  {dmg_tot} {spell_data['damage_type']} damage — "
                                  f"{target_name} HP: {result['new_hp']}\n\n", "hit")
                if result.get("killed"):
                    self._display(f"  ☠  {target_name} has fallen!\n\n", "danger")
            elif spell_data.get("on_hit_effect"):
                self._display(f"  {spell_data['on_hit_effect']}\n\n", "system")

            if skip_dm_call:
                _advance_turn()
            else:
                self._dm_call(
                    f"[COMBAT RESULT — narrate this outcome dramatically in 2-3 sentences] "
                    f"{spell_name} hits {target_name}."
                    + (f" {dmg_tot} {spell_data['damage_type']} damage."
                       f" {target_name} HP: {result['new_hp']}." if dmg_tot else "")
                    + (f" Effect: {spell_data['on_hit_effect']}."
                       if not dmg_tot and spell_data.get("on_hit_effect") else "")
                    + (" {target_name} has been defeated!" if result.get("killed") else ""),
                    on_complete=_advance_turn)

    def _show_damage_roll(self, notation, pre_dmg, is_crit, on_done):
        """Animate damage dice (up to 2) sequentially, then call on_done."""
        import re
        m = re.match(r"(\d*)d(\d+)", notation.strip().lower())
        if not m or int(m.group(2)) not in {4, 6, 8, 10, 12, 20}:
            on_done()
            return
        sides      = int(m.group(2))
        rolls      = pre_dmg["rolls"]
        show_count = min(len(rolls), 2)   # cap at 2 to keep combat moving

        def show_die(idx):
            if idx >= show_count:
                on_done()
                return
            if is_crit and idx == 0:
                title = f"CRITICAL HIT! — d{sides}"
            elif len(rolls) > 1:
                title = f"Damage d{sides}  ({idx + 1}/{len(rolls)})"
            else:
                title = f"Damage d{sides}"
            DiceRollerWindow(self.root, sides=sides, value=rolls[idx],
                             on_confirm=lambda: show_die(idx + 1),
                             title_override=title)

        show_die(0)

    def _do_enemy_turn(self):
        current = gs.current_combatant(self.session)
        if not current or current["is_player"]:
            self._next_turn()
            return
        if current["hp"] <= 0:
            cb.end_turn(self.session)
            self._next_turn()
            return

        self._display(f"── {current['name']}'s turn ──\n", "header")
        result = cb.enemy_attack(self.session, current["name"])
        self._display_attack_result(result)
        self._update_sidebar()

        # Build DM narration context for enemy action
        if result.get("hit"):
            dmg     = result["damage"]["total"]
            outcome = f"Hit {result['target']} for {dmg} damage. {result['target']} HP: {result['new_hp']}."
        else:
            outcome = f"The attack against {result.get('target', 'the player')} misses."
        dm_prompt = f"[Enemy turn] {current['name']} attacks. {outcome}"

        def _after_enemy_dm():
            cb.end_turn(self.session)
            self._next_turn()

        self._dm_call(dm_prompt, on_complete=_after_enemy_dm)

    def _do_companion_turn(self):
        from models.companions import companion_ai, companion_sneak_attack_damage
        current = gs.current_combatant(self.session)
        if not current or not current.get("is_companion"):
            self._next_turn()
            return

        comp_data = next(
            (c for c in self.session.get("companions", [])
             if c["name"] == current["name"]), None)

        # Dead/missing companion data — skip
        if not comp_data:
            cb.end_turn(self.session)
            self.root.after(300, self._next_turn)
            return

        # ── Unconscious: death save ────────────────────────────────────────────
        if current["hp"] <= 0 or comp_data.get("status") == "unconscious":
            self._do_companion_death_save(current, comp_data)
            return

        self._display(f"── {current['name']}'s turn ──\n", "header")

        action = companion_ai(comp_data, self.session)
        act    = action.get("action", "none")
        target = action.get("target", "")

        def _advance():
            self._sync_companion_hp_to_data()
            cb.end_turn(self.session)
            if self._sb_active_tab == "party":
                self._refresh_party_tab()
            self.root.after(300, self._next_turn)

        if act == "none":
            cb.end_turn(self.session)
            self.root.after(300, self._next_turn)
            return

        elif act == "attack":
            atk   = comp_data["attack"]
            sneak = action.get("sneak_attack", False)
            bonus = atk["bonus"]
            dmg_note = atk["damage"]
            if sneak:
                sa = companion_sneak_attack_damage(comp_data["level"])
                dmg_note = f"{dmg_note}+{sa}"

            result = cb.resolve_attack(
                self.session, current["name"], target, bonus, dmg_note)
            self._display_attack_result(result)
            self._update_sidebar()

            if result.get("hit"):
                dmg     = result["damage"]["total"]
                outcome = (f"{current['name']} hits {target} for {dmg} damage."
                           + (f" {target} has been defeated!" if result.get("killed") else ""))
            else:
                outcome = f"{current['name']} attacks {target} and misses."

            self._dm_call(
                f"[Companion turn — ONE sentence only] {outcome}",
                on_complete=_advance)

        elif act == "spell":
            spell    = action["spell"]
            is_heal  = action.get("is_heal", False)
            slot_lvl = action.get("slot_level", 0)
            dmg_note = action.get("damage", "1d6")

            if is_heal:
                # Apply healing
                heal_roll = dice.damage(dmg_note) if dmg_note else {"total": 0}
                amount    = heal_roll["total"]
                # Find target: player or companion
                player_c  = next(
                    (c for c in self.session["initiative_order"] if c["is_player"]), None)
                t_entry   = next(
                    (c for c in self.session["initiative_order"]
                     if c["name"] == target), None)
                if target == (player_c["name"] if player_c else "") and player_c:
                    new_hp = gs.apply_healing(
                        self.session, amount,
                        self.char["hp"].get("max", 1))
                    self._display(
                        f"  {current['name']} heals {target} for {amount} HP. "
                        f"HP: {new_hp}\n\n", "hit")
                elif t_entry:
                    new_hp = gs.apply_combat_healing(self.session, target, amount)
                    self._display(
                        f"  {current['name']} heals {target} for {amount} HP. "
                        f"HP: {new_hp}\n\n", "hit")
                else:
                    self._display(
                        f"  {current['name']} casts {spell}.\n\n", "system")

                self._update_sidebar()
                self._dm_call(
                    f"[Companion turn — ONE sentence only] "
                    f"{current['name']} casts {spell} and heals {target}.",
                    on_complete=_advance)

            else:
                # Offensive spell
                has_dmg = any(c.isdigit() for c in dmg_note) and "0" not in dmg_note.replace("0", "")
                if has_dmg and dmg_note != "0":
                    dmg_roll = dice.damage(dmg_note)
                    total    = dmg_roll["total"]
                    new_hp   = gs.apply_combat_damage(self.session, target, total)
                    killed   = new_hp is not None and new_hp <= 0
                    self._display(
                        f"  {current['name']} casts {spell} on {target}. "
                        f"{total} damage. {target} HP: {new_hp}\n\n",
                        "hit")
                    if killed:
                        self._display(f"  ☠  {target} has fallen!\n\n", "danger")
                    outcome = (f"{current['name']} casts {spell}. "
                               f"{total} damage to {target}."
                               + (f" {target} is defeated!" if killed else ""))
                else:
                    self._display(
                        f"  {current['name']} casts {spell} on {target}.\n\n", "system")
                    outcome = f"{current['name']} casts {spell} targeting {target}."

                self._update_sidebar()
                self._dm_call(
                    f"[Companion turn — ONE sentence only] {outcome}",
                    on_complete=_advance)

        elif act == "feature":
            feature     = action["feature"]
            heal_amount = action.get("heal_amount", 0)
            feat_target = action.get("target", current["name"])

            if feature == "Second Wind":
                dmg_note = action.get("damage", f"1d10+{comp_data['level']}")
                heal_roll = dice.damage(dmg_note)
                heal_amount = heal_roll["total"]

            if heal_amount > 0:
                t_entry = next(
                    (c for c in self.session["initiative_order"]
                     if c["name"] == feat_target), None)
                player_c = next(
                    (c for c in self.session["initiative_order"]
                     if c["is_player"]), None)
                if feat_target == (player_c["name"] if player_c else "") and player_c:
                    new_hp = gs.apply_healing(self.session, heal_amount,
                                              self.char["hp"].get("max", 1))
                    self._display(
                        f"  {current['name']} uses {feature} on {feat_target}. "
                        f"+{heal_amount} HP. HP: {new_hp}\n\n", "hit")
                elif t_entry:
                    new_hp = gs.apply_combat_healing(self.session, feat_target, heal_amount)
                    self._display(
                        f"  {current['name']} uses {feature} on {feat_target}. "
                        f"+{heal_amount} HP. HP: {new_hp}\n\n", "hit")
                else:
                    self._display(
                        f"  {current['name']} uses {feature}.\n\n", "system")
            elif feature == "Bardic Inspiration":
                self._display(
                    f"  {current['name']} grants Bardic Inspiration to {feat_target}.\n\n",
                    "system")
            else:
                self._display(
                    f"  {current['name']} uses {feature}.\n\n", "system")

            self._update_sidebar()
            self._dm_call(
                f"[Companion turn — ONE sentence only] "
                f"{current['name']} uses {feature}.",
                on_complete=_advance)

    def _do_companion_death_save(self, entry, comp_data):
        """Roll a death save for an unconscious companion."""
        import random as _rand
        comp_data["status"] = "unconscious"
        self._display(f"── {entry['name']} — Death Saving Throw! ──\n", "danger")
        raw = _rand.randint(1, 20)
        ds  = comp_data.setdefault("death_saves", {"successes": 0, "failures": 0})

        if raw == 20:
            comp_data["status"] = "active"
            entry["hp"] = 1
            comp_data["hp"]["current"] = 1
            ds["successes"] = 0
            ds["failures"]  = 0
            self._display(f"  Natural 20! {entry['name']} revives at 1 HP!\n\n", "hit")
        elif raw >= 10:
            ds["successes"] = min(3, ds["successes"] + 1)
            if ds["successes"] >= 3:
                comp_data["status"] = "active"
                self._display(f"  {entry['name']} stabilizes.\n\n", "system")
            else:
                self._display(
                    f"  Success ({raw}). {ds['successes']}/3 successes.\n\n", "system")
        elif raw == 1:
            ds["failures"] = min(3, ds["failures"] + 2)
            self._display(f"  Natural 1! Two failures. {ds['failures']}/3.\n\n", "danger")
        else:
            ds["failures"] = min(3, ds["failures"] + 1)
            self._display(
                f"  Failure ({raw}). {ds['failures']}/3 failures.\n\n", "danger")

        if ds["failures"] >= 3:
            comp_data["status"]       = "dead"
            comp_data["dead_at_scene"] = self.session.get("location", "Unknown")
            self._display(f"  ☠  {entry['name']} has died.\n\n", "danger")
            def _after_death():
                cb.end_turn(self.session)
                self.root.after(300, self._next_turn)
            self._dm_call(
                f"[Companion death] {entry['name']} has just died from their wounds. "
                f"Narrate their death in ONE dramatic sentence.",
                on_complete=_after_death)
            if self._sb_active_tab == "party":
                self._refresh_party_tab()
            return

        if self._sb_active_tab == "party":
            self._refresh_party_tab()
        cb.end_turn(self.session)
        self.root.after(300, self._next_turn)

    def _sync_companion_hp_to_data(self):
        """Sync initiative-order HP back to companion data (for party tab display)."""
        for entry in self.session.get("initiative_order", []):
            if not entry.get("is_companion"):
                continue
            for comp in self.session.get("companions", []):
                if comp["name"] == entry["name"]:
                    comp["hp"]["current"] = entry["hp"]
                    if entry["hp"] <= 0 and comp.get("status") == "active":
                        comp["status"] = "unconscious"
                    break

    def _display_attack_result(self, result):
        if "error" in result:
            self._display(f"  Error: {result['error']}\n\n", "danger")
            return
        attacker = result["attacker"]
        target   = result["target"]
        roll     = result["roll"]
        if result["hit"]:
            dmg  = result["damage"]["total"]
            tag  = "hit"
            crit = " CRITICAL HIT!" if result.get("critical") else ""
            self._display(
                f"  {attacker} attacks {target} — "
                f"roll {roll['kept']} (total {roll['total']}) vs AC {result['target_ac']}."
                f" HIT!{crit} {dmg} damage."
                f" {target} HP: {result['new_hp']}\n\n", tag)
            if result.get("killed"):
                self._display(f"  ☠  {target} has fallen!\n\n", "danger")
        else:
            self._display(
                f"  {attacker} attacks {target} — "
                f"roll {roll['kept']} (total {roll['total']}) vs AC {result['target_ac']}."
                f" Miss.\n\n", "miss")

    def _end_combat(self, victory=True):
        self._sync_companion_hp_to_data()
        xp = cb.xp_from_combat(self.session)
        gs.end_combat(self.session)
        self.state = "EXPLORING"
        self._update_sidebar()
        self._build_explore_input()
        if victory:
            self._display(f"── Victory! ──\n\n", "header")
            if xp:
                self._award_xp(xp, after=lambda: self._dm_call(
                    "The combat is over. We won. Describe the aftermath."))
            else:
                self._set_input_enabled(False)
                self._dm_call("The combat is over. We won. Describe the aftermath.")
        else:
            self._display("── Defeated ──\n\n", "danger")
            self._set_input_enabled(False)
            self._dm_call("The player has been defeated. Narrate the ending.")

    def _handle_death_saves(self):
        self._display("── You are dying — Death Saving Throw! ──\n", "danger")
        import random as _rand
        raw = _rand.randint(1, 20)
        pre_roll = {
            "roll":        raw,
            "success":     raw >= 10,
            "critical":    raw == 20,
            "double_fail": raw == 1,
        }

        def _after_save():
            result = cb.handle_death_save(self.session, pre_roll=pre_roll)
            if result["outcome"] == "revived":
                self._display("  NATURAL 20! You stabilize at 1 HP!\n\n", "hit")
                self.session["current_hp"] = 1
                self._update_sidebar()
                cb.end_turn(self.session)
                self.root.after(800, self._next_turn)
            elif result["outcome"] == "stable":
                self._display("  3 successes — you stabilize.\n\n", "system")
                self._update_sidebar()
                cb.end_turn(self.session)
                self.root.after(800, self._next_turn)
            elif result["outcome"] == "dead":
                self._display("  3 failures — you have died.\n\n", "danger")
                self.state = "DEAD"
                self._set_input_enabled(False)
                self._dm_call("The player character has died. Narrate their death.")
            else:
                ds     = result["death_saves"]
                double = " (counts as 2 failures!)" if result["double_fail"] else ""
                self._display(
                    f"  {double.strip() or 'Ongoing.'} "
                    f"Successes: {ds['successes']}  Failures: {ds['failures']}\n\n",
                    "system" if result["success"] else "danger")
                self._update_sidebar()
                cb.end_turn(self.session)
                self.root.after(800, self._next_turn)

        DiceRollerWindow(self.root, sides=20, value=raw, on_confirm=_after_save,
                         title_override="DEATH SAVING THROW")

    # ── Skill checks ───────────────────────────────────────────────────────────

    def _handle_skill_check(self, skill, dc):
        ability    = SKILL_ABILITIES.get(skill, "")
        ab         = self.char.get("abilities", {})
        ab_mod     = modifier(ab.get(ability, 10)) if ability else 0
        prof_b     = proficiency_bonus(self.char.get("level", 1))
        proficient = skill in self.char.get("skill_proficiencies", [])
        total_mod  = ab_mod + (prof_b if proficient else 0)

        pre_roll  = dice.d20_check(modifier=total_mod)
        prof_note = f", proficiency +{prof_b}" if proficient else ""

        self._display(f"── Skill Check: {skill} DC {dc} ──\n"
                      f"  Modifier: {total_mod:+d}{prof_note}\n\n", "header")

        def _after_roll():
            result  = pre_roll["total"]
            success = pre_roll["nat20"] or (not pre_roll["nat1"] and result >= dc)
            self._display(
                f"  Rolled {pre_roll['kept']} + {total_mod:+d} = {result} "
                f"vs DC {dc} — {'SUCCESS' if success else 'FAILURE'}\n\n",
                "hit" if success else "danger")
            if pre_roll["nat20"]:
                result_tag = "CRITICAL SUCCESS"
                instruction = "The player rolled a natural 20 — a spectacular success. Reward them with something extra: exceptional information, a bonus, or a lucky break beyond what they expected."
            elif pre_roll["nat1"]:
                result_tag = "CRITICAL FAILURE"
                instruction = "The player rolled a natural 1 — a catastrophic failure. Punish them: something goes wrong beyond just failing, an unexpected complication, embarrassment, or consequence."
            elif success:
                result_tag = "SUCCESS"
                instruction = "Narrate a clean success."
            else:
                result_tag = "FAILURE"
                instruction = "Narrate a clean failure."
            outcome = (f"[{skill} check: {result_tag}] "
                       f"{instruction} Do not mention the roll value, the DC, or any game stats.")
            self._set_input_enabled(False)
            self._dm_call(outcome)

        self._show_roll_button(f"d20 ({skill} DC {dc})", pre_roll["kept"], _after_roll)

    # ── Display helpers ────────────────────────────────────────────────────────

    def _display(self, text, tag="dm"):
        self._narration.config(state="normal")
        self._narration.insert("end", text, tag)
        self._narration.see("end")
        self._narration.config(state="disabled")

    def _erase_last_line(self):
        self._narration.config(state="normal")
        self._narration.delete("end-2l", "end-1c")
        self._narration.config(state="disabled")

    def _update_sidebar(self):
        if not self.char or not self.session:
            return
        ab      = self.char.get("abilities", {})
        lvl     = self.char.get("level", 1)
        pb      = proficiency_bonus(lvl)
        cur_hp  = self.session.get("current_hp", 0) or 0
        max_hp  = self.char["hp"].get("max", 1)
        ac      = self.char.get("armor_class", 10)
        speed   = self.char.get("speed", 30)
        dex_mod = modifier(ab.get("dexterity", 10))
        conds   = self.session.get("conditions", [])

        # Character info
        name    = self.char.get("name", "—")
        race    = self.char.get("race", "—")
        cls     = self.char.get("class", "—")
        sub     = self.char.get("subclass", "")
        bg_name = self.char.get("background", "—")
        sub_str = f" ({sub})" if sub else ""
        self._char_info_label.config(
            text=f"{name}\n{race}  {cls}{sub_str}\nLevel {lvl}  •  {bg_name}")

        # Vitals
        self._hp_label.config(text=f"HP: {cur_hp} / {max_hp}")
        ratio  = cur_hp / max(1, max_hp)
        colour = GREEN if ratio > 0.5 else (YELLOW if ratio > 0.25 else RED)
        self._hp_bar_canvas.delete("all")
        bw = self._hp_bar_canvas.winfo_width() or 260
        self._hp_bar_canvas.create_rectangle(0, 0, bw, 8, fill=BTN_BG, outline="")
        self._hp_bar_canvas.create_rectangle(0, 0, int(bw * ratio), 8,
                                             fill=colour, outline="")
        self._ac_label.config(text=f"AC {ac}")
        self._spd_label.config(text=f"Spd {speed}")
        self._init_label.config(text=f"Init {dex_mod:+d}")
        self._cond_label.config(
            text="Conditions: " + (", ".join(conds) if conds else "—"))

        # Inspiration
        insp = self.char.get("inspiration", False)
        self._insp_btn.config(
            bg=ACCENT if insp else BTN_BG,
            fg="#1a1a2e" if insp else DIM)

        # XP bar
        from models.progression import xp_for_level, XP_THRESHOLDS
        xp      = self.char.get("experience", 0)
        xp_cur  = xp_for_level(lvl)
        xp_next = XP_THRESHOLDS[lvl] if lvl < 20 else XP_THRESHOLDS[19]
        if lvl >= 20:
            self._xp_label.config(text=f"XP: {xp}  (Max Level)")
            ratio_xp = 1.0
        else:
            self._xp_label.config(
                text=f"XP: {xp} / {xp_next}  (Lv {lvl}→{lvl+1})")
            ratio_xp = max(0.0, min(1.0, (xp - xp_cur) / max(1, xp_next - xp_cur)))
        self._xp_bar_canvas.delete("all")
        bw2 = self._xp_bar_canvas.winfo_width() or 260
        self._xp_bar_canvas.create_rectangle(0, 0, bw2, 6, fill=BTN_BG, outline="")
        self._xp_bar_canvas.create_rectangle(
            0, 0, int(bw2 * ratio_xp), 6, fill=ACCENT, outline="")

        # Abilities
        for key, lbl in self._ab_labels.items():
            score = ab.get(key, 10)
            lbl.config(text=f"{score}\n({modifier(score):+d})")

        # Saving throws
        for w in self._save_frame.winfo_children():
            w.destroy()
        save_profs = set(self.char.get("saving_throw_proficiencies", []))
        sg = tk.Frame(self._save_frame, bg=PANEL)
        sg.pack(anchor="w")
        for i, (abbr, key) in enumerate(ABILITY_KEYS):
            prof  = key in save_profs
            mod_v = modifier(ab.get(key, 10)) + (pb if prof else 0)
            col   = 0 if i < 3 else 1
            row_i = i % 3
            f = tk.Frame(sg, bg=PANEL)
            f.grid(row=row_i, column=col, sticky="w", padx=(0,10), pady=1)
            tk.Label(f, text="●" if prof else "○", font=FONT_SM,
                     bg=PANEL, fg=ACCENT if prof else DIM).pack(side="left")
            tk.Label(f, text=f" {abbr} {mod_v:+d}", font=FONT_SM,
                     bg=PANEL, fg=FG if prof else DIM).pack(side="left")

        # Proficient skills
        for w in self._skills_frame.winfo_children():
            w.destroy()
        skill_profs = self.char.get("skill_proficiencies", [])
        if skill_profs:
            sk_grid = tk.Frame(self._skills_frame, bg=PANEL)
            sk_grid.pack(anchor="w")
            for i, sk in enumerate(skill_profs):
                ab_key = SKILL_ABILITY.get(sk, "")
                mod_v  = modifier(ab.get(ab_key, 10)) + pb
                col    = 0 if i % 2 == 0 else 1
                row_i  = i // 2
                f = tk.Frame(sk_grid, bg=PANEL)
                f.grid(row=row_i, column=col, sticky="w", padx=(0,6), pady=1)
                tk.Label(f, text=f"● {sk[:13]} {mod_v:+d}",
                         font=("Segoe UI", 8), bg=PANEL, fg=FG).pack(side="left")
        else:
            tk.Label(self._skills_frame, text="—",
                     font=FONT_SM, bg=PANEL, fg=DIM).pack(anchor="w")

        # Attacks (state-aware)
        # Spellcasting stats (DC / ATK / slot pips)
        self._refresh_spells()

        # Actions (weapons + spells + standard)
        self._refresh_actions()

        # Bonus actions
        self._refresh_bonus_actions()

        # Feature charges (non-BA)
        self._refresh_features()

        # Combat order
        for w in self._combat_frame.winfo_children():
            w.destroy()
        if self.session.get("in_combat"):
            current = gs.current_combatant(self.session)
            for c in self.session["initiative_order"]:
                active = current and c["name"] == current["name"]
                fg     = ACCENT if active else (DIM if c["hp"] <= 0 else FG)
                marker = "▶ " if active else "  "
                ratio2 = c["hp"] / max(1, c["max_hp"])
                bar_c  = GREEN if ratio2 > 0.5 else (YELLOW if ratio2 > 0.25 else RED)
                row = tk.Frame(self._combat_frame, bg=PANEL)
                row.pack(fill="x", pady=1)
                tk.Label(row, text=f"{marker}{c['name']}", font=FONT_SM,
                         bg=PANEL, fg=fg, width=16, anchor="w").pack(side="left")
                tk.Label(row, text=f"{c['hp']}/{c['max_hp']}", font=FONT_SM,
                         bg=PANEL, fg=bar_c).pack(side="right")
        else:
            tk.Label(self._combat_frame, text="Not in combat",
                     font=FONT_SM, bg=PANEL, fg=DIM).pack(anchor="w")

    def _is_player_turn(self):
        if not self.session or not self.session.get("in_combat"):
            return False
        current = gs.current_combatant(self.session)
        return bool(current and current.get("is_player", False))

    # ── Sidebar tab switcher ──────────────────────────────────────────────────

    def _switch_sidebar_tab(self, tab):
        self._sb_active_tab = tab
        if tab == "character":
            self._party_panel.pack_forget()
            self._char_panel.pack(fill="both", expand=True)
            self._sb_tab_char.config(bg=ACCENT, fg="#1a1a2e")
            self._sb_tab_party.config(bg=BTN_BG, fg=DIM)
        else:
            self._char_panel.pack_forget()
            self._party_panel.pack(fill="both", expand=True)
            self._sb_tab_char.config(bg=BTN_BG, fg=DIM)
            self._sb_tab_party.config(bg=ACCENT, fg="#1a1a2e")
            self._refresh_party_tab()

    # ── Party tab ─────────────────────────────────────────────────────────────

    def _refresh_party_tab(self):
        """Rebuild all companion cards in the party panel."""
        for w in self._party_inner.winfo_children():
            w.destroy()
        if not self.session:
            return
        companions = self.session.get("companions", [])
        if not companions:
            tk.Label(self._party_inner, text="No companions yet.",
                     font=FONT_SM, bg=PANEL, fg=DIM).pack(pady=20, padx=10)
            return
        for comp in companions:
            self._build_companion_card(self._party_inner, comp)

    def _build_companion_card(self, parent, comp):
        """Build one companion card widget."""
        status = comp.get("status", "active")
        dead   = status == "dead"
        uncon  = status == "unconscious"

        card_bg = BTN_BG if dead else PANEL
        fg_main = DIM   if dead else FG
        fg_dim  = DIM

        card = tk.Frame(parent, bg=card_bg, padx=8, pady=8,
                        highlightbackground=ACCENT if not dead else DIM,
                        highlightthickness=1)
        card.pack(fill="x", padx=6, pady=(6, 0))

        # ── Header row (name, class, level) ──────────────────────────────────
        hdr = tk.Frame(card, bg=card_bg)
        hdr.pack(fill="x")
        name_text = comp["name"]
        if dead:
            name_text += "  ✝"
        tk.Label(hdr, text=name_text, font=("Segoe UI", 10, "bold"),
                 bg=card_bg, fg=fg_main, anchor="w").pack(side="left")
        status_text = " [UNCONSCIOUS]" if uncon else (" [FALLEN]" if dead else "")
        if status_text:
            tk.Label(hdr, text=status_text, font=FONT_SM,
                     bg=card_bg, fg=RED).pack(side="left", padx=(4, 0))
        tk.Label(card,
                 text=f"{comp['race']}  {comp['class']} ({comp['subclass']})  •  Level {comp['level']}",
                 font=FONT_SM, bg=card_bg, fg=fg_dim, anchor="w").pack(fill="x")

        if dead:
            return  # dead cards show minimal info, no more content

        # ── HP bar ────────────────────────────────────────────────────────────
        hp_cur, hp_max = self._companion_hp(comp)
        tk.Label(card, text=f"HP: {hp_cur} / {hp_max}",
                 font=FONT_SM, bg=card_bg, fg=fg_main).pack(anchor="w", pady=(4, 0))
        hp_bar = tk.Canvas(card, bg=card_bg, height=7, highlightthickness=0)
        hp_bar.pack(fill="x", pady=(1, 2))
        def _draw_hp_bar(canvas=hp_bar, cur=hp_cur, mx=hp_max):
            canvas.delete("all")
            w = canvas.winfo_width() or 260
            canvas.create_rectangle(0, 0, w, 7, fill=BTN_BG, outline="")
            ratio  = cur / max(1, mx)
            colour = GREEN if ratio > 0.5 else (YELLOW if ratio > 0.25 else RED)
            canvas.create_rectangle(0, 0, int(w * ratio), 7, fill=colour, outline="")
        hp_bar.bind("<Configure>", lambda e: _draw_hp_bar())
        self.root.after(50, _draw_hp_bar)

        # ── AC ────────────────────────────────────────────────────────────────
        tk.Label(card, text=f"AC {comp['ac']}", font=FONT_SM,
                 bg=card_bg, fg=fg_dim).pack(anchor="w")

        # ── Death saves (only when unconscious) ───────────────────────────────
        if uncon:
            ds = comp.get("death_saves", {"successes": 0, "failures": 0})
            ds_frame = tk.Frame(card, bg=card_bg)
            ds_frame.pack(anchor="w", pady=(2, 0))
            tk.Label(ds_frame, text="Death Saves:", font=FONT_SM,
                     bg=card_bg, fg=RED).pack(side="left")
            succ = "●" * ds["successes"] + "○" * (3 - ds["successes"])
            fail = "●" * ds["failures"]  + "○" * (3 - ds["failures"])
            tk.Label(ds_frame, text=f"  ✓{succ}", font=FONT_SM,
                     bg=card_bg, fg=GREEN).pack(side="left")
            tk.Label(ds_frame, text=f"  ✗{fail}", font=FONT_SM,
                     bg=card_bg, fg=RED).pack(side="left")

        # ── Feature charges ───────────────────────────────────────────────────
        feat_uses = comp.get("feature_uses", {})
        if feat_uses:
            tk.Frame(card, bg=BTN_BG, height=1).pack(fill="x", pady=(4, 2))
            for fname, data in feat_uses.items():
                cur = data.get("current", 0)
                mx  = data.get("max", 1)
                pips = ("●" * cur + "○" * (mx - cur)) if mx <= 10 else f"{cur}/{mx}"
                row  = tk.Frame(card, bg=card_bg)
                row.pack(fill="x")
                tk.Label(row, text=f"{fname}", font=FONT_SM,
                         bg=card_bg, fg=fg_main if cur > 0 else fg_dim,
                         anchor="w").pack(side="left")
                tk.Label(row, text=f"  {pips}", font=FONT_SM,
                         bg=card_bg, fg=ACCENT if cur > 0 else fg_dim).pack(side="left")

        # ── Spell slots (casters only) ────────────────────────────────────────
        slots = comp.get("spell_slots", {})
        if slots:
            tk.Frame(card, bg=BTN_BG, height=1).pack(fill="x", pady=(4, 2))
            slot_row = tk.Frame(card, bg=card_bg)
            slot_row.pack(fill="x")
            tk.Label(slot_row, text="Slots:", font=FONT_SM,
                     bg=card_bg, fg=fg_dim).pack(side="left")
            for lvl_str in sorted(slots.keys(), key=int):
                data  = slots[lvl_str]
                total = data.get("total", 0)
                used  = data.get("used", 0)
                avail = total - used
                pips  = "●" * avail + "○" * used
                tk.Label(slot_row, text=f"  L{lvl_str}:{pips}", font=FONT_SM,
                         bg=card_bg, fg=ACCENT if avail > 0 else fg_dim).pack(side="left")

        # ── Personality ───────────────────────────────────────────────────────
        tk.Frame(card, bg=BTN_BG, height=1).pack(fill="x", pady=(4, 2))
        for trait in comp.get("personality_traits", []):
            tk.Label(card, text=f'"{trait}"', font=FONT_SM,
                     bg=card_bg, fg=fg_dim, wraplength=270, justify="left",
                     anchor="w").pack(fill="x")
        if comp.get("ideal"):
            tk.Label(card, text=f"Ideal: {comp['ideal']}", font=FONT_SM,
                     bg=card_bg, fg=fg_dim, wraplength=270, justify="left",
                     anchor="w").pack(fill="x", pady=(2, 0))
        if comp.get("bond"):
            tk.Label(card, text=f"Bond: {comp['bond']}", font=FONT_SM,
                     bg=card_bg, fg=fg_dim, wraplength=270, justify="left",
                     anchor="w").pack(fill="x", pady=(2, 0))
        if comp.get("flaw"):
            tk.Label(card, text=f"Flaw: {comp['flaw']}", font=FONT_SM,
                     bg=card_bg, fg=fg_dim, wraplength=270, justify="left",
                     anchor="w").pack(fill="x", pady=(2, 0))
        tk.Label(card, text=comp.get("alignment", ""), font=FONT_SM,
                 bg=card_bg, fg=fg_dim).pack(anchor="w", pady=(2, 0))

    def _companion_hp(self, comp):
        """Return (current, max) HP — uses initiative order during combat."""
        if self.session and self.session.get("in_combat"):
            for entry in self.session.get("initiative_order", []):
                if entry.get("is_companion") and entry["name"] == comp["name"]:
                    return entry["hp"], entry["max_hp"]
        return comp["hp"]["current"], comp["hp"]["max"]

    # ── Companion join ────────────────────────────────────────────────────────

    def _handle_companion_join(self, name):
        from models.companions import find_companion_template, build_companion_at_level
        template = find_companion_template(name)
        if not template:
            self._display(f"  [System: unknown companion '{name}']\n\n", "danger")
            return
        companions = self.session.setdefault("companions", [])
        if any(c["name"].lower() == name.lower() for c in companions):
            return  # already in party
        level = self.char.get("level", 1)
        comp  = build_companion_at_level(template, level)
        companions.append(comp)
        self._display(f"\n  {comp['name']} joins the party.\n\n", "system")
        if self._sb_active_tab == "party":
            self._refresh_party_tab()

    def _companion_long_rest(self):
        """Restore companion HP and all resources on a long rest."""
        for comp in self.session.get("companions", []):
            if comp.get("status") == "dead":
                continue
            comp["hp"]["current"] = comp["hp"]["max"]
            if comp.get("status") == "unconscious":
                comp["status"] = "active"
                comp["death_saves"] = {"successes": 0, "failures": 0}
            # Restore all spell slots
            for data in comp.get("spell_slots", {}).values():
                data["used"] = 0
            # Restore long-rest features
            for feat_data in comp.get("feature_uses", {}).values():
                if feat_data.get("recharge") in ("long", "short", "turn"):
                    feat_data["current"] = feat_data["max"]

    def _companion_short_rest(self):
        """Restore companion short-rest features on a short rest (rough avg heal)."""
        import math, random
        from models.companions import _HIT_DICE, _mod
        for comp in self.session.get("companions", []):
            if comp.get("status") == "dead":
                continue
            # Restore short-rest features (Channel Divinity, Second Wind, Ki, etc.)
            for feat_data in comp.get("feature_uses", {}).values():
                if feat_data.get("recharge") == "short":
                    feat_data["current"] = feat_data["max"]
            # Heal ~avg hit die roll
            hd      = _HIT_DICE.get(comp["class"], 8)
            con_mod = _mod(comp["abilities"].get("constitution", 10))
            gained  = max(1, hd // 2 + 1 + con_mod)
            comp["hp"]["current"] = min(comp["hp"]["max"],
                                        comp["hp"]["current"] + gained)

    def _on_scene_change(self, location):
        """Update location display and remove dead companion cards on next scene."""
        self._loc_var.set(location)
        companions = self.session.get("companions", [])
        # Remove companions who died before this scene change
        self.session["companions"] = [
            c for c in companions
            if not (c.get("status") == "dead" and c.get("dead_at_scene") is not None)
        ]
        if self._sb_active_tab == "party":
            self._refresh_party_tab()

    # ── helpers shared by action-panel and sidebar refresh ───────────────────

    def _action_blocked_state(self):
        """Return (action_blocked: bool, reason: str) based on character conditions."""
        if not self.session:
            return False, ""
        INCAP = {"Stunned", "Paralyzed", "Incapacitated", "Unconscious"}
        player_comb = next(
            (c for c in self.session.get("initiative_order", []) if c.get("is_player")), None)
        p_conds = set(player_comb.get("conditions", []) if player_comb
                      else self.session.get("conditions", []))
        blocked = bool(INCAP & p_conds)
        reason  = f"Condition: {', '.join(INCAP & p_conds)}" if blocked else ""
        return blocked, reason

    # ── Sidebar refresh methods ───────────────────────────────────────────────

    def _refresh_spells(self):
        """Compact spellcasting stats: DC, ATK, slot pips. Shows — for non-casters."""
        for w in self._spells_frame.winfo_children():
            w.destroy()
        _dash = lambda: tk.Label(self._spells_frame, text="—",
                                 font=FONT_SM, bg=PANEL, fg=DIM).pack(anchor="w", padx=4)
        if not self.char:
            _dash(); return
        sc = self.char.get("spellcasting", {})
        if not sc.get("enabled"):
            _dash(); return
        dc  = sc.get("spell_save_dc", "?")
        atk = sc.get("attack_bonus", 0)
        tk.Label(self._spells_frame, text=f"Save DC {dc}  •  Atk {atk:+d}",
                 font=FONT_SM, bg=PANEL, fg=DIM).pack(anchor="w", padx=4, pady=(0,2))
        slots   = sc.get("slots", {})
        active  = sorted((int(l), v) for l, v in slots.items() if v.get("total", 0) > 0)
        if active:
            row_f = tk.Frame(self._spells_frame, bg=PANEL)
            row_f.pack(anchor="w", padx=4, fill="x")
            for lvl, data in active:
                total = data.get("total", 0)
                used  = data.get("used", 0)
                cur   = total - used
                pips  = "●" * cur + "○" * used
                col   = FG if cur > 0 else DIM
                tk.Label(row_f, text=f"L{lvl}{pips} ",
                         font=("Segoe UI", 8), bg=PANEL, fg=col).pack(side="left")

    def _refresh_actions(self):
        """Weapons, action-cast spells, standard actions — greyed when unavailable."""
        for w in self._attacks_frame.winfo_children():
            w.destroy()
        if not self.char:
            return

        blocked, blocked_reason = self._action_blocked_state()

        def _sub(text):
            tk.Label(self._attacks_frame, text=text,
                     font=("Segoe UI", 8, "bold"), bg=PANEL, fg=DIM).pack(
                         anchor="w", padx=4, pady=(4,0))

        def _row(text, avail, reason=""):
            fg_col = FG if avail else DIM
            lbl = tk.Label(self._attacks_frame, text=text, font=FONT_SM,
                           bg=PANEL, fg=fg_col, anchor="w", justify="left",
                           wraplength=270, padx=4)
            lbl.pack(fill="x")
            if not avail and reason:
                _Tooltip(lbl, lambda r=reason: r)

        # ── Weapons ──────────────────────────────────────────────────────────
        attacks     = self.char.get("attacks", [])
        main_atks   = [a for a in attacks
                       if not a.get("_offhand")]
        attack_opts = self._get_attack_options()
        main_opts   = [o for o in attack_opts if o.get("mode") != "offhand"]
        if main_opts:
            _sub("── Weapons")
            for opt in main_opts:
                text = (f"⚔ {opt['label']}  {opt['bonus']:+d}"
                        f"  {opt['damage']} {opt.get('dmg_type','')}")
                _row(text, avail=not blocked,
                     reason=blocked_reason or "")
        elif not attacks:
            _sub("── Weapons")
            _row("No weapons equipped",
                 avail=False, reason="Add a weapon in the character builder")

        # ── Spells (action-cast) ──────────────────────────────────────────────
        sc = self.char.get("spellcasting", {})
        if sc.get("enabled"):
            from models.spells import SPELLS as _SP
            sc_slots = sc.get("slots", {})
            prepared = list(dict.fromkeys(
                sc.get("spells_prepared", []) + sc.get("spells_known", [])))
            SAVE_AB = {"dex":"DEX","con":"CON","wis":"WIS",
                       "str":"STR","int":"INT","cha":"CHA"}
            ICON = {"attack":"⚔","save":"⊕","auto":"★"}

            # Build list: (level, name, delivery_str, available, reason)
            spell_rows = []
            for item in prepared:
                name = item["name"] if isinstance(item, dict) else item
                lvl  = item.get("level", _SP[name]["level"] if name in _SP else 99) \
                       if isinstance(item, dict) else (_SP[name]["level"] if name in _SP else 99)
                sp   = _SP.get(name)
                if sp:
                    icon = ICON.get(sp["delivery"], "·")
                    sab  = SAVE_AB.get(sp.get("save_ability") or "", "")
                    dtype = f"{icon} {sab}" if sab else icon
                else:
                    dtype = "·"
                if lvl == 0:
                    slots_str = "cantrip"
                    avail = not blocked
                    reason = blocked_reason
                else:
                    avail_slots = sum(
                        max(0, v.get("total",0) - v.get("used",0))
                        for k, v in sc_slots.items() if int(k) >= lvl)
                    avail = avail_slots > 0 and not blocked
                    if blocked:
                        reason = blocked_reason
                    elif avail_slots == 0:
                        reason = f"No L{lvl}+ spell slots remaining"
                    else:
                        reason = ""
                    slots_str = f"L{lvl}"
                spell_rows.append((lvl, name, slots_str, dtype, avail, reason))

            spell_rows.sort(key=lambda x: (x[0], x[1]))
            if spell_rows:
                _sub("── Spells")
                for (_, name, slots_str, dtype, avail, reason) in spell_rows:
                    _row(f"✦ {name}  {slots_str}  {dtype}",
                         avail=avail, reason=reason)

        # ── Standard actions ──────────────────────────────────────────────────
        _sub("── Standard")
        for std in ("Dash", "Dodge", "Disengage", "Hide"):
            _row(f"◈ {std}", avail=not blocked, reason=blocked_reason)

    def _refresh_bonus_actions(self):
        """Off-hand attacks and bonus-action features, greyed when unavailable."""
        for w in self._bonus_frame.winfo_children():
            w.destroy()
        if not self.char:
            tk.Label(self._bonus_frame, text="—",
                     font=FONT_SM, bg=PANEL, fg=DIM).pack(anchor="w", padx=4)
            return

        blocked, blocked_reason = self._action_blocked_state()
        any_shown = False

        def _row(text, avail, reason=""):
            nonlocal any_shown
            any_shown = True
            fg_col = FG if avail else DIM
            lbl = tk.Label(self._bonus_frame, text=text, font=FONT_SM,
                           bg=PANEL, fg=fg_col, anchor="w", padx=4)
            lbl.pack(fill="x")
            if not avail and reason:
                _Tooltip(lbl, lambda r=reason: r)

        # Off-hand attacks
        attack_opts = self._get_attack_options()
        for opt in (o for o in attack_opts if o.get("mode") == "offhand"):
            text = (f"⚔ {opt['label']} (off-hand)  {opt['bonus']:+d}"
                    f"  {opt['damage']} {opt.get('dmg_type','')}")
            _row(text, avail=not blocked, reason=blocked_reason)

        # Bonus-action class features
        uses = self.char.get("feature_uses", {})
        for fname, data in uses.items():
            if fname not in self._BONUS_ACTION_FEATURES:
                continue
            cur   = data.get("current", 0)
            mx    = data.get("max", 1)
            avail = cur > 0 and not blocked
            pips  = "●" * cur + "○" * (mx - cur) if mx <= 10 else f"{cur}/{mx}"
            if blocked:
                reason = blocked_reason
            elif cur == 0:
                reason = f"No charges remaining — use a rest to recover"
            else:
                reason = ""
            tip = f"{self._COMBAT_FEATURES.get(fname, fname)}"
            lbl = tk.Label(self._bonus_frame,
                           text=f"★ {fname}  {pips}",
                           font=FONT_SM, bg=PANEL,
                           fg=FG if avail else DIM,
                           anchor="w", padx=4)
            lbl.pack(fill="x")
            any_shown = True
            _Tooltip(lbl, lambda t=tip, r=reason, a=avail:
                     (r if not a else t))
            if avail:
                use_btn = tk.Button(
                    self._bonus_frame, text="Use", font=("Segoe UI", 8),
                    bg=BTN_BG, fg=FG, relief="flat", bd=0, padx=6, pady=2,
                    activebackground=ACCENT, activeforeground="#1a1a2e",
                    command=lambda n=fname: self._use_feature(n))
                use_btn.pack(anchor="e", padx=4)

        if not any_shown:
            tk.Label(self._bonus_frame, text="—",
                     font=FONT_SM, bg=PANEL, fg=DIM).pack(anchor="w", padx=4)

    def _set_input_enabled(self, enabled):
        state = "normal" if enabled else "disabled"
        for w in self._input_frame.winfo_children():
            try:
                w.config(state=state)
            except tk.TclError:
                pass
        if enabled:
            try:
                self._input_entry.focus_set()
            except AttributeError:
                pass

    def _show_roll_button(self, label, d20_value, on_confirm):
        self._narration.config(state="normal")
        btn = tk.Button(
            self._narration, text=f"  Roll {label}  ",
            font=FONT_BODY, bg=ACCENT, fg="#1a1a2e",
            relief="flat", bd=0, padx=4, pady=6,
            activebackground="#e0c060", activeforeground="#1a1a2e",
        )
        def _clicked():
            btn.config(state="disabled")
            D20RollerWindow(self.root, d20_value, on_confirm)
        btn.config(command=_clicked)
        self._narration.window_create("end", window=btn)
        self._narration.insert("end", "\n\n")
        self._narration.see("end")
        self._narration.config(state="disabled")

    def _show_damage_button(self, notation, pre_dmg, is_crit, on_done):
        """Embed a Roll Damage button in the narration; clicking opens the die animation."""
        import re
        m     = re.match(r"(\d*)d(\d+)", notation.strip().lower())
        sides = int(m.group(2)) if m else None
        if sides not in {4, 6, 8, 10, 12, 20}:
            on_done()
            return
        crit_tag = " — CRIT!" if is_crit else ""
        self._narration.config(state="normal")
        btn = tk.Button(
            self._narration,
            text=f"  Roll Damage (d{sides}){crit_tag}  ",
            font=FONT_BODY, bg=ACCENT, fg="#1a1a2e",
            relief="flat", bd=0, padx=4, pady=6,
            activebackground="#e0c060", activeforeground="#1a1a2e",
        )
        def _clicked():
            btn.config(state="disabled")
            self._show_damage_roll(notation, pre_dmg, is_crit, on_done)
        btn.config(command=_clicked)
        self._narration.window_create("end", window=btn)
        self._narration.insert("end", "\n\n")
        self._narration.see("end")
        self._narration.config(state="disabled")

    # ── Inspiration & features ────────────────────────────────────────────────

    def _toggle_inspiration(self):
        if not self.char:
            return
        self.char["inspiration"] = not self.char.get("inspiration", False)
        insp = self.char["inspiration"]
        self._insp_btn.config(
            bg=ACCENT if insp else BTN_BG,
            fg="#1a1a2e" if insp else DIM)

    def _refresh_features(self):
        """Non-bonus-action feature charges (Arcane Recovery, etc.)."""
        for w in self._features_frame.winfo_children():
            w.destroy()
        if not self.char:
            return
        uses = {k: v for k, v in self.char.get("feature_uses", {}).items()
                if k not in self._BONUS_ACTION_FEATURES}
        if not uses:
            tk.Label(self._features_frame, text="—",
                     font=FONT_SM, bg=PANEL, fg=DIM).pack(anchor="w", padx=4)
            return

        for name, data in uses.items():
            current = data.get("current", 0)
            max_u   = data.get("max", 1)

            row = tk.Frame(self._features_frame, bg=PANEL)
            row.pack(fill="x", pady=2)

            if max_u <= 10:
                pips   = "●" * current + "○" * (max_u - current)
                pip_fg = ACCENT if current > 0 else DIM
                pip_lbl = tk.Label(row, text=pips, font=("Segoe UI", 9),
                                   bg=PANEL, fg=pip_fg)
                pip_lbl.pack(side="left", padx=(4, 4))
            else:
                pip_lbl = tk.Label(row, text=f"{current}/{max_u}",
                                   font=FONT_SM, bg=PANEL,
                                   fg=ACCENT if current > 0 else DIM)
                pip_lbl.pack(side="left", padx=(4, 4))

            tk.Label(row, text=name, font=FONT_SM, bg=PANEL,
                     fg=FG if current > 0 else DIM,
                     wraplength=150, anchor="w").pack(side="left", fill="x", expand=True)

            if current > 0:
                use_btn = tk.Button(
                    row, text="Use", font=("Segoe UI", 8),
                    bg=BTN_BG, fg=FG, relief="flat", bd=0,
                    padx=6, pady=2,
                    activebackground=ACCENT, activeforeground="#1a1a2e",
                    command=lambda n=name: self._use_feature(n))
                use_btn.pack(side="right", padx=4)

    def _use_feature(self, name):
        if not self.char:
            return
        uses = self.char.get("feature_uses", {})
        if name not in uses or uses[name]["current"] <= 0:
            return
        uses[name]["current"] -= 1
        self._display(f"  Used {name}. ({uses[name]['current']}/{uses[name]['max']} remaining)\n\n",
                      "system")
        self._refresh_features()
        self._refresh_bonus_actions()

    # ── Rest dialogs ──────────────────────────────────────────────────────────

    def _show_short_rest_dialog(self):
        if not self.char:
            return
        import random
        hit_dice  = self.char.get("hit_dice", {})
        total     = hit_dice.get("total", 1)
        used      = hit_dice.get("used", 0)
        available = max(0, total - used)
        die_type  = hit_dice.get("type", "d8")
        die_max   = int(die_type.replace("d", ""))
        con_mod   = modifier(self.char.get("abilities", {}).get("constitution", 10))
        max_hp    = self.char["hp"]["max"]
        cur_hp    = self.char["hp"]["current"]
        hp_missing = max_hp - cur_hp

        d = tk.Toplevel(self.root)
        d.title("Short Rest")
        d.configure(bg=BG)
        d.grab_set()
        d.resizable(False, False)
        self.root.update_idletasks()
        rx = self.root.winfo_x() + self.root.winfo_width()  // 2 - 175
        ry = self.root.winfo_y() + self.root.winfo_height() // 2 - 140
        d.geometry(f"350x280+{rx}+{ry}")

        tk.Frame(d, bg=BLUE, height=4).pack(fill="x")
        tk.Label(d, text="  Short Rest", font=FONT_HDR,
                 bg=PANEL, fg=FG, pady=8).pack(fill="x")

        body = tk.Frame(d, bg=BG, padx=16, pady=12)
        body.pack(fill="both", expand=True)

        tk.Label(body,
                 text=f"HP: {cur_hp}/{max_hp}   Hit dice: {available}/{total} {die_type} available",
                 font=FONT_SM, bg=BG, fg=DIM).pack(anchor="w")
        tk.Label(body, text="", bg=BG).pack()

        if available == 0:
            tk.Label(body, text="No hit dice remaining.", font=FONT_SM,
                     bg=BG, fg=DIM).pack(anchor="w")
            tk.Button(body, text="Close", font=FONT_SM, bg=BTN_BG, fg=FG,
                      relief="flat", bd=0, padx=12, pady=6,
                      command=d.destroy).pack(anchor="e", pady=8)
            return

        row = tk.Frame(body, bg=BG)
        row.pack(anchor="w")
        tk.Label(row, text="Spend ", font=FONT_SM, bg=BG, fg=FG).pack(side="left")
        dice_var = tk.IntVar(value=1)
        tk.Spinbox(row, from_=1, to=available, textvariable=dice_var,
                   width=3, font=FONT_SM, bg=INPUT_BG, fg=FG,
                   buttonbackground=BTN_BG, relief="flat",
                   insertbackground=FG).pack(side="left", padx=4)
        tk.Label(row, text=f"{die_type} hit dice", font=FONT_SM,
                 bg=BG, fg=FG).pack(side="left")

        avg_per_die = max(1, die_max // 2 + 1 + con_mod)
        est_lbl = tk.Label(body, font=FONT_SM, bg=BG, fg=DIM)
        est_lbl.pack(anchor="w", pady=(4, 0))
        result_lbl = tk.Label(body, text="", font=("Segoe UI", 13, "bold"),
                              bg=BG, fg=ACCENT)
        result_lbl.pack(pady=(4, 0))

        btn_row = tk.Frame(body, bg=BG)
        btn_row.pack(fill="x", pady=(8, 0))

        def _update_est(*_):
            try:
                n = max(1, min(int(dice_var.get()), available))
            except Exception:
                n = 1
            est = min(hp_missing, n * avg_per_die)
            est_lbl.config(text=f"Expected recovery: ~{est} HP")

        dice_var.trace_add("write", _update_est)
        _update_est()

        def _apply(rolls):
            from controllers.game_controller import process_short_rest
            from models.character import save_character as _save_char
            try:
                n = max(1, min(int(dice_var.get()), available))
            except Exception:
                n = 1
            result = process_short_rest(self.session, self.char, n, rolls[:n])
            lines = [f"  Short rest: spent {n} {die_type}, recovered {result['hp_recovered']} HP."]
            if result["features_recharged"]:
                lines.append(f"  Recharged: {', '.join(result['features_recharged'])}.")
            self._display("\n".join(lines) + "\n\n", "system")
            self._companion_short_rest()
            self._update_sidebar()
            if self._sb_active_tab == "party":
                self._refresh_party_tab()
            _save_char(self.char)
            d.destroy()

        def _roll():
            try:
                n = max(1, min(int(dice_var.get()), available))
            except Exception:
                n = 1
            pre_rolls = [random.randint(1, die_max) for _ in range(n)]

            def show_die(idx):
                if idx >= n:
                    total_hp = sum(max(1, r + con_mod) for r in pre_rolls)
                    result_lbl.config(text=f"Rolled {pre_rolls}  →  +{total_hp} HP")
                    for w in btn_row.winfo_children():
                        w.destroy()
                    tk.Button(btn_row, text=f"Accept +{total_hp} HP",
                              font=FONT_SM, bg=ACCENT, fg="#1a1a2e",
                              relief="flat", bd=0, padx=12, pady=6,
                              activebackground="#e0c060", activeforeground="#1a1a2e",
                              command=lambda: _apply(pre_rolls)).pack(side="right")
                    return
                title = (f"Hit Die {die_type}" if n == 1
                         else f"Hit Die {die_type}  ({idx + 1}/{n})")
                DiceRollerWindow(d, sides=die_max, value=pre_rolls[idx],
                                 on_confirm=lambda: show_die(idx + 1),
                                 title_override=title)

            show_die(0)

        def _avg():
            try:
                n = max(1, min(int(dice_var.get()), available))
            except Exception:
                n = 1
            _apply([die_max // 2 + 1] * n)

        tk.Button(btn_row, text="Roll Dice", font=FONT_SM,
                  bg=BTN_BG, fg=FG, relief="flat", bd=0, padx=10, pady=6,
                  activebackground=ACCENT, activeforeground="#1a1a2e",
                  command=_roll).pack(side="left", padx=(0, 6))
        tk.Button(btn_row, text="Take Average", font=FONT_SM,
                  bg=BTN_BG, fg=DIM, relief="flat", bd=0, padx=10, pady=6,
                  command=_avg).pack(side="left")
        tk.Button(btn_row, text="Cancel", font=FONT_SM,
                  bg=BTN_BG, fg=DIM, relief="flat", bd=0, padx=10, pady=6,
                  command=d.destroy).pack(side="right")

    def _do_long_rest(self):
        if not self.char:
            return
        if not tk.messagebox.askyesno(
                "Long Rest",
                "Take a long rest?\n\n"
                "• Full HP restored\n"
                "• Half your hit dice recovered\n"
                "• All spell slots restored\n"
                "• All long-rest features recharged\n"
                "• Conditions cleared",
                parent=self.root):
            return
        from controllers.game_controller import process_long_rest
        result = process_long_rest(self.session, self.char)
        from models.character import save_character
        save_character(self.char)
        lines = [f"  Long rest complete. Recovered {result['hp_recovered']} HP."]
        slots = {k: v for k, v in result.get("slots_recovered", {}).items() if v}
        if slots:
            lines.append(f"  Spell slots restored: {', '.join(f'L{k}×{v}' for k,v in slots.items())}.")
        if result.get("features_recharged"):
            lines.append(f"  Features recharged: {', '.join(result['features_recharged'])}.")
        # Restore companion resources on long rest
        self._companion_long_rest()
        self._display("\n".join(lines) + "\n\n", "system")
        self._update_sidebar()
        if self._sb_active_tab == "party":
            self._refresh_party_tab()

    # ── XP & level-up ─────────────────────────────────────────────────────────

    def _award_xp(self, amount, after=None):
        result = process_xp_award(self.session, self.char, amount)
        self._display(
            f"  +{amount} XP  (Total: {result['total_xp']})\n\n", "system")
        if result["leveled_up"]:
            # Level companions alongside the player
            from models.companions import level_up_companion
            new_level = result["new_level"]
            for comp in self.session.get("companions", []):
                if comp.get("status") != "dead" and comp["level"] < new_level:
                    level_up_companion(comp, new_level)
                    self._display(
                        f"  {comp['name']} advances to level {new_level}.\n\n", "system")
            if self._sb_active_tab == "party":
                self._refresh_party_tab()
            self._show_levelup_dialog(result, on_close=after or self._resume_after_levelup)
        else:
            xp_next = result["xp_to_next"]
            self._display(
                f"  {xp_next} XP to level {result['new_level'] + 1}\n\n", "system")
            if after:
                after()
            else:
                self._set_input_enabled(True)

    def _resume_after_levelup(self):
        self._set_input_enabled(True)

    def _show_levelup_dialog(self, result, on_close=None):
        from models.character import save_character
        import sys as _sys
        from pathlib import Path as _Path
        _cb = _Path(__file__).parent / "character_builder"
        if str(_cb) not in _sys.path:
            _sys.path.insert(0, str(_cb))
        from dnd_data import SUBCLASSES, CLASS_HIT_DICE

        cls     = self.char.get("class", "")
        new_lvl = result["new_level"]
        features = result["new_features"]
        con_mod  = modifier(self.char.get("abilities", {}).get("constitution", 10))
        hit_die  = self.char.get("hit_dice", {}).get("type", "d8")
        die_max  = int(hit_die.replace("d", ""))
        avg_hp   = max(1, die_max // 2 + 1 + con_mod)

        needs_subclass = (
            get_subclass_trigger(cls) == new_lvl
            and not self.char.get("subclass", "").strip()
        )
        needs_asi    = is_asi_level(cls, new_lvl)
        has_spells   = self.char.get("spellcasting", {}).get("enabled", False)

        steps = ["features", "hp"]
        if needs_subclass:
            steps.append("subclass")
        if needs_asi:
            steps.append("asi")
        if has_spells:
            steps.append("spells")

        d = tk.Toplevel(self.root)
        d.title(f"Level Up — Level {new_lvl}")
        d.configure(bg=BG)
        d.grab_set()
        d.resizable(False, False)
        self.root.update_idletasks()
        rx = self.root.winfo_x() + self.root.winfo_width()  // 2 - 210
        ry = self.root.winfo_y() + self.root.winfo_height() // 2 - 220
        d.geometry(f"420x440+{rx}+{ry}")

        tk.Frame(d, bg=ACCENT, height=4).pack(fill="x")
        hdr_lbl = tk.Label(d, text=f"  ⬆  LEVEL UP — Level {new_lvl}",
                           font=FONT_HDR, bg=PANEL, fg=ACCENT, pady=8)
        hdr_lbl.pack(fill="x")

        body      = tk.Frame(d, bg=BG, padx=20, pady=12)
        body.pack(fill="both", expand=True)
        btn_frame = tk.Frame(d, bg=BG, padx=20, pady=8)
        btn_frame.pack(fill="x")

        step_idx = [0]

        def _clear():
            for w in body.winfo_children():
                w.destroy()
            for w in btn_frame.winfo_children():
                w.destroy()

        def _next_btn(label="Next →", cmd=None):
            tk.Button(btn_frame, text=label, font=FONT_SM,
                      bg=ACCENT, fg="#1a1a2e", relief="flat", bd=0,
                      padx=14, pady=6,
                      activebackground="#e0c060", activeforeground="#1a1a2e",
                      command=cmd).pack(side="right")

        def _advance():
            step_idx[0] += 1
            if step_idx[0] >= len(steps):
                _finish()
            else:
                _show_step()

        def _finish():
            save_character(self.char)
            self._update_sidebar()
            self._char_var.set(
                f"{self.char.get('name','')}  —  "
                f"{self.char.get('race','')} {self.char.get('class','')} "
                f"Lv.{self.char.get('level',1)}")
            d.destroy()
            self._display(f"── Character saved at Level {new_lvl} ──\n\n", "system")
            if on_close:
                on_close()

        # ── Step: features ─────────────────────────────────────────────────────
        def _step_features():
            tk.Label(body, text=f"You have reached Level {new_lvl}!",
                     font=FONT_HDR, bg=BG, fg=ACCENT).pack(anchor="w", pady=(0, 6))
            if features:
                tk.Label(body, text="New class features:",
                         font=FONT_SM, bg=BG, fg=DIM).pack(anchor="w", pady=(0, 4))
                for feat in features:
                    tk.Label(body, text=f"  •  {feat}", font=FONT_BODY,
                             bg=BG, fg=FG, wraplength=360,
                             justify="left").pack(anchor="w")
            else:
                tk.Label(body, text="No new class features at this level.",
                         font=FONT_SM, bg=BG, fg=DIM).pack(anchor="w")
            upcoming = []
            if needs_subclass:
                upcoming.append("Choose your subclass")
            if needs_asi:
                upcoming.append("Ability Score Improvement")
            if upcoming:
                tk.Label(body, text="", bg=BG).pack()
                for u in upcoming:
                    tk.Label(body, text=f"  ★  {u}",
                             font=FONT_SM, bg=BG, fg=ACCENT).pack(anchor="w")
            _next_btn(cmd=_advance)

        # ── Step: hp roll ──────────────────────────────────────────────────────
        def _step_hp():
            tk.Label(body, text="Roll for HP",
                     font=FONT_HDR, bg=BG, fg=ACCENT).pack(anchor="w", pady=(0, 6))
            tk.Label(body,
                     text=f"Hit die: {hit_die}   CON modifier: {con_mod:+d}   Average: {avg_hp}",
                     font=FONT_SM, bg=BG, fg=DIM).pack(anchor="w", pady=(0, 10))

            result_var = tk.StringVar(value="")
            rolled     = [False]

            res_lbl = tk.Label(body, text="", font=("Segoe UI", 22, "bold"),
                               bg=BG, fg=ACCENT)
            res_lbl.pack(pady=8)

            def _apply(hp_gain):
                self.char["hp"]["max"]     += hp_gain
                self.char["hp"]["current"] += hp_gain
                if self.session:
                    self.session["current_hp"] = (
                        (self.session.get("current_hp") or 0) + hp_gain)
                rolled[0] = True
                res_lbl.config(text=f"+{hp_gain} HP")
                for w in btn_frame.winfo_children():
                    w.destroy()
                _next_btn(cmd=_advance)

            def _roll():
                import random as _rand
                raw  = _rand.randint(1, die_max)
                gain = max(1, raw + con_mod)

                def _after_levelup_roll():
                    res_lbl.config(text=f"Rolled {raw} + {con_mod:+d} = {gain} HP")
                    for w in btn_frame.winfo_children():
                        w.destroy()
                    tk.Button(btn_frame, text=f"Accept +{gain} HP",
                              font=FONT_SM, bg=ACCENT, fg="#1a1a2e",
                              relief="flat", bd=0, padx=14, pady=6,
                              activebackground="#e0c060", activeforeground="#1a1a2e",
                              command=lambda: _apply(gain)).pack(side="right")

                DiceRollerWindow(d, sides=die_max, value=raw,
                                 on_confirm=_after_levelup_roll,
                                 title_override=f"Level Up — Roll {hit_die}")

            def _take_avg():
                _apply(avg_hp)

            row = tk.Frame(body, bg=BG)
            row.pack()
            tk.Button(row, text=f"Roll {hit_die}", font=FONT_BODY,
                      bg=BTN_BG, fg=FG, relief="flat", bd=0, padx=12, pady=8,
                      activebackground=ACCENT, activeforeground="#1a1a2e",
                      command=_roll).pack(side="left", padx=(0, 8))
            tk.Button(row, text=f"Take Average ({avg_hp})", font=FONT_SM,
                      bg=BTN_BG, fg=DIM, relief="flat", bd=0, padx=12, pady=8,
                      activebackground=BTN_BG, activeforeground=FG,
                      command=_take_avg).pack(side="left")

        # ── Step: subclass ─────────────────────────────────────────────────────
        def _step_subclass():
            tk.Label(body, text="Choose Your Subclass",
                     font=FONT_HDR, bg=BG, fg=ACCENT).pack(anchor="w", pady=(0, 6))
            tk.Label(body, text=f"Select a {cls} subclass:",
                     font=FONT_SM, bg=BG, fg=DIM).pack(anchor="w", pady=(0, 4))

            options = SUBCLASSES.get(cls, [])
            lf = tk.Frame(body, bg=INPUT_BG)
            lf.pack(fill="both", expand=True)
            sb2 = tk.Scrollbar(lf, bg=BG, troughcolor=INPUT_BG)
            sb2.pack(side="right", fill="y")
            lb = tk.Listbox(lf, bg=INPUT_BG, fg=FG, font=FONT_BODY,
                            selectbackground=ACCENT, selectforeground="#1a1a2e",
                            relief="flat", bd=0, activestyle="none",
                            exportselection=False,
                            yscrollcommand=sb2.set, height=6)
            sb2.config(command=lb.yview)
            lb.pack(fill="both", expand=True, padx=4, pady=4)
            for opt in options:
                lb.insert("end", opt)
            if options:
                lb.select_set(0)

            err = tk.Label(body, text="", font=FONT_SM, bg=BG, fg=RED)
            err.pack(anchor="w")

            def _confirm_subclass():
                sel = lb.curselection()
                if not sel:
                    err.config(text="Please choose a subclass.")
                    return
                self.char["subclass"] = lb.get(sel[0])
                _advance()

            _next_btn("Confirm →", _confirm_subclass)

        # ── Step: ASI ──────────────────────────────────────────────────────────
        def _step_asi():
            tk.Label(body, text="Ability Score Improvement",
                     font=FONT_HDR, bg=BG, fg=ACCENT).pack(anchor="w", pady=(0, 6))

            ability_names = [
                "Strength", "Dexterity", "Constitution",
                "Intelligence", "Wisdom", "Charisma",
            ]
            ability_keys = [
                "strength", "dexterity", "constitution",
                "intelligence", "wisdom", "charisma",
            ]

            mode_var = tk.StringVar(value="plus2")

            mode_frame = tk.Frame(body, bg=BG)
            mode_frame.pack(anchor="w", pady=(0, 10))
            tk.Radiobutton(mode_frame, text="+2 to one ability",
                           variable=mode_var, value="plus2",
                           bg=BG, fg=FG, selectcolor=BTN_BG,
                           activebackground=BG, font=FONT_SM,
                           command=lambda: _refresh_asi()).pack(side="left", padx=(0, 16))
            tk.Radiobutton(mode_frame, text="+1 to two abilities",
                           variable=mode_var, value="plus1each",
                           bg=BG, fg=FG, selectcolor=BTN_BG,
                           activebackground=BG, font=FONT_SM,
                           command=lambda: _refresh_asi()).pack(side="left")

            pick_frame = tk.Frame(body, bg=BG)
            pick_frame.pack(anchor="w", pady=(0, 6))

            err = tk.Label(body, text="", font=FONT_SM, bg=BG, fg=RED)
            err.pack(anchor="w")

            var1 = tk.StringVar(value=ability_names[0])
            var2 = tk.StringVar(value=ability_names[1])

            def _refresh_asi():
                for w in pick_frame.winfo_children():
                    w.destroy()
                if mode_var.get() == "plus2":
                    tk.Label(pick_frame, text="+2  ", font=FONT_BODY,
                             bg=BG, fg=ACCENT).pack(side="left")
                    tk.OptionMenu(pick_frame, var1, *ability_names).pack(side="left")
                    pick_frame.winfo_children()[-1].config(
                        bg=BTN_BG, fg=FG, relief="flat",
                        activebackground=ACCENT, activeforeground="#1a1a2e",
                        font=FONT_SM, highlightthickness=0)
                else:
                    tk.Label(pick_frame, text="+1  ", font=FONT_BODY,
                             bg=BG, fg=ACCENT).pack(side="left")
                    tk.OptionMenu(pick_frame, var1, *ability_names).pack(side="left")
                    pick_frame.winfo_children()[-1].config(
                        bg=BTN_BG, fg=FG, relief="flat",
                        activebackground=ACCENT, activeforeground="#1a1a2e",
                        font=FONT_SM, highlightthickness=0)
                    tk.Label(pick_frame, text="   +1  ", font=FONT_BODY,
                             bg=BG, fg=ACCENT).pack(side="left")
                    tk.OptionMenu(pick_frame, var2, *ability_names).pack(side="left")
                    pick_frame.winfo_children()[-1].config(
                        bg=BTN_BG, fg=FG, relief="flat",
                        activebackground=ACCENT, activeforeground="#1a1a2e",
                        font=FONT_SM, highlightthickness=0)

            _refresh_asi()

            def _confirm_asi():
                err.config(text="")
                ab = self.char.get("abilities", {})
                if mode_var.get() == "plus2":
                    key = ability_keys[ability_names.index(var1.get())]
                    if ab.get(key, 10) >= 20:
                        err.config(text=f"{var1.get()} is already at maximum (20).")
                        return
                    ab[key] = min(20, ab.get(key, 10) + 2)
                else:
                    k1 = ability_keys[ability_names.index(var1.get())]
                    k2 = ability_keys[ability_names.index(var2.get())]
                    if k1 == k2:
                        err.config(text="Choose two different abilities.")
                        return
                    if ab.get(k1, 10) >= 20 and ab.get(k2, 10) >= 20:
                        err.config(text="Both abilities are already at maximum (20).")
                        return
                    ab[k1] = min(20, ab.get(k1, 10) + 1)
                    ab[k2] = min(20, ab.get(k2, 10) + 1)
                _advance()

            _next_btn("Confirm →", _confirm_asi)

        # ── Step: spells ───────────────────────────────────────────────────────
        def _step_spells():
            tk.Label(body, text="Spellcasting",
                     font=FONT_HDR, bg=BG, fg=ACCENT).pack(anchor="w", pady=(0, 6))
            sc = self.char.get("spellcasting", {})
            slots = sc.get("slots", {})
            new_slots = [
                f"Level {lvl}: {data['total']} slots"
                for lvl, data in slots.items()
                if data["total"] > 0
            ]
            if new_slots:
                tk.Label(body, text="Current spell slots:",
                         font=FONT_SM, bg=BG, fg=DIM).pack(anchor="w", pady=(0, 4))
                for line in new_slots:
                    tk.Label(body, text=f"  {line}", font=FONT_SM,
                             bg=BG, fg=FG).pack(anchor="w")
            tk.Label(body, text="",  bg=BG).pack()
            tk.Label(body,
                     text="To add new spells or cantrips, use the\nCharacter Builder (Main Menu → New Adventure → Create Character).",
                     font=FONT_SM, bg=BG, fg=DIM, justify="left").pack(anchor="w")
            _next_btn("Done", _advance)

        def _show_step():
            _clear()
            step = steps[step_idx[0]]
            if step == "features":
                _step_features()
            elif step == "hp":
                _step_hp()
            elif step == "subclass":
                _step_subclass()
            elif step == "asi":
                _step_asi()
            elif step == "spells":
                _step_spells()

        _show_step()

    # ── DEV panel (Ctrl+D) ────────────────────────────────────────────────────

    def _open_dev_panel(self, event=None):
        try:
            self._open_dev_panel_inner()
        except Exception as _e:
            import traceback
            tk.messagebox.showerror("DEV panel error", traceback.format_exc(), parent=self.root)
        return "break"

    def _open_dev_panel_inner(self):
        if not self.char or not self.session:
            tk.messagebox.showinfo("DEV", "Start an adventure first.", parent=self.root)
            return
        if self._dev_panel and self._dev_panel.winfo_exists():
            self._dev_panel.lift()
            return

        d = tk.Toplevel(self.root)
        d.title("DEV")
        d.configure(bg=BG)
        d.resizable(False, False)
        self.root.update_idletasks()
        pw, ph = 270, 660
        sw = self.root.winfo_screenwidth()
        sh = self.root.winfo_screenheight()
        rx = min(self.root.winfo_x() + self.root.winfo_width() + 6, sw - pw - 10)
        ry = max(10, min(self.root.winfo_y(), sh - ph - 40))
        d.geometry(f"{pw}x{ph}+{rx}+{ry}")
        self._dev_panel = d

        def _sec(label):
            tk.Label(d, text=label, font=("Segoe UI", 8, "bold"),
                     bg=PANEL, fg=ACCENT, padx=8, pady=4).pack(
                         fill="x", pady=(6, 0))
            tk.Frame(d, bg=BTN_BG, height=1).pack(fill="x")

        # ── Award XP ──────────────────────────────────────────────────────────
        _sec("AWARD XP")
        xp_frame = tk.Frame(d, bg=BG, padx=8, pady=6)
        xp_frame.pack(fill="x")
        xp_var = tk.StringVar(value="100")
        xp_entry = tk.Entry(xp_frame, textvariable=xp_var, width=8,
                            bg=INPUT_BG, fg=FG, font=FONT_SM,
                            relief="flat", insertbackground=FG)
        xp_entry.pack(side="left", padx=(0, 6))

        def _award():
            try:
                amt = int(xp_var.get())
            except ValueError:
                return
            self._award_xp(amt)

        tk.Button(xp_frame, text="Award XP", font=FONT_SM,
                  bg=BTN_BG, fg=FG, relief="flat", bd=0, padx=10, pady=4,
                  activebackground=ACCENT, activeforeground="#1a1a2e",
                  command=_award).pack(side="left")

        # ── Jump to Level ──────────────────────────────────────────────────────
        _sec("JUMP TO LEVEL")
        lv_outer = tk.Frame(d, bg=BG, padx=8, pady=6)
        lv_outer.pack(fill="x")

        def _jump(target):
            from models.progression import XP_THRESHOLDS
            if target < 2 or target > 20:
                return
            prev_xp   = XP_THRESHOLDS[target - 2]
            target_xp = XP_THRESHOLDS[target - 1]
            self.char["experience"] = prev_xp
            self.char["level"]      = target - 1
            self._award_xp(target_xp - prev_xp)

        row1 = tk.Frame(lv_outer, bg=BG)
        row1.pack(anchor="w")
        row2 = tk.Frame(lv_outer, bg=BG)
        row2.pack(anchor="w", pady=(4, 0))

        for lvl in range(2, 7):
            tk.Button(row1, text=f"Lv{lvl}", font=("Segoe UI", 8),
                      bg=BTN_BG, fg=FG, relief="flat", bd=0,
                      padx=6, pady=4, width=4,
                      activebackground=ACCENT, activeforeground="#1a1a2e",
                      command=lambda l=lvl: _jump(l)).pack(side="left", padx=(0, 3))

        for lvl in range(7, 12):
            tk.Button(row2, text=f"Lv{lvl}", font=("Segoe UI", 8),
                      bg=BTN_BG, fg=FG, relief="flat", bd=0,
                      padx=6, pady=4, width=4,
                      activebackground=ACCENT, activeforeground="#1a1a2e",
                      command=lambda l=lvl: _jump(l)).pack(side="left", padx=(0, 3))

        # ── Set HP ────────────────────────────────────────────────────────────
        _sec("SET HP")
        hp_frame = tk.Frame(d, bg=BG, padx=8, pady=6)
        hp_frame.pack(fill="x")
        hp_var = tk.IntVar(value=self.char["hp"]["current"])
        hp_spin = tk.Spinbox(hp_frame,
                             from_=0, to=self.char["hp"]["max"],
                             textvariable=hp_var, width=5,
                             font=FONT_SM, bg=INPUT_BG, fg=FG,
                             buttonbackground=BTN_BG, relief="flat",
                             insertbackground=FG)
        hp_spin.pack(side="left", padx=(0, 6))

        def _set_hp():
            try:
                val = max(0, min(int(hp_var.get()), self.char["hp"]["max"]))
            except ValueError:
                return
            self.char["hp"]["current"] = val
            if self.session and self.session.get("current_hp") is not None:
                self.session["current_hp"] = val
            self._update_sidebar()
            self._display(f"  [DEV] HP set to {val}/{self.char['hp']['max']}\n\n", "system")

        tk.Button(hp_frame, text="Set HP", font=FONT_SM,
                  bg=BTN_BG, fg=FG, relief="flat", bd=0, padx=10, pady=4,
                  activebackground=ACCENT, activeforeground="#1a1a2e",
                  command=_set_hp).pack(side="left")

        # ── Rest ──────────────────────────────────────────────────────────────
        _sec("REST (INSTANT)")
        rest_frame = tk.Frame(d, bg=BG, padx=8, pady=6)
        rest_frame.pack(fill="x")

        def _dev_short_rest():
            from controllers.game_controller import process_short_rest
            from models.character import save_character as _save_char
            hit_dice  = self.char.get("hit_dice", {})
            available = max(0, hit_dice.get("total", 1) - hit_dice.get("used", 0))
            if available == 0:
                self._display("  [DEV] No hit dice remaining.\n\n", "system")
                return
            die_max = int(hit_dice.get("type", "d8").replace("d", ""))
            rolls   = [die_max // 2 + 1]
            result  = process_short_rest(self.session, self.char, 1, rolls)
            self._display(
                f"  [DEV] Short rest (avg). +{result['hp_recovered']} HP."
                + (f"  Recharged: {', '.join(result['features_recharged'])}." if result["features_recharged"] else "")
                + "\n\n", "system")
            self._update_sidebar()
            _save_char(self.char)

        def _dev_long_rest():
            from controllers.game_controller import process_long_rest
            from models.character import save_character
            result = process_long_rest(self.session, self.char)
            save_character(self.char)
            self._display(
                f"  [DEV] Long rest. +{result['hp_recovered']} HP. "
                + (f"Recharged: {', '.join(result['features_recharged'])}." if result["features_recharged"] else "")
                + "\n\n", "system")
            self._update_sidebar()

        tk.Button(rest_frame, text="Short Rest", font=FONT_SM,
                  bg=BTN_BG, fg=FG, relief="flat", bd=0, padx=10, pady=4,
                  activebackground=BLUE, activeforeground=FG,
                  command=_dev_short_rest).pack(side="left", padx=(0, 6))
        tk.Button(rest_frame, text="Long Rest", font=FONT_SM,
                  bg=BTN_BG, fg=FG, relief="flat", bd=0, padx=10, pady=4,
                  activebackground=BLUE, activeforeground=FG,
                  command=_dev_long_rest).pack(side="left")

        # ── Conditions ────────────────────────────────────────────────────────
        _sec("CONDITIONS")
        cond_frame = tk.Frame(d, bg=BG, padx=8, pady=6)
        cond_frame.pack(fill="x")

        CONDITIONS = [
            "Blinded", "Charmed", "Deafened", "Exhaustion",
            "Frightened", "Grappled", "Incapacitated", "Invisible",
            "Paralyzed", "Petrified", "Poisoned", "Prone",
            "Restrained", "Stunned", "Unconscious",
        ]
        cond_var = tk.StringVar(value=CONDITIONS[0])
        cond_menu = tk.OptionMenu(cond_frame, cond_var, *CONDITIONS)
        cond_menu.config(bg=BTN_BG, fg=FG, font=FONT_SM, relief="flat",
                         activebackground=ACCENT, activeforeground="#1a1a2e",
                         highlightthickness=0)
        cond_menu["menu"].config(bg=BTN_BG, fg=FG, font=FONT_SM)
        cond_menu.pack(side="left", padx=(0, 6))

        def _add_cond():
            c = cond_var.get()
            if c not in self.char.get("conditions", []):
                self.char.setdefault("conditions", []).append(c)
                if self.session and self.session.get("in_combat"):
                    player_name = self.char.get("name") or "Player"
                    gs.add_condition(self.session, player_name, c)
                self._update_sidebar()
                self._display(f"  [DEV] Condition added: {c}\n\n", "system")

        def _clear_conds():
            self.char["conditions"] = []
            if self.session:
                self.session["conditions"] = []
            self._update_sidebar()
            self._display("  [DEV] All conditions cleared.\n\n", "system")

        tk.Button(cond_frame, text="Add", font=FONT_SM,
                  bg=BTN_BG, fg=FG, relief="flat", bd=0, padx=8, pady=4,
                  activebackground=ACCENT, activeforeground="#1a1a2e",
                  command=_add_cond).pack(side="left", padx=(0, 4))
        tk.Button(cond_frame, text="Clear All", font=FONT_SM,
                  bg=BTN_BG, fg=DIM, relief="flat", bd=0, padx=8, pady=4,
                  command=_clear_conds).pack(side="left")

        # ── Test Combat ───────────────────────────────────────────────────────
        _sec("COMBAT")
        cb_frame = tk.Frame(d, bg=BG, padx=8, pady=6)
        cb_frame.pack(fill="x")

        QUICK_ENEMIES = ["Goblin", "Bandit", "Skeleton", "Orc", "Ogre"]
        enemy_var = tk.StringVar(value="Goblin")
        enemy_menu = tk.OptionMenu(cb_frame, enemy_var, *QUICK_ENEMIES)
        enemy_menu.config(bg=BTN_BG, fg=FG, font=FONT_SM, relief="flat",
                          activebackground=ACCENT, activeforeground="#1a1a2e",
                          highlightthickness=0)
        enemy_menu["menu"].config(bg=BTN_BG, fg=FG, font=FONT_SM)
        enemy_menu.pack(fill="x", pady=(0, 4))

        def _test_combat():
            if self.state == "COMBAT":
                self._display("  [DEV] Already in combat.\n\n", "system")
                return
            self._start_combat([{"name": enemy_var.get(), "count": 1}])

        tk.Button(cb_frame, text="Start Test Combat", font=FONT_SM,
                  bg=BTN_BG, fg=FG, relief="flat", bd=0, padx=10, pady=6,
                  activebackground=RED, activeforeground=FG,
                  command=_test_combat).pack(fill="x")

        # ── Story Mode ────────────────────────────────────────────────────────
        _sec("STORY MODE")
        story_frame = tk.Frame(d, bg=BG, padx=8, pady=6)
        story_frame.pack(fill="x")

        _s_text = "Exit Story Mode" if self._story_mode else "Enter Story Mode"
        _s_bg   = ACCENT if self._story_mode else BTN_BG
        _s_fg   = "#1a1a2e" if self._story_mode else FG
        story_btn = tk.Button(story_frame, text=_s_text, font=FONT_SM,
                              bg=_s_bg, fg=_s_fg, relief="flat", bd=0,
                              padx=10, pady=6,
                              activebackground=ACCENT, activeforeground="#1a1a2e")
        story_btn.pack(fill="x")

        def _toggle_story():
            if self._story_mode:
                self._exit_story_mode()
                story_btn.config(text="Enter Story Mode", bg=BTN_BG, fg=FG)
            else:
                if self.state in ("COMBAT", "DEAD"):
                    self._display("  [DEV] Cannot enter Story Mode in current state.\n\n",
                                  "system")
                    return
                def _on_confirmed(location):
                    story_btn.config(text="Exit Story Mode", bg=ACCENT, fg="#1a1a2e")
                    self._enter_story_mode(location)
                self._ask_starting_location(_on_confirmed)

        story_btn.config(command=_toggle_story)

    def _save_and_quit(self):
        if self.session:
            gs.save_session(self.session)
        self.root.destroy()


def main():
    root = tk.Tk()
    app  = GameApp(root)
    root.protocol("WM_DELETE_WINDOW", app._save_and_quit)
    root.mainloop()


if __name__ == "__main__":
    main()
