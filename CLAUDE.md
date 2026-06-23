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
Complete rewrite — fully GUI-driven Tkinter app, NO text input except Personality section. Launched via `python character_builder_app.py` or the .bat file.

**Architecture:** Single `CharacterBuilderApp` class, no threads, `self.char` dict held directly. Module-level helpers `_btn()`, `_listbox()`, `_pick_from_list()`, `_pick_suggestion()`.

**Main window:** Left panel (9 clickable section buttons showing ✔/· status), right panel (live character preview in Consolas font), bottom bar (Save/Load/Delete/New/Quit).

**9 section dialogs (all modal Toplevels with grab_set):**
1. **Basic Info** — name entry, Race/Class/Subclass/Background/Alignment pickers (all with searchable list dialogs), Level/XP spinboxes. Subclass list filters to selected class. Class change clears subclass.
2. **Ability Scores** — Standard Array (OptionMenu dropdowns) / Point Buy (8–15 spinboxes, 27-point budget) / Manual (1–30 spinboxes). Racial bonuses auto-applied. Class primary stats marked ★, saving throw proficiencies marked ◇. Live totals and modifiers update as you pick.
3. **Combat Stats** — HP with auto-calc checkbox (class hit die + CON × level), armor picker (auto-calculates AC from ARMOR_TABLE), race speed auto-filled, hit dice type/total/used spinboxes.
4. **Proficiencies** — Tabbed (ttk.Notebook): Saving Throws (class auto-checked/disabled), Skills (multi-select listbox, background skills auto-selected), Languages (race langs auto-selected), Armor & Weapons (class profs auto-checked), Tools.
5. **Attacks** — Left: weapon browser with category radio filter (All/Simple Melee/Simple Ranged/Martial Melee/Martial Ranged), detail label, proficiency+finesse checkboxes, Add Weapon button (auto-calcs attack bonus and damage). Right: current attacks list with remove buttons, custom attack entry row.
6. **Spellcasting** — Class-aware (shows message for non-casters). Spell slot tracker (shows count, used spinbox per level). Tabbed: Cantrips + one tab per spell level with available spells. Slots auto-calculated from FULL_CASTER_SLOTS / HALF_CASTER_SLOTS / WARLOCK_SLOTS by level.
7. **Equipment** — Tabbed: Equipment Packs (checkboxes with item previews, Add button), Equipment List (custom item entry + quantity, remove buttons), Currency (cp/sp/ep/gp/pp spinboxes, starting gold button).
8. **Features & Traits** — Tabbed read-only: Racial Traits, Class Features (levels 1–N), Background Feature. Plus Custom Features tab with add/remove.
9. **Personality** — Text widgets (only section with text input). Suggestions button per field pulls from `get_personality_suggestions(background)`. Fields: Personality Traits, Ideals, Bonds, Flaws, Backstory.

**Bottom bar actions:** Save (calls `save_character`), Load (picker dialog, auto-marks sections done), Delete (removes JSON file), New (clears `self.char`), Quit (confirmation dialog).

### `Character Builder/dnd_data.py`
Comprehensive D&D 5e data module. Key exports:
- `RACES` — list of 29 race names
- `CLASSES` — list of 13 class names
- `SUBCLASSES` — dict: class → list of subclass names
- `BACKGROUNDS` — list of 37 background names
- `ALIGNMENTS` — 9 alignments
- `RACIAL_BONUSES` — dict: race → {ability: bonus}
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
- **Python 3.14**, Windows 11, launched with `python` (not `pythonw` — we moved away from the console-hiding approach).
- **Import path:** `sys.path.insert(0, str(Path(__file__).parent.parent))` in Character Builder files to reach `character.py`.

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
