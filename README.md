# D&D AI Dungeon Master

A fully playable D&D 5e adventure game built in Python. Create a character with the GUI character builder, then play through a text adventure where an AI Dungeon Master narrates the world, adjudicates rules, and runs combat — powered by either a free local model (Ollama) or Google Gemini's free tier.

---

## Project Status

| Module | Status | Description |
|---|---|---|
| `Character Builder/` | ✅ Complete | Full GUI character builder |
| `character.py` | ✅ Complete | Character data model, save/load |
| `dice.py` | ✅ Complete | Dice rolling engine |
| `game_state.py` | ✅ Complete | Session persistence and combat state |
| `combat.py` | ✅ Complete | Turn-based combat engine |
| `dm.py` | ✅ Complete | AI Dungeon Master (Ollama + Gemini) |
| `d20_roller.py` | ✅ Complete | 3D animated d20 roll window |
| `game.py` | 🚧 In Progress | Main game interface (GUI) |

---

## Gameplay

Launch with:
```
cd dndgame
python game.py
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

## Character Builder

A complete GUI-driven D&D 5e character builder. No text input required — every option is selected from accurate 5e lists, filtered dynamically by prior choices.

**To launch:**
```
cd "Character Builder"
python character_builder_app.py
```
Or double-click `Launch Character Builder.bat`.

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

The DM supports two free backends. Copy `dm_config.example.json` to `dm_config.json` and configure one:

### Option A — Google Gemini (free cloud)
No special hardware needed. Free tier: 1,500 requests/day.

1. Go to **aistudio.google.com** and sign in with your Google account
2. Click **Get API key** → **Create API key**
3. Edit `dm_config.json`:
```json
{
  "backend": "gemini",
  "model": "gemini-2.0-flash",
  "api_key": "your-api-key-here"
}
```

### Option B — Ollama (free local, no internet required)
Runs entirely on your machine. Requires 8 GB+ RAM.

1. Install Ollama: `winget install Ollama.Ollama` (starts automatically in background)
2. Pull a model:
   - Standard: `ollama pull llama3.1`
   - Uncensored (mature content): `ollama pull dolphin-mistral`
3. Edit `dm_config.json`:
```json
{
  "backend": "ollama",
  "model": "llama3.1",
  "api_key": ""
}
```

> `dm_config.json` is gitignored — your API key will never be committed to the repo.

---

## Core Modules

### `character.py`
Character data model used by both the builder and the game engine.
- `empty_character()` — blank character dict
- `save_character(char)` / `load_character(name)` / `list_characters()`
- `modifier(score)` — D&D ability modifier formula
- `proficiency_bonus(level)` — standard 5e proficiency progression

### `dice.py`
Pure Python dice engine. No API calls.
- Supports d4, d6, d8, d10, d12, d20, d100
- `roll_dice("2d6+3")` — full notation parsing
- `d20_check(modifier, advantage, disadvantage)` — with nat20/nat1 flags
- `critical_damage(notation)` — doubles dice on a crit
- `hit_die("d8", con_mod)` — short rest HP recovery
- `death_save()` — includes nat1 double-failure per 5e RAW

### `d20_roller.py`
3D animated d20 roll window. Renders a proper icosahedron with perspective projection and gold shading. Click the die to spin it; it decelerates and lands on the accurate pre-computed roll. Used for skill checks, initiative, and player attacks.

### `game_state.py`
JSON session persistence. Saves to `sessions/`. Keeps mid-game character state (current HP, spell slots used, conditions) separate from the permanent character sheet.
- Scene history, story flags, transient HP/slots/conditions
- Full combat state: initiative order, turn tracker, per-combatant HP and conditions
- Long rest / short rest helpers

### `combat.py`
Turn-based combat engine. Uses `dice.py` and `game_state.py`.
- Initiative rolling for all combatants
- Attack resolution with automatic condition-based advantage/disadvantage
- Critical hits (doubled dice), death saves (nat1 = double failure)
- Condition tracking (Prone, Poisoned, Stunned, Frightened, etc.)
- XP tallying from defeated enemies

### `dm.py`
AI Dungeon Master. Supports Ollama (local) and Google Gemini (cloud).
- Builds a system prompt from the character sheet for personalized narration
- Maintains full session history for context continuity
- Parses structured game events from DM responses:
  - `[COMBAT: Goblin×2, Hobgoblin×1]` — triggers the combat engine
  - `[CHECK: Perception DC13]` — requests a skill check
  - `[SCENE: The Village Square]` — updates the current location
- `from_config()` — loads backend settings from `dm_config.json`

### `game.py` *(in progress)*
Main game interface. Full play loop including narration, skill checks, turn-based combat, death saves, and session save/resume. 3D d20 roll window pauses the game at every player roll.

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
