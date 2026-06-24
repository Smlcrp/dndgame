# D&D AI Dungeon Master — Project Context

## Security Constraint (NEVER SKIP)
**Always warn the user before making any Claude API calls that will cost tokens. Get explicit confirmation before proceeding.** This applies to any AI Dungeon Master calls, `dm.py` testing, or any Anthropic API invocation.

**WARN USER before any DM testing — Gemini API calls cost quota.**

---

## Project Vision
A fully playable D&D 5e adventure game with an AI Dungeon Master. Currently a Python/Tkinter desktop app. The next major milestone is restructuring to MVC so the same game logic can power a future web frontend with no rewriting.

## Current File Structure (pre-MVC)
```
dndgame/
├── character.py              # ✅ Core character data model, save/load, helpers
├── characters/               # Saved character JSON files (gitignored)
├── Character Builder/
│   ├── character_builder_app.py   # ✅ Main GUI character builder
│   ├── dnd_data.py               # ✅ Complete D&D 5e rules data
│   ├── spells.py                 # ✅ Full spell lists by class/level
│   ├── ddb_import.py             # ✅ D&D Beyond import
│   ├── character_builder.py      # Legacy CLI builder (unused)
│   └── Launch Character Builder.bat
├── dice.py                   # ✅ Dice rolling engine
├── game_state.py             # ✅ Session persistence and combat state
├── combat.py                 # ✅ Turn-based combat engine
├── dm.py                     # ✅ AI Dungeon Master (Ollama + Gemini)
├── d20_roller.py             # ✅ 3D animated d20 roll window
├── dm_config.json            # Gitignored — backend/API key config
├── dm_config.example.json    # Committed template
├── sessions/                 # Saved session JSON files (gitignored)
└── game.py                   # 🚧 Main game interface (GUI) — in progress
```

## Target MVC Structure (next milestone)
```
dndgame/
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
│   └── game_controller.py   # process_action, start_combat, process_attack,
│                            #   process_skill_check, process_enemy_turn,
│                            #   process_death_save, build_enemy_list
│
├── views/
│   ├── desktop/              # Tkinter desktop app
│   │   ├── app.py            # GameApp (was game.py) — pure UI, calls controller
│   │   ├── d20_roller.py
│   │   └── character_builder/  # (was Character Builder/)
│   │       ├── character_builder_app.py
│   │       ├── dnd_data.py
│   │       ├── spells.py
│   │       ├── ddb_import.py
│   │       └── Launch Character Builder.bat
│   └── web/                  # Future web frontend
│       ├── api.py            # Flask/FastAPI — same controller calls, JSON responses
│       ├── templates/
│       └── static/
│
├── data/
│   ├── characters/
│   ├── sessions/
│   ├── dm_config.json
│   └── dm_config.example.json
│
└── main.py                   # Entry point: python main.py → desktop app
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

**Import path in Character Builder files:** `sys.path.insert(0, str(Path(__file__).parent.parent))` to reach `character.py`.

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
AI DM. Supports Ollama (local) and Google Gemini (cloud). Config from `dm_config.json` (gitignored).

- `DungeonMaster(backend, model, api_key)`
- `respond(session, character, player_input)` → `{"narration": str, "events": list}`
- `_parse_events(raw_text)` — extracts `[CHECK: Skill DC##]`, `[COMBAT: Name×N]`, `[SCENE: Location]`
- `from_config(path)` — loads backend settings

### `d20_roller.py`
3D animated d20 roll window. Renders an icosahedron with perspective projection and gold shading.

**Architecture:**
- `ANIMATIONS` dict (module-level) — pre-computed at import time. Keys 1–20, each a list of `(rx, ry)` frame tuples generated by `_generate_animation(face_idx, seed)`.
- `_generate_animation`: single smooth ease-out curve (no phases). Each axis gets a random number of extra full rotations (2–4) and a random deceleration exponent (2.6–3.4) seeded by roll value × 137 + 42. 100 frames at 35ms = ~3.5 seconds.
- `_face_target_angles(face_idx)` — computes `(rx, ry)` with rz=0 to align face to camera using exact trigonometry (no matrix decomposition).
- `D20RollerWindow(parent, d20_value, on_confirm)` — Toplevel, plays `ANIMATIONS[d20_value]` on click via `_play_frame(i)`, calls `on_confirm()` after Confirm button.
- Face numbers: black text with light `#dddddd` halo shadow. Visibility threshold `normal[2] > 0.15`.
- Standalone: `root.geometry("1x1+0+0")` NOT `root.withdraw()` — withdraw breaks Toplevel display on Windows.

### `game.py` *(in progress — will become `views/desktop/app.py` after MVC split)*
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

**MVC Restructure** — agreed plan, ready to execute:
1. Create `models/`, `controllers/`, `views/desktop/`, `views/web/`, `data/` folders
2. Move model files into `models/`, add `__init__.py`, fix imports
3. Move `d20_roller.py` and `Character Builder/` into `views/desktop/`
4. Extract game logic from `game.py` → `controllers/game_controller.py`
5. Rewrite `game.py` → `views/desktop/app.py` as pure UI calling the controller
6. Add `main.py` entry point
7. Move `characters/`, `sessions/`, config into `data/`
8. Update all import paths
9. Verify game runs identically

---

## GitHub
Repository: https://github.com/Smlcrp/dndgame
Clone: `git clone https://github.com/Smlcrp/dndgame.git`
