# D&D AI Dungeon Master — Project Context

## Security Constraint (NEVER SKIP)
**Always warn the user before making any Claude API calls that will cost tokens. Get explicit confirmation before proceeding.** This applies to any AI Dungeon Master calls, `dm.py` testing, or any Anthropic API invocation.

---

## Project Vision
A fully playable D&D 5e adventure game with an AI Dungeon Master. Currently a Python/Tkinter desktop app. The next major milestone is restructuring to MVC so the same game logic can power a future web frontend with no rewriting.

## Current File Structure (MVC — complete)
```
dndgame/
├── main.py                   # Entry point: python main.py → desktop app
│
├── models/                   # Pure logic — zero UI imports
│   ├── __init__.py
│   ├── character.py
│   ├── dice.py
│   ├── game_state.py
│   ├── combat.py
│   └── dm.py
│
├── controllers/              # Orchestrates models, returns plain dicts — no UI
│   ├── __init__.py
│   └── game_controller.py   # setup_combat, process_attack, process_skill_check,
│                            #   process_enemy_turn, process_death_save, ENEMY_STATS
│
├── views/
│   ├── desktop/              # Tkinter desktop app
│   │   ├── __init__.py
│   │   ├── app.py            # GameApp — pure UI, calls controller
│   │   ├── d20_roller.py     # 3D animated d20 roll window
│   │   └── character_builder/
│   │       ├── __init__.py
│   │       ├── character_builder_app.py
│   │       ├── dnd_data.py
│   │       ├── spells.py
│   │       ├── ddb_import.py
│   │       └── Launch Character Builder.bat
│   └── web/                  # Future web frontend
│       ├── __init__.py
│       └── api.py            # Flask/FastAPI stub — same controller calls, JSON responses
│
└── data/
    ├── characters/           # Saved character JSON files (gitignored)
    ├── sessions/             # Saved session JSON files (gitignored)
    ├── dm_config.json        # Gitignored — backend/API key config
    └── dm_config.example.json
```

### MVC Boundary Rules
- **Models** (`models/`): no `import tkinter`, no `import flask`, no `import requests` except in `dm.py`. Pure game logic only.
- **Controller** (`controllers/game_controller.py`): no UI imports. Takes dicts, returns dicts. A Flask endpoint and a Tkinter callback call the exact same controller functions.
- **Views** (`views/`): calls controller functions, renders the result. No game logic lives here.

### Controller API (game_controller.py)
```python
build_enemy_list(enemy_specs, player_level) -> list[dict]
process_action(session, char, dm, action_text) -> {"narration": str, "events": list}
start_combat(session, char, enemy_specs, player_level, d20_initiative) -> {"order": list, "display": str}
process_attack(session, char, weapon_name, target_name, d20_value) -> {"hit": bool, "damage": int, "narrative": str, ...}
process_skill_check(session, char, skill, dc, d20_value) -> {"success": bool, "total": int, "narrative": str}
process_enemy_turn(session) -> {"attacker": str, "narrative": str, "player_hp": int, ...}
process_death_save(session) -> {"outcome": str, "roll": int, "narrative": str}
```

---

## What Is COMPLETE

### `character.py`
- `empty_character()` — returns blank character dict with all fields
- `save_character(char)` / `load_character(name)` / `list_characters()`
- `modifier(score)` — D&D ability modifier formula
- `proficiency_bonus(level)` — standard 5e proficiency progression
- `SKILLS` dict, HP/rest/spell slot helpers
- Saves to `characters/<name>.json`

### `Character Builder/character_builder_app.py`
Complete GUI-driven Tkinter app. Launched via `python character_builder_app.py` or the .bat file.

**Architecture:** Single `CharacterBuilderApp` class, no threads, `self.char` dict held directly. Module-level helpers `_btn()`, `_listbox()`, `_pick_from_list()`, `_pick_suggestion()`, `_weapon_proficient()`.

**Main window:** Left panel (clickable section buttons showing ✔/· status), right panel (live character preview in Consolas font), bottom bar (Save/Load/Delete/New/Quit).

