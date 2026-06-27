"""
Flask web API — JSON backend for the browser and Electron frontend.

All game logic is delegated to the existing controller/model layer.
This file only does HTTP plumbing: parse request JSON, call the right
controller function, return JSON. No game logic lives here.

Routes
------
GET  /api/ping                          health check
GET  /api/characters                    list saved characters
DELETE /api/characters/<name>           delete a character
GET  /api/sessions                      list saved sessions

POST /api/game/new                      start a fresh adventure (resets to Lv 1)
POST /api/game/next                     start a next adventure (keeps progress)
POST /api/game/resume                   resume a saved session
POST /api/game/save                     flush state to disk
GET  /api/game/state                    current game state snapshot

POST /api/action                        player input -> DM narration + events

POST /api/roll                          roll a single die (for UI animation)
POST /api/roll/damage                   roll a damage notation string
POST /api/roll/initiative               roll initiative for the player
POST /api/roll/hit-die                  roll the character's hit die

POST /api/combat/setup                  initialise combat after [COMBAT:] event
GET  /api/combat/attack-options         expanded weapon list (versatile/thrown/offhand variants)
POST /api/combat/attack                 resolve a player weapon attack
POST /api/combat/spell                  resolve a player spell
POST /api/combat/death-save             roll a death saving throw
POST /api/combat/end-turn               advance to the next combatant
POST /api/combat/end                    force-end combat (all enemies dead)

POST /api/skill-check                   resolve a skill check

POST /api/rest/short                    take a short rest
POST /api/rest/long                     take a long rest

POST /api/adventure/beat                advance the story beat

POST /api/award/xp                      award XP (DEV panel / beat events)
POST /api/award/gold                    award gold
POST /api/award/item                    award a magic item

POST /api/levelup                       apply all level-up choices
"""

import sys
from pathlib import Path

_root = Path(__file__).parent.parent.parent
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))

import json
import os
import re as _re
import subprocess
import threading
import time

import requests as _http
from flask import Flask, request, jsonify, render_template, send_from_directory, Response, stream_with_context

from models.character import (
    load_character, save_character, list_characters,
    modifier, reset_to_level1,
)
from models import game_state as gs
from models import dice as dice_mod
from models import combat as cb
from models.dm import from_config
from controllers import game_controller as gc

# ── App setup ─────────────────────────────────────────────────────────────────

_static = Path(__file__).parent / "static"
_tmpl   = Path(__file__).parent / "templates"

app = Flask(__name__, static_folder=str(_static), template_folder=str(_tmpl))
app.secret_key = "dnd-local-dev"

# Single-user in-process state — fine for a local desktop app.
_state: dict = {"session": None, "character": None, "dm": None}

# ── Ollama process management ─────────────────────────────────────────────────

_ollama_mode = "gpu"  # updated to "cpu" if GPU crashes
_OLLAMA_URL  = "http://localhost:11434"

def _ollama_healthy():
    try:
        _http.get(f"{_OLLAMA_URL}/api/tags", timeout=2)
        return True
    except Exception:
        return False

def _restart_ollama_cpu():
    """Kill any running ollama.exe and relaunch with CUDA disabled. Returns True on success."""
    global _ollama_mode
    print("[ollama] CUDA crash — restarting in CPU-only mode…")
    subprocess.run(["taskkill", "/F", "/IM", "ollama.exe", "/T"], capture_output=True)
    time.sleep(2)
    env = os.environ.copy()
    env["CUDA_VISIBLE_DEVICES"] = "-1"
    env["OLLAMA_NUM_GPU"]       = "0"
    flags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
    subprocess.Popen(
        ["ollama", "serve"],
        env=env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        creationflags=flags,
    )
    for _ in range(20):
        if _ollama_healthy():
            _ollama_mode = "cpu"
            print("[ollama] Running in CPU mode.")
            return True
        time.sleep(0.5)
    print("[ollama] CPU restart timed out.")
    return False

def _is_cuda_crash(err: str) -> bool:
    return "CUDA" in err or "0xc0000409" in err

_CHARS_DIR = _root / "data" / "characters"

# ── Startup pre-loading ───────────────────────────────────────────────────────
# Load the Kokoro narrator model in the background the moment Flask starts so
# the first Play click is instant instead of waiting 1-2 s for model init.

