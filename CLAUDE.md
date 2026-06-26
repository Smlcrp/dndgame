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
│   ├── dm.py
│   ├── progression.py
│   ├── adventure.py
│   ├── enemies.py
│   ├── companions.py
│   └── spells.py
│
├── controllers/              # Orchestrates models, returns plain dicts — no UI
│   ├── __init__.py
│   └── game_controller.py   # setup_combat, process_attack, process_skill_check,
│                            #   process_enemy_turn, process_death_save, process_xp_award,
│                            #   process_short_rest, process_long_rest, process_spell_cast
│
├── views/
│   ├── desktop/              # Tkinter desktop app
│   │   ├── __init__.py
│   │   ├── app.py            # GameApp — pure UI, calls controller
│   │   ├── d20_roller.py     # 3D animated d20 roll window
│   │   ├── dice_roller.py    # 3D animated roller for d4/d6/d8/d10/d12/d20
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
├── tests/                    # pytest suite — 373 tests
│   ├── conftest.py           # sys.path setup
│   ├── test_dice.py
│   ├── test_character.py
│   ├── test_game_state.py
│   ├── test_combat.py
│   ├── test_progression.py
│   ├── test_adventure.py
│   ├── test_dm.py
│   ├── test_integration.py
│   └── test_companions.py
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
- `empty_character()` — canonical character dict; single source of truth for all field defaults
- `migrate_character(char)` — fills any key missing from an old save with the correct default; called automatically on load so no existing save breaks
- `validate_character(char)` — raises `ValueError` with a clear message on malformed data (wrong `hp` shape, bad `level` range, missing ability keys, etc.); called automatically on load
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
- `_build_system_prompt(character, session)` — full system prompt including: character block with ability mods + passive Perception/Investigation/Insight; NARRATION RULES 1–12; enemy list; adventure arc; party block; knowledge checks block; combat block (if in combat)
- `_build_knowledge_checks_block(character)` — tells the DM when to ask for a roll vs narrate freely, skill→topic mapping, DC calibration by level, natural phrasing, 5-tier result quality scale (nat-20=vivid, solid pass=clear, bare pass=gist, bare fail=vague, nat-1=confidently wrong)
- `_build_combat_prompt_block(character)` — live combat context (weapons, spells, features) + action/bonus action tag instructions
- `_parse_events(raw_text)` — extracts all tag types: `[CHECK:]`, `[COMBAT:]`, `[SCENE:]`, `[XP:]`, `[BEAT]`, `[CLIMAX]`, `[BREAK]`, `[COMPANION:]`, `[ACTION:]`, `[BONUS:]`
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

**Constants:** `_EXPLORE_PLACEHOLDER`, `SKILL_ABILITIES`, `SKILL_ABILITY`

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

- **`_parse_events` dict comprehension guard order** — In `dm.py:_parse_events`, the `pairs` dict used to parse `[ACTION:]` and `[BONUS:]` tag content has `if "=" in part` as a filter on the outer `for part in content.split(",")` loop. Do NOT move it to a trailing position after the inner `for k, v in [part.split("=", 1)]` — the inner destructuring runs before any trailing `if`, causing a `ValueError` for bare-word entries like `[ACTION: dodge]`.

- **`skill_proficiencies` must be Title Case** — The entire game stores and checks skill proficiencies as Title Case strings (`"Acrobatics"`, `"Sleight of Hand"`) matching `ALL_SKILLS` in `dnd_data.py`. The model layer's `SKILLS` dict uses lowercase_underscore keys but `skill_bonus()` should only be called with those keys for derived-stat calculations, not for checking `skill_proficiencies`. Do not write lowercase_underscore values into `skill_proficiencies`.

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

### ✅ DONE — Adventure Progress System (completed)
- `reset_to_level1(char)` in `models/character.py` — strips XP/level/HP/conditions/feature uses back to level 1. Clears subclass for classes whose trigger > 1. Saves to disk immediately on New Adventure.
- Main menu now has three modes: **New Adventure** (reset to Lv1), **Next Adventure** (carry existing progress into a fresh story — only shown when characters with level > 1 or XP > 0 exist), **Resume Session** (mid-session save).
- Warning dialog if New Adventure would overwrite stored progress.
- `_launch_new_adventure(d)` helper shared between both new-adventure flows.

---

### ✅ DONE — Animated Dice for All Die Types (completed)
- `views/desktop/dice_roller.py` — generic 3D animated roller for d4, d6, d8, d10, d12, d20.
- `_build_animation(normals, target_fi)` — verify-and-retry loop guarantees frame[0] orientation shows a different face than the landing face. Same fix applied to `d20_roller.py` via `_front_face_d20()`. All die types, all values pass diagnostic.
- Used for: damage rolls, death saving throws, hit dice (short rest + level-up).
- Attack/damage split into two explicit player actions with a "Roll Damage" button embedded in narration via `window_create`.

---