**Guard:** Clicking any section other than Basic Info before setting race and class redirects to Basic Info with a prompt. Race and class must be set first as they drive all other sections.

**Auto-derived stats (not editable sections):**
- **Combat Stats** — HP, AC, speed, initiative, hit die, and passive perception computed automatically on every refresh. AC handles Barbarian and Monk unarmored defense formulas.
- **Attacks** — Auto-generated from weapons in the Equipment list. Proficiency applied via `_weapon_proficient()`. Monk Unarmed Strike auto-added (Martial Arts die scales by level).

**7 clickable section dialogs (all modal Toplevels with grab_set):**
1. **Basic Info** — name, Race/Class/Subclass/Background/Alignment pickers, Level/XP spinboxes. Race and Background pickers include "Details" buttons. Subclass hidden below level 3.
2. **Ability Scores** — Standard Array, Point Buy, or Manual. Racial bonuses auto-applied. Flexible bonus pickers for Half-Elf and Human (Variant).
3. **Proficiencies** — Tabbed: Saving Throws, Skills, Languages, Armor & Weapons, Tools.
4. **Spellcasting** — Only for caster classes. Spell slots, cantrips, spells per level.
5. **Equipment** — Weapons, Equipment Packs, Item List, Currency. Worn Armor picker drives AC.
6. **Features & Traits** — Read-only: Racial Traits, Class Features, Background Feature, Custom.
7. **Personality** — Traits, ideals, bonds, flaws, backstory with background-based suggestions.

**Import path in Character Builder files:** `sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))` to reach the project root; imports use `from models.character import ...`.

### `Character Builder/dnd_data.py`
Comprehensive D&D 5e data. Key exports: `RACES` (28), `CLASSES` (13), `SUBCLASSES`, `BACKGROUNDS` (37), `RACIAL_BONUSES`, `RACE_DESCRIPTIONS`, `STANDARD_ARRAY`, `POINT_BUY_COSTS/BUDGET`, `ABILITIES`, `CLASS_PRIMARY_STATS`, `CLASS_SAVING_THROWS`, `BACKGROUND_PROFICIENCIES`, `ALL_SKILLS`, `ALL_LANGUAGES`, `CLASS_HIT_DICE`, `RACE_SPEED`, `ARMOR_TABLE`, `CLASS_SKILLS`, `CLASS_ARMOR_PROFS`, `CLASS_WEAPON_PROFS`, `CLASS_SPELLCASTING`, `FULL/HALF/WARLOCK_CASTER_SLOTS`, `WEAPONS`, `WEAPON_CATEGORIES`, `EQUIPMENT_PACKS`, `BACKGROUND_FEATURES`, `BACKGROUND_DESCRIPTIONS`, `RACIAL_TRAITS`, `CLASS_FEATURES`, `PERSONALITY_SUGGESTIONS`.

### `dice.py`
Pure logic dice engine — no API calls, no imports beyond `random` and `re`.
- `roll(sides)` — validates against `VALID_DICE = {4,6,8,10,12,20,100}`
- `roll_dice(notation)` — parses "2d6+3", "d20", "3d6-1". Returns `{notation, rolls, modifier, total}`
- `d20_check(modifier, advantage, disadvantage)` — Returns `{rolls, kept, modifier, total, nat20, nat1}`
- `damage(notation)` — alias for `roll_dice`
- `critical_damage(notation)` — doubles dice count. Returns `{..., critical: True}`
- `hit_die(die_str, con_mod)` — accepts "d8" or "1d8", regex parsing. Min total 1.
- `death_save()` — nat20 = revived, nat1 = double failure. Returns `{roll, success, critical, double_fail}`
- `initiative(dex_mod)` — Returns `{roll, modifier, total}`

### `combat.py`
Turn-based combat engine. Uses `dice.py`, `game_state.py`, `character.py`. No UI.

**Enemy format:** `{name, hp, max_hp, ac, initiative_mod, attacks: [{name, bonus, damage, damage_type}], is_player: False, conditions: [], xp}`