def _preload_narrator():
    try:
        from models.narrator import _get_kokoro
        _get_kokoro()
        print("[narrator] Model ready.")
    except Exception as e:
        print(f"[narrator] Pre-load skipped: {e}")

threading.Thread(target=_preload_narrator, daemon=True).start()


# ── Helpers ───────────────────────────────────────────────────────────────────

def _ok(**kw):
    return jsonify({"ok": True, **kw})


def _err(msg, code=400):
    return jsonify({"ok": False, "error": msg}), code


def _active():
    """Return (session, char) — both None if no game is running."""
    return _state["session"], _state["character"]


def _snapshot():
    """Build a JSON-serialisable snapshot of the current in-memory game state."""
    session, char = _active()
    if not session:
        return {}
    return {
        "session": {
            k: session.get(k)
            for k in (
                "session_name", "character_name", "location", "scene",
                "in_combat", "round", "current_hp", "temp_hp",
                "hit_dice_spent", "spell_slots_used", "conditions",
                "death_saves", "stable", "initiative_order", "current_turn",
                "adventure", "companions", "flags", "story_mode",
            )
        },
        "character": char,
    }


def _init_game(char, preset, reset=False):
    """Shared setup for new/next adventure. Mutates _state. Returns (session, dm)."""
    if reset:
        char = reset_to_level1(char)
        save_character(char)
    session = gs.empty_session(
        character_name=char["name"],
        session_name=char["name"],
    )
    gs.init_hp(session, char)
    gc.start_adventure(session, char, preset=preset)
    dm = from_config()
    _state.update(session=session, character=char, dm=dm)
    return session, dm


# ── Frontend ─────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    return render_template("index.html")


# ── Health ────────────────────────────────────────────────────────────────────

@app.route("/api/ping")
def ping():
    return _ok(message="D&D API running")


# ── Characters ────────────────────────────────────────────────────────────────

@app.route("/api/characters")
def get_characters():
    return _ok(characters=list_characters())


@app.route("/api/characters/import-ddb", methods=["POST"])
def import_ddb():
    """Import a D&D Beyond character. Body: {"url": str, "token": str (optional)}"""
    body  = request.get_json(silent=True) or {}
    url   = body.get("url", "").strip()
    token = body.get("token", "").strip()
    if not url:
        return _err("url is required")
    try:
        sys.path.insert(0, str(_root / "views" / "desktop" / "character_builder"))
        from ddb_import import import_from_ddb
        from models.character import migrate_character, validate_character
        char = import_from_ddb(url, cobalt_token=token)
        char = migrate_character(char)
        validate_character(char)
        save_character(char)
        return _ok(name=char["name"])
    except Exception as e:
        return _err(str(e), 500)


@app.route("/api/characters/<name>", methods=["DELETE"])
def delete_character(name):
    path = _CHARS_DIR / f"{name}.json"
    if not path.exists():
        return _err(f"Character '{name}' not found", 404)
    path.unlink()
    return _ok(deleted=name)


# ── Sessions ──────────────────────────────────────────────────────────────────

@app.route("/api/sessions")
def get_sessions():
    return _ok(sessions=gs.list_sessions())


# ── Game lifecycle ────────────────────────────────────────────────────────────

@app.route("/api/game/new", methods=["POST"])
def new_game():
    """Start a fresh adventure — resets the character to level 1.
    Returns state immediately; the opening DM narration streams via /api/action/stream.
    Body: {"char_name": str, "preset": "Quest" | "One Shot" | "Epic"}
    """
    body   = request.get_json(silent=True) or {}
    name   = body.get("char_name", "")
    preset = body.get("preset", "Quest")
    if not name:
        return _err("char_name is required")
    try:
        char = load_character(name)
    except FileNotFoundError:
        return _err(f"Character '{name}' not found", 404)
    except ValueError as e:
        return _err(str(e))
    try:
        session, _dm = _init_game(char, preset, reset=True)
        gs.save_session(session)
        save_character(_state["character"])
        return _ok(state=_snapshot())
    except Exception as e:
        return _err(str(e), 500)