### ✅ DONE — Character Progression (Phase 1 complete)
- `models/progression.py` — XP thresholds, ASI levels, subclass triggers, CLASS_FEATURE_CHARGES, `level_from_xp`, `feature_charges_gained_at`, `current_max_uses`, `recharges_on_short_rest`.
- `models/character.py` — `feature_uses`, `inspiration` fields; `reset_to_level1()`.
- `controllers/game_controller.py` — `process_xp_award`, `process_short_rest`, `process_long_rest`.
- Level-up dialog (multi-step Toplevel): new features → HP roll (animated hit die) → subclass picker → ASI/Feat.
- XP award events from DM `[XP: N]` handled in `_handle_dm_response`.
- Short rest: hit-dice spending dialog with animated die rolls.
- Long rest: one-click with confirmation.

**Remaining (Phases 2 & 3 not yet built):**
- Phase 2: XP bar in sidebar, feature charges display (`[●●○] Action Surge`), Inspiration toggle, Short/Long Rest sidebar buttons.
- Phase 3: Ctrl+D DEV panel (award XP, quick level jump, set HP, add conditions, test combat).

---

### ✅ DONE — SRD Enemy List (models/enemies.py)

`models/enemies.py` — ~160 monsters from CR 0 to CR 30. Compact `_e()` / `_atk()` helpers keep the file readable. Key exports:
- `ENEMIES` — dict keyed by display name (what DM writes in `[COMBAT:]` tags)
- `by_cr(cr)` / `by_cr_range(min, max)` — filter by CR
- `appropriate_for_level(player_level)` — returns `(min_cr, max_cr)` tuple
- `enemy_list_for_dm(player_level)` — compact tiered string injected into DM system prompt

`game_controller.py` imports `ENEMIES` from this module. `dm.py` injects `enemy_list_for_dm(level)` at the end of its system prompt. `data/dm_config.json` (gitignored) sets the Ollama model.

**Current default model:** `hermes-3-llama-3.1:8b-q4_K_M`

---

### ✅ DONE — DEV Panel Password Gate

The DEV button and F4 shortcut are protected by a password prompt. First press shows a modal dialog with a masked `●` entry field. Wrong passwords clear the field and display "Incorrect password." without any hint. On success `self._dev_unlocked = True` is set for the lifetime of that process — subsequent presses in the same session go straight to the panel.

**Password:** `0922` — do not add this to README or any public-facing file.

**Implementation:** `_prompt_dev_password()` in `views/desktop/app.py`. `self._dev_unlocked` initialized `False` at startup. `_open_dev_panel()` checks it before calling `_open_dev_panel_inner()`.

---

### ✅ DONE — Story Mode (DEV panel button)

A **Story Mode** toggle is available in the DEV panel (F4 or DEV button in header). When active:
- The DM opens a scene in a small village populated entirely by women, starting with the character deciding what to do next.
- All D&D game mechanics are suspended: no `[COMBAT:]`, `[CHECK:]`, or `[XP:]` events are processed — pure narrative only.
- A gold **◆ STORY MODE** badge appears in the header.
- The player types responses normally; the DM narrates back without triggering any game systems.
- Clicking **Exit Story Mode** in the DEV panel restores normal play.

**Implementation:** `self._story_mode` flag on `GameApp`. `_handle_dm_response` skips all event processing when `True`. `_enter_story_mode()` sets the flag, shows the header badge, and sends the opening prompt to the DM. `_exit_story_mode()` clears flag and badge.

---

### ✅ DONE — DM Adventure Structure

**Context from DMG research:** The current DM has no concept of story arc — it narrates indefinitely with no structure. The DMG defines adventures as having: a hook → rising tension → climax → resolution.

**Plan:**
- Give the DM a structured adventure outline at session start (hook + antagonist + 3 escalating beats + climax goal).
- The DM should track which beat it's on and escalate toward the climax.
- Introduce a named antagonist early (villain with a plan already in motion).
- Balance the three pillars: combat, exploration (discovery/mystery), social (named NPCs).
- Adventures should feel like a story with a beginning, middle, and end — not an infinite sandbox.

**Implementation (complete):**
- `models/adventure.py` — 8 adventure templates (town, wilderness, dungeon, urban, coastal). `generate_adventure(char)` picks one randomly. `advance_beat(adventure)` advances `current_beat` and returns XP. `adventure_prompt_block(adventure)` returns the system prompt section.
- `session["adventure"]` — stored on session dict. Fields: `title, setting, hook, antagonist {name, role, motivation, plan}, beats [str×3], climax, resolution, current_beat (0–5), beat_xp [150,300,500], climax_xp 800`.
- `models/dm.py` — `_build_system_prompt(character, session=None)` now injects `adventure_prompt_block` after the enemy list. Parses three new tags:
  - `[BEAT]` → `beat_complete` event — advance beat, award XP (150/300/500)
  - `[CLIMAX]` → `climax_reached` event — display final confrontation header
  - `[BREAK]` → `break_suggested` event — display session break banner in narration