- `build_enemy(name, hp, ac, attacks, initiative_mod, xp)`
- `setup_combat(session, character, enemies, player_initiative=None)` — accepts pre-rolled initiative
- `resolve_attack(session, attacker, target, attack_bonus, damage_notation, advantage, disadvantage, d20_override=None)`
- `player_attack(session, character, weapon_name, target_name, advantage, disadvantage, d20_override=None)`
- `enemy_attack(session, enemy_name, attack_index)`
- `handle_death_save(session)` — returns `{..., outcome: "revived"/"stable"/"dead"/"ongoing"}`
- `end_turn(session)` / `combat_summary(session)` / `xp_from_combat(session)`

**Conditions:** Prone/Paralyzed/Stunned/Unconscious/Blinded → advantage to attackers; Prone/Blinded/Poisoned/Frightened/Restrained/Exhaustion → disadvantage on attacker.

### `game_state.py`
JSON session persistence to `sessions/<name>.json`.

**Session keys:** `character_name`, `session_name`, `location`, `scene`, `history` (list of `{role, text}`), `flags`, `current_hp`, `temp_hp`, `hit_dice_spent`, `spell_slots_used`, `conditions`, `death_saves`, `stable`, `in_combat`, `round`, `initiative_order`, `current_turn`.

- `empty_session` / `save_session` / `load_session` / `list_sessions` / `delete_session`
- `add_history` / `set_flag` / `get_flag`
- `init_hp` / `apply_damage` / `apply_healing`
- `use_spell_slot` / `restore_spell_slot`
- `long_rest` / `short_rest`
- `start_combat` / `end_combat` / `advance_turn` / `current_combatant`
- `apply_combat_damage` / `apply_combat_healing`
- `add_condition` / `remove_condition`
- `living_combatants` / `enemies_alive`

### `dm.py`
AI DM. Runs via Ollama (local). Config from `dm_config.json` (gitignored).

- `DungeonMaster(model)`
- `respond(session, character, player_input)` → `{"narration": str, "events": list}`
- `_parse_events(raw_text)` — extracts `[CHECK: Skill DC##]`, `[COMBAT: Name×N]`, `[SCENE: Location]`
- `from_config(path)` — loads model setting from config

### `d20_roller.py`
3D animated d20 roll window. Renders an icosahedron with perspective projection and gold shading.

**Architecture:**
- `ANIMATIONS` dict (module-level) — pre-computed at import time. Keys 1–20, each a list of `(rx, ry)` frame tuples generated by `_generate_animation(face_idx, seed)`.
- `_generate_animation`: single smooth ease-out curve (no phases). Each axis gets a random number of extra full rotations (2–4) and a random deceleration exponent (2.6–3.4) seeded by roll value × 137 + 42. 100 frames at 35ms = ~3.5 seconds.
- `_face_target_angles(face_idx)` — computes `(rx, ry)` with rz=0 to align face to camera using exact trigonometry (no matrix decomposition).
- `D20RollerWindow(parent, d20_value, on_confirm)` — Toplevel, plays `ANIMATIONS[d20_value]` on click via `_play_frame(i)`, calls `on_confirm()` after Confirm button.
- Face numbers: black text with light `#dddddd` halo shadow. Visibility threshold `normal[2] > 0.15`.
- Standalone: `root.geometry("1x1+0+0")` NOT `root.withdraw()` — withdraw breaks Toplevel display on Windows.

### `views/desktop/app.py`
Main game interface. `GameApp` class.

**Constants:** `ENEMY_STATS` (20 monsters), `_enemy_defaults(name, level)`, `SKILL_ABILITIES`

**UI layout:** Header bar, narration Text (Consolas, INPUT_BG), sidebar (220px: HP bar, AC, speed, conditions, combat tracker), input area (explore: entry + Send; combat: attack buttons).

**Startup dialog:** Mode page → Character page or Resume page. `_btn_large()` for clickable cards with hover highlight.

