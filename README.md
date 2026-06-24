# D&D AI Dungeon Master

A fully playable D&D 5e adventure game built in Python. Create a character with the GUI character builder, then play through a text adventure where an AI Dungeon Master narrates the world, adjudicates rules, and runs combat — powered by either a free local model (Ollama) or Google Gemini's free tier.

---

## Project Status

| Module | Status | Description |
|---|---|---|
| `models/character.py` | ✅ Complete | Character data model, save/load |
| `models/dice.py` | ✅ Complete | Dice rolling engine |
| `models/game_state.py` | ✅ Complete | Session persistence and combat state |
| `models/combat.py` | ✅ Complete | Turn-based combat engine |
| `models/dm.py` | ✅ Complete | AI Dungeon Master (Ollama + Gemini) |
| `controllers/game_controller.py` | ✅ Complete | Game logic — combat, skills, enemies |
| `views/desktop/d20_roller.py` | ✅ Complete | 3D animated d20 roll window |
| `views/desktop/app.py` | ✅ Complete | Main game interface (GUI) |
| `views/desktop/character_builder/` | ✅ Complete | Full GUI character builder |
| `views/web/api.py` | 🚧 Stub | Future web frontend (Flask/FastAPI) |

---

## Gameplay

Launch with:
```
python main.py
```

**Startup:**
1. Choose **New Adventure** or **Resume Session**
2. New Adventure → pick a saved character (or launch the builder to create one)
3. The AI DM opens the scene and the adventure begins

**During play:**
- Type actions in the input bar — the DM responds and drives the story
- When a **skill check** is triggered, a **Roll** button appears in the narration — click it to open the 3D d20 window, click the die to spin it, and it lands on your actual roll
- **Combat** starts automatically when the DM encounters enemies — roll for initiative the same way, then choose your attack each turn
- The sidebar tracks HP, AC, conditions, and the combat initiative order live
- Death saves trigger automatically when the player hits 0 HP
- Sessions save on quit and can be resumed from the main menu

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

The DM supports two free backends. Copy `data/dm_config.example.json` to `data/dm_config.json` and configure one:

### Option A — Ollama (free local, no internet required)
Runs entirely on your machine. Requires 8 GB+ RAM.

1. Install Ollama: `winget install Ollama.Ollama` (starts automatically in background)
2. Pull the recommended model: `ollama pull dolphin-llama3`
3. Edit `data/dm_config.json`:
```json
{
  "backend": "ollama",
  "model": "dolphin-llama3",
  "api_key": ""
}
```

Other models that work well: `llama3.1`, `mistral`, `gemma2`

### Option B — Google Gemini (free cloud)
No special hardware needed. Free tier: 1,500 requests/day.

1. Go to **aistudio.google.com** and sign in with your Google account
2. Click **Get API key** → **Create API key**
3. Edit `data/dm_config.json`:
```json
{
  "backend": "gemini",
  "model": "gemini-2.0-flash",
  "api_key": "your-api-key-here"
}
```

> `dm_config.json` is gitignored — your API key will never be committed to the repo.

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
AI Dungeon Master. Supports Ollama (local) and Google Gemini (cloud).
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
- `requests` — for DM API calls (Ollama and Gemini)
- Ollama installed locally **or** a free Google Gemini API key

## Repository

```
git clone https://github.com/Smlcrp/dndgame.git
```
