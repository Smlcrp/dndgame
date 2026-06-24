# D&D AI Dungeon Master

A fully playable D&D 5e adventure game built in Python. Create a character with the GUI character builder, then play through a text adventure where an AI Dungeon Master narrates the world, adjudicates rules, and runs combat — powered by a free local model via Ollama.

---

## Project Status

| Module | Status | Description |
|---|---|---|
| `models/character.py` | ✅ Complete | Character data model, save/load |
| `models/dice.py` | ✅ Complete | Dice rolling engine |
| `models/game_state.py` | ✅ Complete | Session persistence and combat state |
| `models/combat.py` | ✅ Complete | Turn-based combat engine |
| `models/dm.py` | ✅ Complete | AI Dungeon Master (Ollama) |
| `controllers/game_controller.py` | ✅ Complete | Game logic — combat, skills, enemies |
| `views/desktop/d20_roller.py` | ✅ Complete | 3D animated d20 roll window |
| `views/desktop/app.py` | ✅ Complete | Main game interface (GUI) |
| `views/desktop/character_builder/` | ✅ Complete | Full GUI character builder |
| `models/progression.py` | 🔜 Next | XP thresholds, level-up logic, feature charges |
| `views/web/api.py` | 🚧 Stub | Future web frontend (Flask/FastAPI) |

> **Next milestone:** Full D&D 5e character progression — XP tracking, level-up dialog (HP roll, ASI/Feat, subclass, spell selection), feature charge tracking, short/long rest UI, and a dev test panel for simulating level-ups.

---

## Gameplay

Launch with:
```
python main.py
```

### Main Menu

Choose **New Adventure** to pick a character and begin, or **Resume Session** to continue from where you left off.

<img src="docs/screenshots/01_startup.png" alt="Main menu — New Adventure or Resume Session" width="280"/>

---

### The Game Interface

Type actions in the input bar — the AI DM narrates the world and drives the story. The right-hand sidebar tracks your character's HP, AC, ability scores, saving throws, skills, and attack options in real time.

<img src="docs/screenshots/06_main_game.png" alt="Main game interface showing narration and character sidebar" width="700"/>

---

### Skill Checks — 3D Animated d20

When the DM triggers a skill check, a **Roll** button appears in the narration. Click it to open the 3D d20 window — click the die to spin it, and it eases to a stop landing exactly on your result. Each of the 20 possible roll values has its own pre-computed animation.

<img src="docs/screenshots/08_d20_roller.png" alt="3D animated d20 roller showing a roll of 17" width="200"/>

---

### Combat

Combat starts automatically when the DM encounters enemies. A `[COMBAT:]` event spins up the initiative engine — everyone rolls, and turns proceed in order. The narration shows the initiative list; the sidebar's **COMBAT** section tracks every combatant's current HP live. Your **ATTACKS** become clickable buttons that open the d20 roller for the attack roll.

<img src="docs/screenshots/09_combat.png" alt="Combat encounter — initiative order, narration, and attack buttons" width="700"/>

The sidebar combat tracker with HP bars for all combatants:

<img src="docs/screenshots/10_combat_sidebar.png" alt="Sidebar showing the combat initiative tracker and attack buttons" width="200"/>

**During combat:**
- Roll for initiative the same way as skill checks — click the die, it lands on your result
- Choose your attack from the sidebar buttons each turn; the d20 determines whether you hit
- Enemy turns resolve automatically with narrated outcomes
- Death saves trigger automatically when the player reaches 0 HP
- Sessions save on quit and resume mid-combat

---

## Architecture

The project follows a clean MVC structure so the same game logic can power a future web frontend with no rewriting.

```
dndgame/
├── main.py                   # Entry point: python main.py
│
├── models/                   # Pure logic — no UI, no framework imports
│   ├── character.py
│   ├── dice.py
│   ├── game_state.py
│   ├── combat.py
│   └── dm.py
│
├── controllers/              # Orchestrates models, returns plain dicts
│   └── game_controller.py   # Same functions called by Tkinter or Flask
│
├── views/
│   ├── desktop/              # Tkinter desktop app
│   │   ├── app.py            # GameApp — pure UI, calls controller
│   │   ├── d20_roller.py     # 3D animated d20
│   │   └── character_builder/
│   │       ├── character_builder_app.py
│   │       ├── dnd_data.py
│   │       ├── spells.py
│   │       └── ddb_import.py
│   └── web/                  # Future web frontend
│       └── api.py            # Flask/FastAPI endpoints (stub)
│
└── data/
    ├── characters/           # Saved character JSON files (gitignored)
    ├── sessions/             # Saved session JSON files (gitignored)
    ├── dm_config.json        # Backend/API key config (gitignored)
    └── dm_config.example.json
```

