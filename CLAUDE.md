# D&D AI Dungeon Master — Project Context

## Security Constraint (NEVER SKIP)
**Always warn the user before making any Claude API calls that will cost tokens. Get explicit confirmation before proceeding.** This applies to any AI Dungeon Master calls, `dm.py` testing, or any Anthropic API invocation.

---

## Project Vision
A fully playable D&D 5e adventure game with an AI Dungeon Master. MVC architecture complete. Stage 4 (Flask + HTML/JS/CSS + Electron) is done — the game now runs in the browser at `http://localhost:5000` in addition to the Tkinter desktop app.

**To launch the web version:** `python run_server.py` → open `http://localhost:5000`
**To launch the desktop version:** `python main.py`

## Current File Structure
```
dndgame/
├── main.py                   # Entry point: python main.py → Tkinter desktop app
├── run_server.py             # Web entry point: python run_server.py → Flask on :5000
├── requirements.txt          # flask>=3.0.0, requests>=2.31.0, pytest>=7.0.0
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
│   └── game_controller.py
│
├── character_builder/        # D&D 5e data + DDB import (used by Flask backend)
│   ├── dnd_data.py           # WEAPONS, CLASS_FEATURES, RACES, CLASSES — used by api.py + progression.py
│   ├── spells.py             # Spell list data
│   ├── ddb_import.py         # D&D Beyond scraper (import_from_ddb)
│   ├── character_builder_app.py  # Standalone Tkinter character builder (optional tool)
│   └── Launch Character Builder.bat
│
├── views/
│   └── web/                  # Flask + browser frontend (Stage 4)
│       ├── __init__.py
│       ├── api.py            # Flask app — 24 routes, JSON API, in-memory session state
│       ├── templates/
│       │   └── index.html    # Single-page app shell; loads all JS/CSS
│       └── static/
│           ├── css/
│           │   └── style.css # Dark theme; CSS vars match Tkinter constants
│           └── js/
│               ├── api.js    # API.get/post/del fetch wrappers
│               ├── dice.js   # DiceRoller.show(value, label) animated modal
│               ├── main.js   # SceneManager class + App boot
│               └── scenes/
│                   ├── MainMenuScene.js       # New / Next / Resume cards
│                   ├── CharacterSelectScene.js
│                   ├── PresetScene.js         # One Shot / Quest / Epic
│                   ├── GameScene.js           # Narration + sidebar + input + events
│                   └── LevelUpScene.js        # Multi-step modal (HP→subclass→ASI→spells)
│
├── electron/                 # Electron shell (Stage 4c)
│   ├── main.js               # Spawn Flask, wait for /api/ping, open BrowserWindow
│   └── package.json          # electron + electron-builder config
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

### `character_builder/`
Data package used by the Flask web backend. `dnd_data.py` exports `WEAPONS`, `CLASS_FEATURES`, `RACES`, `CLASSES`. `ddb_import.py` exports `import_from_ddb(url, cobalt_token)`. `character_builder_app.py` is a standalone optional Tkinter tool (not part of the main game).

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

**UI layout:** Header bar, narration Text (Consolas, INPUT_BG), sidebar (220px: HP bar, AC, speed, conditions, combat tracker), input area (explore: entry + Send; combat: attack buttons).

**Startup dialog:** Mode page → Character page or Resume page. `_btn_large()` for clickable cards with hover highlight.

**Game flow:**
- `_start_adventure(new)` → `_dm_call()` in daemon thread → `_handle_dm_response()`
- Events dispatched: `combat_start` → `_start_combat()`, `skill_check` → `_handle_skill_check()`
- Roll button pattern: `_show_roll_button(label, d20_value, on_confirm)` embeds a gold Button in the narration Text widget via `window_create`; clicking opens `D20RollerWindow`
- Combat loop: `_next_turn()` → player turn (`_build_combat_input`) or enemy turn (`_do_enemy_turn`)
- Death saves triggered at 0 HP

---

## Known Issues

- **Ollama CUDA crash on model load** — `exit status 0xc0000409` + `CUDA error: shared object initialization failed` — Root cause: model weights + KV cache overhead can exceed RTX 3060 Ti's 8 GB VRAM. `nous-hermes2:10.7b` is 6.1 GB on disk (~6.5 GB VRAM at Q4). Keep `num_ctx` at 4096 to limit KV cache. Auto-recovery is in place: `api.py` kills `ollama.exe` and restarts with `CUDA_VISIBLE_DEVICES=-1` (CPU fallback), then a gold banner appears in the browser. Do NOT raise `num_ctx` above 4096 on this GPU.
- **DM narration length** — `nous-hermes2:10.7b` routinely ignores the "3-5 sentences" rule and writes 10+ sentence responses. This directly increases TTS generation time and Ollama response time. Prompt says "3–5 sentences" but enforcement is weak.

---

## Known Quirks & Pitfalls

- **Character `hp` field must be a dict** — `init_hp()` in `models/game_state.py` calls `character["hp"].get("max", 1)`. Always store `hp` as `{"max": N, "current": N, "temp": 0}`. `empty_character()` does this correctly; the risk is hand-edited JSON files.

- **`_parse_events` dict comprehension guard order** — In `dm.py:_parse_events`, the `pairs` dict used to parse `[ACTION:]` and `[BONUS:]` tag content has `if "=" in part` as a filter on the outer `for part in content.split(",")` loop. Do NOT move it to a trailing position after the inner `for k, v in [part.split("=", 1)]` — the inner destructuring runs before any trailing `if`, causing a `ValueError` for bare-word entries like `[ACTION: dodge]`.

- **`skill_proficiencies` must be Title Case** — The entire game stores and checks skill proficiencies as Title Case strings (`"Acrobatics"`, `"Sleight of Hand"`) matching `ALL_SKILLS` in `dnd_data.py`. The model layer's `SKILLS` dict uses lowercase_underscore keys but `skill_bonus()` should only be called with those keys for derived-stat calculations, not for checking `skill_proficiencies`. Do not write lowercase_underscore values into `skill_proficiencies`.

- **Companion system — organic introduction only** — The DM's `_build_party_block()` passes companion names to the model as internal anchors for the `[COMPANION: First Last]` tag. The model must NEVER list these names to the player or present companion selection as a choice. The prompt explicitly prohibits this, but if the model recites the roster again, strengthen the prohibition wording. Do NOT remove the roster from the prompt — the model needs it to emit the correct tag.

- **Kokoro TTS — sentence splitting regex** — `respond_stream()` in `dm.py` emits tokens; `GameScene.js` splits the final `data.narration` on `/(?<=[.!?])\s+/` to build the TTS sentence queue. Lookbehind assertions require Chrome 62+/Firefox 78+. The mid-stream first-sentence detection uses `/^(.*?[.!?])\s/s` (dotAll flag). Do not change these to split on commas or colons — it over-splits and causes choppy audio.

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

## Master Roadmap

All planned work for the game lives here. This is the single source of truth — do not create planning lists anywhere else.

---

### ✅ Stage 4d — Retire Tkinter

- [x] **Weapon variants ported to web** — `GET /api/combat/attack-options` + `mode` param on `POST /api/combat/attack`
  - [x] Versatile weapons: one-handed / two-handed buttons with correct damage dice
  - [x] Thrown weapons: thrown option with range label alongside melee
  - [x] Dual wielding: off-hand bonus action with no ability modifier on damage (PHB rule)
  - [x] Actions panel is now clickable — each variant fires `_doAttack(weapon, mode)` directly
- [x] **Deleted `views/desktop/`** — Tkinter app (app.py, dice_roller.py, d20_roller.py) removed
- [x] **Moved `character_builder/`** to project root (still used by Flask web backend for dnd_data + ddb_import)
- [x] **`main.py` now launches Electron** via `npm start` (with auto `npm install` on first run)

---

### Stage 5 — Visual Design Pass

- [ ] **Typography**: replace system fonts with game fonts (Crimson Text or IM Fell for narrative; monospace for rolls)
- [ ] **Color system**: add surface elevation tokens (`--surface-0`, `--surface-1`, `--surface-2`) for card layering
- [ ] **Narration panel**: parchment-style texture background; smooth auto-scroll; animated "DM is thinking…" typing indicator
- [ ] **Sidebar**: collapsible sections; HP bar animates on damage/healing; magic item cards with rarity color border
- [ ] **d20 roller**: CSS keyframe version with glow on nat-20; shake on nat-1
- [ ] **Combat tracker**: highlight active combatant row with pulse animation; dead enemies shown with strikethrough and reduced opacity
- [ ] **Level-up dialog**: full-screen overlay with particle effect on level gain
- [ ] **Responsive layout**: support 900px–1920px window widths

---

### Stage 5b — Kokoro TTS Narrator

- [x] **Re-enable narrator**: Kokoro TTS (`models/narrator.py`, `/api/narrate` route, `_appendPlayButton` in `GameScene.js`) re-enabled with sentence-queue playback
- [x] **UX**: `▶` / `⏹` symbol-only Play button per DM entry; AbortController stop; sequential sentence playback
- [x] **Performance**: model preloaded at Flask startup; first sentence pre-fetched mid-stream for near-instant playback
- [ ] **Dual-voice narration (Option A)**: parse DM narration into narrator segments (outside quotes) and dialogue segments (inside quotes); narrator uses `bm_george`, dialogue uses a second Kokoro voice — no model prompt changes needed

---

### Stage 6 — Distribution

#### GitHub Releases (first)
- [ ] Tag `v1.0.0`; `electron-builder` CI workflow produces `.exe` and `.dmg` on push to `release/*` branches
- [ ] Auto-updater via `electron-updater` reading GitHub Releases API

#### itch.io (second)
- [ ] Store page with screenshots, trailer, pay-what-you-want pricing
- [ ] Butler CLI in CI for automated uploads on release tag

#### Steam (third — see "Steam — Technical Reference" section)
- [ ] Steamworks partner account; AppID configured
- [ ] `SteamAPI_RunCallbacks()` on 1-second interval in `electron/main.js`
- [ ] Steam Overlay: enable GPU acceleration in Electron (`--enable-gpu` launch flag)
- [ ] Steam Cloud: Auto-Cloud for `data/sessions/` and `data/characters/` — config only, no code changes needed
- [ ] Steam Achievements: Steamworks.js / Greenworks bindings in `electron/main.js`; achievement IDs defined in Steamworks portal
- [ ] Steam Deck: verify input mapping; controller-friendly UI pass (larger hit targets, gamepad navigation)

---

### Stage 7 — Content Expansion (post-launch)

- [ ] **Adventure templates**: expand from 8 to 20+; add seafaring, underdark, planar travel, heist themes
- [ ] **Enemy roster**: expand beyond 160 monsters; add legendary actions and lair actions for boss fights
- [ ] **Multiclassing**: add `"multiclass": []` to `empty_character()`; progression table; spell slot merging; feature eligibility checks
- [ ] **New races**: Aasimar, Githyanki, Fairy
- [ ] **New classes**: Artificer, Blood Hunter
- [ ] **Crafting system**: components dropped by enemies; recipes unlock with Arcana/Smith proficiency
- [ ] **World map**: persistent overworld between adventures; unlockable locations
- [ ] **Mod support**: JSON-defined adventure templates, enemies, and items users can drop into `data/`

---

### Stage 8 — Code Audit & Cleanup (post-launch)

- [ ] Delete legacy/duplicate root-level files that survived prior cleanup passes
- [ ] Audit models and controllers for O(n²) loops and redundant recomputation
- [ ] Consolidate repeated patterns (tag parsing, sidebar rendering, dialog scaffolding) into shared helpers
- [ ] Remove unused imports across all files
- [ ] Audit `empty_character()` for fields defined but never read anywhere in the codebase
- [ ] Run coverage report; add tests for untested branches in `models/`
- [ ] Audit `requirements.txt` for installed-but-unused packages

---

### Known Technical Debt

Intentional simplifications — not bugs, but known deviations from the SRD:

- **Enemy saving throws** — use raw d20 with no ability modifier. Per-monster saves deferred to Stage 7 content pass.
- **Prone condition** — grants advantage to all attackers. SRD: ranged attackers should have *disadvantage* vs prone targets. Deferred because attack type (melee vs ranged) is not tracked per attack.
- **`multiclass` field** — Stage 7 item; `empty_character()` does not yet have this field even though Stage 7 documentation references it.

---

### ✅ Completed

#### ✅ Stage 1 — Game Mechanics
- ✅ Turn-based combat: conditions, crits, death saves, enemy AI
- ✅ Character progression: XP awards, level-up dialog (features → HP roll → subclass → ASI/feat → spell learning)
- ✅ 30 PHB feats at ASI levels; spell learning for all caster archetypes
- ✅ In-game economy: `[GOLD: N]` and `[ITEM:]` DM tags; magic weapon/armor bonuses applied in combat
- ✅ DM-driven action parsing via `[ACTION:]` and `[BONUS:]` tags; fallback client-side regex
- ✅ 8 adventure templates; 3 length presets (One Shot / Quest / Epic)
- ✅ Companion system: 10 templates, combat AI, spell slots, death saves
- ✅ D&D Beyond character import (`ddb_import.py`)
- ✅ Passive perception/investigation/insight; natural knowledge checks with 5-tier quality scale
- ✅ ~160 SRD monsters (CR 0–30); 376-test suite, all passing

#### ✅ Stage 2 — Sidebar & Rest UI
- ✅ XP progress bar; feature charges (`[●●○]` style); Inspiration toggle
- ✅ Short Rest (hit-dice spending dialog); Long Rest (one-click confirm)

#### ✅ Stage 3 — DEV Panel
- ✅ Password-gated (F4 / DEV button) — password: `0922`
- ✅ Award XP; level jump Lv2–Lv10; set HP; add condition; spawn test combat; rest buttons

#### ✅ Stage 4a — Flask Backend
- ✅ 24+ API routes; SSE streaming; CUDA crash auto-recovery; `num_ctx` 4096 limit
- ✅ `/api/ollama/mode`; story mode routes; DDB import route; Kokoro TTS narrator

#### ✅ Stage 4b — HTML/JS/CSS Frontend
- ✅ Scene-based vanilla JS; all 5 scenes; animated dice modal
- ✅ Full sidebar (vitals, abilities, saves, skills, spellcasting, inventory, party, combat tracker)
- ✅ DEV panel; Story Mode; Actions reference panel; companion join event; DDB import modal; CPU banner

#### ✅ Stage 4c — Electron Shell
- ✅ Flask subprocess lifecycle; `/api/ping` polling; Ollama GPU→CPU fallback; electron-builder config

#### ✅ Session fixes (2026-06-27)

**Streaming & performance:**
- ✅ `respond_stream()` in `dm.py` switched from `stream=False` (fake streaming) to real Ollama `stream=True` with `iter_lines()` — first tokens now visible within ~1-2 s instead of waiting for full response
- ✅ DM history window trimmed from 20 → 12 entries to reduce per-call token count
- ✅ `[BEGIN]` / `[END]` / `[START]` bare tags (no colon) now stripped from narration — previous regex only caught `[BEGIN: ...]` form

**Narrator (TTS):**
- ✅ Re-enabled Kokoro TTS narrator (`/api/narrate` route + preload thread in `api.py`)
- ✅ `_appendPlayButton` rewritten — takes `Promise<Blob>[]` queue (one per sentence); `AbortController` stop; sequential playback via `async/await` loop
- ✅ First sentence pre-fetched mid-stream (fires as soon as first `.!?` boundary detected in token stream) so Play button is enabled immediately when streaming ends
- ✅ All sentences voiced: on `done`, full `data.narration` split on `/(?<=[.!?])\s+/`, TTS fired for each sentence; sentence 0 reuses the mid-stream pre-fetch
- ✅ Play/Stop button uses symbols only (`▶` / `⏹`) — no text labels

**DM prompt fixes:**
- ✅ Companion catalog dump fixed — model was listing all roster names to the player as a menu. `_build_party_block()` now explicitly prohibits this; roster passed as internal-only anchor for `[COMPANION:]` tag
- ✅ `[CHOOSE A GOD]` placeholder fixed — added `deity: "Lathander"` to Elara Voss (Cleric) and `deity: "Tyr"` to Torben Ironwall (Paladin) in `companions.py`; deity included in roster hint

---


## Steam — Technical Reference