- `controllers/game_controller.py` — `start_adventure(session, char)` and `advance_beat(session)` public API.
- `views/desktop/app.py` — `start_adventure()` called in `_launch_new_adventure`. `_advance_beat()` and `_show_break_point()` methods. Break point banner is embedded directly in the narration Text widget.

---

### ✅ DONE — Natural Conversation System (Roadmap Item 2)

Player can ask the DM questions mid-scene and receive the full D&D roll experience.

- **`models/dm.py` — `_build_knowledge_checks_block(character)`** — injected into every system prompt. Tells the DM: when no roll is needed (common knowledge, already established this session, obvious observation) vs when to call for one (obscure lore, reading a creature under pressure, hidden details, deciphering symbols). Skill→topic mapping (Arcana→magic, History→kingdoms, Perception→movement/distance, etc.). DC calibration scaled by character level. Natural phrasing examples ("Give me an Arcana check" ✓, "A check is required" ✗). Five-tier result quality scale: nat-20 = vivid extra detail, solid success (margin ≥+5) = clear complete info, bare success (margin 0–4) = gist only, bare failure (margin −1 to −4) = vague/uncertain, nat-1 = confidently wrong (no signal to the player).
- **`models/dm.py` — passive scores** — `Passive Perception`, `Passive Investigation`, `Passive Insight` computed from ability mods + proficiency and injected into the character block. Rule 12 tells the DM to use these for automatic awareness during scene descriptions without ever saying "passive check."
- **`views/desktop/app.py` — `_handle_skill_check`** — now sends `d20=N, total=N, DC=N, margin=+/-N` plus the matching tier label (CRITICAL SUCCESS / SOLID SUCCESS / BARE SUCCESS / BARE FAILURE / CRITICAL FAILURE) so the DM can apply the exact quality tier from the knowledge checks block.
- **`views/desktop/app.py` — placeholder text** — input field shows "What do you do? You can also ask questions." when empty and unfocused. `_on_input_focus_in` / `_on_input_focus_out` handlers. Placeholder value guarded in `_send_action` so it can't be submitted.

---

### ✅ DONE — Character Schema Enforcement (Roadmap Item 3)

Every character loaded from disk is migrated to the current schema and validated before the game starts.

- **`models/character.py` — `migrate_character(char)`** — walks every key in `empty_character()` and fills any gap in a loaded save, including nested dicts (abilities, hp, spellcasting slots 1–9, currency, etc.). Safe to run on any save regardless of age — only fills, never overwrites.
- **`models/character.py` — `validate_character(char)`** — raises `ValueError` naming the character and the exact bad field. Checks: `hp` is a dict with int values and `max ≥ 1`; all six abilities are ints; `level` is 1–20; `experience ≥ 0`; `hit_dice.total ≥ 1`; `spellcasting.enabled` is a bool; all list fields are actually lists.
- **`models/character.py` — `load_character()`** — now calls `migrate_character` then `validate_character` on every load. Old manual `setdefault` calls removed; `migrate_character` covers them.
- **`views/desktop/character_builder/character_builder_app.py`** — spellcasting save now explicitly includes `"spells_prepared": []` so the full schema is preserved instead of silently dropping the field.
- **Audit result:** Zero crash risks found. All fields accessed by game code are present in `empty_character()`. All direct bracket accesses (`char["hp"]`, `char["class"]`, etc.) are safe. Builder correctly populates all required fields.

---

### ✅ DONE — D&D Beyond Character Import (Roadmap Item 4)

- **`views/desktop/character_builder/ddb_import.py` — `SKILL_MAP` fix** — all 18 skill values changed from lowercase_underscore (`"acrobatics"`, `"sleight_of_hand"`) to Title Case (`"Acrobatics"`, `"Sleight of Hand"`) to match `ALL_SKILLS` in `dnd_data.py` and the rest of the game's `skill_proficiencies` format. Without this fix, imported characters silently failed all skill proficiency checks.
- **`views/desktop/app.py` — import UI** — "⬇ DDB Import" button added to the character select row (alongside New Character and Delete). Clicking opens a centered `Toplevel` dialog with a URL/ID field, a masked CobaltSession token field (for private characters), status label, and Import/Cancel buttons. Import runs in a daemon thread: `import_from_ddb()` → `migrate_character()` → `validate_character()` → `save_character()`, then the character list refreshes automatically. Success message shown for 1.4 seconds before the dialog closes.
- **`models/character.py`** — `migrate_character` and `validate_character` imported into `app.py` and wired into the import pipeline so every DDB import is schema-enforced on save.

---

### ✅ DONE — Comprehensive Test Suite (Roadmap Item 5)

376 tests total (87 existing companion tests + 289 new). All pass. Run with: `python -m pytest tests/ -q`

