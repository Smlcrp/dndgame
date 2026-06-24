# D&D AI Dungeon Master — Project Context

## Security Constraint (NEVER SKIP)
**Always warn the user before making any Claude API calls that will cost tokens. Get explicit confirmation before proceeding.** This applies to any AI Dungeon Master calls, `dm.py` testing, or any Anthropic API invocation.

---

## Project Vision
A fully playable D&D 5e adventure game with an AI Dungeon Master powered by the Claude API. The player builds a character, then plays through a text/GUI adventure where Claude acts as the DM — describing scenes, adjudicating rules, and running combat.

## Full Architecture
```
dndgame/
├── character.py              # ✅ Core character data model, save/load, helpers
├── characters/               # Saved character JSON files (gitignored)
├── Character Builder/
│   ├── character_builder_app.py   # ✅ Main GUI character builder
│   ├── dnd_data.py               # ✅ Complete D&D 5e rules data
│   ├── spells.py                 # ✅ Full spell lists by class/level
│   ├── ddb_import.py             # ✅ D&D Beyond import
│   ├── character_builder.py      # Legacy CLI builder (unused, kept for reference)
│   └── Launch Character Builder.bat
├── dice.py                   # ✅ Dice rolling engine
├── game_state.py             # ✅ Session persistence and combat state
├── combat.py                 # ✅ Turn-based combat engine
├── dm.py                     # ✅ AI Dungeon Master (Ollama + Gemini)
├── dm_config.json            # Gitignored — backend/API key config
├── dm_config.example.json    # Committed template for dm_config.json
├── sessions/                 # Saved session JSON files (gitignored)
└── game.py                   # 🚧 Main game interface (GUI) — in progress
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
1. **Basic Info** — name entry, Race/Class/Subclass/Background/Alignment pickers, Level/XP spinboxes. Race picker includes a "Details" button showing lore, size, speed, ability bonuses, languages, key advantages, and all racial traits. Background picker includes a "Details" button showing lore, skill/tool/language proficiencies, and the background feature. Subclass row is hidden when level < 3 (appears at level 3+, clears if level drops back below 3). Subclass list filters to selected class.
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
- `RACES` — list of 28 race names
- `CLASSES` — list of 13 class names
- `SUBCLASSES` — dict: class → list of subclass names
- `BACKGROUNDS` — list of 37 background names
- `ALIGNMENTS` — 9 alignments
- `RACIAL_BONUSES` — dict: race → `{"fixed": {ability: bonus}, "flexible": {count, amount, exclude} or None}`
- `RACE_DESCRIPTIONS` — dict: race → lore paragraph string (accurate D&D 5e descriptions for all 28 races)
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
- `BACKGROUND_DESCRIPTIONS` — dict: background → lore paragraph string (accurate D&D 5e descriptions for all 37 backgrounds)
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

### `dice.py`
Pure logic dice engine — no API calls, no imports beyond `random` and `re`. All functions return dicts so callers get full context for narration.

- `roll(sides)` — single die, validates against `VALID_DICE = {4,6,8,10,12,20,100}`
- `roll_dice(notation)` — parses "2d6+3", "d20", "3d6-1" etc. Returns `{notation, rolls, modifier, total}`
- `d20_check(modifier, advantage, disadvantage)` — advantage/disadvantage cancel if both True. Returns `{rolls, kept, modifier, total, nat20, nat1}`
- `damage(notation)` — alias for `roll_dice`, named for call-site clarity
- `critical_damage(notation)` — doubles the dice count, keeps same modifier ("2d6+3" → 4d6+3). Returns `{..., critical: True}`
- `hit_die(die_str, con_mod)` — accepts "d8" or "1d8", uses regex (not lstrip) to avoid corrupting d12/d10. Minimum total is 1. Returns `{roll, con_mod, total}`
- `death_save()` — 10+ success, 20 = critical (regain 1 HP), 1 = double failure (two failures instead of one, per 5e RAW). Returns `{roll, success, critical, double_fail}`
- `initiative(dex_mod)` — d20 + DEX mod. Returns `{roll, modifier, total}`

### `combat.py`
Turn-based combat engine. Uses `dice.py`, `game_state.py`, and `character.py`. Pure logic — no UI or API calls.

**Enemy format:** `{name, hp, max_hp, ac, initiative_mod, attacks: [{name, bonus, damage, damage_type}], is_player: False, conditions: [], xp}`

**Functions:**
- `build_enemy(name, hp, ac, attacks, initiative_mod, xp)` — convenience constructor
- `setup_combat(session, character, enemies)` — rolls initiative for all, calls `gs.start_combat()`, returns sorted order
- `resolve_attack(session, attacker, target, attack_bonus, damage_notation, advantage, disadvantage)` — core attack logic; auto-applies condition-based adv/disadv; handles nat20 crits (doubled dice); returns `{attacker, target, target_ac, roll, hit, damage, new_hp, killed, critical}`
- `player_attack(session, character, weapon_name, target_name, advantage, disadvantage)` — looks up weapon from `character["attacks"]`, calls `resolve_attack`
- `enemy_attack(session, enemy_name, attack_index)` — enemy attacks the player; syncs damage to `session["current_hp"]`
- `handle_death_save(session)` — rolls death save, updates `session["death_saves"]`; handles nat20 (revived at 1 HP), nat1 (double failure); returns `{..., outcome: "revived"/"stable"/"dead"/"ongoing"}`
- `end_turn(session)` — advances to next living combatant, skips dead; increments round when order wraps
- `combat_summary(session)` — snapshot dict for DM narration
- `xp_from_combat(session)` — sums XP from all defeated enemies

**Conditions tracked:** Prone, Paralyzed, Stunned, Unconscious, Blinded grant advantage to attackers; Prone, Blinded, Poisoned, Frightened, Restrained, Exhaustion impose disadvantage on the afflicted attacker.

### `game_state.py`
JSON-based session persistence. Saves to `sessions/<name>.json`. Separates transient mid-game state from the permanent character sheet so a long rest or combat doesn't corrupt the saved character.

**Session dict keys:**
- `character_name`, `session_name` — identity
- `location`, `scene`, `history` — scene state. `history` is a list of `{role, text}` entries ("dm"/"player")
- `flags` — arbitrary story booleans/values, e.g. `{"rescued_villager": True}`
- `current_hp`, `temp_hp`, `hit_dice_spent`, `spell_slots_used`, `conditions`, `death_saves`, `stable` — transient character state
- `in_combat`, `round`, `initiative_order`, `current_turn` — combat state. `initiative_order` is sorted descending by initiative; each entry is `{name, initiative, hp, max_hp, is_player, conditions}`

**Functions:**
- `empty_session(character_name, session_name)` — blank session dict
- `save_session(session)` / `load_session(name)` / `list_sessions()` / `delete_session(name)`
- `add_history(session, role, text)` / `set_flag(session, key, value)` / `get_flag(session, key)`
- `init_hp(session, character)` — sets `current_hp` from character max on first load
- `apply_damage(session, amount)` — consumes temp HP first
- `apply_healing(session, amount, max_hp)`
- `use_spell_slot(session, level)` / `restore_spell_slot(session, level)`
- `long_rest(session, character)` — restores HP, slots, clears conditions; recovers half level in hit dice
- `short_rest(session, hp_gained)` — applies hit die healing
- `start_combat(session, combatants)` / `end_combat(session)` / `advance_turn(session)`
- `current_combatant(session)` — returns the active combatant dict
- `apply_combat_damage(session, name, amount)` / `apply_combat_healing(session, name, amount)`
- `add_condition(session, name, condition)` / `remove_condition(session, name, condition)`
- `living_combatants(session)` / `enemies_alive(session)`

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

### `dm.py`
AI Dungeon Master. Supports two free backends — Ollama (local) and Google Gemini (cloud). Config loaded from `dm_config.json` (gitignored).

- `DungeonMaster(backend, model, api_key)` — main class
- `_build_system_prompt(character)` — personalised system prompt from character sheet
- `_messages_for_ollama(session, character, player_input)` — OpenAI-style message list
- `_messages_for_gemini(session, character, player_input)` — Gemini contents array
- `_call_ollama(messages)` — POST to `http://localhost:11434/api/chat`, stream=False
- `_call_gemini(system_prompt, contents)` — POST to Gemini REST API with API key
- `_parse_events(raw_text)` — extracts `[CHECK: Skill DC##]`, `[COMBAT: Name×N]`, `[SCENE: Location]` tags; returns `(clean_narration, events_list)`
- `respond(session, character, player_input)` — main entry point; saves both turns to session history; returns `{"narration": str, "events": list}`
- `load_config(path)` / `save_config(config, path)` / `from_config(path)` — config helpers

