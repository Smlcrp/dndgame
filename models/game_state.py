import json
import os
from pathlib import Path

# Points two levels up from models/ to the project root, then into data/sessions/
SESSIONS_DIR = Path(__file__).parent.parent / "data" / "sessions"


def _ensure_dir():
    SESSIONS_DIR.mkdir(parents=True, exist_ok=True)


def empty_session(character_name="", session_name=""):
    return {
        "character_name": character_name,
        "session_name":   session_name,

        "location":       "Unknown",
        "scene":          "",
        "history":        [],
        "flags":          {},

        "current_hp":     None,
        "temp_hp":        0,
        "hit_dice_spent": 0,
        "spell_slots_used": {},
        "conditions":     [],
        "death_saves":    {"successes": 0, "failures": 0},
        "stable":         False,

        "in_combat":      False,
        "round":          0,
        "initiative_order": [],
        "current_turn":   0,
    }


def save_session(session):
    _ensure_dir()
    name = session.get("session_name") or session.get("character_name") or "session"
    path = SESSIONS_DIR / f"{name}.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(session, f, indent=2)
    return str(path)


def load_session(name):
    path = SESSIONS_DIR / f"{name}.json"
    if not path.exists():
        raise FileNotFoundError(f"No session found: {name}")
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def list_sessions():
    _ensure_dir()
    return [p.stem for p in sorted(SESSIONS_DIR.glob("*.json"))]


def delete_session(name):
    path = SESSIONS_DIR / f"{name}.json"
    if path.exists():
        path.unlink()


# ── Scene helpers ──────────────────────────────────────────────────────────────

def add_history(session, role, text):
    session["history"].append({"role": role, "text": text})


def set_flag(session, key, value=True):
    session["flags"][key] = value


def get_flag(session, key, default=False):
    return session["flags"].get(key, default)


# ── Transient character state ──────────────────────────────────────────────────

def init_hp(session, character):
    if session["current_hp"] is None:
        session["current_hp"] = character["hp"].get("max", 1)


def apply_damage(session, amount):
    if amount <= 0:
        return session["current_hp"]
    temp = session.get("temp_hp", 0)
    absorbed = min(temp, amount)
    session["temp_hp"] = temp - absorbed
    session["current_hp"] = max(0, session["current_hp"] - (amount - absorbed))
    return session["current_hp"]


def apply_healing(session, amount, max_hp):
    session["current_hp"] = min(max_hp, session["current_hp"] + amount)
    return session["current_hp"]


def use_spell_slot(session, level):
    key = str(level)
    session["spell_slots_used"][key] = session["spell_slots_used"].get(key, 0) + 1


def restore_spell_slot(session, level):
    key = str(level)
    used = session["spell_slots_used"].get(key, 0)
    if used > 0:
        session["spell_slots_used"][key] = used - 1


def long_rest(session, character):
    session["current_hp"]       = character["hp"].get("max", 1)
    session["temp_hp"]          = 0
    session["hit_dice_spent"]   = max(0, session["hit_dice_spent"] - max(1, character["level"] // 2))
    session["spell_slots_used"] = {}
    session["conditions"]       = []
    session["death_saves"]      = {"successes": 0, "failures": 0}
    session["stable"]           = False


def short_rest(session, hp_gained):
    session["hit_dice_spent"] += 1
    session["current_hp"] = min(
        session["current_hp"] + hp_gained,
        session.get("_max_hp_cache", session["current_hp"] + hp_gained)
    )


# ── Combat state ───────────────────────────────────────────────────────────────

def start_combat(session, combatants):
    ordered = sorted(combatants, key=lambda c: c["initiative"], reverse=True)
    for c in ordered:
        c.setdefault("conditions", [])
    session["in_combat"]         = True
    session["round"]             = 1
    session["current_turn"]      = 0
    session["initiative_order"]  = ordered


def end_combat(session):
    session["in_combat"]        = False
    session["round"]            = 0
    session["current_turn"]     = 0
    session["initiative_order"] = []


def advance_turn(session):
    order = session["initiative_order"]
    if not order:
        return
    session["current_turn"] += 1
    if session["current_turn"] >= len(order):
        session["current_turn"] = 0
        session["round"] += 1


def current_combatant(session):
    order = session["initiative_order"]
    if not order:
        return None
    return order[session["current_turn"]]


def apply_combat_damage(session, combatant_name, amount):
    for c in session["initiative_order"]:
        if c["name"] == combatant_name:
            c["hp"] = max(0, c["hp"] - amount)
            return c["hp"]
    return None


def apply_combat_healing(session, combatant_name, amount):
    for c in session["initiative_order"]:
        if c["name"] == combatant_name:
            c["hp"] = min(c["max_hp"], c["hp"] + amount)
            return c["hp"]
    return None


def add_condition(session, combatant_name, condition):
    for c in session["initiative_order"]:
        if c["name"] == combatant_name:
            if condition not in c["conditions"]:
                c["conditions"].append(condition)
            return


def remove_condition(session, combatant_name, condition):
    for c in session["initiative_order"]:
        if c["name"] == combatant_name:
            c["conditions"] = [x for x in c["conditions"] if x != condition]
            return


def living_combatants(session):
    return [c for c in session["initiative_order"] if c["hp"] > 0]


def enemies_alive(session):
    return any(c["hp"] > 0 for c in session["initiative_order"] if not c["is_player"])
