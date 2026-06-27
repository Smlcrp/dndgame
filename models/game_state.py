"""
Game state model — the live state of an in-progress play session.

A session is everything that changes DURING an adventure: current HP, spell slots
used, conversation history, combat tracker, location, flags, and companions.
It is separate from the character (who the player IS) so a single character can
run multiple adventures without losing their permanent stats.

Sessions are saved to disk as JSON files in data/sessions/. Every piece of
transient game state lives here — nothing in the character file changes during
play except XP and level-ups.
"""

import json
import os
from pathlib import Path

# Points two levels up from models/ to the project root, then into data/sessions/
SESSIONS_DIR = Path(__file__).parent.parent / "data" / "sessions"


def _ensure_dir():
    """Create the sessions directory if it doesn't already exist."""
    SESSIONS_DIR.mkdir(parents=True, exist_ok=True)


def empty_session(character_name="", session_name=""):
    """Return a blank session dict with all required fields at their starting values.

    Call this when beginning a fresh adventure. The session holds all the
    in-play state that changes during a game — HP, spell slots, combat order,
    conversation history, and so on.
    """
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

        "adventure":      None,
        "companions":     [],
        "story_mode":     False,
    }


def save_session(session):
    """Save the session dict to disk as JSON. Returns the file path as a string."""
    _ensure_dir()
    name = session.get("session_name") or session.get("character_name") or "session"
    path = SESSIONS_DIR / f"{name}.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(session, f, indent=2)
    return str(path)


def load_session(name):
    """Load a session from disk by name. Raises FileNotFoundError if not found."""
    path = SESSIONS_DIR / f"{name}.json"
    if not path.exists():
        raise FileNotFoundError(f"No session found: {name}")
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def list_sessions():
    """Return a sorted list of all saved session names (file stems, no .json)."""
    _ensure_dir()
    return [p.stem for p in sorted(SESSIONS_DIR.glob("*.json"))]


def delete_session(name):
    """Delete a session file from disk if it exists. Silent if it doesn't."""
    path = SESSIONS_DIR / f"{name}.json"
    if path.exists():
        path.unlink()


# ── Scene helpers ──────────────────────────────────────────────────────────────

def add_history(session, role, text):
    """Append a message to the session's conversation history.
    role must be 'player' or 'dm'. The DM model uses this history to stay in context.
    """
    session["history"].append({"role": role, "text": text})


def set_flag(session, key, value=True):
    """Set a story flag on the session (e.g. 'met_aldric', 'door_unlocked').
    Flags are arbitrary key-value pairs the DM can use to track story state.
    """
    session["flags"][key] = value


def get_flag(session, key, default=False):
    """Read a story flag. Returns the default if the flag hasn't been set."""
    return session["flags"].get(key, default)


# ── Transient character state ──────────────────────────────────────────────────

def init_hp(session, character):
    """Set session HP to max if it hasn't been initialised yet (first load)."""
    if session["current_hp"] is None:
        session["current_hp"] = character["hp"].get("max", 1)


def apply_damage(session, amount):
    """Apply damage to the session's HP, absorbing temp HP first.
    Returns the new current HP value.
    """
    if amount <= 0:
        return session["current_hp"]
    temp = session.get("temp_hp", 0)
    absorbed = min(temp, amount)
    session["temp_hp"] = temp - absorbed
    session["current_hp"] = max(0, session["current_hp"] - (amount - absorbed))
    return session["current_hp"]


def apply_healing(session, amount, max_hp):
    """Heal the session's HP, capped at max_hp. Returns the new current HP."""
    session["current_hp"] = min(max_hp, session["current_hp"] + amount)
    return session["current_hp"]


def use_spell_slot(session, level):
    """Increment the used count for a spell slot of the given level."""
    key = str(level)
    session["spell_slots_used"][key] = session["spell_slots_used"].get(key, 0) + 1