**WARN USER before any DM testing — Gemini API calls cost quota.**

### `game.py` *(in progress)*
Main game interface. Launch with `python game.py`. Uses `GameApp` class.

**Module-level constants:**
- `ENEMY_STATS` — dict of ~20 common 5e monsters with hp, ac, xp, initiative_mod, attacks list
- `_enemy_defaults(name, level)` — fallback scaled stat block for unlisted enemies
- `SKILL_ABILITIES` — dict mapping skill/ability names to ability score keys

**`GameApp.__init__`:** Creates root window (1100×700), calls `_build_ui()`, then `_startup_dialog()` after 150ms.

**UI layout (`_build_ui`):**
- Header bar — character name (gold) + current location (dim)
- Left: narration `Text` widget (Consolas, INPUT_BG, read-only). Tags: `dm`, `player`, `system`, `hit`, `miss`, `danger`, `header`
- Right sidebar (220px, PANEL): HP label + canvas HP bar, AC, speed, conditions, combat tracker frame, Save & Quit button
- Bottom input area: explore mode (text entry + Send) or combat mode (attack buttons), swapped via `_build_explore_input()` / `_build_combat_input()`

**Startup flow (multi-page dialog in one Toplevel):**
- `_startup_dialog()` — creates the dialog shell with title label and body/error frames; calls `_show_mode_page()`
- `_clear_body()` — destroys all body children, clears error label
- `_btn_large(parent, text, sub, command)` — styled clickable card; hover highlights entire card gold (frame + both labels change on Enter/Leave); all three widgets bound to click
- `_show_mode_page(d)` — Page 1: "New Adventure" and "Resume Session" large buttons
- `_show_character_page(d)` — Page 2a: scrollable Listbox of characters; "+ New Character" (subprocess builder, auto-refresh), "Delete" (with messagebox confirm, unlinks `characters/<name>.json`), "← Back", "Begin →"
- `_show_resume_page(d)` — Page 2b: scrollable Listbox of sessions; loads session + its character; "← Back", "Resume →"