**Game flow:**
- `_start_adventure(new)` → `_dm_call()` in daemon thread → `_handle_dm_response()`
- Events dispatched: `combat_start` → `_start_combat()`, `skill_check` → `_handle_skill_check()`
- Roll button pattern: `_show_roll_button(label, d20_value, on_confirm)` embeds a gold Button in the narration Text widget via `window_create`; clicking opens `D20RollerWindow`
- Combat loop: `_next_turn()` → player turn (`_build_combat_input`) or enemy turn (`_do_enemy_turn`)
- Death saves triggered at 0 HP

---

## Known Quirks & Pitfalls

- **Listbox `exportselection`** — Both `char_lb` (character select) and `ses_lb` (session select) in `views/desktop/app.py` must have `exportselection=False`. Without it, clicking any button causes the Listbox to clear its selection, making `curselection()` return an empty tuple. The failure is silent because the error label (`_dlg_err`) is positioned at the very bottom of the dialog and gets obscured.

- **Character `hp` field must be a dict** — `init_hp()` in `models/game_state.py` calls `character["hp"].get("max", 1)`. If `hp` is stored as a plain integer, this raises `AttributeError: 'int' object has no attribute 'get'` which Tkinter silently swallows inside callbacks. Always store `hp` as `{"max": N, "current": N, "temp": 0}`. `empty_character()` does this correctly; the risk is hand-edited JSON files.

- **Tkinter swallows callback exceptions silently** — Any exception raised inside a Tkinter event callback (button click, etc.) is caught by Tkinter, printed to stderr, and the UI stays open with no visible feedback to the user. If `begin()` or any callback appears to do nothing, check stderr or add a try/except with explicit error display.

---

## Coding Conventions
- **GUI:** Tkinter, dark theme. `BG="#1a1a2e"`, `ACCENT="#c8a951"` (gold), `INPUT_BG="#0f0f1a"`, `PANEL="#16213e"`, `BTN_BG="#2a2a4a"`, `FG="#e0e0e0"`, `DIM="#888888"`, `GREEN="#4caf50"`, `RED="#e05050"`, `BLUE="#5b8cdc"`
- **Fonts:** `FONT_TITLE=("Segoe UI",13,"bold")`, `FONT_HDR=("Segoe UI",11,"bold")`, `FONT_BODY=("Segoe UI",10)`, `FONT_SM=("Segoe UI",9)`, `FONT_MONO=("Consolas",10)`
- **Dialogs:** Modal `Toplevel` with `grab_set()`. No `wait_window()` needed — callbacks handle teardown.
- **No threads** in the character builder. Daemon threads only in `game.py` for DM calls.
- **No comments** unless the WHY is non-obvious.
- **Python 3.14**, Windows 11, launched with `python`.
- `sys.path.insert(0, ...)` for cross-directory imports until the MVC restructure adds proper packages.

---

## What to Build Next

**MVC Restructure** — ✅ Complete. `python main.py` launches the game.

---

### NEXT SESSION — Character Progression & Leveling System

Build full D&D 5e character progression. Execute in three committed phases so context limits don't lose work.

#### Phase 1 — Core data + level-up flow (do this first)
- **New file `models/progression.py`** — all progression data in one place:
  - `XP_THRESHOLDS` list (levels 1–20): `[0, 300, 900, 2700, 6500, 14000, 23000, 34000, 48000, 64000, 83000, 100000, 120000, 140000, 165000, 195000, 225000, 265000, 305000, 355000]`
  - `ASI_LEVELS` dict — per-class levels that grant ASI/Feat (Fighter gets extras at 6, 14)
  - `SUBCLASS_TRIGGER_LEVELS` — level at which each class picks a subclass (most=3, Cleric/Sorcerer/Warlock=1, Druid/Wizard=2)
  - `CLASS_FEATURE_CHARGES` — structured dict: feature name → `{max_uses, recharge: "short_rest"|"long_rest", desc}`
    - Fighter: Second Wind (1, short), Action Surge (1, short), Indomitable (1→3, long)
    - Rogue: Cunning Action (passive), Uncanny Dodge (passive), Evasion (passive)
    - Cleric: Channel Divinity (1→3, short)
    - Bard: Bardic Inspiration (CHA mod, long→short at Lv5)
    - Druid: Wild Shape (2, short)
    - Monk: Ki Points (level, short)
    - Paladin: Lay on Hands (5×level pool, long), Divine Smite (passive/spell slots)
    - Ranger: (mostly passive)
    - Barbarian: Rage (2→∞, long)
    - Warlock: Eldritch Invocations (passive), spell slots (short)
    - Wizard: Arcane Recovery (1/2 level slots, long)
    - Sorcerer: Sorcery Points (level, long)
  - `level_from_xp(xp)` → int
  - `xp_for_level(level)` → int (XP needed to reach that level)
  - `xp_to_next_level(xp, current_level)` → int (XP remaining)
  - `is_asi_level(cls, level)` → bool
  - `get_subclass_trigger(cls)` → int
  - `features_gained_at(cls, level)` → list of feature names (from CLASS_FEATURES in dnd_data.py)
  - `feature_charges_gained_at(cls, level)` → list of charge dicts for features newly gained

