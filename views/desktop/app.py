import sys
import threading
import tkinter as tk
from tkinter import messagebox, ttk
from pathlib import Path

_root = Path(__file__).parent.parent.parent
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))

from models.character import load_character, list_characters, modifier, proficiency_bonus
import models.game_state as gs
import models.combat as cb
import models.dm as dm_module
import models.dice as dice
from controllers.game_controller import (
    setup_combat as gc_setup_combat,
    process_skill_check,
    process_enemy_turn,
    process_death_save,
    SKILL_ABILITIES,
)
from views.desktop.d20_roller import D20RollerWindow

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


class GameApp:

    def __init__(self, root):
        self.root    = root
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
        hdr = tk.Frame(self.root, bg=PANEL, pady=6)
        hdr.pack(fill="x")
        tk.Frame(hdr, bg=ACCENT, width=4).pack(side="left", fill="y")
        self._loc_var  = tk.StringVar(value="D&D AI Dungeon Master")
        self._char_var = tk.StringVar(value="")
        tk.Label(hdr, textvariable=self._char_var, font=FONT_TITLE,
                 bg=PANEL, fg=ACCENT, padx=12).pack(side="left")
        tk.Label(hdr, textvariable=self._loc_var, font=FONT_BODY,
                 bg=PANEL, fg=DIM, padx=8).pack(side="left")

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
                        "Create or select a character and start a new session.",
                        lambda: self._show_character_page(d))

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
            try:
                self.dm = dm_module.from_config()
            except Exception as e:
                self._dlg_err.config(text=f"DM config error: {e}")
                return
            self.session = gs.empty_session(character_name=char_name,
                                            session_name=char_name)
            gs.init_hp(self.session, self.char)
            d.destroy()
            self._start_adventure(new=True)

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
                msg = str(e) or repr(e)
                self.root.after(0, lambda: self._handle_dm_error(msg))
        threading.Thread(target=_thread, daemon=True).start()

    def _handle_dm_response(self, result):
        self._erase_last_line()
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
        dex_mod   = modifier(self.char["abilities"].get("dexterity", 10))
        init_roll = dice.initiative(dex_mod)

        self._display(f"Roll for initiative!  (modifier {init_roll['modifier']:+d})\n\n", "system")

        def _after_init():
            result = gc_setup_combat(self.session, self.char, enemy_specs,
                                     d20_initiative=init_roll["total"])
            self.state = "COMBAT"
            self._update_sidebar()
            self._display("Initiative order:\n", "system")
            self._display(result["display"] + "\n\n", "system")
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
        target = living_enemies[0]["name"]

        weapon = next((a for a in self.char.get("attacks", [])
                       if a["name"].lower() == weapon_name.lower()), None)
        if not weapon:
            self._display(f"  Weapon '{weapon_name}' not found.\n\n", "danger")
            return

        attack_bonus = weapon.get("attack_bonus", 0)
        pre_roll     = dice.d20_check(modifier=attack_bonus)

        self._display(f"── Attacking {target} with {weapon_name} ──\n"
                      f"  Attack bonus: {attack_bonus:+d}\n\n", "header")
        self._build_explore_input()

        def _after_roll():
            result = cb.player_attack(self.session, self.char, weapon_name, target,
                                      d20_override=pre_roll["kept"])
            self._display_attack_result(result)
            if not gs.enemies_alive(self.session):
                self.root.after(600, lambda: self._end_combat(victory=True))
            else:
                self.root.after(600, lambda: (
                    cb.end_turn(self.session), self._next_turn()))

        self._show_roll_button(f"d20 ({weapon_name})", pre_roll["kept"], _after_roll)

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

        ratio  = cur_hp / max(1, max_hp)
        colour = GREEN if ratio > 0.5 else (YELLOW if ratio > 0.25 else RED)
        self._hp_bar_canvas.delete("all")
        w = 180
        self._hp_bar_canvas.config(width=w)
        self._hp_bar_canvas.create_rectangle(0, 0, w, 8, fill=BTN_BG, outline="")
        self._hp_bar_canvas.create_rectangle(0, 0, int(w * ratio), 8,
                                             fill=colour, outline="")

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