**Models** contain pure game logic with no UI imports. **Controllers** orchestrate models and return plain dicts — identical whether called from Tkinter or a Flask API. **Views** handle presentation only: Tkinter today, HTML/JS tomorrow.

---

## Character Builder

A complete GUI-driven D&D 5e character builder. No text input required — every option is selected from accurate 5e lists, filtered dynamically by prior choices.

**To launch:**
```
python main.py
```
Then click **New Adventure → Create Character**, or run directly:
```
cd views/desktop/character_builder
python character_builder_app.py
```

The builder opens with a left-panel section list and a live character sheet preview on the right:

<img src="docs/screenshots/03_character_builder.png" alt="Character builder — section list and live character sheet preview" width="600"/>

Clicking a section opens a focused dialog. The **Basic Info** dialog covers name, race, class, background, alignment, and level:

<img src="docs/screenshots/04_basic_info.png" alt="Basic Info dialog with race, class, background selectors" width="380"/>

Every picker is a filterable list. Here's the race picker — 28 options with a Details button for lore and racial traits:

<img src="docs/screenshots/05_race_picker.png" alt="Race picker showing all 28 D&D 5e race options" width="200"/>

### What it covers

- **Basic Info** — Name, Race (28 options with lore + trait details), Class (13), Subclass (filtered by class, only appears at level 3+), Background (37 with proficiency + feature details), Alignment, Level/XP
- **Ability Scores** — Standard Array (filtered dropdowns), Point Buy (27-point budget), or Manual entry. Racial bonuses auto-applied — flexible bonuses (Half-Elf, Human Variant) have interactive pickers.
- **Proficiencies** — Saving throws, skills, languages, armor & weapon proficiencies, tools. Class and background grants auto-applied.
- **Spellcasting** — Only shown for caster classes. Spell slots auto-calculated by level and caster type (full/half/warlock). Cantrip and spell pickers per level.
- **Equipment** — Weapons tab (filtered to class proficiencies), equipment packs, item list, currency, worn armor picker (drives AC calculation).
- **Features & Traits** — Read-only view of racial traits, class features by level, background feature, and custom features.
- **Personality** — Traits, ideals, bonds, flaws, and backstory with background-based suggestion buttons.

**Auto-derived (not editable):**
- HP calculated from class hit die + CON modifier × level
- AC calculated from equipped armor (with Barbarian/Monk unarmored defense)
- Attacks auto-generated from equipped weapons with proficiency and modifier applied
- Speed set by race

---

## AI Dungeon Master Setup

The DM runs locally via Ollama. Copy `data/dm_config.example.json` to `data/dm_config.json` and configure it:

1. Install Ollama: `winget install Ollama.Ollama` (starts automatically in background)
2. Pull the recommended model: `ollama pull dolphin-llama3`
3. Edit `data/dm_config.json`:
```json
{
  "model": "dolphin-llama3"
}
```

Other models that work well: `llama3.1`, `mistral`, `gemma2`

---

## Core Modules

### `models/character.py`
Character data model used by both the builder and the game engine.
- `empty_character()` — blank character dict
- `save_character(char)` / `load_character(name)` / `list_characters()`
- `modifier(score)` — D&D ability modifier formula
- `proficiency_bonus(level)` — standard 5e proficiency progression

### `models/dice.py`
Pure Python dice engine. No API calls.
- Supports d4, d6, d8, d10, d12, d20, d100
- `roll_dice("2d6+3")` — full notation parsing
- `d20_check(modifier, advantage, disadvantage)` — with nat20/nat1 flags
- `critical_damage(notation)` — doubles dice on a crit
- `hit_die("d8", con_mod)` — short rest HP recovery
- `death_save()` — includes nat1 double-failure per 5e RAW

### `views/desktop/d20_roller.py`
3D animated d20 roll window. Renders a proper icosahedron with perspective projection and gold shading. Each face displays its number (1–20, opposite faces sum to 21). Each roll value 1–20 has its own unique pre-computed animation that spins naturally and lands exactly on the correct face via a single smooth ease-out deceleration curve. Used for skill checks, initiative, and player attacks.

### `models/game_state.py`
JSON session persistence. Saves to `data/sessions/`. Keeps mid-game character state (current HP, spell slots used, conditions) separate from the permanent character sheet.
- Scene history, story flags, transient HP/slots/conditions
- Full combat state: initiative order, turn tracker, per-combatant HP and conditions
- Long rest / short rest helpers