**New test files:**
- `tests/conftest.py` — central `sys.path` setup so no per-file boilerplate needed
- `tests/test_dice.py` — `roll`, `roll_dice` (notation parsing, bounds), `d20_check` (advantage/disadvantage, nat20/nat1), `critical_damage` (doubled dice), `hit_die` (minimum 1 guarantee), `death_save`, `initiative`
- `tests/test_character.py` — modifier math, modifier_str, proficiency_bonus by level, `skill_bonus` (no prof / proficient / expertise / override / invalid), `saving_throw_bonus`, `apply_damage` (temp absorption, bleedthrough, floor-zero), `apply_healing` (cap), `add_temp_hp` (keep higher), `is_unconscious`, spell slot use/exhaust/restore, `short_rest` (con mod, min heal, too-many-dice guard), `long_rest` (HP restore, temp clear, condition clear, death save reset, hit dice recovery), `migrate_character` (fills gaps, idempotent, non-destructive), `validate_character` (all error paths, error message includes character name)
- `tests/test_game_state.py` — `empty_session`, `apply_damage` (temp absorption, floor-zero, zero-damage noop), `apply_healing` (cap), spell slot use/restore by level, `long_rest` / `short_rest`, `start_combat` (initiative sort, in_combat flag, round=1, conditions init), `end_combat`, `advance_turn` (wrap + round increment), `current_combatant`, `apply_combat_damage` / `apply_combat_healing`, `add_condition` / `remove_condition` (dedup), `living_combatants`, `enemies_alive` (companion not counted, player not counted)
- `tests/test_combat.py` — `build_enemy`, `resolve_attack` (nat20 hit, nat1 miss, hit above AC, miss below AC, pre_damage, overkill, result shape, unknown target), `player_attack` (weapon not found, valid hit), `enemy_attack` (valid, not found, no attacks), `handle_death_save` (all 6 outcomes), `xp_from_combat` (dead enemies only, player excluded, multiple, empty), `combat_summary`
- `tests/test_progression.py` — `level_from_xp` (all 20 thresholds), `xp_for_level`, `xp_to_next_level`, `is_asi_level` (Fighter has level 6, standard classes, unknown), `get_subclass_trigger` (all known classes, unknown defaults 3), `current_max_uses` (fixed int, level-based, cha_mod min-1, int_mod, 5x_level, scaling override, unknown feature/class), `recharges_on_short_rest` (short/long/short_rest_at threshold), `feature_charges_gained_at`
- `tests/test_adventure.py` — `generate_adventure` (required keys, beat=0, nonempty beats, XP list, climax_xp, antagonist keys, non-deterministic), `advance_beat` (increments, positive XP, capped at 4, repeated noop, full arc), `adventure_prompt_block` (None → "", title/antagonist in block, stage labels for all beats, [BEAT]/[CLIMAX]/[BREAK] instructions present)
- `tests/test_dm.py` — all 9 tag types: `[CHECK:]` (skill, dc, case-insensitive, multi-word skill), `[COMBAT:]` (count, multiple enemies, no-count default, latin-x), `[SCENE:]`, `[XP:]`, `[BEAT]` / `[CLIMAX]` / `[BREAK]` (case-insensitive), `[COMPANION:]`, `[ACTION:]` (attack/mode, spell/slot, feature, dodge/dash/disengage/hide), `[BONUS:]` (attack, feature); narration cleaning (tags stripped, excessive newlines collapsed, all types together)
- `tests/test_integration.py` — full combat round (kill enemy → XP), player miss (enemy alive), crit (doubled dice), death save arc (stabilize / die / nat1 → dead / nat20 revive), full adventure beat sequence, beat XP → level-up threshold, schema round-trip (`migrate_character` + `validate_character` on sparse char)

**Bug found and fixed by tests:** `[ACTION: dodge]` / `[ACTION: dash]` / `[ACTION: disengage]` / `[ACTION: hide]` crashed with `ValueError` in `dm.py:_parse_events` — `if "=" in part` guard was in the wrong position in the dict comprehension, running after the inner for-loop destructuring instead of before. Same fix applied to `[BONUS:]` parser. (Bug would have silently crashed any combat turn where the DM chose a non-attack action.)

---

### ✅ DONE — In-Game Economy, Magic Items, Feats, and Spell Learning

Four gaps closed to make the game mechanically complete:

**1. In-Game Economy (gold + loot)**
- `models/character.py` — `currency` and `magic_items` / `magic_weapon_bonus` / `magic_armor_bonus` / `feats` added to `empty_character()` schema; `migrate_character()` fills these on any old save.
- `models/dm.py` — Two new DM tags: `[GOLD: N]` (award N gp) and `[ITEM: name, slot=weapon|armor|misc, bonus=N]`. Added to `tag_rules` in the system prompt and parsed in `_parse_events`. Clean regex updated to strip them from displayed narration.
- `controllers/game_controller.py` — `process_gold_award(char, amount)` and `process_item_award(char, name, slot, bonus)` — apply bonuses immediately and return updated values.
- `views/desktop/app.py` — Events handled in `_handle_dm_response`: shows inline system messages ("── 50 gp added (Total: 50 gp) ──") and saves character automatically. New INVENTORY sidebar section shows coin purse (pp/gp/sp/cp) and magic items list.