@app.route("/api/game/next", methods=["POST"])
def next_game():
    """Start a next adventure — keeps existing character progress, fresh story.
    Returns state immediately; the opening DM narration streams via /api/action/stream.
    Body: {"char_name": str, "preset": str}
    """
    body   = request.get_json(silent=True) or {}
    name   = body.get("char_name", "")
    preset = body.get("preset", "Quest")
    if not name:
        return _err("char_name is required")
    try:
        char = load_character(name)
    except (FileNotFoundError, ValueError) as e:
        return _err(str(e), 404)
    try:
        session, _dm = _init_game(char, preset, reset=False)
        gs.save_session(session)
        save_character(_state["character"])
        return _ok(state=_snapshot())
    except Exception as e:
        return _err(str(e), 500)


@app.route("/api/game/resume", methods=["POST"])
def resume_game():
    """Resume a saved session.
    Body: {"session_name": str}
    """
    body         = request.get_json(silent=True) or {}
    session_name = body.get("session_name", "")
    if not session_name:
        return _err("session_name is required")
    try:
        session = gs.load_session(session_name)
        char    = load_character(session.get("character_name", session_name))
    except FileNotFoundError as e:
        return _err(str(e), 404)
    except ValueError as e:
        return _err(str(e))

    gs.init_hp(session, char)
    dm = from_config()
    _state.update(session=session, character=char, dm=dm)
    try:
        narration = dm.recap(session, char)
        return _ok(narration=narration, state=_snapshot())
    except Exception as e:
        return _err(str(e), 500)


@app.route("/api/game/save", methods=["POST"])
def save_game():
    session, char = _active()
    if not session:
        return _err("No active game")
    gs.save_session(session)
    save_character(char)
    return _ok(saved=True)


@app.route("/api/game/state")
def get_state():
    if not _state["session"]:
        return _ok(active=False)
    return _ok(active=True, **_snapshot())


# ── Player action (DM call) ───────────────────────────────────────────────────

@app.route("/api/action", methods=["POST"])
def player_action():
    """Send player text to the DM and get narration + parsed events back.
    Body: {"text": str}
    This call blocks until Ollama responds (~5-30 s depending on model/hardware).
    """
    session, char = _active()
    if not session:
        return _err("No active game")
    body = request.get_json(silent=True) or {}
    text = body.get("text", "").strip()
    if not text:
        return _err("text is required")
    try:
        result = _state["dm"].respond(session, char, text)
        gs.save_session(session)
        return _ok(narration=result["narration"], events=result["events"],
                   state=_snapshot())
    except Exception as e:
        return _err(str(e), 500)


# ── Streaming player action (SSE) ────────────────────────────────────────────

