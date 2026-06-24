import sys
import threading
import tkinter as tk
from tkinter import messagebox, ttk
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "Character Builder"))

from character import load_character, list_characters, modifier, proficiency_bonus
import game_state as gs
import combat as cb
import dm as dm_module
import dice

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

# ── Enemy stat blocks ──────────────────────────────────────────────────────────
ENEMY_STATS = {
    "Bandit":          {"hp": 11, "ac": 12, "xp": 25,  "initiative_mod": 1,
                        "attacks": [{"name": "Scimitar",   "bonus": 3, "damage": "1d6+1", "damage_type": "slashing"}]},
    "Cultist":         {"hp":  9, "ac": 12, "xp": 25,  "initiative_mod": 1,
                        "attacks": [{"name": "Dagger",     "bonus": 3, "damage": "1d4+1", "damage_type": "piercing"}]},
    "Goblin":          {"hp":  7, "ac": 15, "xp": 50,  "initiative_mod": 2,
                        "attacks": [{"name": "Scimitar",   "bonus": 4, "damage": "1d6+2", "damage_type": "slashing"}]},
    "Kobold":          {"hp":  5, "ac": 12, "xp": 25,  "initiative_mod": 2,
                        "attacks": [{"name": "Dagger",     "bonus": 4, "damage": "1d4+2", "damage_type": "piercing"}]},
    "Skeleton":        {"hp": 13, "ac": 13, "xp": 50,  "initiative_mod": 2,
                        "attacks": [{"name": "Shortsword", "bonus": 4, "damage": "1d6+2", "damage_type": "piercing"}]},
    "Zombie":          {"hp": 22, "ac":  8, "xp": 50,  "initiative_mod":-2,
                        "attacks": [{"name": "Slam",       "bonus": 3, "damage": "1d6+1", "damage_type": "bludgeoning"}]},
    "Wolf":            {"hp": 11, "ac": 13, "xp": 50,  "initiative_mod": 2,
                        "attacks": [{"name": "Bite",       "bonus": 4, "damage": "2d4+2", "damage_type": "piercing"}]},
    "Guard":           {"hp": 11, "ac": 16, "xp": 25,  "initiative_mod": 1,
                        "attacks": [{"name": "Spear",      "bonus": 3, "damage": "1d6+1", "damage_type": "piercing"}]},
    "Gnoll":           {"hp": 22, "ac": 15, "xp": 100, "initiative_mod": 1,
                        "attacks": [{"name": "Spear",      "bonus": 4, "damage": "1d6+2", "damage_type": "piercing"}]},
    "Hobgoblin":       {"hp": 11, "ac": 18, "xp": 100, "initiative_mod": 1,
                        "attacks": [{"name": "Longsword",  "bonus": 3, "damage": "1d8+1", "damage_type": "slashing"}]},
    "Lizardfolk":      {"hp": 22, "ac": 15, "xp": 100, "initiative_mod": 1,
                        "attacks": [{"name": "Bite",       "bonus": 4, "damage": "1d6+2", "damage_type": "piercing"}]},
    "Orc":             {"hp": 15, "ac": 13, "xp": 100, "initiative_mod": 1,
                        "attacks": [{"name": "Greataxe",   "bonus": 5, "damage": "1d12+3","damage_type": "slashing"}]},
    "Thug":            {"hp": 32, "ac": 11, "xp": 100, "initiative_mod": 0,
                        "attacks": [{"name": "Mace",       "bonus": 4, "damage": "1d6+2", "damage_type": "bludgeoning"}]},
    "Spy":             {"hp": 27, "ac": 12, "xp": 200, "initiative_mod": 2,
                        "attacks": [{"name": "Shortsword", "bonus": 4, "damage": "1d6+2", "damage_type": "piercing"}]},
    "Ogre":            {"hp": 59, "ac": 11, "xp": 450, "initiative_mod":-1,
                        "attacks": [{"name": "Greatclub",  "bonus": 6, "damage": "2d8+4", "damage_type": "bludgeoning"}]},
    "Troll":           {"hp": 84, "ac": 15, "xp":1800, "initiative_mod": 2,
                        "attacks": [{"name": "Claw",       "bonus": 7, "damage": "2d6+4", "damage_type": "slashing"}]},
    "Bandit Captain":  {"hp": 65, "ac": 15, "xp": 450, "initiative_mod": 2,
                        "attacks": [{"name": "Scimitar",   "bonus": 5, "damage": "1d6+3", "damage_type": "slashing"}]},
    "Werewolf":        {"hp": 58, "ac": 12, "xp": 700, "initiative_mod": 1,
                        "attacks": [{"name": "Claws",      "bonus": 4, "damage": "2d4+2", "damage_type": "slashing"}]},
    "Vampire Spawn":   {"hp": 82, "ac": 15, "xp":1800, "initiative_mod": 3,
                        "attacks": [{"name": "Claws",      "bonus": 6, "damage": "2d4+3", "damage_type": "slashing"}]},
}