**2. Magic Items Affect Combat**
- `models/combat.py:player_attack()` — reads `char["magic_weapon_bonus"]` and adds it to both the attack roll and damage notation (shown as "1d8+1" for a +1 weapon).
- `views/desktop/app.py:_update_sidebar()` — AC display adds `char["magic_armor_bonus"]` so the sidebar reflects the true AC with magic armor equipped.

**3. Feats at ASI Levels**
- `views/desktop/app.py:_step_asi()` — Level-up ASI step now has three radio options: "+2 to one ability", "+1 to two abilities", "Take a Feat". Selecting feat shows a scrollable listbox of 30 PHB feats with a one-line description area below (updated on selection). Confirming appends feat name to `char["feats"]`. Tough feat applies its HP bonus immediately (2 HP × level, retroactive).
- Feat list defined inline in `_step_asi()`: Alert, Athlete, Actor, Charger, Crossbow Expert, Defensive Duelist, Dual Wielder, Dungeon Delver, Durable, Great Weapon Master, Healer, Inspiring Leader, Lucky, Mage Slayer, Magic Initiate, Martial Adept, Mobile, Observant, Polearm Master, Resilient, Savage Attacker, Sentinel, Sharpshooter, Shield Master, Skilled, Tavern Brawler, Tough, War Caster, Weapon Master.
- `models/dm.py` — character block now includes "Feats: ..." and "Magic Items: ..." lines when non-empty, so the DM knows what the player has.

**4. Spell Learning at Level-Up**
- `views/desktop/app.py:_step_spells()` — Replaced the redirect stub with a real spell picker:
  - Prepare classes (Cleric, Druid, Paladin, Artificer): shown an informational message only ("prepares from full list each long rest").
  - Known classes (Bard, Ranger, Sorcerer, Warlock): can pick 1 new spell from accessible spell levels not already known.
  - Wizard: can pick 2 new spells.
  - Dynamically imports from `character_builder/spells.py` (CANTRIPS, SPELLS dicts). Filters out already-known spells. Shows "[Lv3] Fireball" style labels. Multi-select Listbox capped at N picks; confirms into `sc["spells_known"]`.

---

### ✅ DONE — Game Mechanics Audit (Roadmap Item 8)

Full audit of `dice.py`, `character.py`, `combat.py`, `progression.py` against D&D 5e SRD. Four bugs found and fixed. 3 new tests added (376 total).

**Findings and fixes:**

- ✅ `dice.py` — all functions correct: d20 advantage/disadvantage, nat20/nat1, critical damage (double dice count), death save outcomes, initiative.
- ✅ `character.py` modifiers, proficiency bonus, skill/save bonuses — all correct.
- ✅ `combat.py` — attack resolution (nat20 hit, nat1 miss, tie beats AC), crit delegation, death saves, XP from dead enemies only — all correct.
- ❌ **FIXED — Level 11 XP threshold**: `progression.py` had `83000`; SRD value is **85,000**. Characters were reaching level 11 two thousand XP early.
- ❌ **FIXED — Barbarian Rage scaling** (`progression.py`): old `{9: 3, 12: 3, 17: 4, 20: 6}` was wrong (wrong trigger levels, missing the 5-uses tier). Correct SRD progression: `{3: 3, 6: 4, 12: 5, 17: 6, 20: 999}` (999 = unlimited at level 20). The `current_max_uses` function applies scaling in sorted key order, so this fully implements the SRD table: 2 uses (Lv1-2) → 3 (Lv3-5) → 4 (Lv6-11) → 5 (Lv12-16) → 6 (Lv17-19) → unlimited (Lv20).
- ⚠️ **FIXED — Long rest hit dice recovery** (`character.py`): used `total // 2` (floor) instead of ceil. A character with 5 total hit dice (levels 5, 7, 9 etc.) would recover 2 dice instead of the correct 3. Fixed to `(total + 1) // 2`.
- 💡 **FIXED — Warlock Pact Magic short rest recharge** (`character.py`): `short_rest()` now calls `restore_spell_slots(char)` when `char["class"] == "Warlock"`. Previously Warlocks never recovered spell slots on a short rest, effectively breaking the class at mid/high levels.
- ⚠️ NOT FIXED — Prone condition grants advantage to melee and ranged (SRD: disadvantage to ranged). Intentional simplification for a text-based game where attack type is not tracked.
- 💡 NOT FIXED — Enemy saving throws use a raw d20 with no ability modifier. Tracked for future improvement but out of scope for this pass.

---

### ✅ DONE — QA Validation Pass (Roadmap Item 6)

373 tests, all passing in 0.5 s. Repo clean. Everything committed and pushed before starting items 7–9.

---

### ✅ DONE — Main Menu Redesign (Roadmap Item 7)

Replaced the floating `tk.Toplevel` startup dialog with a full-screen inline `tk.Frame` that covers the main window. Key changes in `views/desktop/app.py`:

- `_startup_dialog()` now creates `d = tk.Frame(self.root, bg=BG)` and places it full-screen with `d.place(relx=0, rely=0, relwidth=1, relheight=1)`. The frame is stored as `self._startup_frame` and destroyed when setup completes.
- A centered 440-wide content panel is built inside `d` using a grid with column/row weights.
- All `_show_*_page(d)` methods are unchanged — `d` is now the inline Frame (not a Toplevel) and all page navigation still works via the same `d` reference.
- `grab_set()`, `d.title()`, `d.geometry()`, `d.resizable()` removed (not applicable to Frames).
- All `messagebox.askyesno(..., parent=d)` calls changed to `parent=self.root` (messageboxes require a Toplevel-level parent).
- DDB import dialog centering was already using `parent.winfo_x()` — changed to pass `self.root` instead of `d` as parent.
- `_launch_new_adventure()`: `d.destroy()` changed to `self._startup_frame.destroy()`.

---

### ✅ DONE — Adventure Length Presets (Roadmap Item 9)

Three adventure tiers selectable before each game. Full implementation across models, controller, and UI:

**`models/adventure.py`:**
- `PRESETS` dict: `{"One Shot": {"beats": 1, "estimate": "~1–2h"}, "Quest": {"beats": 3, "estimate": "~3–4h"}, "Epic": {"beats": 5, "estimate": "~5–8h"}}`
- `generate_adventure(char, preset="Quest")` — backward-compatible new signature; `preset` stored in returned adventure dict
- `_build_beats(template, count)` — generates beat list of the right length:
  - One Shot: uses template's climax text as the single beat (goes straight to the confrontation)
  - Quest: 3 template beats unchanged
  - Epic: 5 beats — template beat 1, then 2 synthesized mid-act beats referencing the antagonist, then template beats 2 and 3
- `_beat_xp_for_preset(preset)` — One Shot `[600]`, Quest `[150, 300, 500]`, Epic `[100, 150, 200, 300, 450]`
- `_stage_labels(n_story_beats)` — dynamic stage labels (replaces hardcoded 6-entry list); builds HOOK + N ACT labels + CLIMAX + RESOLUTION; correctly names the final act "crisis point" and the one-shot single beat "FINAL ACT"
- `advance_beat(adventure)` — now caps at `beat > n_story_beats` (dynamic, based on actual beat list length) instead of hardcoded `beat >= 4`
- `adventure_prompt_block` — scope line injected after the title for One Shot and Epic presets:
  - One Shot: "SCOPE: One-shot — deliver a complete, satisfying confrontation in a single compact session. Reach the climax briskly; do not pad."
  - Epic: "SCOPE: Epic campaign — let each act breathe fully. Build subplots, deepen NPC relationships, and escalate tension gradually across multiple sessions."

**`controllers/game_controller.py`:**
- `start_adventure(session, char, preset="Quest")` — threads preset through to `generate_adventure`

**`views/desktop/app.py`:**
- New `_show_preset_page(d, back_fn=None)` method — shown after character selection:
  - Three cards: Epic (~5–8h), Quest (~3–4h, highlighted gold by default), One Shot (~1–2h)
  - Clicking a card selects it (ACCENT highlight); Begin → calls `_launch_new_adventure(d, preset)`
  - Back button uses `back_fn` so both New Adventure and Next Adventure flows return to the right page
- `_show_character_page`: `begin()` now routes to `_show_preset_page(d, back_fn=lambda: self._show_character_page(d))`
- `_show_next_adventure_page`: same routing to preset page with its own back_fn
- `_launch_new_adventure(d, preset="Quest")` — passes preset to `start_adventure()`

All 373 tests still pass after these changes (the new signature is backward-compatible, Quest XP values unchanged).

---

### NEXT NEXT — Character Progression (Phase 2 & 3)

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

### ✅ DONE — Actions Reference Panel + DM-Driven Action Parsing

Replace the current compact attack/feature text block above the combat input bar with an "⚔ Actions" button that opens a read-only reference panel. All mechanical actions are still triggered through the player's typed dialogue — the DM parses natural language to determine what action and bonus action are being used.

#### Reference panel (`_open_action_panel()`)
A `Toplevel` modal with two sections — ACTIONS and BONUS ACTIONS. Nothing is clickable; it is a quick-reference card only.

- **ACTIONS:** weapon attacks (+ versatile/thrown variants), "✦ Cast a Spell" (if spellcasting enabled + slots available), Dash, Dodge, Disengage, Hide
- **BONUS ACTIONS:** off-hand attack (if dual-wielding light melee), class features marked as bonus actions (Rage, Second Wind, Wild Shape, Bardic Inspiration, Ki Points, Channel Divinity, etc.)
- Unavailable entries are greyed out. Hovering shows a small floating tooltip explaining why: e.g. "Stunned — cannot take actions", "0 / 2 charges remaining", "No castable combat spells available"
- Tooltip implementation: `Toplevel(overrideredirect=True)` shown on `<Enter>`, hidden on `<Leave>`

#### Input row change
Remove the compact reference block (the two-line `ref` frame in `_build_combat_input` that lists weapons and feature charges as text). Replace with:

`[⚔ Actions]  [text entry — expands to fill]  [✦ Spells]  [→]`