def restore_spell_slot(session, level):
    """Decrement the used count for a spell slot of the given level (minimum 0)."""
    key = str(level)
    used = session["spell_slots_used"].get(key, 0)
    if used > 0:
        session["spell_slots_used"][key] = used - 1


def long_rest(session, character):
    """Apply a long rest to the session: restore HP, clear conditions, reset slots.
    Also recovers half the character's hit dice (minimum 1).
    """
    session["current_hp"]       = character["hp"].get("max", 1)
    session["temp_hp"]          = 0
    session["hit_dice_spent"]   = max(0, session["hit_dice_spent"] - max(1, character["level"] // 2))
    session["spell_slots_used"] = {}
    session["conditions"]       = []
    session["death_saves"]      = {"successes": 0, "failures": 0}
    session["stable"]           = False


def short_rest(session, hp_gained, max_hp):
    """Apply a short rest to the session: spend one hit die and gain hp_gained HP."""
    session["hit_dice_spent"] += 1
    session["current_hp"] = min(session["current_hp"] + hp_gained, max_hp)


# ── Combat state ───────────────────────────────────────────────────────────────

def start_combat(session, combatants):
    """Begin combat by sorting combatants by initiative (highest goes first).
    Sets in_combat=True and resets the round counter and turn pointer.
    combatants is a list of dicts with 'initiative', 'hp', 'max_hp', 'ac', etc.
    """
    ordered = sorted(combatants, key=lambda c: c["initiative"], reverse=True)
    for c in ordered:
        c.setdefault("conditions", [])   # ensure conditions list exists on each combatant
    session["in_combat"]         = True
    session["round"]             = 1
    session["current_turn"]      = 0
    session["initiative_order"]  = ordered


def end_combat(session):
    """Clear all combat state from the session after combat ends."""
    session["in_combat"]        = False
    session["round"]            = 0
    session["current_turn"]     = 0
    session["initiative_order"] = []


def advance_turn(session):
    """Move to the next combatant in initiative order.
    When the last combatant's turn ends, wraps back to index 0 and increments the round.
    """
    order = session["initiative_order"]
    if not order:
        return
    session["current_turn"] += 1
    if session["current_turn"] >= len(order):
        session["current_turn"] = 0
        session["round"] += 1


def current_combatant(session):
    """Return the combatant dict whose turn it currently is, or None if no combat."""
    order = session["initiative_order"]
    if not order:
        return None
    return order[session["current_turn"]]


def apply_combat_damage(session, combatant_name, amount):
    """Apply damage to a combatant by name. Returns their new HP, or None if not found."""
    for c in session["initiative_order"]:
        if c["name"] == combatant_name:
            c["hp"] = max(0, c["hp"] - amount)
            return c["hp"]
    return None


def apply_combat_healing(session, combatant_name, amount):
    """Heal a combatant by name, capped at their max HP. Returns their new HP, or None."""
    for c in session["initiative_order"]:
        if c["name"] == combatant_name:
            c["hp"] = min(c["max_hp"], c["hp"] + amount)
            return c["hp"]
    return None


def add_condition(session, combatant_name, condition):
    """Add a status condition (e.g. 'Blinded', 'Prone') to a combatant. No-op if already present."""
    for c in session["initiative_order"]:
        if c["name"] == combatant_name:
            if condition not in c["conditions"]:
                c["conditions"].append(condition)
            return


def remove_condition(session, combatant_name, condition):
    """Remove a status condition from a combatant. No-op if the condition isn't present."""
    for c in session["initiative_order"]:
        if c["name"] == combatant_name:
            c["conditions"] = [x for x in c["conditions"] if x != condition]
            return


def living_combatants(session):
    """Return all combatants with HP > 0 (still alive and fighting)."""
    return [c for c in session["initiative_order"] if c["hp"] > 0]


def enemies_alive(session):
    """Return True if any non-player, non-companion combatant still has HP > 0."""
    return any(c["hp"] > 0 for c in session["initiative_order"]
               if not c["is_player"] and not c.get("is_companion"))
