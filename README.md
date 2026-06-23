# dndgame

A D&D 5e adventure game with an AI Dungeon Master, built in Python with a Tkinter GUI.

## Project Structure

```
dndgame/
├── character.py              # Core character data model, save/load, helpers
├── characters/               # Saved character JSON files (gitignored)
│
├── Character Builder/
│   ├── character_builder_app.py   # Main GUI character builder (fully clickable)
│   ├── dnd_data.py               # Complete D&D 5e rules data (races, classes, spells, etc.)
│   ├── spells.py                 # Full spell lists by class and level
│   ├── ddb_import.py             # D&D Beyond character import
│   ├── character_builder.py      # Legacy CLI builder
│   └── Launch Character Builder.bat
│
├── dice.py                   # (planned) Dice rolling engine
├── combat.py                 # (planned) Combat system
├── game_state.py             # (planned) Game state persistence
├── dm.py                     # (planned) AI Dungeon Master (Claude API)
└── game.py                   # (planned) Main game interface
```

## What's Built

### Character Builder
A fully GUI-driven D&D 5e character builder with no text input required (except Personality).
Every option is selected from accurate 5e lists, with selections filtered by prior choices where applicable.

**9 sections:**
- **Basic Info** — Name, Race (29 options), Class (13), Subclass (filtered by class), Background (37), Alignment, Level/XP
- **Ability Scores** — Standard Array, Point Buy (27-point budget), or Manual; racial bonuses auto-applied; class primary stats and saving throw proficiencies highlighted
- **Combat Stats** — HP auto-calculated from class hit die + CON × level, armor picker with auto AC, race speed auto-filled
- **Proficiencies** — Class saving throws auto-checked, skill choices, language picker (race auto-selected), armor/weapon profs, tool proficiencies
- **Attacks** — Weapon browser with category filter, auto-calculated attack bonus and damage, custom attack entry
- **Spellcasting** — Class-aware (non-casters get a message), spell slots auto-calculated by level and caster type, cantrip and spell pickers
- **Equipment** — Equipment pack browser, custom item entry, currency
- **Features & Traits** — Read-only racial traits, class features by level, background feature; custom features tab
- **Personality** — Text fields with clickable suggestion buttons sourced from background

### D&D 5e Data (`dnd_data.py`)
Comprehensive rules data including: all races with traits and speed, all classes with hit dice/armor/weapon/skill proficiencies and spell slots, all 37 backgrounds with proficiencies, armor table with AC calculation, 38 weapons with properties, equipment packs, class features levels 1–20, racial traits, personality suggestions.

## Running

```
cd "Character Builder"
python character_builder_app.py
```

Or double-click `Launch Character Builder.bat`.

## Requirements

- Python 3.8+
- tkinter (included with Python on Windows)
- `requests` (for D&D Beyond import only)