The "⚔ Actions" button sits on the left edge; everything else stays on the right.

#### DM-driven action parsing (core change)
Extend `models/dm.py` — `_build_system_prompt()` gains a combat block when `session.get("in_combat")` is True:

```
COMBAT ACTION TAGS — Embed the appropriate tag on its own line when the player takes an action:
  [ACTION: attack=ExactWeaponName]
  [ACTION: attack=ExactWeaponName, mode=twohanded]
  [ACTION: attack=ExactWeaponName, mode=thrown]
  [ACTION: spell=ExactSpellName, slot=N]   ← pick lowest available slot if player did not specify
  [ACTION: feature=ExactFeatureName]
  [ACTION: dodge]  [ACTION: dash]  [ACTION: disengage]  [ACTION: hide]

  Bonus actions:
  [BONUS: attack=ExactWeaponName]
  [BONUS: feature=ExactFeatureName]

Available weapons: {live list injected at call time}
Available spells:  {live list with slot counts injected at call time}
Available features: {live list with charge counts injected at call time}
```

Extend `_parse_events()` in `dm.py` to extract `action_taken` and `bonus_action_taken` from these tags and return them as events.

#### `_send_combat_action()` new flow
1. Build enriched context string (available weapons/spells/features) and send player text to DM
2. Display DM narration
3. Parse returned events for `action_taken` / `bonus_action_taken`
4. Dispatch:
   - `attack=X` → `_do_player_attack(X, mode=...)` (d20 + damage roll flow)
   - `spell=X, slot=N` → consume slot then `_do_player_spell(X, slot=N, target)` flow
   - `feature=X` → `_apply_combat_feature(X)`
   - `dodge/dash/disengage/hide` → end turn (DM already narrated it)
   - `[BONUS: ...]` → process before or after main action depending on type
5. Fallback: if no action tags in DM response, fall back to current client-side regex matching (`_find_weapon_in_text`, `_detect_feature_in_text`); if still no match, treat as narrative turn and end turn

#### Slot targeting for spells
If `[ACTION: spell=X]` arrives without a slot number and the spell requires a slot, present the slot-level picker (same one used in `_open_spell_picker`) before resolving the spell. For cantrips, no picker needed.

#### Files to change
- `models/dm.py` — extend `_build_system_prompt()` (combat block), extend `_parse_events()`
- `views/desktop/app.py` — remove `ref` frame from `_build_combat_input`, add Actions button, new `_open_action_panel()` method, update `_send_combat_action()` dispatch logic

---

## Project Roadmap

### ✅ Stage 1 — Game Mechanics (COMPLETE)

All core D&D 5e mechanics implemented and tested (376 tests passing):
- Turn-based combat with conditions, crits, death saves
- Full character progression: XP, level-up dialog (features → HP → subclass → ASI/feat → spells)
- 30 PHB feats at ASI levels; spell learning for all caster archetypes
- In-game economy: gold awards, magic items, mechanical bonuses applied at combat resolution
- DM-driven action parsing via structured tags
- 8 adventure templates, 3 length presets (One Shot / Quest / Epic)
- Companion system: 10 classes, combat AI, spell slots, death saves
- D&D Beyond character import
- Passive perception/investigation/insight in DM system prompt
- Natural knowledge check system with 5-tier result quality scale

### ✅ Stage 2 — Sidebar & Rest UI (COMPLETE)

- XP progress bar in VITALS section
- Feature charge display with current/max counts; clickable to use
- Inspiration toggle
- Short Rest button (hit-dice spending with animated die rolls)
- Long Rest button (one-click confirm, restores HP/slots/features)

### ✅ Stage 3 — DEV Panel (COMPLETE)

Floating panel (F4 / DEV button in header):
- Award XP; level jump to Lv2–Lv10
- Set HP (spinbox)
- Add condition (dropdown)
- Spawn test combat
- Short/Long Rest instant buttons

---

### Stage 4 — Electron + Flask Migration

Migrate from Tkinter to a proper game frontend: **Flask backend + HTML/JS/CSS + Electron shell**.

**Why this path:**
- Tkinter has a hard ceiling on visual quality and cannot support Steam Overlay (requires OpenGL/D3D)
- MVC is already framework-agnostic — `controllers/` return plain dicts and need no changes
- Electron + Flask is the proven Python-backed desktop game path for Steam
- NW.js is a viable alternative (5,700+ Steam games); evaluate at build time
- Tauri is off the table — its Steam integration requires writing Rust

**⚠️ Discuss with the user before starting:**
- Bundle Ollama + model in the installer, or download on first run? (models are 4–8 GB)
- Target distribution: GitHub releases → itch.io → Steam (in that order)
- Scene architecture: define `MainMenuScene`, `GameScene`, `CombatScene` as explicit classes with `on_enter() / update() / render()` before writing any HTML