**Adventure flow:**
- `_start_adventure(new)` — updates header, updates sidebar, displays opening prompt, calls DM in thread
- `_send_action()` — reads input, displays player text, disables input, calls DM in thread
- `_dm_call(player_input)` — daemon thread; calls `self.dm.respond()`; posts result via `root.after(0, ...)`
- `_handle_dm_response(result)` — displays narration, processes events (combat_start → `_start_combat`, skill_check → `_handle_skill_check`, scene_change → updates location), saves session
- `_start_combat(enemies)` — builds enemy list from `ENEMY_STATS` / `_enemy_defaults`, calls `cb.setup_combat()`, updates sidebar, calls `_next_turn()`
- `_next_turn()` — checks combat end; on player turn → `_build_combat_input()`; on enemy turn → `_do_enemy_turn()`
- `_do_player_attack(weapon_name)` — calls `cb.player_attack()`, displays result, calls `_end_combat()` or `end_turn()` + `_next_turn()`
- `_do_enemy_turn()` — calls `cb.enemy_attack()`, displays result, checks player HP (0 → death saves), calls `end_turn()` + `_next_turn()`
- `_display_attack_result(result, attacker_name)` — formats hit/miss/kill line with colour tags
- `_end_combat(xp)` — calls `gs.end_combat()`, awards XP, re-enables explore input, tells DM combat ended
- `_handle_death_saves(session)` — calls `cb.handle_death_save()`, displays outcome, marks DEAD or stable
- `_handle_skill_check(event)` — auto-rolls the check with proficiency if applicable, displays result, feeds outcome to DM
- `_display(text, tag)` — appends to narration Text, auto-scrolls
- `_erase_last_line()` — removes last line from narration (used for "thinking…" spinner)
- `_update_sidebar()` — refreshes HP label + canvas bar (green/yellow/red by percentage), AC, speed, conditions, combat initiative list
- `_set_input_enabled(enabled)` — enables/disables the input entry
- `_save_and_quit()` — saves session if active, destroys root

## What to Build Next

- **Continue `game.py`** — exercise and test the full play loop end-to-end: narration → skill checks → combat → death saves → rest → session save/resume

## GitHub
Repository: https://github.com/Smlcrp/dndgame
Clone: `git clone https://github.com/Smlcrp/dndgame.git`