def _enemy_defaults(name, level):
    """Fallback stat block for unlisted enemies, scaled to player level."""
    hp  = max(5, level * 7)
    ac  = 10 + max(0, level // 3)
    atk = max(2, level // 2 + 1)
    dmg = f"1d{'6' if level < 5 else '8'}+{max(1, level//3)}"
    return {"hp": hp, "ac": ac, "xp": level * 50, "initiative_mod": 1,
            "attacks": [{"name": "Attack", "bonus": atk, "damage": dmg,
                         "damage_type": "slashing"}]}

# ── Skill → ability mapping ────────────────────────────────────────────────────
SKILL_ABILITIES = {
    "Acrobatics": "dexterity",    "Animal Handling": "wisdom",
    "Arcana": "intelligence",     "Athletics": "strength",
    "Deception": "charisma",      "History": "intelligence",
    "Insight": "wisdom",          "Intimidation": "charisma",
    "Investigation": "intelligence","Medicine": "wisdom",
    "Nature": "intelligence",     "Perception": "wisdom",
    "Performance": "charisma",    "Persuasion": "charisma",
    "Religion": "intelligence",   "Sleight of Hand": "dexterity",
    "Stealth": "dexterity",       "Survival": "wisdom",
    "Strength": "strength",       "Dexterity": "dexterity",
    "Constitution": "constitution","Intelligence": "intelligence",
    "Wisdom": "wisdom",           "Charisma": "charisma",
    "Thieves Tools": "dexterity", "Thieves' Tools": "dexterity",
}


class GameApp:

    def __init__(self, root):
        self.root  = root
        self.char    = None
        self.session = None
        self.dm      = None
        self.state   = "STARTUP"   # EXPLORING | COMBAT | DEAD

        root.title("D&D AI Dungeon Master")
        root.configure(bg=BG)
        root.geometry("1100x700")
        root.minsize(800, 560)

        self._build_ui()
        root.after(150, self._startup_dialog)

    # ── UI construction ────────────────────────────────────────────────────────

    def _build_ui(self):
        # header bar
        hdr = tk.Frame(self.root, bg=PANEL, pady=6)
        hdr.pack(fill="x")
        tk.Frame(hdr, bg=ACCENT, width=4).pack(side="left", fill="y")
        self._loc_var  = tk.StringVar(value="D&D AI Dungeon Master")
        self._char_var = tk.StringVar(value="")
        tk.Label(hdr, textvariable=self._char_var, font=FONT_TITLE,
                 bg=PANEL, fg=ACCENT, padx=12).pack(side="left")
        tk.Label(hdr, textvariable=self._loc_var, font=FONT_BODY,
                 bg=PANEL, fg=DIM, padx=8).pack(side="left")

        # main area: narration + sidebar
        main = tk.Frame(self.root, bg=BG)
        main.pack(fill="both", expand=True)

        # narration panel
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

        # text tags
        self._narration.tag_config("dm",     foreground=FG)
        self._narration.tag_config("player", foreground=ACCENT)
        self._narration.tag_config("system", foreground=BLUE)
        self._narration.tag_config("hit",    foreground=GREEN)
        self._narration.tag_config("miss",   foreground=DIM)
        self._narration.tag_config("danger", foreground=RED)
        self._narration.tag_config("header", foreground=ACCENT,
                                   font=("Consolas", 10, "bold"))

        # sidebar
        sf = tk.Frame(main, bg=PANEL, width=220)
        sf.pack(side="right", fill="y", padx=(4,8), pady=6)
        sf.pack_propagate(False)

        tk.Label(sf, text="CHARACTER", font=FONT_SM, bg=PANEL,
                 fg=ACCENT).pack(anchor="w", padx=10, pady=(10,2))
        self._hp_label  = tk.Label(sf, text="HP: —", font=FONT_BODY,
                                   bg=PANEL, fg=FG)
        self._hp_label.pack(anchor="w", padx=10)
        self._hp_bar_canvas = tk.Canvas(sf, bg=PANEL, height=8,
                                        highlightthickness=0)
        self._hp_bar_canvas.pack(fill="x", padx=10, pady=2)
        self._ac_label  = tk.Label(sf, text="AC: —", font=FONT_SM,
                                   bg=PANEL, fg=DIM)
        self._ac_label.pack(anchor="w", padx=10)
        self._spd_label = tk.Label(sf, text="Speed: —", font=FONT_SM,
                                   bg=PANEL, fg=DIM)
        self._spd_label.pack(anchor="w", padx=10)
        self._cond_label = tk.Label(sf, text="Conditions: —", font=FONT_SM,
                                    bg=PANEL, fg=DIM, wraplength=190,
                                    justify="left")
        self._cond_label.pack(anchor="w", padx=10, pady=(0,6))

        tk.Frame(sf, bg=BTN_BG, height=1).pack(fill="x", padx=10, pady=4)

        tk.Label(sf, text="COMBAT", font=FONT_SM, bg=PANEL,
                 fg=ACCENT).pack(anchor="w", padx=10, pady=(4,2))
        self._combat_frame = tk.Frame(sf, bg=PANEL)
        self._combat_frame.pack(fill="x", padx=6)

        tk.Frame(sf, bg=BTN_BG, height=1).pack(fill="x", padx=10, pady=8)
        tk.Button(sf, text="Save & Quit", font=FONT_SM, bg=BTN_BG, fg=FG,
                  relief="flat", bd=0, padx=8, pady=4,
                  activebackground=ACCENT, activeforeground="#1a1a2e",
                  command=self._save_and_quit).pack(padx=10, pady=4, fill="x")

        # input area
        inp = tk.Frame(self.root, bg=PANEL, pady=6)
        inp.pack(fill="x", side="bottom")
        tk.Frame(inp, bg=ACCENT, height=2).pack(fill="x")
        self._input_frame = tk.Frame(inp, bg=PANEL)
        self._input_frame.pack(fill="x", padx=8, pady=6)
        self._build_explore_input()

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

    def _build_combat_input(self):
        for w in self._input_frame.winfo_children():
            w.destroy()
        tk.Label(self._input_frame, text="YOUR TURN — choose an attack:",
                 font=FONT_SM, bg=PANEL, fg=ACCENT).pack(anchor="w", padx=4)
        btn_row = tk.Frame(self._input_frame, bg=PANEL)
        btn_row.pack(fill="x", padx=4, pady=4)
        attacks = self.char.get("attacks", [])
        if not attacks:
            tk.Label(btn_row, text="No attacks available.", font=FONT_SM,
                     bg=PANEL, fg=DIM).pack(side="left")
            return
        for atk in attacks:
            name = atk["name"]
            tk.Button(
                btn_row, text=name, font=FONT_SM, bg=BTN_BG, fg=FG,
                relief="flat", bd=0, padx=8, pady=4,
                activebackground=ACCENT, activeforeground="#1a1a2e",
                command=lambda n=name: self._do_player_attack(n)
            ).pack(side="left", padx=3)

    # ── Startup ────────────────────────────────────────────────────────────────

    def _startup_dialog(self):
        chars = list_characters()

        d = tk.Toplevel(self.root)
        d.title("Start Game")
        d.configure(bg=BG)
        d.grab_set()
        d.resizable(False, False)
        self.root.update_idletasks()
        rx = self.root.winfo_x() + self.root.winfo_width()  // 2 - 220
        ry = self.root.winfo_y() + self.root.winfo_height() // 2 - 190
        d.geometry(f"440x380+{rx}+{ry}")

        tk.Frame(d, bg=ACCENT, height=4).pack(fill="x")
        tk.Label(d, text="  ⚔  START ADVENTURE", font=FONT_HDR,
                 bg=PANEL, fg=ACCENT, pady=8).pack(fill="x")

        body = tk.Frame(d, bg=BG, padx=20, pady=10)
        body.pack(fill="both", expand=True)

        # character row: label + dropdown + New button
        char_row = tk.Frame(body, bg=BG)
        char_row.pack(fill="x", pady=(0, 2))
        tk.Label(char_row, text="Select Character:", font=FONT_SM,
                 bg=BG, fg=DIM).pack(side="left")
        tk.Button(char_row, text="+ New", font=FONT_SM, bg=BTN_BG, fg=ACCENT,
                  relief="flat", bd=0, padx=6, pady=2,
                  activebackground=ACCENT, activeforeground="#1a1a2e",
                  command=lambda: self._launch_builder(d, char_var,
                                                       char_menu)).pack(side="right")

        char_var  = tk.StringVar(value=chars[0] if chars else "")
        char_menu = tk.OptionMenu(body, char_var, *(chars or ["—"]))
        char_menu.config(bg=INPUT_BG, fg=FG, font=FONT_BODY, relief="flat",
                         activebackground=ACCENT, activeforeground="#1a1a2e",
                         highlightthickness=0, bd=0, width=28)
        char_menu["menu"].config(bg=INPUT_BG, fg=FG, font=FONT_BODY)
        char_menu.pack(fill="x", pady=(0, 12))

        mode_var = tk.StringVar(value="new")
        tk.Label(body, text="Session:", font=FONT_SM, bg=BG, fg=DIM).pack(anchor="w")
        tk.Radiobutton(body, text="New adventure", variable=mode_var, value="new",
                       bg=BG, fg=FG, selectcolor=BTN_BG,
                       activebackground=BG, font=FONT_BODY).pack(anchor="w")
        tk.Radiobutton(body, text="Resume session", variable=mode_var, value="resume",
                       bg=BG, fg=FG, selectcolor=BTN_BG,
                       activebackground=BG, font=FONT_BODY).pack(anchor="w")

        sessions = gs.list_sessions()
        session_var = tk.StringVar(value=sessions[0] if sessions else "")
        session_menu = tk.OptionMenu(body, session_var,
                                     *sessions if sessions else ["—"])
        session_menu.config(bg=INPUT_BG, fg=FG, font=FONT_BODY, relief="flat",
                            activebackground=ACCENT, activeforeground="#1a1a2e",
                            highlightthickness=0, bd=0, width=28)
        session_menu["menu"].config(bg=INPUT_BG, fg=FG, font=FONT_BODY)
        session_menu.pack(fill="x", pady=(2,12))

        err_lbl = tk.Label(body, text="", font=FONT_SM, bg=BG, fg=RED)
        err_lbl.pack()

        def start():
            char_name = char_var.get()
            if not char_name or char_name == "—":
                err_lbl.config(text="No character selected. Create one with '+ New'.")
                return
            mode = mode_var.get()
            try:
                self.char = load_character(char_name)
            except Exception as e:
                err_lbl.config(text=f"Could not load character: {e}")
                return
            if mode == "resume":
                sname = session_var.get()
                if not sname or sname == "—":
                    err_lbl.config(text="No session selected.")
                    return
                try:
                    self.session = gs.load_session(sname)
                except Exception as e:
                    err_lbl.config(text=f"Could not load session: {e}")
                    return
            else:
                self.session = gs.empty_session(
                    character_name=char_name,
                    session_name=char_name)
                gs.init_hp(self.session, self.char)

            try:
                self.dm = dm_module.from_config()
            except Exception as e:
                err_lbl.config(text=f"DM config error: {e}")
                return

            d.destroy()
            self._start_adventure(new=(mode == "new"))

        tk.Button(body, text="⚔  Begin", font=FONT_HDR, bg=ACCENT,
                  fg="#1a1a2e", relief="flat", bd=0, padx=12, pady=6,
                  activebackground="#e0c060", activeforeground="#1a1a2e",
                  command=start).pack(pady=4, fill="x")

    def _launch_builder(self, dialog, char_var, char_menu):
        """Launch character builder in background. Refresh dropdown when it closes."""
        import subprocess
        builder = Path(__file__).parent / "Character Builder" / "character_builder_app.py"

        def _run():
            subprocess.run([sys.executable, str(builder)],
                           cwd=str(builder.parent))
            dialog.after(0, lambda: self._refresh_char_dropdown(char_var, char_menu))

        threading.Thread(target=_run, daemon=True).start()

    def _refresh_char_dropdown(self, char_var, char_menu):
        """Repopulate the character dropdown and select the newest character."""
        chars = list_characters()
        menu  = char_menu["menu"]
        menu.delete(0, "end")
        for c in chars:
            menu.add_command(label=c, command=lambda v=c: char_var.set(v))
        if chars:
            char_var.set(chars[-1])   # newest character is last alphabetically

    def _start_adventure(self, new=True):
        self._char_var.set(
            f"{self.char.get('name','')}  —  "
            f"{self.char.get('race','')} {self.char.get('class','')} "
            f"Lv.{self.char.get('level',1)}")
        self._loc_var.set(self.session.get("location", "Unknown"))
        self._update_sidebar()
        self.state = "EXPLORING"

        if not new and self.session.get("history"):
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

    def _dm_call(self, action):
        self._display("DM is thinking...\n", "system")
        def _thread():
            try:
                result = self.dm.respond(self.session, self.char, action)
                self.root.after(0, lambda: self._handle_dm_response(result))
            except Exception as e:
                self.root.after(0, lambda: self._handle_dm_error(str(e)))
        threading.Thread(target=_thread, daemon=True).start()

    def _handle_dm_response(self, result):
        self._erase_last_line()   # remove "DM is thinking..."
        self._display(result["narration"] + "\n\n", "dm")
        self._loc_var.set(self.session.get("location", self.session.get("scene", "")[:40]))

        for ev in result["events"]:
            if ev["type"] == "combat_start":
                self._start_combat(ev["enemies"])
                return
            elif ev["type"] == "skill_check":
                self._handle_skill_check(ev["skill"], ev["dc"])
                return

        self._set_input_enabled(True)

    def _handle_dm_error(self, msg):
        self._erase_last_line()
        self._display(f"[DM Error: {msg}]\n\n", "danger")
        self._set_input_enabled(True)

    # ── Combat ─────────────────────────────────────────────────────────────────

    def _start_combat(self, enemy_specs):
        self._display("── Combat begins! ──\n\n", "header")
        level = self.char.get("level", 1)
        enemies = []
        counts  = {}
        for spec in enemy_specs:
            base  = ENEMY_STATS.get(spec["name"], _enemy_defaults(spec["name"], level))
            count = spec.get("count", 1)
            for i in range(count):
                label = spec["name"] if count == 1 else f"{spec['name']} {i+1}"
                counts[label] = counts.get(label, 0)
                enemies.append(cb.build_enemy(
                    label, base["hp"], base["ac"], base["attacks"],
                    base["initiative_mod"], base["xp"]))
        cb.setup_combat(self.session, self.char, enemies)
        self.state = "COMBAT"
        self._update_sidebar()
        self._display("Initiative order:\n", "system")
        for c in self.session["initiative_order"]:
            marker = "▶" if c["is_player"] else "·"
            self._display(f"  {marker} {c['name']} (HP {c['hp']}/{c['max_hp']}) "
                          f"— init {c['initiative']}\n", "system")
        self._display("\n", "dm")
        self._next_turn()

    def _next_turn(self):
        self._update_sidebar()
        current = gs.current_combatant(self.session)
        if not current:
            self._end_combat(victory=True)
            return
        if not gs.enemies_alive(self.session):
            self._end_combat(victory=True)
            return
        if self.session["current_hp"] <= 0:
            self._handle_death_saves()
            return

        if current["is_player"]:
            self._display(f"── Round {self.session['round']} — Your turn ──\n\n", "header")
            self._build_combat_input()
        else:
            self.root.after(800, self._do_enemy_turn)

    def _do_player_attack(self, weapon_name):
        living_enemies = [c for c in self.session["initiative_order"]
                          if not c["is_player"] and c["hp"] > 0]
        if not living_enemies:
            self._end_combat(victory=True)
            return
        # auto-target single enemy; if multiple, pick first for now
        target = living_enemies[0]["name"]
        result = cb.player_attack(self.session, self.char, weapon_name, target)
        self._display_attack_result(result)
        self._build_explore_input()
        if not gs.enemies_alive(self.session):
            self.root.after(600, lambda: self._end_combat(victory=True))
        else:
            self.root.after(600, lambda: (
                cb.end_turn(self.session), self._next_turn()))

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

        if self.session["current_hp"] <= 0:
            self.root.after(600, self._handle_death_saves)
            return

        cb.end_turn(self.session)
        self.root.after(600, self._next_turn)

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
        xp = cb.xp_from_combat(self.session)
        gs.end_combat(self.session)
        self.state = "EXPLORING"
        self._update_sidebar()
        self._build_explore_input()
        if victory:
            self._display(f"── Victory! ({xp} XP earned) ──\n\n", "header")
            self._set_input_enabled(False)
            self._dm_call("The combat is over. We won. Describe the aftermath.")
        else:
            self._display("── Defeated ──\n\n", "danger")
            self._set_input_enabled(False)
            self._dm_call("The player has been defeated. Narrate the ending.")

    def _handle_death_saves(self):
        self._display("── You are dying — Death Saving Throw! ──\n", "danger")
        result = cb.handle_death_save(self.session)
        if result["outcome"] == "revived":
            self._display(f"  Rolled {result['roll']} — NATURAL 20! You stabilize at 1 HP!\n\n", "hit")
            self.session["current_hp"] = 1
            self._update_sidebar()
            cb.end_turn(self.session)
            self.root.after(800, self._next_turn)
        elif result["outcome"] == "stable":
            self._display(f"  Rolled {result['roll']} — 3 successes. You stabilize.\n\n", "system")
            self._update_sidebar()
            cb.end_turn(self.session)
            self.root.after(800, self._next_turn)
        elif result["outcome"] == "dead":
            self._display(f"  Rolled {result['roll']} — 3 failures. You have died.\n\n", "danger")
            self.state = "DEAD"
            self._set_input_enabled(False)
            self._dm_call("The player character has died. Narrate their death.")
        else:
            ds = result["death_saves"]
            double = " (counts as 2 failures!)" if result["double_fail"] else ""
            self._display(
                f"  Rolled {result['roll']}{double} — "
                f"Successes: {ds['successes']}  Failures: {ds['failures']}\n\n",
                "system" if result["success"] else "danger")
            self._update_sidebar()
            cb.end_turn(self.session)
            self.root.after(800, self._next_turn)

    # ── Skill checks ───────────────────────────────────────────────────────────

    def _handle_skill_check(self, skill, dc):
        ability = SKILL_ABILITIES.get(skill, "")
        ab      = self.char.get("abilities", {})
        ab_mod  = modifier(ab.get(ability, 10)) if ability else 0
        prof_b  = proficiency_bonus(self.char.get("level", 1))
        proficient = skill in self.char.get("skill_proficiencies", [])
        total_mod  = ab_mod + (prof_b if proficient else 0)

        roll   = dice.d20_check(modifier=total_mod)
        result = roll["total"]
        success = roll["nat20"] or (not roll["nat1"] and result >= dc)

        prof_note = f" (proficient, +{prof_b})" if proficient else ""
        self._display(
            f"── Skill Check: {skill} DC {dc} ──\n"
            f"  Rolled {roll['kept']} + {total_mod} modifier{prof_note} = {result} "
            f"vs DC {dc} — {'SUCCESS' if success else 'FAILURE'}\n\n",
            "hit" if success else "danger")

        outcome = f"I attempted a {skill} check (DC {dc}) and {'succeeded' if success else 'failed'} with a roll of {result}."
        self._set_input_enabled(False)
        self._dm_call(outcome)

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
        cur_hp  = self.session.get("current_hp", 0) or 0
        max_hp  = self.char["hp"].get("max", 1)
        ac      = self.char.get("armor_class", 10)
        speed   = self.char.get("speed", 30)
        conds   = self.session.get("conditions", [])

        self._hp_label.config(text=f"HP: {cur_hp} / {max_hp}")
        self._ac_label.config(text=f"AC: {ac}")
        self._spd_label.config(text=f"Speed: {speed} ft")
        self._cond_label.config(
            text="Conditions: " + (", ".join(conds) if conds else "—"))

        # HP bar colour
        ratio = cur_hp / max(1, max_hp)
        colour = GREEN if ratio > 0.5 else (YELLOW if ratio > 0.25 else RED)
        self._hp_bar_canvas.delete("all")
        w = 180
        self._hp_bar_canvas.config(width=w)
        self._hp_bar_canvas.create_rectangle(0, 0, w, 8, fill=BTN_BG, outline="")
        self._hp_bar_canvas.create_rectangle(0, 0, int(w * ratio), 8,
                                             fill=colour, outline="")

        # combat tracker
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
            tk.Label(self._combat_frame, text="Not in combat", font=FONT_SM,
                     bg=PANEL, fg=DIM).pack(anchor="w")

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

    # ── Save & quit ────────────────────────────────────────────────────────────

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