#### 4a — Flask Backend
- Create `views/web/api.py` — Flask app with routes mirroring every Tkinter callback
- Routes: `POST /action`, `GET /state`, `POST /roll`, `POST /attack`, `POST /rest`, `POST /level-up`, `POST /save`, `GET /characters`, `POST /characters/new`, `DELETE /characters/<name>`
- Session state lives server-side (Flask `session`) backed by the same `data/sessions/` JSON files already in use
- All routes return JSON; errors follow `{"error": "...", "code": N}`
- Add pytest tests for every route alongside the existing model tests

#### 4b — HTML/CSS Frontend
- One-page app — vanilla JS with fetch API (no framework required)
- Scene classes in `static/js/scenes/`: `MainMenuScene`, `CharacterSelectScene`, `PresetScene`, `GameScene`, `CombatScene`, `LevelUpScene`
- Each scene manages its own DOM subtree; `SceneManager` swaps active scene and calls lifecycle hooks
- Narration panel: `<div id="narration">` append-only, auto-scrolls; player text styled distinctly in blue
- Sidebar: sticky right panel updated by `GameScene.updateSidebar(state)` after every response
- Dark theme CSS vars matching current constants: `--bg: #1a1a2e`, `--accent: #c8a951`, etc.
- d20 roller: CSS 3D transform animation replacing the Tkinter Canvas — same 20 pre-computed spin angles as CSS keyframes
- Combat tracker: `<div id="combat-tracker">` inside the sidebar, visible only during combat

#### 4c — Electron Shell
- `main.js`: spawn Flask subprocess on app launch, wait for `/ping`, then load `http://localhost:5000`
- Graceful shutdown: kill Flask subprocess on `app.on('before-quit')`
- `electron-builder` config: package Python (via PyInstaller one-dir bundle) + Electron together
- Single `.exe` installer on Windows via NSIS; `.dmg` on Mac
- First-run wizard: detect Ollama → if absent show download link; if present check model → if absent run `ollama pull` with progress bar

#### 4d — Retire Tkinter
- Delete `views/desktop/` once web UI has full feature parity and all routes are test-covered
- Update `main.py` to launch Electron instead of `tk.Tk()`
- `take_screenshots.py` can be archived (browser DevTools replaces it)

---

### Stage 5 — Visual Design Pass

Full design pass after the Electron shell is running and all scenes are functional.

- **Typography** — proper game font (e.g. Crimson Text or IM Fell for narrative, monospace for rolls)
- **Color system** — expand beyond the 9 current constants; add surface elevation tokens (`--surface-0`, `--surface-1`, `--surface-2`) for card layering
- **Narration panel** — parchment-style texture background; smooth auto-scroll; animated "DM is thinking…" typing indicator
- **Sidebar** — collapsible sections; HP bar animates on damage/healing; magic item cards with rarity color border
- **d20 roller** — CSS keyframe version with glow effect on nat-20; shake on nat-1
- **Combat tracker** — highlight active combatant row with a pulse animation; dead enemies shown with strikethrough and reduced opacity
- **Level-up dialog** — full-screen overlay with particle effect on level gain
- **Responsive layout** — support window widths from 900px to 1920px

---

### Stage 6 — Distribution

Release pipeline once Stage 5 is complete.

#### GitHub Releases (first)
- Tag `v1.0.0`; `electron-builder` CI workflow produces `.exe` and `.dmg` artifacts automatically on push to `release/*` branches
- Auto-updater via `electron-updater` reading GitHub Releases API

#### itch.io (second)
- Itch.io page with screenshots, trailer, and a "pay what you want" price
- Butler CLI in CI to upload builds automatically on release tag

#### Steam (third — when ready)
- Steamworks partner account; AppID configured
- `SteamAPI_RunCallbacks()` on a 1-second interval in `main.js`
- Steam Overlay: enable GPU acceleration in Electron (`--enable-gpu` launch flag)
- Steam Cloud: Auto-Cloud configured for `data/sessions/` and `data/characters/` — no code changes needed
- Steam Achievements: `Steamworks.js` / Greenworks bindings in `main.js`; achievement IDs defined in Steamworks partner portal
- Steam Deck: verify input mapping; controller-friendly UI pass (larger hit targets, gamepad navigation)

---

### Stage 7 — Content Expansion (post-launch)

- **More adventure templates** — expand from 8 to 20+; add templates for specific settings (seafaring, underdark, planar travel, heist)
- **More enemies** — expand the 160-monster `enemies.py` roster; add legendary actions and lair actions for boss fights
- **Multiclassing** — tracked in character schema already (`"multiclass": []`); need progression table, spell slot merging, and feature eligibility checks
- **More races and classes** — Artificer, Blood Hunter; Aasimar, Githyanki, Fairy
- **Crafting system** — components dropped by enemies; recipes unlock with Arcana/Smith proficiency
- **World map** — persistent overworld between adventures; unlockable locations
- **Mod support** — JSON-defined adventure templates, enemies, and items that users can drop into `data/`

---

## Steam — Technical Reference

Notes for when Steam distribution becomes relevant (Stage 6). Do not build any of this until Stage 5 is complete and the user explicitly asks.

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