@app.route("/api/action/stream", methods=["POST"])
def player_action_stream():
    """Streaming version of /api/action using Server-Sent Events.
    Tokens arrive immediately as the model generates them.
    Final event contains the parsed game events and updated state.
    Body: {"text": str}
    """
    session, char = _active()
    if not session:
        return _err("No active game")
    body = request.get_json(silent=True) or {}
    text = body.get("text", "").strip()
    if not text:
        return _err("text is required")

    def generate():
        try:
            for chunk in _state["dm"].respond_stream(session, char, text):
                if "token" in chunk:
                    yield f"data: {json.dumps({'token': chunk['token']})}\n\n"
                elif chunk.get("done"):
                    gs.save_session(session)
                    yield f"data: {json.dumps({'done': True, 'narration': chunk['narration'], 'events': chunk['events'], 'state': _snapshot(), 'ollama_mode': _ollama_mode})}\n\n"
        except RuntimeError as e:
            err = str(e)
            if _is_cuda_crash(err):
                yield f"data: {json.dumps({'error': 'GPU crashed — restarting in CPU mode. Please try again in a few seconds.'})}\n\n"
                threading.Thread(target=_restart_ollama_cpu, daemon=True).start()
            else:
                yield f"data: {json.dumps({'error': err})}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'error': str(e)})}\n\n"

    return Response(
        stream_with_context(generate()),
        mimetype="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@app.route("/api/narrate", methods=["POST"])
def narrate():
    """Convert DM narration text to speech and return WAV audio.
    Body: {"text": str}
    First call may take a few seconds while Kokoro loads.
    """
    body = request.get_json(silent=True) or {}
    text = body.get("text", "").strip()
    if not text:
        return _err("text is required")
    try:
        from models.narrator import speak
        wav_bytes = speak(text)
        return Response(wav_bytes, mimetype="audio/wav")
    except ImportError:
        return _err("Narrator not available — run: pip install kokoro-onnx soundfile", 503)
    except Exception as e:
        return _err(str(e), 500)


@app.route("/api/warmup", methods=["POST"])
def warmup():
    """Load the AI model into VRAM in the background.
    Call this early (e.g. on the main menu) so the first adventure starts fast.
    Returns immediately — the actual load happens on a background thread.
    If a CUDA crash is detected, Ollama is automatically restarted in CPU mode.
    """
    def _do():
        try:
            from_config().warmup()
        except RuntimeError as e:
            if _is_cuda_crash(str(e)):
                if _restart_ollama_cpu():
                    try:
                        from_config().warmup()
                    except Exception as e2:
                        print(f"[ollama] CPU warmup also failed: {e2}")
            else:
                print(f"[ollama] Warmup error: {e}")
        except Exception as e:
            print(f"[ollama] Warmup error: {e}")
    threading.Thread(target=_do, daemon=True).start()
    return _ok(warming=True)


@app.route("/api/ollama/mode")
def ollama_mode_route():
    """Return current Ollama execution mode (gpu or cpu)."""
    return _ok(mode=_ollama_mode)


# ── Dice ──────────────────────────────────────────────────────────────────────

@app.route("/api/roll", methods=["POST"])
def roll_single():
    """Roll a single die. Call this first, animate on the client, then pass
    the returned value into the relevant action endpoint.
    Body: {"sides": int}
    """
    body  = request.get_json(silent=True) or {}
    sides = int(body.get("sides", 20))
    try:
        return _ok(value=dice_mod.roll(sides), sides=sides)
    except Exception as e:
        return _err(str(e))


@app.route("/api/roll/damage", methods=["POST"])
def roll_damage():
    """Roll a damage notation string (e.g. "2d6+3").
    Body: {"notation": str, "critical": bool}
    """
    body     = request.get_json(silent=True) or {}
    notation = body.get("notation", "1d6")
    critical = bool(body.get("critical", False))
    try:
        result = (dice_mod.critical_damage(notation) if critical
                  else dice_mod.damage(notation))
        return _ok(**result)
    except Exception as e:
        return _err(str(e))


@app.route("/api/roll/initiative", methods=["POST"])
def roll_initiative():
    """Roll player initiative (DEX mod applied server-side)."""
    session, char = _active()
    if not session:
        return _err("No active game")
    dex_mod = modifier(char["abilities"].get("dexterity", 10))
    result  = dice_mod.initiative(dex_mod)
    return _ok(value=result["roll"], modifier=result["modifier"],
               total=result["total"])


@app.route("/api/roll/hit-die", methods=["POST"])
def roll_hit_die():
    """Roll the character's hit die for healing (CON mod applied server-side)."""
    session, char = _active()
    if not session:
        return _err("No active game")
    die_str = char.get("hit_dice", {}).get("type", "d8")
    con_mod = modifier(char["abilities"].get("constitution", 10))
    result  = dice_mod.hit_die(die_str, con_mod)
    return _ok(**result)


# ── Combat ────────────────────────────────────────────────────────────────────

def _get_attack_options(char):
    """Return expanded weapon attack options including versatile, thrown, and off-hand variants.
    Ported from views/desktop/app.py:_get_attack_options().
    Each option dict: {label, weapon, bonus, damage, dmg_type, mode, note?}
    mode values: melee | ranged | melee_2h | thrown | offhand
    """
    _cb_path = str(_root / "views" / "desktop" / "character_builder")
    if _cb_path not in sys.path:
        sys.path.insert(0, _cb_path)
    try:
        from dnd_data import WEAPONS as WPN_DATA
    except ImportError:
        WPN_DATA = {}

    attacks    = char.get("attacks", [])
    options    = []
    light_melee = []

    for atk in attacks:
        name     = atk["name"]
        bonus    = atk.get("attack_bonus", 0)
        damage   = atk.get("damage", "—")
        dmg_type = atk.get("damage_type", "")

        wpn   = WPN_DATA.get(name, {})
        props = wpn.get("props", [])
        cat   = wpn.get("cat", "")

        is_melee  = "Ranged" not in cat and not any("ammunition" in p for p in props)
        has_light = "light" in props
        has_reach = "reach" in props

        # Parse "versatile (1d10)" → two-handed damage die
        vers_dmg = None
        for p in props:
            if p.startswith("versatile"):
                m = _re.search(r'\((.+?)\)', p)
                if m:
                    die   = m.group(1)
                    mod_m = _re.search(r'([+-]\d+)$', damage)
                    vers_dmg = die + (mod_m.group(1) if mod_m else "")

        # Parse "thrown (20/60)" → thrown range string
        thrown_range = None
        for p in props:
            if p.startswith("thrown"):
                m = _re.search(r'\((.+?)\)', p)
                if m:
                    thrown_range = m.group(1)

        # Parse "ammunition (80/320)" → ranged weapon range
        ammo_range = None
        for p in props:
            if p.startswith("ammunition"):
                m = _re.search(r'\((.+?)\)', p)
                if m:
                    ammo_range = m.group(1)

        reach_note = " · reach 10ft" if has_reach else ""

        if vers_dmg:
            label = f"{name} (one-handed){reach_note}"
        elif ammo_range:
            label = f"{name} · range {ammo_range} ft"
        else:
            label = f"{name}{reach_note}"

        options.append({
            "label": label, "weapon": name, "bonus": bonus,
            "damage": damage, "dmg_type": dmg_type,
            "mode": "ranged" if ammo_range else "melee",
        })

        if vers_dmg:
            options.append({
                "label": f"{name} (two-handed){reach_note}",
                "weapon": name, "bonus": bonus,
                "damage": vers_dmg, "dmg_type": dmg_type,
                "mode": "melee_2h",
            })

        if thrown_range and is_melee:
            options.append({
                "label": f"{name} (thrown · {thrown_range} ft)",
                "weapon": name, "bonus": bonus,
                "damage": damage, "dmg_type": dmg_type,
                "mode": "thrown",
            })

        if has_light and is_melee:
            light_melee.append(atk)

    # Dual-wield off-hand: PHB rule — no ability modifier on off-hand damage
    if len(light_melee) >= 2:
        off           = light_melee[1]
        off_name      = off["name"]
        off_dmg       = off.get("damage", "—")
        off_type      = off.get("damage_type", "")
        die_m         = _re.match(r'(\d*d\d+)', off_dmg)
        off_dmg_no_mod = die_m.group(1) if die_m else off_dmg
        options.append({
            "label":  f"{off_name} (off-hand · bonus action)",
            "weapon": off_name,
            "bonus":  off.get("attack_bonus", 0),
            "damage": off_dmg_no_mod, "dmg_type": off_type,
            "mode":   "offhand",
            "note":   "No ability modifier to damage (PHB two-weapon fighting rule)",
        })

    return options


@app.route("/api/combat/attack-options")
def combat_attack_options():
    """Return expanded weapon attack options for the current character.
    Includes versatile (one/two-handed), thrown, and dual-wield off-hand variants.
    """
    session, char = _active()
    if not session:
        return _err("No active game")
    try:
        return _ok(options=_get_attack_options(char))
    except Exception as e:
        return _err(str(e), 500)


@app.route("/api/combat/setup", methods=["POST"])
def combat_setup():
    """Initialise combat with a pre-rolled initiative value.
    Body: {"enemies": [{"name": str, "count": int}], "d20_initiative": int}
    """
    session, char = _active()
    if not session:
        return _err("No active game")
    body  = request.get_json(silent=True) or {}
    specs = body.get("enemies", [])
    d20   = int(body.get("d20_initiative", 10))
    try:
        result = gc.setup_combat(session, char, specs, d20)
        return _ok(order=result["order"], display=result["display"],
                   state=_snapshot())
    except Exception as e:
        return _err(str(e), 500)


@app.route("/api/combat/attack", methods=["POST"])
def combat_attack():
    """Resolve a player weapon attack with a pre-rolled d20.
    Body: {"weapon": str, "target": str, "d20": int, "mode": str (optional)}
    mode: melee (default) | ranged | melee_2h | thrown | offhand
    For melee_2h/thrown/offhand, damage_override is resolved from attack-options.
    """
    session, char = _active()
    if not session:
        return _err("No active game")
    body   = request.get_json(silent=True) or {}
    weapon = body.get("weapon", "")
    target = body.get("target", "")
    d20    = int(body.get("d20", 10))
    mode   = body.get("mode", "melee")
    if not weapon or not target:
        return _err("weapon and target are required")
    try:
        damage_override = None
        if mode in ("melee_2h", "thrown", "offhand"):
            opts = _get_attack_options(char)
            opt  = next((o for o in opts
                         if o["weapon"].lower() == weapon.lower()
                         and o["mode"] == mode), None)
            if opt:
                damage_override = opt["damage"]
        result = gc.process_attack(session, char, weapon, target, d20,
                                   damage_override=damage_override)
        if "error" in result:
            return _err(result["error"])
        save_character(char)
        return _ok(**result, state=_snapshot())
    except Exception as e:
        return _err(str(e), 500)


@app.route("/api/combat/spell", methods=["POST"])
def combat_spell():
    """Resolve a player spell. Slot is consumed here before calling the controller.
    Body: {"spell": str, "target": str, "slot_level": int, "d20": int | null}
    d20 is only needed for attack-roll spells (delivery == "attack").
    """
    session, char = _active()
    if not session:
        return _err("No active game")
    body       = request.get_json(silent=True) or {}
    spell_name = body.get("spell", "")
    target     = body.get("target", "")
    slot_level = int(body.get("slot_level", 1))
    d20        = body.get("d20")
    if not spell_name or not target:
        return _err("spell and target are required")

    if slot_level > 0:
        try:
            from models.character import use_spell_slot
            use_spell_slot(char, slot_level)
        except ValueError as e:
            return _err(str(e))

    try:
        result = gc.process_spell_cast(
            session, char, spell_name, target, slot_level,
            d20_override=int(d20) if d20 is not None else None,
        )
        if "error" in result:
            return _err(result["error"])
        save_character(char)
        return _ok(**result, state=_snapshot())
    except Exception as e:
        return _err(str(e), 500)


@app.route("/api/combat/death-save", methods=["POST"])
def death_save():
    """Roll a death saving throw. The server always rolls independently.
    Call /api/roll first if you want to animate a die before resolving.
    """
    session, char = _active()
    if not session:
        return _err("No active game")
    try:
        result = gc.process_death_save(session)
        gs.save_session(session)
        return _ok(**result, state=_snapshot())
    except Exception as e:
        return _err(str(e), 500)


@app.route("/api/combat/end-turn", methods=["POST"])
def end_turn():
    """Advance to the next combatant's turn.
    If the next combatant is an enemy, their attack is resolved automatically.
    """
    session, char = _active()
    if not session:
        return _err("No active game")
    next_c       = cb.end_turn(session)
    enemy_result = None
    if next_c and not next_c.get("is_player") and not next_c.get("is_companion"):
        if next_c["hp"] > 0:
            enemy_result = gc.process_enemy_turn(session)
    return _ok(
        current=gs.current_combatant(session),
        enemy_result=enemy_result,
        state=_snapshot(),
    )


@app.route("/api/combat/end", methods=["POST"])
def end_combat():
    """Force-end combat (called when all enemies reach 0 HP) and award XP."""
    session, char = _active()
    if not session:
        return _err("No active game")
    xp        = cb.xp_from_combat(session)
    gs.end_combat(session)
    xp_result = None
    if xp > 0:
        xp_result = gc.process_xp_award(session, char, xp)
        save_character(char)
    gs.save_session(session)
    return _ok(xp_result=xp_result, state=_snapshot())


# ── Skill check ───────────────────────────────────────────────────────────────

@app.route("/api/skill-check", methods=["POST"])
def skill_check():
    """Resolve a skill check with a pre-rolled d20.
    Body: {"skill": str, "dc": int, "d20": int}
    """
    session, char = _active()
    if not session:
        return _err("No active game")
    body  = request.get_json(silent=True) or {}
    skill = body.get("skill", "")
    dc    = int(body.get("dc", 10))
    d20   = int(body.get("d20", 10))
    if not skill:
        return _err("skill is required")
    result = gc.process_skill_check(char, skill, dc, d20)
    return _ok(**result, state=_snapshot())


# ── Rest ──────────────────────────────────────────────────────────────────────

@app.route("/api/rest/short", methods=["POST"])
def short_rest():
    """Take a short rest — spend hit dice, recharge short-rest features.
    Body: {"dice_spent": int, "rolls": [int, ...]}
    rolls contains one raw die result per hit die spent (from /api/roll/hit-die).
    """
    session, char = _active()
    if not session:
        return _err("No active game")
    body       = request.get_json(silent=True) or {}
    dice_spent = int(body.get("dice_spent", 1))
    rolls      = body.get("rolls", [])
    try:
        result = gc.process_short_rest(session, char, dice_spent, rolls)
        save_character(char)
        gs.save_session(session)
        return _ok(**result, state=_snapshot())
    except Exception as e:
        return _err(str(e))


@app.route("/api/rest/long", methods=["POST"])
def long_rest():
    """Take a long rest — fully restores HP, spell slots, and feature charges."""
    session, char = _active()
    if not session:
        return _err("No active game")
    try:
        result = gc.process_long_rest(session, char)
        save_character(char)
        gs.save_session(session)
        return _ok(**result, state=_snapshot())
    except Exception as e:
        return _err(str(e), 500)


# ── Adventure ─────────────────────────────────────────────────────────────────

@app.route("/api/adventure/beat", methods=["POST"])
def advance_beat():
    """Advance the story beat and award beat XP."""
    session, char = _active()
    if not session:
        return _err("No active game")
    xp        = gc.advance_beat(session)
    xp_result = None
    if xp > 0:
        xp_result = gc.process_xp_award(session, char, xp)
        save_character(char)
    gs.save_session(session)
    return _ok(xp=xp, xp_result=xp_result, state=_snapshot())


# ── Awards ────────────────────────────────────────────────────────────────────

@app.route("/api/award/xp", methods=["POST"])
def award_xp():
    """Award XP directly. Used by the [XP:] DM tag handler and the DEV panel.
    Body: {"amount": int}
    """
    session, char = _active()
    if not session:
        return _err("No active game")
    body   = request.get_json(silent=True) or {}
    amount = int(body.get("amount", 0))
    if amount <= 0:
        return _err("amount must be a positive integer")
    result = gc.process_xp_award(session, char, amount)
    save_character(char)
    return _ok(**result, state=_snapshot())


@app.route("/api/award/gold", methods=["POST"])
def award_gold():
    """Award gold pieces from a [GOLD:] DM tag.
    Body: {"amount": int}
    """
    session, char = _active()
    if not session:
        return _err("No active game")
    body      = request.get_json(silent=True) or {}
    amount    = int(body.get("amount", 0))
    new_total = gc.process_gold_award(char, amount)
    save_character(char)
    return _ok(new_total=new_total, state=_snapshot())


@app.route("/api/award/item", methods=["POST"])
def award_item():
    """Award a magic item from an [ITEM:] DM tag.
    Body: {"name": str, "slot": "weapon"|"armor"|"misc", "bonus": int}
    """
    session, char = _active()
    if not session:
        return _err("No active game")
    body  = request.get_json(silent=True) or {}
    name  = body.get("name", "")
    slot  = body.get("slot", "misc")
    bonus = int(body.get("bonus", 0))
    if not name:
        return _err("name is required")
    item = gc.process_item_award(char, name, slot, bonus)
    save_character(char)
    return _ok(item=item, state=_snapshot())


# ── Level-up ──────────────────────────────────────────────────────────────────

@app.route("/api/levelup", methods=["POST"])
def apply_levelup():
    """Apply all level-up choices after the client detects leveled_up == True.
    Body: {
        "hp_roll":  int,               raw die result (CON mod applied here)
        "subclass": str | null,        only sent at the subclass trigger level
        "asi": {                       only sent at ASI levels
            "type":  "+2" | "+1+1" | "feat",
            "a1":    ability_key,
            "a2":    ability_key | null,
            "feat":  feat_name | null,
        },
        "spells": [str, ...]           newly learned spell names (casters only)
    }
    """
    session, char = _active()
    if not session:
        return _err("No active game")

    body    = request.get_json(silent=True) or {}
    level   = char.get("level", 1)
    con_mod = modifier(char["abilities"].get("constitution", 10))

    # HP
    hp_roll = int(body.get("hp_roll", 1))
    hp_gain = max(1, hp_roll + con_mod)
    char["hp"]["max"]     += hp_gain
    char["hp"]["current"] += hp_gain
    char["hit_dice"]["total"] = level
    char["hit_dice"]["used"]  = 0

    # Subclass
    subclass = body.get("subclass")
    if subclass:
        char["subclass"] = subclass

    # ASI / Feat
    asi = body.get("asi") or {}
    if asi:
        t = asi.get("type", "")
        if t == "+2":
            ab = asi.get("a1", "strength")
            char["abilities"][ab] = char["abilities"].get(ab, 10) + 2
        elif t == "+1+1":
            for key in ("a1", "a2"):
                ab = asi.get(key)
                if ab:
                    char["abilities"][ab] = char["abilities"].get(ab, 10) + 1
        elif t == "feat":
            feat = asi.get("feat")
            if feat:
                char.setdefault("feats", [])
                if feat not in char["feats"]:
                    char["feats"].append(feat)
                    if feat == "Tough":
                        char["hp"]["max"]     += 2 * level
                        char["hp"]["current"] += 2 * level

    # Spell learning
    spells = body.get("spells") or []
    if spells:
        sc    = char.get("spellcasting", {})
        known = sc.setdefault("spells_known", [])
        for s in spells:
            if s not in known:
                known.append(s)

    save_character(char)
    return _ok(state=_snapshot())


# ── Story Mode ────────────────────────────────────────────────────────────────

@app.route("/api/story-mode", methods=["POST"])
def story_mode():
    """Enter or exit Story Mode. Body: {"enter": bool}"""
    session, char = _active()
    if not session:
        return _err("No active game")
    body  = request.get_json(silent=True) or {}
    enter = body.get("enter", True)
    session["story_mode"] = bool(enter)
    gs.save_session(session)
    return _ok(story_mode=session["story_mode"], state=_snapshot())


# ── DEV panel ─────────────────────────────────────────────────────────────────

@app.route("/api/dev/set-hp", methods=["POST"])
def dev_set_hp():
    """Set current HP directly. Body: {"hp": int}"""
    session, char = _active()
    if not session:
        return _err("No active game")
    body = request.get_json(silent=True) or {}
    hp   = int(body.get("hp", 1))
    max_hp = char.get("hp", {}).get("max", 1)
    session["current_hp"] = max(0, min(max_hp, hp))
    gs.save_session(session)
    return _ok(state=_snapshot())


@app.route("/api/dev/add-condition", methods=["POST"])
def dev_add_condition():
    """Add a condition. Body: {"condition": str}"""
    session, char = _active()
    if not session:
        return _err("No active game")
    body = request.get_json(silent=True) or {}
    cond = body.get("condition", "").strip()
    if not cond:
        return _err("condition is required")
    gs.add_condition(session, cond)
    gs.save_session(session)
    return _ok(state=_snapshot())


@app.route("/api/dev/remove-condition", methods=["POST"])
def dev_remove_condition():
    """Remove a condition. Body: {"condition": str}"""
    session, char = _active()
    if not session:
        return _err("No active game")
    body = request.get_json(silent=True) or {}
    cond = body.get("condition", "").strip()
    gs.remove_condition(session, cond)
    gs.save_session(session)
    return _ok(state=_snapshot())


@app.route("/api/dev/spawn-combat", methods=["POST"])
def dev_spawn_combat():
    """Spawn a test combat with a single Goblin for testing."""
    session, char = _active()
    if not session:
        return _err("No active game")
    level  = char.get("level", 1)
    from models.enemies import ENEMIES
    enemy  = ENEMIES.get("Goblin") or list(ENEMIES.values())[0]
    result = gc.start_combat(session, char, [{"name": enemy["name"], "count": 1}], level,
                             dice_mod.roll(20))
    gs.save_session(session)
    return _ok(**result, state=_snapshot())


# ── Entry point ───────────────────────────────────────────────────────────────

def create_app():
    """App factory used by tests and run_server.py."""
    return app


if __name__ == "__main__":
    print("D&D API -> http://localhost:5000")
    app.run(debug=True, port=5000, use_reloader=False)