- **`models/character.py`** — add to `empty_character()`:
  - `"feature_uses": {}` — `{feature_name: {"current": N, "max": N, "recharge": "short_rest"|"long_rest"}}`
  - `"inspiration": False`

- **`models/dm.py`** — add `[XP: N]` tag parsing in `_parse_events`. Returns event `{"type": "xp_award", "amount": N}`.

- **`controllers/game_controller.py`** — add:
  - `process_xp_award(session, char, amount)` → `{"xp_gained": int, "total_xp": int, "leveled_up": bool, "new_level": int}`
  - `process_short_rest(session, char, dice_spent)` → `{"hp_recovered": int, "features_recharged": list}`
  - `process_long_rest(session, char)` → `{"hp_recovered": int, "slots_recovered": dict, "features_recharged": list}`

- **`views/desktop/app.py`** — add level-up dialog (multi-step modal Toplevel):
  - Step 1: "You reached Level N!" — display all new class features as readable text
  - Step 2: HP roll — show the hit die, Roll button (uses D20RollerWindow pattern but for hit die), or "Take Average" button. Apply result.
  - Step 3: Subclass picker — only shown if `char["level"]` == `get_subclass_trigger(cls)` AND `char["subclass"]` is empty. Reuse `_pick_from_list` pattern.
  - Step 4: ASI/Feat — only shown if `is_asi_level(cls, level)`. Two options: "+2 to one ability" (dropdown) or "+1/+1 to two abilities" (two dropdowns). Feat option: "Choose Feat" (stub — show coming soon).
  - Step 5: Spell selection — only shown for caster classes. Show new slot levels unlocked, let player pick new spells/cantrips if class is Bard/Ranger/Sorcerer/Warlock (spells known). Wizard gets "add 2 spells to spellbook." Skip for Cleric/Druid (prepare from full list).
  - Handle XP award event from DM in `_handle_dm_response`

→ **Commit after Phase 1**

#### Phase 2 — Sidebar upgrades + rest UI
- **XP bar in sidebar** — below vitals: "XP: 450 / 900 (Lv 2→3)" with a gold progress bar
- **Feature charges in sidebar** — new "FEATURES" section below ATTACKS showing each limited-use feature as `[●●○] Action Surge` style with current/max pips. Clickable to use (with confirmation). Recharge on rest.
- **Inspiration** — small toggle button in vitals row. Gold when active, grey when not.
- **Short Rest / Long Rest buttons** in sidebar — Short rest opens a hit-dice spending dialog (spinbox for dice to spend, shows expected HP recovery, Roll or Take Average). Long rest is one-click with confirmation.
- `_update_sidebar` already calls `_refresh_attacks` — also add `_refresh_features()`

→ **Commit after Phase 2**

#### Phase 3 — Test harness (DEV panel)
- **Ctrl+D** opens a floating DEV panel (Toplevel, no grab_set so game stays interactive):
  - "Award XP" — text entry + button (calls `process_xp_award`)
  - Quick jump buttons: "→ Lv 2" through "→ Lv 10" — sets XP to exact threshold and triggers level-up dialog
  - "Short Rest" / "Long Rest" instant buttons
  - "Set HP" — spinbox to set current HP to any value (for testing death saves)
  - "Add Condition" — dropdown of all conditions
  - "Start Combat (test)" — spawns 1 Goblin immediately for combat testing
