# D&D AI Dungeon Master — Project Context

## Security Constraint (NEVER SKIP)
**Always warn the user before making any Claude API calls that will cost tokens. Get explicit confirmation before proceeding.** This applies to any AI Dungeon Master calls, `dm.py` testing, or any Anthropic API invocation.

---

## Project Vision
A fully playable D&D 5e adventure game with an AI Dungeon Master powered by the Claude API. The player builds a character, then plays through a text/GUI adventure where Claude acts as the DM — describing scenes, adjudicating rules, and running combat.

## Planned Full Architecture
```
dndgame/
├── character.py              # Core character data model, save/load, helpers
├── characters/               # Saved character JSON files (gitignored)
├── Character Builder/
│   ├── character_builder_app.py   # Main GUI character builder (COMPLETE)
│   ├── dnd_data.py               # Complete D&D 5e rules data (COMPLETE)
│   ├── spells.py                 # Full spell lists by class/level (COMPLETE)
│   ├── ddb_import.py             # D&D Beyond import (COMPLETE)
│   ├── character_builder.py      # Legacy CLI builder (unused, kept for reference)
│   └── Launch Character Builder.bat
├── dice.py                   # (PLANNED) Dice rolling engine
├── combat.py                 # (PLANNED) Combat system
├── game_state.py             # (PLANNED) Game state persistence
├── dm.py                     # (PLANNED) AI Dungeon Master (Claude API)
└── game.py                   # (PLANNED) Main game interface
```

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
- **Combat Stats** — removed as a clickable section. HP, AC, speed, initiative, hit die, and passive perception are computed automatically on every refresh from class/race/ability scores/equipped armor and written directly to `self.char`. AC handles Barbarian and Monk unarmored defense formulas.
- **Attacks** — removed as a clickable section. Auto-generated from weapons in the Equipment list (cross-referenced against `WEAPONS` dict). Proficiency applied via `_weapon_proficient()`. Monk Unarmed Strike auto-added (Martial Arts die scales by level). Attacks update live when Equipment is saved.

**7 clickable section dialogs (all modal Toplevels with grab_set):**
1. **Basic Info** — name entry, Race/Class/Subclass/Background/Alignment pickers. Race picker includes a "Details" button showing lore, size, speed, ability bonuses, languages, key advantages, and all racial traits. Subclass list filters to selected class.
2. **Ability Scores** — Standard Array (dropdowns that filter to unselected values only), Point Buy, or Manual. Racial bonuses auto-applied from `RACIAL_BONUSES["fixed"]`. Half-Elf and Human (Variant) show flexible bonus pickers. Live totals and modifiers update as you pick.
3. **Proficiencies** — Tabbed: Saving Throws, Skills, Languages, Armor & Weapons, Tools.
4. **Spellcasting** — only visible when selected class can cast spells (checked via `CLASS_SPELLCASTING`). Spell slot tracker, cantrips tab, one tab per spell level.
5. **Equipment** — Tabbed: Weapons (filtered to class proficiencies, adds to equipment list), Equipment Packs, Equipment List, Currency. Worn Armor picker at top (drives AC calculation).
6. **Features & Traits** — Tabbed read-only: Racial Traits, Class Features, Background Feature, Custom Features.
7. **Personality** — Text widgets for traits/ideals/bonds/flaws/backstory with background-based suggestions.

**Bottom bar actions:** Save, Load, Delete, New, Quit.

**Character sheet preview** shows: name/race/class/level, all 6 abilities with modifiers, full combat block (HP, AC, initiative, speed, proficiency bonus, hit die, passive perception, worn armor), attacks with proficiency notes, spellcasting, equipment, and personality traits.

