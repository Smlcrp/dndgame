"""D&D 5e Character Builder — fully GUI-driven."""

import tkinter as tk
from tkinter import ttk, messagebox
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from models.character import (empty_character, save_character, load_character,
                       list_characters, modifier, proficiency_bonus)
from dnd_data import (
    RACES, CLASSES, SUBCLASSES, BACKGROUNDS, ALIGNMENTS as DND_ALIGNMENTS,
    RACIAL_BONUSES, STANDARD_ARRAY, POINT_BUY_COSTS, POINT_BUY_BUDGET,
    ABILITIES, ABILITY_LABELS, CLASS_PRIMARY_STATS, CLASS_SAVING_THROWS,
    BACKGROUND_PROFICIENCIES, ALL_LANGUAGES, ALL_SKILLS,
    CLASS_HIT_DICE, HIT_DIE_AVERAGES, RACE_SPEED, ARMOR_TABLE,
    CLASS_SKILLS, CLASS_ARMOR_PROFS, CLASS_WEAPON_PROFS,
    RACE_LANGUAGES, RACE_EXTRA_LANGUAGES, CLASS_SPELLCASTING,
    FULL_CASTER_SLOTS, HALF_CASTER_SLOTS, WARLOCK_SLOTS, CANTRIPS_KNOWN,
    WEAPONS, WEAPON_CATEGORIES, CLASS_STARTING_GOLD, EQUIPMENT_PACKS,
    BACKGROUND_FEATURES, BACKGROUND_DESCRIPTIONS, BACKGROUND_PROFICIENCIES,
    RACIAL_TRAITS, RACE_DESCRIPTIONS, CLASS_FEATURES,
    get_personality_suggestions, ARTISAN_TOOLS, GAMING_SETS,
    MUSICAL_INSTRUMENTS,
)
from spells import CANTRIPS as SPELL_CANTRIPS, SPELLS as SPELL_LISTS

BG       = "#1a1a2e"
ACCENT   = "#c8a951"
FG       = "#e0e0e0"
INPUT_BG = "#0f0f1a"
PANEL    = "#16213e"
BTN_BG   = "#2a2a4a"
DIM      = "#888888"
GREEN    = "#4caf50"
RED      = "#e05050"
BLUE     = "#5b8cdc"

FONT_TITLE = ("Segoe UI", 14, "bold")
FONT_HDR   = ("Segoe UI", 11, "bold")
FONT_BODY  = ("Segoe UI", 10)
FONT_SM    = ("Segoe UI", 9)


def _weapon_proficient(cls, name, cat):
    profs = CLASS_WEAPON_PROFS.get(cls, [])
    if "Simple weapons" in profs and cat in ("Simple Melee", "Simple Ranged"):
        return True
    if "Martial weapons" in profs and cat in ("Martial Melee", "Martial Ranged"):
        return True
    wn = name.lower()
    return any(p.lower().rstrip("s") == wn or p.lower() == wn for p in profs)


def _btn(parent, text, cmd, bg=BTN_BG, fg=FG, font=FONT_BODY, **kw):
    return tk.Button(parent, text=text, command=cmd, bg=bg, fg=fg, font=font,
                     relief="flat", activebackground=ACCENT, activeforeground="#1a1a2e",
                     cursor="hand2", padx=8, pady=4, **kw)


def _listbox(parent, items, height=10, width=28, multi=False):
    frame = tk.Frame(parent, bg=BG)
    sb = tk.Scrollbar(frame, bg=BG, troughcolor=INPUT_BG)
    mode = tk.MULTIPLE if multi else tk.SINGLE
    lb = tk.Listbox(frame, height=height, width=width, selectmode=mode,
                    bg=INPUT_BG, fg=FG, font=FONT_BODY,
                    selectbackground=ACCENT, selectforeground="#1a1a2e",
                    activestyle="none", bd=0, highlightthickness=1,
                    highlightcolor=ACCENT, highlightbackground=PANEL,
                    yscrollcommand=sb.set)
    sb.config(command=lb.yview)
    lb.pack(side="left", fill="both", expand=True)
    sb.pack(side="right", fill="y")
    for item in items:
        lb.insert(tk.END, item)
    return frame, lb


def _pick_from_list(parent, title, options, var, callback=None, detail_fn=None):
    d = tk.Toplevel(parent)
    d.title(title)
    d.configure(bg=BG)
    d.geometry("340x420")
    d.grab_set()
    d.focus_set()
    parent.update_idletasks()
    rx = parent.winfo_x() + parent.winfo_width()//2 - 170
    ry = parent.winfo_y() + parent.winfo_height()//2 - 210
    d.geometry(f"340x420+{rx}+{ry}")
    tk.Label(d, text=title, font=FONT_HDR, bg=PANEL, fg=ACCENT, pady=6).pack(fill="x")
    search_var = tk.StringVar()
    tk.Entry(d, textvariable=search_var, bg=INPUT_BG, fg=FG, font=FONT_BODY,
             insertbackground=FG, relief="flat", bd=4).pack(fill="x", padx=8, pady=4)
    frame, lb = _listbox(d, options, height=16, width=32)
    frame.pack(padx=8, pady=4, fill="both", expand=True)

    def filter_list(*_):
        q = search_var.get().lower()
        lb.delete(0, tk.END)
        for item in options:
            if q in item.lower():
                lb.insert(tk.END, item)
        cur = var.get()
        for i in range(lb.size()):
            if lb.get(i) == cur:
                lb.selection_set(i)
                lb.see(i)
                break

    search_var.trace_add("write", filter_list)
    filter_list()

    def confirm(*_):
        sel = lb.curselection()
        if sel:
            var.set(lb.get(sel[0]))
            if callback:
                callback()
        d.destroy()

    lb.bind("<Double-Button-1>", confirm)
    lb.bind("<Return>", confirm)

    btn_row = tk.Frame(d, bg=BG)
    btn_row.pack(pady=6)
    _btn(btn_row, "Select", confirm, bg=ACCENT, fg="#1a1a2e").pack(side="left", padx=4)
    if detail_fn:
        def show_detail():
            sel = lb.curselection()
            item = lb.get(sel[0]) if sel else var.get()
            detail_fn(d, item)
        _btn(btn_row, "Details", show_detail, bg=BTN_BG).pack(side="left", padx=4)

    d.wait_window()


def _pick_suggestion(parent, label, suggestions, text_widget):
    d = tk.Toplevel(parent)
    d.title(f"Suggestions: {label}")
    d.configure(bg=BG)
    d.geometry("440x380")
    d.grab_set()
    parent.update_idletasks()
    rx = parent.winfo_x() + parent.winfo_width()//2 - 220
    ry = parent.winfo_y() + parent.winfo_height()//2 - 190
    d.geometry(f"440x380+{rx}+{ry}")
    tk.Label(d, text=f"💡 {label}", font=FONT_HDR, bg=PANEL, fg=ACCENT, pady=6).pack(fill="x")
    frame, lb = _listbox(d, suggestions, height=14, width=52)
    frame.pack(padx=8, pady=4, fill="both", expand=True)

    def insert(*_):
        sel = lb.curselection()
        if sel:
            text = lb.get(sel[0])
            cur = text_widget.get("1.0", "end").strip()
            if cur:
                text_widget.insert("end", "\n" + text)
            else:
                text_widget.delete("1.0", "end")
                text_widget.insert("1.0", text)
        d.destroy()

    lb.bind("<Double-Button-1>", insert)
    _btn(d, "Insert", insert, bg=ACCENT, fg="#1a1a2e").pack(pady=6)
    d.wait_window()