- Panel stays open across multiple uses so you can level up 1→10 repeatedly without reopening it

→ **Commit after Phase 3**

---

## Project Roadmap

### Stage 1 — Game Mechanics (current focus)
Complete the character progression system (Phases 1–3 above). This is the priority because UI polish and packaging work should wrap around a mechanically finished game, not the other way around.

Remaining mechanical work after progression:
- Spell combat support (spellcasting attacks, save DCs) in `models/combat.py`
- Expanded enemy roster and encounter tables
- Multiclassing (defer until single-class leveling is solid)

### Stage 2 — Electron + Flask Migration (confirmed plan)
Migrate from Tkinter to a proper game architecture: **Flask backend + HTML/JS/CSS frontend packaged via Electron**.

**Why this path:**
- Tkinter has a hard ceiling on visual quality and cannot support the Steam Overlay (requires OpenGL/D3D)
- The MVC structure already anticipates this — controllers return plain dicts, nothing in models touches Tkinter
- Electron + Flask is the proven path for Python-backed desktop games on Steam
- NW.js is also a viable alternative (5,700+ Steam games use it); evaluate at build time
- **Tauri is off the table** — its Steam integration requires writing Rust, which defeats using Python as the backend

**Architecture after migration:**
- `controllers/` unchanged — same functions called by Flask routes instead of Tkinter callbacks
- `views/web/api.py` becomes the real backend (Flask routes, JSON responses)
- `views/desktop/` retired once web UI reaches feature parity
- Frontend: HTML/CSS/JS, styled with Bootstrap or equivalent
- Packaged as an Electron app with a bundled Ollama setup flow

**⚠️ STOP before building — discuss with the user:**
- Whether to bundle Ollama + model in the installer or download on first run (models are 4–8 GB)
- Target distribution (GitHub releases, itch.io, Steam)
- Scene architecture: make the Scene pattern explicit before building the frontend (MainMenuScene, GameScene, CombatScene — each a class with `on_enter()`, `update()`, `render()`)

### Stage 3 — UI Polish
Full CSS/Bootstrap pass once the Electron shell is running and mechanics are complete.

---

## Steam (Low Priority — Future Reference)

Notes for when Steam distribution becomes relevant. Do not act on any of this until Stage 2 is complete and the user explicitly asks.

### What Steam actually requires
- **`SteamAPI_RunCallbacks()` must be called at least once per second** — the only hard architectural constraint. In an Electron app this goes in the main process on a 1-second interval
- **Steam Overlay** requires OpenGL or Direct3D rendering. Electron can support this; plain Tkinter and plain HTML cannot without GPU-accelerated rendering enabled
- **Steam Cloud saves** — use Auto-Cloud (config file only, no code changes needed). Saves must be files on disk, not in the Windows registry. Current `data/sessions/` JSON layout is already correct; just configure the Auto-Cloud path in Steamworks
- **Steam achievements** — call `SteamUserStats()->SetAchievement()` then `StoreStats()`. In Python via Steamworks flat C API using `ctypes`, or via the SteamworksPy compiled wrapper (DLL/SO — not pure Python)

### Python + Steam integration options
- **`ctypes` + flat C API** — Steamworks provides a special flat C API for language interop; Python can call it directly via `ctypes` without C++ bindings
- **SteamworksPy** — compiled native extension (DLL on Windows), ships alongside a `steamworks.py` wrapper. Requires distributing compiled binaries
- **Steamworks.js / Greenworks** — JavaScript bindings for Electron; the most natural fit once on the Electron path

### Disk layout Steam expects
- Save files: `%APPDATA%` or `%LOCALAPPDATA%\[GameName]\saves\` on Windows
- Config: same parent folder as saves
- Do not use the Windows registry for any game state

---

## GitHub
Repository: https://github.com/Smlcrp/dndgame
Clone: `git clone https://github.com/Smlcrp/dndgame.git`