### `models/combat.py`
Turn-based combat engine. Uses `dice.py` and `game_state.py`.
- Initiative rolling for all combatants
- Attack resolution with automatic condition-based advantage/disadvantage
- Critical hits (doubled dice), death saves (nat1 = double failure)
- Condition tracking (Prone, Poisoned, Stunned, Frightened, etc.)
- XP tallying from defeated enemies

### `models/dm.py`
AI Dungeon Master. Runs via Ollama (local).
- Builds a system prompt from the character sheet for personalized narration
- Maintains full session history for context continuity
- Parses structured game events from DM responses:
  - `[COMBAT: Goblin×2, Hobgoblin×1]` — triggers the combat engine
  - `[CHECK: Perception DC13]` — requests a skill check
  - `[SCENE: The Village Square]` — updates the current location
- `from_config()` — loads backend settings from `data/dm_config.json`

### `controllers/game_controller.py`
Orchestrates model calls and returns plain dicts. Called identically by the Tkinter UI and future web API.
- `setup_combat(session, char, enemy_specs, d20_initiative)` — builds initiative order
- `process_attack(session, char, weapon_name, target_name, d20_value)` — resolves attack
- `process_skill_check(char, skill, dc, d20_value)` — resolves skill check
- `process_enemy_turn(session)` — runs one enemy action
- `process_death_save(session)` — rolls and resolves a death save
- `ENEMY_STATS` — stat blocks for 20 monster types

---

## Requirements

```
pip install requests
```

- Python 3.8+
- `tkinter` (included with Python on Windows)
- `requests` — for DM API calls (Ollama)
- Ollama installed locally

## Bug Fixes

Bugs discovered and fixed in order of discovery.

---

### 1. Character-select Listbox clears selection on button click (`char_lb`)

**Where:** `views/desktop/app.py` → `_show_character_page()` → `char_lb` Listbox.

**Symptom:** Clicking **Begin →** after selecting a character appeared to do nothing. The button would silently return without starting the game. No error was shown to the user because the error label (`_dlg_err`) was positioned at the very bottom of the dialog window and was obscured.

**Root cause:** Tkinter Listbox defaults to `exportselection=True`. When focus moves to another widget (the "Begin →" button), the Listbox automatically clears its selection. `begin()` then called `char_lb.curselection()`, got an empty tuple, and returned early with the message `"Select a character first."` — which was never seen.

**Fix:** Added `exportselection=False` to the `char_lb` Listbox constructor in `views/desktop/app.py` so the selection is retained when the widget loses focus.

---

### 2. Session-select Listbox clears selection on button click (`ses_lb`)

**Where:** `views/desktop/app.py` → `_show_resume_page()` → `ses_lb` Listbox.

**Symptom:** Identical to bug 1 but on the **Resume Session** path — clicking **Resume →** after selecting a session did nothing.

**Root cause:** Same as bug 1: the `ses_lb` Listbox was also missing `exportselection=False`.

**Fix:** Added `exportselection=False` to the `ses_lb` Listbox constructor in `views/desktop/app.py`.

---

### 3. Character `hp` field schema not enforced — `init_hp()` crashes on integer `hp`

**Where:** `models/game_state.py` → `init_hp()`.

**Symptom:** When a character is loaded whose `hp` field is stored as a plain integer (e.g. `28`) rather than the schema dict (`{"max": 28, "current": 28, "temp": 0}`), `init_hp()` raises `AttributeError: 'int' object has no attribute 'get'`. Because this is called inside the `begin()` callback with no surrounding `try/except`, the exception is swallowed silently by Tkinter and the dialog stays open with no feedback to the user — indistinguishable from bug 2 or 3.

**Root cause:** `empty_character()` in `models/character.py` correctly initialises `hp` as a dict, and the character builder always produces this format. However, there is no validation at the `save_character` / `load_character` boundary to catch a malformed `hp` field, and `init_hp()` has no defensive check.

**Fix (immediate):** Ensure all character JSON files store `hp` as `{"max": N, "current": N, "temp": 0}`. A more robust fix would be to add a guard in `init_hp()`:
```python
def init_hp(session, character):
    hp = character["hp"]
    max_hp = hp.get("max", 1) if isinstance(hp, dict) else hp
    if session["current_hp"] is None:
        session["current_hp"] = max_hp
```

---

## Repository

```
git clone https://github.com/Smlcrp/dndgame.git
```