### `Character Builder/dnd_data.py`
Comprehensive D&D 5e data module. Key exports:
- `RACES` — list of 29 race names
- `CLASSES` — list of 13 class names
- `SUBCLASSES` — dict: class → list of subclass names
- `BACKGROUNDS` — list of 37 background names
- `ALIGNMENTS` — 9 alignments
- `RACIAL_BONUSES` — dict: race → `{"fixed": {ability: bonus}, "flexible": {count, amount, exclude} or None}`
- `RACE_DESCRIPTIONS` — dict: race → lore paragraph string (accurate D&D 5e descriptions for all 29 races)
- `STANDARD_ARRAY` — [15,14,13,12,10,8]
- `POINT_BUY_COSTS` — dict: score → point cost (8–15)
- `POINT_BUY_BUDGET` — 27
- `ABILITIES` — ['strength','dexterity','constitution','intelligence','wisdom','charisma']
- `ABILITY_LABELS` — dict: ability → display name
- `CLASS_PRIMARY_STATS` — dict: class → list of primary abilities
- `CLASS_SAVING_THROWS` — dict: class → list of save abilities
- `BACKGROUND_PROFICIENCIES` — dict: background → {skills_fixed, skills_choose, tools_fixed, tools_choose, languages, languages_exotic}
- `ALL_SKILLS` — list of 18 skills
- `ALL_LANGUAGES` / `ALL_STANDARD_LANGUAGES` / `ALL_EXOTIC_LANGUAGES`
- `ARTISAN_TOOLS` / `GAMING_SETS` / `MUSICAL_INSTRUMENTS`
- `CLASS_HIT_DICE` — dict: class → "d8" etc.
- `HIT_DIE_AVERAGES` — dict: "d8" → 5 etc.
- `RACE_SPEED` — dict: race → speed in ft
- `ARMOR_TABLE` — dict: armor name → {ac_base, max_dex, stealth_dis, type}
- `CLASS_SKILLS` — dict: class → {count, from: list or "any"}
- `CLASS_ARMOR_PROFS` / `CLASS_WEAPON_PROFS`
- `RACE_LANGUAGES` / `RACE_EXTRA_LANGUAGES`
- `CLASS_SPELLCASTING` — dict: class → {type: "full/half/warlock", ability, prepares} or None
- `FULL_CASTER_SLOTS` / `HALF_CASTER_SLOTS` / `WARLOCK_SLOTS` / `CANTRIPS_KNOWN`
- `WEAPONS` — dict: name → {damage, type, props, cat}
- `WEAPON_CATEGORIES` — ["Simple Melee","Simple Ranged","Martial Melee","Martial Ranged"]
- `CLASS_STARTING_GOLD` / `EQUIPMENT_PACKS`
- `BACKGROUND_FEATURES` — dict: background → (feature_name, description)
- `RACIAL_TRAITS` — dict: race → [(name, description), ...]
- `CLASS_FEATURES` — dict: class → {level: [feature_names]}
- `PERSONALITY_SUGGESTIONS` — dict: background → {traits, ideals, bonds, flaws}
- `get_personality_suggestions(background)` — returns suggestions dict

### `Character Builder/spells.py`
- `CANTRIPS` — dict: class → [(name, school, ritual, concentration)]
- `SPELLS` — dict: class → {level: [(name, school, ritual, concentration)]}
- `get_spells_for_class(cls, level)` — returns available spells dict for character level
- Coverage: Artificer, Bard, Cleric, Druid, Paladin, Ranger, Sorcerer, Warlock, Wizard

### `Character Builder/ddb_import.py`
D&D Beyond character import via their API. Uses threading for the network call (only place threads are used). Kept separate — don't integrate into the main app's thread model.

---

## Coding Conventions
- **GUI:** Tkinter, dark theme. Colors: `BG="#1a1a2e"`, `ACCENT="#c8a951"` (gold), `INPUT_BG="#0f0f1a"`, `PANEL="#16213e"`, `BTN_BG="#2a2a4a"`, `FG="#e0e0e0"`, `DIM="#888888"`, `GREEN="#4caf50"`, `RED="#e05050"`, `BLUE="#5b8cdc"`
- **Fonts:** `FONT_TITLE=("Segoe UI",14,"bold")`, `FONT_HDR=("Segoe UI",11,"bold")`, `FONT_BODY=("Segoe UI",10)`, `FONT_SM=("Segoe UI",9)`
- **Dialogs:** Modal `Toplevel` with `grab_set()` + `wait_window()`. Helper `_dlg()` creates and centers them. `_ok_cancel()` adds Save/Cancel bar.
- **No threads** in the character builder (pure GUI callbacks).
- **No comments** unless the WHY is non-obvious.
- **Python 3.14**, Windows 11, launched with `python` (not `pythonw`).
- **Import path:** `sys.path.insert(0, str(Path(__file__).parent.parent))` in Character Builder files to reach `character.py`.
- **`_pick_from_list()`** accepts an optional `detail_fn(parent, item)` callback; when provided a "Details" button appears next to "Select" in the picker dialog.
- **`_weapon_proficient(cls, name, cat)`** — module-level function for checking weapon proficiency against `CLASS_WEAPON_PROFS`. Handles "Simple weapons"/"Martial weapons" group strings and specific named weapons (normalises plurals).
- **Auto-calc methods:** `_calc_combat_stats()` and `_calc_attacks()` are called at the start of every `_refresh_preview()` and write results directly back to `self.char` so saves always have current values.

## What to Build Next
In order of dependency:

1. **`dice.py`** — Dice rolling engine (d4/d6/d8/d10/d12/d20/d100, advantage/disadvantage, modifiers). No API calls, pure logic.
2. **`game_state.py`** — Persist the active game session (current scene, inventory changes mid-game, combat state). JSON-based like characters.
3. **`combat.py`** — Turn-based combat engine: initiative, attack resolution, damage, conditions, death saves. Uses `dice.py` and `character.py`.
4. **`dm.py`** — AI Dungeon Master using Claude API. **WARN USER BEFORE ANY TESTING — costs tokens.** Takes game state + player action, returns DM narration + structured game events (combat start, skill check request, etc.).
5. **`game.py`** — Main game interface tying everything together. GUI window: scene description panel, player input, character sheet sidebar.

## GitHub
Repository: https://github.com/Smlcrp/dndgame
Clone: `git clone https://github.com/Smlcrp/dndgame.git`