class CharacterBuilderApp:
    SECTIONS = [
        "Basic Info", "Ability Scores", "Proficiencies",
        "Spellcasting", "Equipment", "Features & Traits", "Personality",
    ]

    def __init__(self, root):
        self.root = root
        self.root.title("D&D 5e Character Builder")
        self.root.configure(bg=BG)
        self.root.geometry("1120x740")
        self.root.minsize(900, 600)
        self.char = empty_character()
        self._build_ui()

    # ── MAIN WINDOW ───────────────────────────────────────────────────────────

    def _build_ui(self):
        tk.Frame(self.root, bg=ACCENT, height=4).pack(fill="x")
        header = tk.Frame(self.root, bg=PANEL, pady=8)
        header.pack(fill="x")
        tk.Label(header, text="⚔  D&D 5e CHARACTER BUILDER",
                 font=FONT_TITLE, bg=PANEL, fg=ACCENT).pack(side="left", padx=16)

        main = tk.Frame(self.root, bg=BG)
        main.pack(fill="both", expand=True, padx=10, pady=8)

        left = tk.Frame(main, bg=PANEL, width=230)
        left.pack(side="left", fill="y", padx=(0, 8))
        left.pack_propagate(False)
        tk.Label(left, text="SECTIONS", font=("Segoe UI", 9, "bold"),
                 bg=PANEL, fg=DIM).pack(pady=(12, 4))
        self._sec_btns = {}
        for sec in self.SECTIONS:
            b = tk.Button(left, text=f"·  {sec}", font=FONT_BODY,
                          bg=PANEL, fg=FG, relief="flat",
                          activebackground=ACCENT, activeforeground="#1a1a2e",
                          anchor="w", padx=12, pady=7, cursor="hand2",
                          command=lambda s=sec: self._open_section(s))
            b.pack(fill="x", padx=4, pady=1)
            self._sec_btns[sec] = b

        right = tk.Frame(main, bg=BG)
        right.pack(side="left", fill="both", expand=True)
        self._preview = tk.Text(right, bg=INPUT_BG, fg=FG, font=("Consolas", 10),
                                state="disabled", relief="flat", bd=0,
                                wrap="word", padx=12, pady=10)
        sb = tk.Scrollbar(right, command=self._preview.yview, bg=BG, troughcolor=INPUT_BG)
        self._preview.config(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")
        self._preview.pack(fill="both", expand=True)

        bottom = tk.Frame(self.root, bg=PANEL, pady=6)
        bottom.pack(fill="x", side="bottom")
        _btn(bottom, "💾  Save",   self._save_char,  bg="#1e4620").pack(side="left", padx=(10, 4))
        _btn(bottom, "📂  Load",   self._load_char).pack(side="left", padx=4)
        _btn(bottom, "🗑  Delete", self._delete_char, bg="#4a1e1e").pack(side="left", padx=4)
        _btn(bottom, "✨  New",    self._new_char).pack(side="left", padx=4)
        _btn(bottom, "✖  Quit",   self._quit,        bg="#3a1e1e").pack(side="right", padx=10)

        self._refresh_preview()

    def _open_section(self, name):
        if name != "Basic Info":
            c = self.char
            if not c.get("race") or not c.get("class"):
                messagebox.showinfo(
                    "Basic Info Required",
                    "Please Enter Basic Info",
                    parent=self.root,
                )
                self._dlg_basic_info()
                return
        {
            "Basic Info":        self._dlg_basic_info,
            "Ability Scores":    self._dlg_ability_scores,
            "Proficiencies":     self._dlg_proficiencies,
            "Spellcasting":      self._dlg_spellcasting,
            "Equipment":         self._dlg_equipment,
            "Features & Traits": self._dlg_features,
            "Personality":       self._dlg_personality,
        }[name]()

    def _mark_done(self, section, done=True):
        icon = "✔" if done else "·"
        col  = GREEN if done else FG
        self._sec_btns[section].config(text=f"{icon}  {section}", fg=col)

    def _calc_combat_stats(self):
        c       = self.char
        cls     = c["class"]
        race    = c["race"]
        lvl     = c["level"] or 1
        ab      = c["abilities"]
        con_mod = modifier(ab.get("constitution", 10))
        dex_mod = modifier(ab.get("dexterity", 10))
        wis_mod = modifier(ab.get("wisdom", 10))
        hit_die = CLASS_HIT_DICE.get(cls, "d8")
        hd_max  = int(hit_die[1:])
        hd_avg  = HIT_DIE_AVERAGES.get(hit_die, 5)
        c["hp"]["max"]     = max(1, hd_max + con_mod) + (lvl - 1) * max(1, hd_avg + con_mod)
        c["hp"]["current"] = c["hp"]["max"]
        armor_name = c.get("_armor_name", "")
        if not armor_name or armor_name == "Unarmored":
            if cls == "Barbarian":
                c["armor_class"] = 10 + dex_mod + con_mod
            elif cls == "Monk":
                c["armor_class"] = 10 + dex_mod + wis_mod
            else:
                c["armor_class"] = 10 + dex_mod
        else:
            ar = ARMOR_TABLE.get(armor_name)
            if ar:
                base = ar["ac_base"]
                md   = ar.get("max_dex")
                if md is None:  c["armor_class"] = base + dex_mod
                elif md == 0:   c["armor_class"] = base
                else:           c["armor_class"] = base + min(dex_mod, md)
            else:
                c["armor_class"] = 10 + dex_mod
        c["speed"]             = RACE_SPEED.get(race, 30)
        c["hit_dice"]["type"]  = hit_die
        c["hit_dice"]["total"] = lvl

    def _calc_attacks(self):
        c       = self.char
        cls     = c["class"]
        lvl     = c["level"] or 1
        ab      = c["abilities"]
        pb      = proficiency_bonus(lvl)
        str_mod = modifier(ab.get("strength", 10))
        dex_mod = modifier(ab.get("dexterity", 10))

        attacks = []
        seen    = set()
        for item in c.get("equipment", []):
            name = item["name"]
            if name in seen:
                continue
            w = WEAPONS.get(name)
            if not w:
                continue
            seen.add(name)
            cat   = w.get("cat", "")
            props = w.get("props", [])
            if "finesse" in props:
                atk_mod = max(str_mod, dex_mod)
            elif "Ranged" in cat:
                atk_mod = dex_mod
            else:
                atk_mod = str_mod
            prof  = _weapon_proficient(cls, name, cat)
            bonus = atk_mod + (pb if prof else 0)
            dmg_b = w.get("damage", "1d4")
            dmg   = f"{dmg_b}+{atk_mod}" if atk_mod >= 0 else f"{dmg_b}{atk_mod}"
            attacks.append({
                "name": name, "attack_bonus": bonus,
                "damage": dmg, "damage_type": w.get("type", "—"),
                "notes": "" if prof else "(not proficient)",
            })

        if cls == "Monk":
            ma_die = "d4"
            for threshold, d in [(1,"d4"),(5,"d6"),(11,"d8"),(17,"d10")]:
                if lvl >= threshold:
                    ma_die = d
            atk_mod = max(str_mod, dex_mod)
            bonus   = atk_mod + pb
            dmg     = f"1{ma_die}+{atk_mod}" if atk_mod >= 0 else f"1{ma_die}{atk_mod}"
            attacks.append({
                "name": "Unarmed Strike", "attack_bonus": bonus,
                "damage": dmg, "damage_type": "bludgeoning",
                "notes": "Martial Arts",
            })

        c["attacks"] = attacks

    def _refresh_section_visibility(self):
        can_cast = bool(CLASS_SPELLCASTING.get(self.char.get("class")))
        btn = self._sec_btns["Spellcasting"]
        if can_cast:
            btn.pack(fill="x", padx=4, pady=1,
                     after=self._sec_btns["Proficiencies"])
        else:
            btn.pack_forget()

    def _refresh_preview(self):
        self._calc_combat_stats()
        self._calc_attacks()
        self._refresh_section_visibility()
        c  = self.char
        ab = c["abilities"]
        def fmt(k): return f"{k[:3].upper()} {ab.get(k,10):>2} ({modifier(ab.get(k,10)):+d})"
        lvl  = c["level"] or 1
        pb   = proficiency_bonus(lvl)
        perc_prof      = "Perception" in c.get("skill_proficiencies", [])
        passive_perc   = 10 + modifier(ab.get("wisdom", 10)) + (pb if perc_prof else 0)
        armor_display  = c.get("_armor_name") or "Unarmored"
        lines = [
            "=" * 48,
            f"  {c['name'] or '(unnamed)'}",
            f"  {c['race'] or '—'}  |  {c['class'] or '—'}"
            + (f" ({c['subclass']})" if c.get("subclass") else "")
            + f"  |  Level {lvl}",
            f"  {c['background'] or '—'}  |  {c['alignment'] or '—'}",
            "-" * 48,
            "  ABILITIES",
            f"  {fmt('strength'):<22} {fmt('dexterity')}",
            f"  {fmt('constitution'):<22} {fmt('intelligence')}",
            f"  {fmt('wisdom'):<22} {fmt('charisma')}",
            "-" * 48,
            "  COMBAT",
            f"  HP {c['hp']['max']}  |  AC {c['armor_class']}  |  Init {modifier(ab.get('dexterity',10)):+d}  |  Spd {c['speed']} ft",
            f"  Prof +{pb}  |  Hit Die {c['hit_dice'].get('type','—')} ×{c['hit_dice'].get('total',1)}  |  Passive Perc {passive_perc}",
            f"  Armor: {armor_display}",
            "-" * 48,
        ]
        saves  = c.get("saving_throw_proficiencies", [])
        skills = c.get("skill_proficiencies", [])
        langs  = c.get("languages", [])
        if saves:  lines.append(f"  Saves: {', '.join(s.capitalize() for s in saves)}")
        if skills: lines.append(f"  Skills: {', '.join(skills)}")
        if langs:  lines.append(f"  Languages: {', '.join(langs)}")
        attacks = c.get("attacks", [])
        if attacks:
            lines.append("-" * 48)
            lines.append("  ATTACKS")
            for a in attacks[:8]:
                note = f"  {a['notes']}" if a.get("notes") else ""
                lines.append(f"  {a['name']}  {a['attack_bonus']:+d}  {a['damage']} {a['damage_type']}{note}")
        sc = c.get("spellcasting", {})
        if sc.get("enabled"):
            lines.append("-" * 48)
            spells   = sc.get("spells_known", [])
            cantrips = [s["name"] for s in spells if s["level"] == 0]
            leveled  = [s["name"] for s in spells if s["level"] > 0]
            lines.append(f"  SPELLCASTING ({sc.get('ability','').capitalize()})")
            if cantrips: lines.append(f"  Cantrips: {', '.join(cantrips[:6])}")
            if leveled:  lines.append(f"  Spells:   {', '.join(leveled[:8])}")
        equip = c.get("equipment", [])
        if equip:
            lines.append("-" * 48)
            lines.append("  EQUIPMENT")
            for it in equip[:6]:
                lines.append(f"  {it['name']} x{it['quantity']}")
        if c.get("personality_traits"):
            lines.append("-" * 48)
            lines.append(f"  {c['personality_traits'][:100]}")
        self._preview.config(state="normal")
        self._preview.delete("1.0", "end")
        self._preview.insert("1.0", "\n".join(lines))
        self._preview.config(state="disabled")

    # ── DIALOG HELPERS ────────────────────────────────────────────────────────

    def _dlg(self, title, w=680, h=540):
        d = tk.Toplevel(self.root)
        d.title(title)
        d.configure(bg=BG)
        d.grab_set()
        d.focus_set()
        self.root.update_idletasks()
        rx = self.root.winfo_x() + self.root.winfo_width()//2 - w//2
        ry = self.root.winfo_y() + self.root.winfo_height()//2 - h//2
        d.geometry(f"{w}x{h}+{rx}+{ry}")
        d.resizable(True, True)
        return d

    def _dlg_hdr(self, d, title):
        tk.Frame(d, bg=ACCENT, height=4).pack(fill="x")
        tk.Label(d, text=title, font=FONT_HDR, bg=PANEL, fg=ACCENT, pady=8).pack(fill="x")

    def _ok_cancel(self, d, save_fn):
        bar = tk.Frame(d, bg=PANEL, pady=6)
        bar.pack(fill="x", side="bottom")
        _btn(bar, "✖  Cancel", d.destroy, bg="#3a1e1e").pack(side="right", padx=8)
        _btn(bar, "✔  Save",   save_fn,   bg="#1e4620").pack(side="right", padx=4)

    def _notebook(self, parent):
        style = ttk.Style()
        style.theme_use("default")
        style.configure("TNotebook", background=BG, borderwidth=0)
        style.configure("TNotebook.Tab", background=BTN_BG, foreground=FG,
                        padding=[10, 4], font=FONT_SM)
        style.map("TNotebook.Tab", background=[("selected", ACCENT)],
                  foreground=[("selected", "#1a1a2e")])
        nb = ttk.Notebook(parent)
        nb.pack(fill="both", expand=True, padx=8, pady=4)
        return nb

    # ── RACE DETAILS ──────────────────────────────────────────────────────────

    def _show_race_details(self, parent, race):
        if not race:
            messagebox.showinfo("No Race Selected", "Select a race first.", parent=parent)
            return

        _SMALL_RACES = {"Gnome (Forest)", "Gnome (Rock)",
                        "Halfling (Lightfoot)", "Halfling (Stout)", "Goblin"}
        size        = "Small" if race in _SMALL_RACES else "Medium"
        speed       = RACE_SPEED.get(race, 30)
        racial_data = RACIAL_BONUSES.get(race, {})
        langs       = RACE_LANGUAGES.get(race, ["Common"])
        extra_langs = RACE_EXTRA_LANGUAGES.get(race, 0)
        traits      = RACIAL_TRAITS.get(race, [])

        d = self._dlg(f"{race} — Details", 600, 580)
        tk.Frame(d, bg=ACCENT, height=4).pack(fill="x")
        tk.Label(d, text=f"  {race.upper()}", font=FONT_HDR,
                 bg=PANEL, fg=ACCENT, pady=8).pack(fill="x")

        txt = tk.Text(d, bg=INPUT_BG, fg=FG, font=("Consolas", 9),
                      relief="flat", bd=0, wrap="word", padx=14, pady=10)
        sb  = tk.Scrollbar(d, command=txt.yview, bg=BG, troughcolor=INPUT_BG)
        txt.config(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")
        txt.pack(fill="both", expand=True, padx=6, pady=4)

        def section(title):
            txt.insert("end", f"\n{'─'*44}\n {title}\n{'─'*44}\n")

        desc = RACE_DESCRIPTIONS.get(race, "")
        if desc:
            txt.insert("end", desc + "\n")

        txt.insert("end", f"\nSize: {size}   |   Speed: {speed} ft\n")

        fixed    = racial_data.get("fixed", {})
        flex     = racial_data.get("flexible")
        if fixed or flex:
            section("ABILITY SCORE BONUSES")
            for ab, val in fixed.items():
                sign = f"+{val}" if val > 0 else str(val)
                txt.insert("end", f"  {ABILITY_LABELS.get(ab, ab)}: {sign}\n")
            if flex:
                exclude_names = ", ".join(ABILITY_LABELS[e] for e in flex.get("exclude", []))
                excl = f" (not {exclude_names})" if exclude_names else ""
                txt.insert("end",
                           f"  +{flex['amount']} to {flex['count']} ability of your choice{excl}\n")

        section("LANGUAGES")
        lang_str = ", ".join(langs)
        if extra_langs:
            lang_str += f"  +{extra_langs} extra of your choice"
        txt.insert("end", f"  {lang_str}\n")

        advantages = [(n, desc) for n, desc in traits
                      if any(kw in desc.lower() for kw in
                             ("advantage", "resistance", "immune", "reroll"))]
        if advantages:
            section("KEY ADVANTAGES")
            for name, desc in advantages:
                txt.insert("end", f"  ★ {name}\n    {desc}\n\n")

        section("ALL RACIAL TRAITS")
        for name, desc in traits:
            txt.insert("end", f"  ▸ {name}\n    {desc}\n\n")

        txt.config(state="disabled")
        _btn(d, "Close", d.destroy, bg=BTN_BG).pack(pady=6)
        d.wait_window()

    # ── BACKGROUND DETAILS ────────────────────────────────────────────────────

    def _show_background_details(self, parent, background):
        if not background:
            messagebox.showinfo("No Background Selected", "Select a background first.", parent=parent)
            return

        profs   = BACKGROUND_PROFICIENCIES.get(background, {})
        feature = BACKGROUND_FEATURES.get(background)

        d = self._dlg(f"{background} — Details", 600, 520)
        tk.Frame(d, bg=ACCENT, height=4).pack(fill="x")
        tk.Label(d, text=f"  {background.upper()}", font=FONT_HDR,
                 bg=PANEL, fg=ACCENT, pady=8).pack(fill="x")

        txt = tk.Text(d, bg=INPUT_BG, fg=FG, font=("Consolas", 9),
                      relief="flat", bd=0, wrap="word", padx=14, pady=10)
        sb  = tk.Scrollbar(d, command=txt.yview, bg=BG, troughcolor=INPUT_BG)
        txt.config(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")
        txt.pack(fill="both", expand=True, padx=6, pady=4)

        def section(title):
            txt.insert("end", f"\n{'─'*44}\n {title}\n{'─'*44}\n")

        desc = BACKGROUND_DESCRIPTIONS.get(background, "")
        if desc:
            txt.insert("end", desc + "\n")

        skills_fixed  = profs.get("skills_fixed", [])
        skills_choose = profs.get("skills_choose")
        tools_fixed   = profs.get("tools_fixed", [])
        tools_choose  = profs.get("tools_choose")
        lang_count    = profs.get("languages", 0)
        lang_exotic   = profs.get("languages_exotic", False)

        section("PROFICIENCIES")
        skill_parts = list(skills_fixed)
        if skills_choose:
            skill_parts.append(f"choose {skills_choose['count']} from "
                               f"{', '.join(skills_choose['from'])}")
        txt.insert("end", f"  Skills: {', '.join(skill_parts) if skill_parts else 'None'}\n")

        tool_parts = list(tools_fixed)
        if tools_choose:
            tool_parts.append(f"choose {tools_choose['count']} {tools_choose.get('label','tool')}")
        txt.insert("end", f"  Tools: {', '.join(tool_parts) if tool_parts else 'None'}\n")

        if lang_count:
            kind = "exotic language" if lang_exotic else "language"
            txt.insert("end", f"  Languages: {lang_count} {kind}{'s' if lang_count > 1 else ''} of your choice\n")
        else:
            txt.insert("end", "  Languages: None\n")

        if feature:
            feat_name, feat_desc = feature
            section(f"FEATURE: {feat_name.upper()}")
            txt.insert("end", f"  {feat_desc}\n")

        txt.config(state="disabled")
        _btn(d, "Close", d.destroy, bg=BTN_BG).pack(pady=6)
        d.wait_window()

    # ── 1. BASIC INFO ─────────────────────────────────────────────────────────

    def _dlg_basic_info(self):
        d = self._dlg("Basic Info", 700, 520)
        self._dlg_hdr(d, "⚔  BASIC INFORMATION")

        body = tk.Frame(d, bg=BG)
        body.pack(fill="both", expand=True, padx=20, pady=10)

        def lrow(label):
            f = tk.Frame(body, bg=BG)
            f.pack(fill="x", pady=5)
            tk.Label(f, text=label, font=FONT_SM, bg=BG, fg=DIM,
                     width=16, anchor="w").pack(side="left")
            return f

        nf = lrow("Character Name")
        name_var = tk.StringVar(value=self.char["name"])
        tk.Entry(nf, textvariable=name_var, bg=INPUT_BG, fg=FG, font=FONT_BODY,
                 insertbackground=FG, relief="flat", bd=4, width=28).pack(side="left")

        race_var  = tk.StringVar(value=self.char["race"])
        class_var = tk.StringVar(value=self.char["class"])
        sub_var   = tk.StringVar(value=self.char.get("subclass", ""))
        bg_var    = tk.StringVar(value=self.char["background"])
        aln_var   = tk.StringVar(value=self.char["alignment"])
        level_var = tk.IntVar(value=self.char["level"] or 1)

        def picker_row(label, options, var):
            f = lrow(label)
            tk.Label(f, textvariable=var, bg=ACCENT, fg="#1a1a2e",
                     font=("Segoe UI", 10, "bold"), padx=8, pady=2).pack(side="left")
            _btn(f, "Change", lambda o=options, v=var, lbl=label:
                 _pick_from_list(d, f"Select {lbl}", o, v),
                 bg=BTN_BG).pack(side="left", padx=6)

        rf = lrow("Race")
        tk.Label(rf, textvariable=race_var, bg=ACCENT, fg="#1a1a2e",
                 font=("Segoe UI", 10, "bold"), padx=8, pady=2).pack(side="left")
        _btn(rf, "Change",
             lambda: _pick_from_list(d, "Select Race", RACES, race_var,
                                     detail_fn=self._show_race_details),
             bg=BTN_BG).pack(side="left", padx=6)

        cf = lrow("Class")
        tk.Label(cf, textvariable=class_var, bg=ACCENT, fg="#1a1a2e",
                 font=("Segoe UI", 10, "bold"), padx=8, pady=2).pack(side="left")
        _btn(cf, "Change", lambda: _pick_from_list(d, "Select Class", CLASSES, class_var),
             bg=BTN_BG).pack(side="left", padx=6)

        sf = lrow("Subclass")
        tk.Label(sf, textvariable=sub_var, bg=BTN_BG, fg=FG,
                 font=FONT_BODY, padx=8, pady=2).pack(side="left")

        def pick_subclass():
            subs = SUBCLASSES.get(class_var.get(), [])
            if not subs:
                messagebox.showinfo("No Subclasses",
                                    f"{class_var.get() or 'This class'} has no listed subclasses.",
                                    parent=d)
                return
            _pick_from_list(d, "Select Subclass", subs, sub_var)

        class_var.trace_add("write", lambda *_: sub_var.set(""))
        _btn(sf, "Choose", pick_subclass, bg=BTN_BG).pack(side="left", padx=6)

        def _refresh_subclass_row(*_):
            if level_var.get() >= 3:
                sf.pack(fill="x", pady=2, after=cf)
            else:
                sf.pack_forget()
                sub_var.set("")

        level_var.trace_add("write", _refresh_subclass_row)
        _refresh_subclass_row()

        bf = lrow("Background")
        tk.Label(bf, textvariable=bg_var, bg=ACCENT, fg="#1a1a2e",
                 font=("Segoe UI", 10, "bold"), padx=8, pady=2).pack(side="left")
        _btn(bf, "Change",
             lambda: _pick_from_list(d, "Select Background", BACKGROUNDS, bg_var,
                                     detail_fn=self._show_background_details),
             bg=BTN_BG).pack(side="left", padx=6)
        picker_row("Alignment",  DND_ALIGNMENTS, aln_var)

        lf = lrow("Level / XP")
        xp_var = tk.IntVar(value=self.char["experience"])
        tk.Label(lf, text="Level:", font=FONT_SM, bg=BG, fg=DIM).pack(side="left")
        tk.Spinbox(lf, from_=1, to=20, textvariable=level_var, width=4,
                   bg=INPUT_BG, fg=FG, font=FONT_BODY,
                   buttonbackground=BTN_BG, relief="flat").pack(side="left", padx=4)
        tk.Label(lf, text="XP:", font=FONT_SM, bg=BG, fg=DIM).pack(side="left", padx=(8, 0))
        tk.Spinbox(lf, from_=0, to=999999, textvariable=xp_var, width=8,
                   bg=INPUT_BG, fg=FG, font=FONT_BODY,
                   buttonbackground=BTN_BG, relief="flat").pack(side="left", padx=4)

        def on_save():
            self.char["name"]       = name_var.get().strip()
            self.char["race"]       = race_var.get()
            self.char["class"]      = class_var.get()
            self.char["subclass"]   = sub_var.get()
            self.char["background"] = bg_var.get()
            self.char["alignment"]  = aln_var.get()
            self.char["level"]      = level_var.get()
            self.char["experience"] = xp_var.get()
            self._mark_done("Basic Info",
                            bool(self.char["name"] and self.char["race"] and self.char["class"]))
            self._refresh_preview()
            d.destroy()

        self._ok_cancel(d, on_save)
        d.wait_window()

    # ── 2. ABILITY SCORES ─────────────────────────────────────────────────────

    def _dlg_ability_scores(self):
        d = self._dlg("Ability Scores", 780, 520)
        self._dlg_hdr(d, "⚄  ABILITY SCORES")

        race        = self.char["race"]
        cls         = self.char["class"]
        racial_data = RACIAL_BONUSES.get(race, {})
        racial      = racial_data.get("fixed", {})
        racial_flex = racial_data.get("flexible")
        primary     = CLASS_PRIMARY_STATS.get(cls, [])
        saves       = CLASS_SAVING_THROWS.get(cls, [])

        existing_flex = self.char.get("_flex_racial_picks", [])
        flex_pick_vars = []

        mode_var  = tk.StringVar(value="standard")
        base_vars = {}
        sa_vars   = {}
        for ab in ABILITIES:
            fixed_b = racial.get(ab, 0)
            flex_b  = (existing_flex.count(ab) * racial_flex["amount"]
                       if racial_flex else 0)
            current = self.char["abilities"].get(ab, 10)
            base_vars[ab] = tk.IntVar(value=max(1, current - fixed_b - flex_b))
            sa_vars[ab]   = tk.StringVar(value="—")

        top = tk.Frame(d, bg=BG)
        top.pack(fill="x", padx=16, pady=6)
        for txt, val in [("Standard Array","standard"),("Point Buy","pointbuy"),("Manual","manual")]:
            tk.Radiobutton(top, text=txt, variable=mode_var, value=val,
                           bg=BG, fg=FG, selectcolor=INPUT_BG, activebackground=BG,
                           font=FONT_BODY).pack(side="left", padx=10)

        status_lbl = tk.Label(d, text="", font=FONT_SM, bg=BG, fg=ACCENT)
        status_lbl.pack(anchor="w", padx=16)

        grid = tk.Frame(d, bg=BG)
        grid.pack(fill="x", padx=16, pady=4)
        for col, txt in enumerate(["Ability","Base Score","Racial Bonus","Total","Mod","Role"]):
            tk.Label(grid, text=txt, font=("Segoe UI",9,"bold"),
                     bg=BG, fg=DIM, width=11).grid(row=0, column=col, padx=2, pady=2)

        total_lbls = {}
        mod_lbls   = {}
        sa_menus   = {}
        pb_spins   = {}

        for i, ab in enumerate(ABILITIES):
            r = i + 1
            bonus = racial.get(ab, 0)
            flex_note = " +flex" if racial_flex and ab not in racial_flex.get("exclude", []) else ""
            if ab in primary:  role, rcol = "* Primary", ACCENT
            elif ab in saves:  role, rcol = "o Save",    BLUE
            else:              role, rcol = "",           DIM

            tk.Label(grid, text=ABILITY_LABELS[ab], font=FONT_BODY, bg=BG, fg=FG,
                     width=13, anchor="w").grid(row=r, column=0, padx=2, pady=3, sticky="w")

            options = ["—"] + [str(v) for v in STANDARD_ARRAY]
            om = tk.OptionMenu(grid, sa_vars[ab], *options)
            om.config(bg=INPUT_BG, fg=FG, font=FONT_BODY, relief="flat",
                      activebackground=ACCENT, activeforeground="#1a1a2e",
                      highlightthickness=0, bd=0, width=6)
            om["menu"].config(bg=INPUT_BG, fg=FG, font=FONT_BODY)
            om.grid(row=r, column=1, padx=2, pady=2)
            sa_menus[ab] = om

            sp = tk.Spinbox(grid, from_=1, to=30, textvariable=base_vars[ab], width=7,
                            bg=INPUT_BG, fg=FG, font=FONT_BODY,
                            buttonbackground=BTN_BG, relief="flat")
            sp.grid(row=r, column=1, padx=2, pady=2)
            pb_spins[ab] = sp

            rb = (f"+{bonus}" if bonus > 0 else (str(bonus) if bonus < 0 else "")) + flex_note
            rb = rb or "—"
            tk.Label(grid, text=rb, font=FONT_BODY, bg=BG,
                     fg=GREEN if (bonus > 0 or flex_note) else (RED if bonus < 0 else DIM),
                     width=8).grid(row=r, column=2, padx=2)

            tl = tk.Label(grid, text="—", font=("Segoe UI",10,"bold"), bg=BG, fg=FG, width=6)
            tl.grid(row=r, column=3, padx=2)
            total_lbls[ab] = tl

            ml = tk.Label(grid, text="—", font=FONT_BODY, bg=BG, fg=DIM, width=6)
            ml.grid(row=r, column=4, padx=2)
            mod_lbls[ab] = ml

            tk.Label(grid, text=role, font=FONT_SM, bg=BG, fg=rcol, width=10).grid(row=r, column=5, padx=2)

        def refresh(*_):
            mode = mode_var.get()
            for ab in ABILITIES:
                sa_menus[ab].grid_remove()
                pb_spins[ab].grid_remove()
                if mode == "standard":
                    sa_menus[ab].grid()
                    v = sa_vars[ab].get()
                    if v and v != "—":
                        try: base_vars[ab].set(int(v))
                        except ValueError: pass
                else:
                    lo = 8 if mode == "pointbuy" else 1
                    hi = 15 if mode == "pointbuy" else 30
                    pb_spins[ab].config(from_=lo, to=hi)
                    pb_spins[ab].grid()
            if mode == "standard":
                assigned = [sa_vars[a].get() for a in ABILITIES if sa_vars[a].get() not in ("","—")]
                rem = list(STANDARD_ARRAY)
                for x in assigned:
                    try: rem.remove(int(x))
                    except ValueError: pass
                status_lbl.config(text=f"Remaining pool: {rem}", fg=ACCENT)
                for ab in ABILITIES:
                    taken = {sa_vars[a].get() for a in ABILITIES
                             if a != ab and sa_vars[a].get() not in ("", "—")}
                    available = ["—"] + [str(v) for v in STANDARD_ARRAY if str(v) not in taken]
                    menu = sa_menus[ab]["menu"]
                    menu.delete(0, "end")
                    for opt in available:
                        menu.add_command(label=opt,
                                         command=lambda v=opt, var=sa_vars[ab]: var.set(v))
            elif mode == "pointbuy":
                cost = sum(POINT_BUY_COSTS.get(base_vars[a].get(), 0) for a in ABILITIES)
                rem  = POINT_BUY_BUDGET - cost
                status_lbl.config(text=f"Points remaining: {rem}/{POINT_BUY_BUDGET}",
                                  fg=GREEN if rem >= 0 else RED)
            else:
                status_lbl.config(text="Enter any values (1-30).", fg=DIM)
            for ab in ABILITIES:
                base  = base_vars[ab].get()
                total = base + racial.get(ab, 0)
                if racial_flex:
                    total += sum(racial_flex["amount"]
                                 for pv in flex_pick_vars if pv.get() == ab)
                m = modifier(total)
                total_lbls[ab].config(text=str(total))
                mod_lbls[ab].config(text=f"{m:+d}",
                                    fg=GREEN if m > 0 else (RED if m < 0 else DIM))

        mode_var.trace_add("write", refresh)
        for ab in ABILITIES:
            base_vars[ab].trace_add("write", refresh)
            sa_vars[ab].trace_add("write", refresh)

        if racial_flex:
            count   = racial_flex["count"]
            amount  = racial_flex["amount"]
            exclude = set(racial_flex.get("exclude", []))
            avail   = [ab for ab in ABILITIES if ab not in exclude]
            ff = tk.Frame(d, bg=BG, padx=16)
            ff.pack(fill="x", pady=4)
            excl_note = (f" — not {', '.join(ABILITY_LABELS[e] for e in exclude)}"
                         if exclude else "")
            tk.Label(ff,
                     text=f"Choose {count} abilit{'y' if count==1 else 'ies'} "
                          f"for +{amount} each{excl_note}:",
                     font=FONT_SM, bg=BG, fg=ACCENT).pack(anchor="w", pady=2)
            fr = tk.Frame(ff, bg=BG)
            fr.pack(fill="x")
            for i in range(count):
                cur = existing_flex[i] if i < len(existing_flex) else "—"
                pv  = tk.StringVar(value=cur)
                tk.Label(fr, text=f"  Choice {i+1}:", font=FONT_SM,
                         bg=BG, fg=DIM).pack(side="left")
                om = tk.OptionMenu(fr, pv, *["—"] + avail)
                om.config(bg=INPUT_BG, fg=FG, font=FONT_BODY, relief="flat",
                          activebackground=ACCENT, activeforeground="#1a1a2e",
                          highlightthickness=0, bd=0)
                om["menu"].config(bg=INPUT_BG, fg=FG, font=FONT_BODY)
                om.pack(side="left", padx=4)
                pv.trace_add("write", refresh)
                flex_pick_vars.append(pv)

        refresh()

        def on_save():
            mode = mode_var.get()
            flex_picks = [pv.get() for pv in flex_pick_vars]
            self.char["_flex_racial_picks"] = [p for p in flex_picks if p != "—"]
            for ab in ABILITIES:
                fixed_b = racial.get(ab, 0)
                flex_b  = (sum(racial_flex["amount"] for pv in flex_pick_vars
                               if pv.get() == ab)
                           if racial_flex else 0)
                if mode == "standard":
                    v = sa_vars[ab].get()
                    base = int(v) if v not in ("","—") else 10
                else:
                    base = base_vars[ab].get()
                self.char["abilities"][ab] = base + fixed_b + flex_b
            self._mark_done("Ability Scores", True)
            self._refresh_preview()
            d.destroy()

        self._ok_cancel(d, on_save)
        d.wait_window()

    # ── 3. PROFICIENCIES ──────────────────────────────────────────────────────

    def _dlg_proficiencies(self):
        d = self._dlg("Proficiencies", 840, 620)
        self._dlg_hdr(d, "PROFICIENCIES")

        c       = self.char
        cls     = c["class"]
        race    = c["race"]
        bg_name = c["background"]
        class_saves   = CLASS_SAVING_THROWS.get(cls, [])
        class_skill_d = CLASS_SKILLS.get(cls, {"count": 2, "from": "any"})
        auto_armor    = list(CLASS_ARMOR_PROFS.get(cls, []))
        auto_weapon   = list(CLASS_WEAPON_PROFS.get(cls, []))
        race_langs    = list(RACE_LANGUAGES.get(race, ["Common"]))
        extra_langs   = RACE_EXTRA_LANGUAGES.get(race, 0)
        bg_data       = BACKGROUND_PROFICIENCIES.get(bg_name, {})
        bg_skills_fix = bg_data.get("skills_fixed", [])
        bg_tools_fix  = bg_data.get("tools_fixed", [])
        nb = self._notebook(d)

        t1 = tk.Frame(nb, bg=BG)
        nb.add(t1, text="Saving Throws")
        tk.Label(t1, text=f"Class auto: {', '.join(s.capitalize() for s in class_saves) or 'none'}",
                 font=FONT_SM, bg=BG, fg=DIM).pack(anchor="w", padx=12, pady=6)
        save_vars = {}
        for ab in ABILITIES:
            auto = ab in class_saves
            var  = tk.BooleanVar(value=(ab in c.get("saving_throw_proficiencies",[]) or auto))
            f    = tk.Frame(t1, bg=BG)
            f.pack(anchor="w", padx=16, pady=2)
            cb = tk.Checkbutton(f, text=ABILITY_LABELS[ab], variable=var,
                                bg=BG, fg=FG, selectcolor=INPUT_BG, activebackground=BG,
                                font=FONT_BODY, state="disabled" if auto else "normal")
            cb.pack(side="left")
            if auto:
                tk.Label(f, text="(class)", font=FONT_SM, bg=BG, fg=DIM).pack(side="left", padx=4)
            save_vars[ab] = var

        t2 = tk.Frame(nb, bg=BG)
        nb.add(t2, text="Skills")
        sk_count = class_skill_d.get("count", 2)
        sk_from  = class_skill_d.get("from", "any")
        pool_txt = "any skill" if sk_from == "any" else f"{len(sk_from)} options"
        hdr2 = f"Choose {sk_count} from {pool_txt}"
        if bg_skills_fix:
            hdr2 += f"\nBackground auto-grants: {', '.join(bg_skills_fix)}"
        tk.Label(t2, text=hdr2, font=FONT_SM, bg=BG, fg=DIM).pack(anchor="w", padx=12, pady=6)
        sk_frame, sk_lb = _listbox(t2, ALL_SKILLS, height=14, width=30, multi=True)
        sk_frame.pack(padx=12, pady=4, fill="x")
        existing_skills = set(c.get("skill_proficiencies", []))
        for i, sk in enumerate(ALL_SKILLS):
            if sk in existing_skills or sk in bg_skills_fix:
                sk_lb.selection_set(i)
        cnt_lbl = tk.Label(t2, text="", font=FONT_SM, bg=BG, fg=ACCENT)
        cnt_lbl.pack(anchor="w", padx=12)
        def update_sk_count(*_):
            sel = sk_lb.curselection()
            bg_sel = sum(1 for s in bg_skills_fix
                         if s in ALL_SKILLS and ALL_SKILLS.index(s) in sel)
            chosen = len(sel) - bg_sel
            cnt_lbl.config(text=f"Class skills chosen: {chosen}/{sk_count}",
                           fg=GREEN if chosen <= sk_count else RED)
        sk_lb.bind("<<ListboxSelect>>", update_sk_count)
        update_sk_count()

        t3 = tk.Frame(nb, bg=BG)
        nb.add(t3, text="Languages")
        tk.Label(t3, text=f"Race grants: {', '.join(race_langs)}"
                          + (f"  +{extra_langs} extra" if extra_langs else ""),
                 font=FONT_SM, bg=BG, fg=DIM).pack(anchor="w", padx=12, pady=6)
        lg_frame, lg_lb = _listbox(t3, ALL_LANGUAGES, height=14, width=30, multi=True)
        lg_frame.pack(padx=12, pady=4, fill="x")
        existing_langs = set(c.get("languages", []))
        for i, lang in enumerate(ALL_LANGUAGES):
            if lang in existing_langs or lang in race_langs:
                lg_lb.selection_set(i)

        t4 = tk.Frame(nb, bg=BG)
        nb.add(t4, text="Armor & Weapons")
        tk.Label(t4, text=f"Class auto: {', '.join(auto_armor + auto_weapon) or 'none'}",
                 font=FONT_SM, bg=BG, fg=DIM, wraplength=560).pack(anchor="w", padx=12, pady=6)
        armor_vars  = {}
        weapon_vars = {}
        for container, items, var_dict, label in [
            (t4, ["Light","Medium","Heavy","Shields"], armor_vars, "Armor:"),
            (t4, WEAPON_CATEGORIES, weapon_vars, "Weapons:"),
        ]:
            auto_list = auto_armor if label == "Armor:" else auto_weapon
            existing_list = c.get("armor_proficiencies",[]) if label=="Armor:" else c.get("weapon_proficiencies",[])
            frm = tk.Frame(container, bg=BG)
            frm.pack(anchor="w", padx=12, pady=4)
            tk.Label(frm, text=label, font=("Segoe UI",9,"bold"), bg=BG, fg=DIM).pack(anchor="w")
            for it in items:
                auto = it in auto_list
                var  = tk.BooleanVar(value=(auto or it in existing_list))
                f2   = tk.Frame(frm, bg=BG)
                f2.pack(anchor="w", padx=8, pady=1)
                cb = tk.Checkbutton(f2, text=it, variable=var,
                                    bg=BG, fg=FG, selectcolor=INPUT_BG, activebackground=BG,
                                    font=FONT_BODY, state="disabled" if auto else "normal")
                cb.pack(side="left")
                if auto:
                    tk.Label(f2, text="(class)", font=FONT_SM, bg=BG, fg=DIM).pack(side="left")
                var_dict[it] = var

        t5 = tk.Frame(nb, bg=BG)
        nb.add(t5, text="Tools")
        all_tools = ARTISAN_TOOLS + GAMING_SETS + MUSICAL_INSTRUMENTS
        tk.Label(t5, text=("Background auto-grants: " + ", ".join(bg_tools_fix)) if bg_tools_fix
                           else "No automatic tool proficiencies.",
                 font=FONT_SM, bg=BG, fg=DIM).pack(anchor="w", padx=12, pady=6)
        tl_frame, tl_lb = _listbox(t5, all_tools, height=14, width=36, multi=True)
        tl_frame.pack(padx=12, pady=4, fill="x")
        existing_tools = set(c.get("tool_proficiencies", []))
        for i, t in enumerate(all_tools):
            if t in existing_tools or t in bg_tools_fix:
                tl_lb.selection_set(i)

        def on_save():
            c["saving_throw_proficiencies"] = [ab for ab in ABILITIES if save_vars[ab].get()]
            c["skill_proficiencies"]        = [ALL_SKILLS[i] for i in sk_lb.curselection()]
            c["languages"]                  = [ALL_LANGUAGES[i] for i in lg_lb.curselection()]
            c["armor_proficiencies"]        = [at for at, v in armor_vars.items() if v.get()]
            c["weapon_proficiencies"]       = [wt for wt, v in weapon_vars.items() if v.get()]
            c["tool_proficiencies"]         = [all_tools[i] for i in tl_lb.curselection()]
            self._mark_done("Proficiencies", True)
            self._refresh_preview()
            d.destroy()

        self._ok_cancel(d, on_save)
        d.wait_window()

    # ── 5. SPELLCASTING ───────────────────────────────────────────────────────

    def _dlg_spellcasting(self):
        d   = self._dlg("Spellcasting", 900, 640)
        self._dlg_hdr(d, "SPELLCASTING")

        c     = self.char
        cls   = c["class"]
        lvl   = c["level"] or 1
        sc_d  = CLASS_SPELLCASTING.get(cls)
        ex_sc = c.get("spellcasting", {})

        if not sc_d:
            tk.Label(d, text=f"{cls or 'This class'} cannot cast spells.",
                     font=FONT_BODY, bg=BG, fg=DIM).pack(pady=40)
            _btn(d, "OK", d.destroy, bg=BTN_BG).pack()
            d.wait_window()
            return

        sc_ability = sc_d["ability"]
        sc_type    = sc_d["type"]
        ab_mod     = modifier(c["abilities"].get(sc_ability, 10))
        pb         = proficiency_bonus(lvl)
        save_dc    = 8 + pb + ab_mod
        atk_bonus  = pb + ab_mod

        if sc_type == "full":
            slots_row = FULL_CASTER_SLOTS.get(lvl, [0]*9)
        elif sc_type == "half":
            slots_row = HALF_CASTER_SLOTS.get(lvl, [0]*9)
        elif sc_type == "warlock":
            wk_cnt, wk_lvl = WARLOCK_SLOTS.get(lvl, (0,0))
            slots_row = [0]*9
            if wk_lvl > 0:
                slots_row[wk_lvl-1] = wk_cnt
        else:
            slots_row = [0]*9

        known_names = {s["name"] for s in ex_sc.get("spells_known", [])}
        known_lvl0  = {s["name"] for s in ex_sc.get("spells_known", []) if s["level"] == 0}

        info_f = tk.Frame(d, bg=BG)
        info_f.pack(fill="x", padx=16, pady=4)
        tk.Label(info_f,
                 text=f"Ability: {sc_ability.capitalize()}  |  Save DC: {save_dc}  |  "
                      f"Attack: {atk_bonus:+d}  |  Type: {sc_type}",
                 font=FONT_SM, bg=BG, fg=ACCENT).pack(side="left")

        slots_f = tk.Frame(d, bg=BG)
        slots_f.pack(fill="x", padx=16, pady=2)
        slot_used_vars = []
        for i, cnt in enumerate(slots_row, start=1):
            if cnt == 0:
                continue
            sf = tk.Frame(slots_f, bg=BTN_BG, padx=6, pady=3)
            sf.pack(side="left", padx=3)
            tk.Label(sf, text=f"Lvl {i}", font=("Segoe UI",8,"bold"), bg=BTN_BG, fg=DIM).pack()
            tk.Label(sf, text=str(cnt), font=("Segoe UI",11,"bold"), bg=BTN_BG, fg=ACCENT).pack()
            used = ex_sc.get("slots",{}).get(str(i),{}).get("used",0)
            uv = tk.IntVar(value=used)
            tk.Spinbox(sf, from_=0, to=cnt, textvariable=uv, width=3,
                       bg=INPUT_BG, fg=FG, font=FONT_SM,
                       buttonbackground=BTN_BG, relief="flat").pack()
            slot_used_vars.append((i, cnt, uv))

        nb = self._notebook(d)

        ct = tk.Frame(nb, bg=BG)
        nb.add(ct, text="Cantrips")
        cantr_data = SPELL_CANTRIPS.get(cls, [])
        ctips_max_d = CANTRIPS_KNOWN.get(sc_type, {})
        max_c = max((v for k,v in ctips_max_d.items() if lvl >= k), default=2)
        tk.Label(ct, text=f"Max cantrips at level {lvl}: {max_c}",
                 font=FONT_SM, bg=BG, fg=DIM).pack(anchor="w", padx=8, pady=4)
        cf2, c_lb = _listbox(ct, [x[0] for x in cantr_data], height=11, width=32, multi=True)
        cf2.pack(padx=8, fill="x")
        for i, (name, *_) in enumerate(cantr_data):
            if name in known_lvl0:
                c_lb.selection_set(i)

        spell_tabs = {}
        cls_spells = SPELL_LISTS.get(cls, {})
        for sl in range(1, 10):
            spells_at = cls_spells.get(sl, [])
            if not spells_at:
                continue
            cnt = slots_row[sl-1] if sl <= len(slots_row) else 0
            st = tk.Frame(nb, bg=BG)
            nb.add(st, text=f"Level {sl}")
            tk.Label(st, text=f"Slots at level {lvl}: {cnt}",
                     font=FONT_SM, bg=BG, fg=DIM).pack(anchor="w", padx=8, pady=4)
            sf2, slb = _listbox(st, [s[0] for s in spells_at], height=11, width=32, multi=True)
            sf2.pack(padx=8, fill="x")
            for i, (name, *_) in enumerate(spells_at):
                if name in known_names:
                    slb.selection_set(i)
            spell_tabs[sl] = (spells_at, slb)

        def on_save():
            spells_known = []
            for i in c_lb.curselection():
                name, school, *_ = cantr_data[i]
                spells_known.append({"name":name,"level":0,"school":school,"description":""})
            for sl, (data, lb) in spell_tabs.items():
                for i in lb.curselection():
                    name, school, *_ = data[i]
                    spells_known.append({"name":name,"level":sl,"school":school,"description":""})
            slots_dict = {str(i):{"total":cnt,"used":uv.get()} for i,cnt,uv in slot_used_vars}
            c["spellcasting"] = {
                "enabled": True, "ability": sc_ability,
                "spell_save_dc": save_dc, "attack_bonus": atk_bonus,
                "slots": slots_dict, "spells_known": spells_known,
            }
            self._mark_done("Spellcasting", True)
            self._refresh_preview()
            d.destroy()

        self._ok_cancel(d, on_save)
        d.wait_window()

    # ── 7. EQUIPMENT ──────────────────────────────────────────────────────────

    def _dlg_equipment(self):
        d = self._dlg("Equipment", 820, 600)
        self._dlg_hdr(d, "EQUIPMENT")

        c         = self.char
        cls       = c["class"]
        equipment = [dict(e) for e in c.get("equipment", [])]
        currency  = dict(c.get("currency", {"cp":0,"sp":0,"ep":0,"gp":0,"pp":0}))
        start_gp  = CLASS_STARTING_GOLD.get(cls, 75)

        armor_row = tk.Frame(d, bg=BG, padx=20, pady=6)
        armor_row.pack(fill="x")
        tk.Label(armor_row, text="Worn Armor:", font=FONT_SM, bg=BG, fg=DIM,
                 width=14, anchor="w").pack(side="left")
        armor_name_var = tk.StringVar(value=c.get("_armor_name", ""))
        tk.Label(armor_row, textvariable=armor_name_var, font=FONT_SM,
                 bg=BTN_BG, fg=FG, padx=8, pady=2, width=22, anchor="w").pack(side="left")
        armor_names = list(ARMOR_TABLE.keys()) + ["Unarmored"]
        _btn(armor_row, "Pick",
             lambda: _pick_from_list(d, "Select Armor", armor_names, armor_name_var),
             bg=BTN_BG).pack(side="left", padx=6)
        _btn(armor_row, "Clear", lambda: armor_name_var.set(""), bg=BTN_BG).pack(side="left")
        tk.Frame(d, bg=PANEL, height=1).pack(fill="x", padx=12)

        nb = self._notebook(d)

        tw = tk.Frame(nb, bg=BG)
        nb.add(tw, text="Weapons")

        avail_weapons = [(name, data) for name, data in WEAPONS.items()
                         if _weapon_proficient(cls, name, data["cat"])] if cls else list(WEAPONS.items())
        avail_names   = [name for name, _ in avail_weapons]

        hdr_text = (f"{cls} weapon proficiencies ({len(avail_names)} weapons)"
                    if cls else "All weapons — set a class in Basic Info to filter")
        tk.Label(tw, text=hdr_text, font=FONT_SM, bg=BG, fg=DIM).pack(anchor="w", padx=12, pady=(6,2))

        tw_body = tk.Frame(tw, bg=BG)
        tw_body.pack(fill="both", expand=True, padx=8, pady=4)

        wf, wlb = _listbox(tw_body, avail_names, height=12, width=26)
        wf.pack(side="left", fill="y")

        det_f = tk.Frame(tw_body, bg=BG)
        det_f.pack(side="left", fill="both", expand=True, padx=12)
        det_lbl = tk.Label(det_f, text="Select a weapon for details.",
                           font=FONT_SM, bg=BG, fg=DIM, justify="left",
                           wraplength=220, anchor="nw")
        det_lbl.pack(anchor="nw", pady=4)

        def on_wep_select(*_):
            sel = wlb.curselection()
            if not sel:
                return
            wname = avail_names[sel[0]]
            w     = WEAPONS[wname]
            props = ", ".join(w.get("props", [])) or "—"
            already = any(e["name"] == wname for e in equipment)
            status  = "  [already in equipment]" if already else ""
            det_lbl.config(
                text=f"{wname}{status}\n\nDamage:  {w['damage']} {w['type']}\n"
                     f"Category: {w['cat']}\nProperties: {props}",
                fg=ACCENT if already else FG,
            )

        wlb.bind("<<ListboxSelect>>", on_wep_select)

        def add_weapon_to_equip():
            sel = wlb.curselection()
            if not sel:
                return
            wname = avail_names[sel[0]]
            if not any(e["name"] == wname for e in equipment):
                equipment.append({"name": wname, "quantity": 1, "weight": 0, "notes": ""})
                on_wep_select()
                refresh_equip()
            nb.select(1)

        _btn(det_f, "+ Add to Equipment", add_weapon_to_equip, bg="#1e4620").pack(anchor="w", pady=6)

        t1 = tk.Frame(nb, bg=BG)
        nb.add(t1, text="Equipment Packs")
        tk.Label(t1, text=f"Starting gold for {cls or 'class'}: {start_gp} gp",
                 font=FONT_SM, bg=BG, fg=DIM).pack(anchor="w", padx=12, pady=4)
        pack_vars = {}
        for pack_name, items in EQUIPMENT_PACKS.items():
            var = tk.BooleanVar(value=False)
            f   = tk.Frame(t1, bg=BG)
            f.pack(anchor="w", padx=12, pady=1)
            tk.Checkbutton(f, text=f"{pack_name}:", variable=var,
                           bg=BG, fg=FG, selectcolor=INPUT_BG, activebackground=BG,
                           font=FONT_BODY).pack(side="left")
            preview = ", ".join(items[:5]) + ("..." if len(items)>5 else "")
            tk.Label(f, text=preview, font=FONT_SM, bg=BG, fg=DIM).pack(side="left", padx=4)
            pack_vars[pack_name] = (var, items)

        def add_packs():
            added = 0
            for pn, (var, items) in pack_vars.items():
                if var.get():
                    for it in items:
                        if not any(e["name"]==it for e in equipment):
                            equipment.append({"name":it,"quantity":1,"weight":0,"notes":""})
                            added += 1
            refresh_equip()
            if added:
                messagebox.showinfo("Added", f"Added {added} items.", parent=d)

        _btn(t1, "+ Add Selected Packs", add_packs, bg="#1e4620").pack(anchor="w", padx=12, pady=8)

        t2 = tk.Frame(nb, bg=BG)
        nb.add(t2, text="Equipment List")
        eq_f = tk.Frame(t2, bg=INPUT_BG)
        eq_f.pack(fill="both", expand=True, padx=8, pady=4)

        def refresh_equip():
            for w in eq_f.winfo_children():
                w.destroy()
            for i, it in enumerate(equipment):
                f = tk.Frame(eq_f, bg=INPUT_BG)
                f.pack(fill="x", pady=1)
                tk.Label(f, text=f"{it['name']} x{it['quantity']}",
                         font=FONT_SM, bg=INPUT_BG, fg=FG, width=32, anchor="w").pack(side="left", padx=4)
                _btn(f, "x", lambda i=i: (equipment.pop(i), refresh_equip()),
                     bg="#3a1e1e", font=("Segoe UI",8)).pack(side="right", padx=2)

        add_r = tk.Frame(t2, bg=BG)
        add_r.pack(fill="x", padx=8, pady=4)
        item_e = tk.Entry(add_r, bg=INPUT_BG, fg=FG, font=FONT_BODY, width=20,
                          insertbackground=FG, relief="flat")
        item_e.pack(side="left", padx=4)
        item_e.insert(0,"Item name")
        qty_sp = tk.Spinbox(add_r, from_=1, to=999, width=4,
                            bg=INPUT_BG, fg=FG, font=FONT_BODY,
                            buttonbackground=BTN_BG, relief="flat")
        qty_sp.pack(side="left", padx=4)
        def add_item():
            name = item_e.get().strip()
            if not name or name=="Item name": return
            equipment.append({"name":name,"quantity":int(qty_sp.get()),"weight":0,"notes":""})
            refresh_equip()
        _btn(add_r, "+ Add", add_item, bg=BTN_BG).pack(side="left")
        refresh_equip()

        t3 = tk.Frame(nb, bg=BG)
        nb.add(t3, text="Currency")
        curr_vars = {}
        for coin in ["cp","sp","ep","gp","pp"]:
            cf = tk.Frame(t3, bg=BG)
            cf.pack(fill="x", padx=20, pady=6)
            tk.Label(cf, text=coin.upper(), font=FONT_BODY, bg=BG, fg=FG, width=5).pack(side="left")
            var = tk.IntVar(value=currency.get(coin,0))
            tk.Spinbox(cf, from_=0, to=99999, textvariable=var, width=8,
                       bg=INPUT_BG, fg=FG, font=FONT_BODY,
                       buttonbackground=BTN_BG, relief="flat").pack(side="left")
            curr_vars[coin] = var
        _btn(t3, f"Set to starting gold ({start_gp} gp)",
             lambda: curr_vars["gp"].set(start_gp), bg=BTN_BG).pack(anchor="w", padx=20, pady=6)

        def on_save():
            c["equipment"]    = equipment
            c["currency"]     = {coin: v.get() for coin, v in curr_vars.items()}
            c["_armor_name"]  = armor_name_var.get()
            self._mark_done("Equipment",
                            len(equipment)>0 or any(v.get()>0 for v in curr_vars.values()))
            self._refresh_preview()
            d.destroy()

        self._ok_cancel(d, on_save)
        d.wait_window()

    # ── 8. FEATURES & TRAITS ──────────────────────────────────────────────────

    def _dlg_features(self):
        d = self._dlg("Features & Traits", 820, 640)
        self._dlg_hdr(d, "FEATURES & TRAITS")

        c    = self.char
        cls  = c["class"]
        race = c["race"]
        bg_n = c["background"]
        lvl  = c["level"] or 1
        nb   = self._notebook(d)

        def ro_tab(parent, text_content):
            txt = tk.Text(parent, bg=INPUT_BG, fg=FG, font=FONT_SM,
                          relief="flat", bd=4, wrap="word", padx=8, pady=8)
            sb = tk.Scrollbar(parent, command=txt.yview, bg=BG, troughcolor=INPUT_BG)
            txt.config(yscrollcommand=sb.set)
            sb.pack(side="right", fill="y")
            txt.pack(fill="both", expand=True)
            txt.insert("1.0", text_content)
            txt.config(state="disabled")

        t1 = tk.Frame(nb, bg=BG)
        nb.add(t1, text="Racial Traits")
        traits = RACIAL_TRAITS.get(race, [])
        rt = f"=== {race or '(no race)'} ===\n\n"
        rt += "\n\n".join(f"> {n}\n  {desc}" for n, desc in traits) if traits else "No traits found."
        ro_tab(t1, rt)

        t2 = tk.Frame(nb, bg=BG)
        nb.add(t2, text="Class Features")
        cf_d = CLASS_FEATURES.get(cls, {})
        ct = f"=== {cls or '(no class)'} — Levels 1-{lvl} ===\n\n"
        for fl in range(1, lvl+1):
            feats = cf_d.get(fl, [])
            if feats:
                ct += f"Level {fl}:\n" + "".join(f"  * {f}\n" for f in feats) + "\n"
        if not cf_d:
            ct = "No class features found."
        ro_tab(t2, ct)

        t3 = tk.Frame(nb, bg=BG)
        nb.add(t3, text="Background Feature")
        bf = BACKGROUND_FEATURES.get(bg_n)
        if bf:
            feat_name, feat_desc = bf
            bt = f"=== {bg_n}: {feat_name} ===\n\n{feat_desc}"
        else:
            bt = f"No background feature found for {bg_n or '(no background)'}."
        ro_tab(t3, bt)

        t4 = tk.Frame(nb, bg=BG)
        nb.add(t4, text="Custom Features")
        custom = [dict(f) for f in c.get("features", [])]
        cf_frame = tk.Frame(t4, bg=INPUT_BG)
        cf_frame.pack(fill="both", expand=True, padx=8, pady=4)

        def refresh_cf():
            for w in cf_frame.winfo_children():
                w.destroy()
            for i, feat in enumerate(custom):
                f = tk.Frame(cf_frame, bg=INPUT_BG)
                f.pack(fill="x", pady=1)
                tk.Label(f, text=f"> {feat['name']} [{feat.get('source','')}]",
                         font=FONT_SM, bg=INPUT_BG, fg=FG).pack(side="left", padx=4)
                _btn(f, "x", lambda i=i: (custom.pop(i), refresh_cf()),
                     bg="#3a1e1e", font=("Segoe UI",8)).pack(side="right", padx=2)

        add_f = tk.Frame(t4, bg=BG)
        add_f.pack(fill="x", padx=8, pady=4)
        fn_e = tk.Entry(add_f, bg=INPUT_BG, fg=FG, font=FONT_SM, width=16,
                        insertbackground=FG, relief="flat")
        fn_e.pack(side="left", padx=2)
        fn_e.insert(0,"Feature name")
        fs_e = tk.Entry(add_f, bg=INPUT_BG, fg=FG, font=FONT_SM, width=10,
                        insertbackground=FG, relief="flat")
        fs_e.pack(side="left", padx=2)
        fs_e.insert(0,"Source")
        fd_e = tk.Entry(add_f, bg=INPUT_BG, fg=FG, font=FONT_SM, width=22,
                        insertbackground=FG, relief="flat")
        fd_e.pack(side="left", padx=2)
        fd_e.insert(0,"Description")

        def add_feat():
            name = fn_e.get().strip()
            if not name or name=="Feature name": return
            custom.append({"name":name,"source":fs_e.get().strip(),
                           "description":fd_e.get().strip(),"uses":None})
            refresh_cf()

        _btn(add_f, "+ Add", add_feat, bg=BTN_BG).pack(side="left", padx=4)
        refresh_cf()

        def on_save():
            c["features"] = custom
            self._mark_done("Features & Traits", True)
            self._refresh_preview()
            d.destroy()

        self._ok_cancel(d, on_save)
        d.wait_window()

    # ── 9. PERSONALITY ────────────────────────────────────────────────────────

    def _dlg_personality(self):
        d = self._dlg("Personality", 760, 580)
        self._dlg_hdr(d, "PERSONALITY & BACKSTORY")

        c    = self.char
        bg_n = c["background"]
        sugg = get_personality_suggestions(bg_n)
        txts = {}

        body = tk.Frame(d, bg=BG)
        body.pack(fill="both", expand=True, padx=14, pady=6)

        def make_field(label, key, height=2):
            hf = tk.Frame(body, bg=BG)
            hf.pack(fill="x", pady=2)
            tk.Label(hf, text=label, font=("Segoe UI",9,"bold"), bg=BG, fg=ACCENT).pack(side="left")
            slist = sugg.get(key, [])
            if slist:
                _btn(hf, "Suggestions",
                     lambda k=key, s=slist, lbl=label: _pick_suggestion(d, lbl, s, txts[k]),
                     bg=BTN_BG, font=FONT_SM).pack(side="right")
            t = tk.Text(body, height=height, bg=INPUT_BG, fg=FG, font=FONT_BODY,
                        relief="flat", bd=4, wrap="word", insertbackground=FG)
            t.pack(fill="x")
            t.insert("1.0", c.get(key,""))
            txts[key] = t

        make_field("Personality Traits", "personality_traits", 3)
        make_field("Ideals",             "ideals",             2)
        make_field("Bonds",              "bonds",              2)
        make_field("Flaws",              "flaws",              2)
        make_field("Backstory",          "backstory",          3)

        if bg_n and sugg:
            tk.Label(body, text=f"Suggestions from: {bg_n}",
                     font=FONT_SM, bg=BG, fg=DIM).pack(anchor="w", pady=4)

        def on_save():
            for key in ("personality_traits","ideals","bonds","flaws","backstory"):
                c[key] = txts[key].get("1.0","end").strip()
            self._mark_done("Personality", bool(c["personality_traits"]))
            self._refresh_preview()
            d.destroy()

        self._ok_cancel(d, on_save)
        d.wait_window()

    # ── BOTTOM BAR ACTIONS ────────────────────────────────────────────────────

    def _save_char(self):
        if not self.char["name"]:
            messagebox.showwarning("No Name", "Set a name in Basic Info first.", parent=self.root)
            return
        path = save_character(self.char)
        messagebox.showinfo("Saved", f"Saved to:\n{path}", parent=self.root)

    def _load_char(self):
        chars = list_characters()
        if not chars:
            messagebox.showinfo("No Characters", "No saved characters found.", parent=self.root)
            return
        d = self._dlg("Load Character", 360, 380)
        self._dlg_hdr(d, "LOAD CHARACTER")
        lf, lb = _listbox(d, chars, height=14, width=30)
        lf.pack(padx=16, pady=8, fill="x")

        def do_load():
            sel = lb.curselection()
            if not sel:
                return
            self.char = load_character(lb.get(sel[0]))
            for sec in self.SECTIONS:
                self._mark_done(sec, False)
            self._mark_done("Basic Info",    bool(self.char["name"]))
            self._mark_done("Ability Scores", any(v!=10 for v in self.char["abilities"].values()))
            self._mark_done("Proficiencies",  bool(self.char.get("skill_proficiencies")))
            self._mark_done("Spellcasting",   self.char.get("spellcasting",{}).get("enabled",False))
            self._mark_done("Equipment",      bool(self.char.get("equipment")))
            self._mark_done("Personality",    bool(self.char.get("personality_traits")))
            self._refresh_preview()
            d.destroy()

        _btn(d, "Load Selected", do_load, bg="#1e4620").pack(pady=6)
        d.wait_window()

    def _delete_char(self):
        name = self.char.get("name","")
        if not name:
            messagebox.showwarning("No Character", "No character loaded.", parent=self.root)
            return
        if not messagebox.askyesno("Delete", f"Delete '{name}'? Cannot be undone.", parent=self.root):
            return
        path = Path(__file__).parent.parent.parent.parent / "data" / "characters" / f"{name}.json"
        if path.exists():
            path.unlink()
        messagebox.showinfo("Deleted", f"'{name}' deleted.", parent=self.root)
        self.char = empty_character()
        for sec in self.SECTIONS:
            self._mark_done(sec, False)
        self._refresh_preview()

    def _new_char(self):
        if self.char.get("name"):
            if not messagebox.askyesno("New Character",
                                       f"Discard '{self.char['name']}'?", parent=self.root):
                return
        self.char = empty_character()
        for sec in self.SECTIONS:
            self._mark_done(sec, False)
        self._refresh_preview()

    def _quit(self):
        if messagebox.askyesno("Quit", "Quit the character builder?", parent=self.root):
            self.root.destroy()


def main():
    root = tk.Tk()
    root.title("D&D 5e Character Builder")
    root.configure(bg=BG)
    CharacterBuilderApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
