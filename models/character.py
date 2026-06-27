"""
Character model — the core data structure for a player character.

This module is the Model layer for everything that defines WHO a character is:
their stats, equipment, spells, skills, and how they change over time (damage,
healing, rest, level-up). It does NOT drive the UI or make DM decisions.

Every character is stored as a plain Python dict and saved to disk as JSON.
Use empty_character() to get a fresh blank dict, save_character() / load_character()
to persist it, and the helper functions below to read or modify specific fields.
"""

import json
import os
from pathlib import Path

# Points two levels up from models/ to the project root, then into data/characters/
CHARACTERS_DIR = Path(__file__).parent.parent / "data" / "characters"


# ── Ability score modifier ────────────────────────────────────────────────────

def modifier(score: int) -> int:
    """Return the D&D ability modifier for a given ability score.
    Formula: (score - 10) // 2.  A score of 10 gives +0, 16 gives +3, etc.
    """
    return (score - 10) // 2


def modifier_str(score: int) -> str:
    """Return the modifier as a display string like '+3' or '-1'."""
    m = modifier(score)
    return f"+{m}" if m >= 0 else str(m)


# ── Proficiency bonus by level ────────────────────────────────────────────────

def proficiency_bonus(level: int) -> int:
    """Return the proficiency bonus for a given character level (1–20).
    Starts at +2 at level 1 and increases by 1 every 4 levels.
    """
    return (level - 1) // 4 + 2


# ── Default empty character ───────────────────────────────────────────────────

def empty_character() -> dict:
    """Return a blank character dict with all required fields set to safe defaults.

    Every field that the rest of the codebase might read is guaranteed to exist here.
    Use this as the starting point when building a new character from scratch or
    as the merge target when importing a character from D&D Beyond.
    """
    return {
        "name": "",
        "race": "",
        "class": "",
        "subclass": "",
        "background": "",
        "level": 1,
        "experience": 0,
        "alignment": "",

        "abilities": {
            "strength":     10,
            "dexterity":    10,
            "constitution": 10,
            "intelligence": 10,
            "wisdom":       10,
            "charisma":     10,
        },

        "hp": {
            "max":     8,
            "current": 8,
            "temp":    0,
        },
        "hit_dice": {
            "type":    "d8",
            "total":   1,
            "used":    0,
        },

        "armor_class":    10,
        "initiative":     0,
        "speed":          30,
        "death_saves": {
            "successes": 0,
            "failures":  0,
        },

        "saving_throw_proficiencies": [],
        "skill_proficiencies":        [],
        "skill_expertises":           [],
        "armor_proficiencies":        [],
        "weapon_proficiencies":       [],
        "tool_proficiencies":         [],
        "languages":                  [],

        "skill_overrides": {},

        "attacks": [],

        "spellcasting": {
            "enabled":      False,
            "ability":      "",
            "spell_save_dc": 0,
            "attack_bonus":  0,
            "slots": {
                "1": {"total": 0, "used": 0},
                "2": {"total": 0, "used": 0},
                "3": {"total": 0, "used": 0},
                "4": {"total": 0, "used": 0},
                "5": {"total": 0, "used": 0},
                "6": {"total": 0, "used": 0},
                "7": {"total": 0, "used": 0},
                "8": {"total": 0, "used": 0},
                "9": {"total": 0, "used": 0},
            },
            "spells_known":    [],
            "spells_prepared": [],
        },

        "equipment": [],

        "currency": {
            "cp": 0,
            "sp": 0,
            "ep": 0,
            "gp": 0,
            "pp": 0,
        },

        "features": [],

        "conditions": [],

        "magic_items":         [],
        "magic_weapon_bonus":  0,
        "magic_armor_bonus":   0,

        "feats": [],

        "inspiration": False,
        "feature_uses": {},

        "personality_traits": "",
        "ideals":             "",
        "bonds":              "",
        "flaws":              "",
        "backstory":          "",

        "notes": "",
    }


# ── Derived stats ─────────────────────────────────────────────────────────────

# Maps each skill name (snake_case) to the ability score it is based on.
# This is the standard D&D 5e skill-to-ability mapping.
SKILLS = {
    "acrobatics":      "dexterity",
    "animal_handling": "wisdom",
    "arcana":          "intelligence",
    "athletics":       "strength",
    "deception":       "charisma",
    "history":         "intelligence",
    "insight":         "wisdom",
    "intimidation":    "charisma",
    "investigation":   "intelligence",
    "medicine":        "wisdom",
    "nature":          "intelligence",
    "perception":      "wisdom",
    "performance":     "charisma",
    "persuasion":      "charisma",
    "religion":        "intelligence",
    "sleight_of_hand": "dexterity",
    "stealth":         "dexterity",
    "survival":        "wisdom",
}


def skill_bonus(char: dict, skill: str) -> int:
    """Return the total modifier for a skill check.

    Checks skill_overrides first (manually set values), then computes:
    - base ability modifier
    - + proficiency bonus if proficient in this skill
    - + proficiency bonus again (double) if the character has Expertise in it
    """
    if skill in char.get("skill_overrides", {}):
        return char["skill_overrides"][skill]
    ability = SKILLS.get(skill)
    if not ability:
        return 0
    base = modifier(char["abilities"][ability])
    pb = proficiency_bonus(char["level"])
    if skill in char.get("skill_expertises", []):
        return base + pb * 2   # Expertise = double proficiency
    if skill in char.get("skill_proficiencies", []):
        return base + pb
    return base


def saving_throw_bonus(char: dict, ability: str) -> int:
    """Return the total modifier for a saving throw against the given ability.
    Adds proficiency bonus if the character is proficient in that save.
    """
    base = modifier(char["abilities"][ability])
    pb = proficiency_bonus(char["level"])
    if ability in char.get("saving_throw_proficiencies", []):
        return base + pb
    return base


def passive_perception(char: dict) -> int:
    """Return the character's passive Perception score (10 + perception bonus)."""
    return 10 + skill_bonus(char, "perception")


def computed_spell_stats(char: dict) -> tuple:
    """Return (spell_save_dc, spell_attack_bonus) for this character.

    If these are already stored on the character (e.g. from a D&D Beyond import),
    use those directly. Otherwise calculate them from the spellcasting ability.
    Returns (0, 0) if the character has no spellcasting ability configured.
    """
    sc = char["spellcasting"]
    if sc.get("spell_save_dc") or sc.get("attack_bonus"):
        return sc["spell_save_dc"], sc["attack_bonus"]
    ability = sc.get("ability", "")
    if not ability:
        return 0, 0
    mod = modifier(char["abilities"][ability])
    pb = proficiency_bonus(char["level"])
    return 8 + pb + mod, pb + mod


# ── Persistence ───────────────────────────────────────────────────────────────

def list_characters() -> list:
    """Return a list of all saved character names (file stems, no extension)."""
    CHARACTERS_DIR.mkdir(parents=True, exist_ok=True)
    return [f.stem for f in CHARACTERS_DIR.glob("*.json")]


def save_character(char: dict) -> Path:
    """Write the character dict to disk as JSON. Returns the file path."""
    CHARACTERS_DIR.mkdir(parents=True, exist_ok=True)
    path = CHARACTERS_DIR / f"{char['name']}.json"
    with open(path, "w") as f:
        json.dump(char, f, indent=2)
    return path


def migrate_character(char: dict) -> dict:
    """Forward-migrate an older saved character to the current schema.

    Any fields that exist in empty_character() but are missing from the loaded
    dict are added with their default value. This lets old saves work seamlessly
    after new fields are added to the schema.
    """
    defaults = empty_character()
    for key, default in defaults.items():
        if key not in char:
            char[key] = default
        elif isinstance(default, dict) and isinstance(char[key], dict):
            for subkey, subdefault in default.items():
                if subkey not in char[key]:
                    char[key][subkey] = subdefault
                elif isinstance(subdefault, dict) and isinstance(char[key][subkey], dict):
                    for k, v in subdefault.items():
                        char[key][subkey].setdefault(k, v)
    return char


def validate_character(char: dict) -> None:
    """Raise ValueError if the character dict is missing required fields or has bad values.

    Called automatically by load_character() after migration. Catches common
    problems early so they surface as clear error messages rather than cryptic
    crashes later in the game loop.
    """
    name = char.get("name", "?")

    def _err(msg):
        raise ValueError(f"Character '{name}': {msg}")

    hp = char.get("hp", {})
    if not isinstance(hp, dict):
        _err(f"'hp' must be a dict, got {type(hp).__name__}")
    for k in ("max", "current", "temp"):
        if not isinstance(hp.get(k), int):
            _err(f"'hp.{k}' must be an int")
    if hp["max"] < 1:
        _err("'hp.max' must be at least 1")

    ab = char.get("abilities", {})
    if not isinstance(ab, dict):
        _err(f"'abilities' must be a dict, got {type(ab).__name__}")
    for key in ("strength", "dexterity", "constitution", "intelligence", "wisdom", "charisma"):
        if not isinstance(ab.get(key), int):
            _err(f"'abilities.{key}' must be an int")

    if not isinstance(char.get("level"), int) or not (1 <= char["level"] <= 20):
        _err("'level' must be an int between 1 and 20")
    if not isinstance(char.get("experience"), int) or char["experience"] < 0:
        _err("'experience' must be a non-negative int")

    hd = char.get("hit_dice", {})
    if not isinstance(hd, dict):
        _err(f"'hit_dice' must be a dict, got {type(hd).__name__}")
    if not isinstance(hd.get("total"), int) or hd["total"] < 1:
        _err("'hit_dice.total' must be a positive int")

    sc = char.get("spellcasting", {})
    if not isinstance(sc, dict):
        _err(f"'spellcasting' must be a dict, got {type(sc).__name__}")
    if not isinstance(sc.get("enabled"), bool):
        _err("'spellcasting.enabled' must be a bool")

    for field in ("skill_proficiencies", "saving_throw_proficiencies",
                  "attacks", "equipment", "features", "conditions"):
        if not isinstance(char.get(field), list):
            _err(f"'{field}' must be a list")


def load_character(name: str) -> dict:
    """Load a character from disk by name, migrate it forward, and validate it.
    Raises FileNotFoundError if no save file exists, or ValueError if the data is invalid.
    """
    path = CHARACTERS_DIR / f"{name}.json"
    if not path.exists():
        raise FileNotFoundError(f"No character named '{name}' found.")
    with open(path) as f:
        char = json.load(f)
    char = migrate_character(char)
    validate_character(char)
    return char


# ── HP helpers ────────────────────────────────────────────────────────────────

def apply_damage(char: dict, amount: int) -> dict:
    """Apply damage to the character, absorbing temp HP first.

    Temp HP acts as a buffer — damage hits temp HP before reducing current HP.
    Temp HP cannot go below 0; remaining damage after temp HP is exhausted
    reduces current HP, which also cannot go below 0.
    """
    temp = char["hp"]["temp"]
    if temp >= amount:
        # All damage absorbed by temp HP
        char["hp"]["temp"] -= amount
        return char
    # Temp HP only covers part of the damage
    amount -= temp
    char["hp"]["temp"] = 0
    char["hp"]["current"] = max(0, char["hp"]["current"] - amount)
    return char


def apply_healing(char: dict, amount: int) -> dict:
    """Heal the character, capped at their maximum HP. Cannot exceed max."""
    char["hp"]["current"] = min(char["hp"]["max"], char["hp"]["current"] + amount)
    return char


def add_temp_hp(char: dict, amount: int) -> dict:
    """Grant temporary HP. Per D&D 5e rules, temp HP don't stack — take the higher value."""
    char["hp"]["temp"] = max(char["hp"]["temp"], amount)
    return char


def is_unconscious(char: dict) -> bool:
    """Return True if the character is at 0 HP (unconscious or dead)."""
    return char["hp"]["current"] == 0


# ── Spell slot helpers ────────────────────────────────────────────────────────

def use_spell_slot(char: dict, level: int) -> dict:
    """Mark one spell slot of the given level as used.
    Raises ValueError if no slots of that level are available.
    """
    slots = char["spellcasting"]["slots"][str(level)]
    available = slots["total"] - slots["used"]
    if available <= 0:
        raise ValueError(f"No level {level} spell slots remaining.")
    slots["used"] += 1
    return char


def restore_spell_slots(char: dict) -> dict:
    """Reset all spell slot usage to 0 (typically called on long rest)."""
    for slot in char["spellcasting"]["slots"].values():
        slot["used"] = 0
    return char


# ── Rest ──────────────────────────────────────────────────────────────────────

def short_rest(char: dict, hit_dice_spent: int, rolls: list) -> dict:
    """Resolve a short rest: spend hit dice to regain HP.

    rolls — list of raw die results (e.g. [5, 3] for two d8s rolled by the player).
    Constitution modifier is added to each roll, minimum 1 HP regained per die.
    Warlocks also recover their Pact Magic spell slots on a short rest.
    Raises ValueError if the character doesn't have enough hit dice remaining.
    """
    con_mod = modifier(char["abilities"]["constitution"])
    available = char["hit_dice"]["total"] - char["hit_dice"]["used"]
    if hit_dice_spent > available:
        raise ValueError(f"Only {available} hit dice available.")
    healing = sum(max(1, r + con_mod) for r in rolls[:hit_dice_spent])
    char["hit_dice"]["used"] += hit_dice_spent
    if char.get("class") == "Warlock":
        restore_spell_slots(char)
    return apply_healing(char, healing)


def long_rest(char: dict) -> dict:
    """Resolve a long rest: fully restore HP, spell slots, half of spent hit dice, and features.

    Per D&D 5e rules, a long rest restores at most half the character's total hit dice
    (minimum 1). All spell slots and all feature uses are also reset.
    """
    char["hp"]["current"] = char["hp"]["max"]
    char["hp"]["temp"] = 0
    total = char["hit_dice"]["total"]
    # Recover up to half the character's total hit dice (round up), minimum 1
    char["hit_dice"]["used"] = max(0, char["hit_dice"]["used"] - max(1, (total + 1) // 2))
    char["death_saves"] = {"successes": 0, "failures": 0}
    char["conditions"] = []
    restore_spell_slots(char)
    for feature in char.get("features", []):
        if feature.get("uses"):
            feature["uses"]["used"] = 0
    return char


# ── Adventure reset ───────────────────────────────────────────────────────────

def reset_to_level1(char: dict) -> dict:
    """Strip all accumulated adventure progress, returning char to level 1 state.

    Keeps identity (race, class, abilities, proficiencies, equipment, personality).
    Resets XP, level, HP, hit dice, conditions, feature uses, and spell slot usage.
    """
    from models.progression import CLASS_FEATURE_CHARGES, current_max_uses, SUBCLASS_TRIGGER_LEVELS

    cls     = char.get("class", "")
    con_mod = modifier(char["abilities"]["constitution"])
    die_str = char.get("hit_dice", {}).get("type", "d8")
    die_max = int(die_str.lstrip("d"))

    if SUBCLASS_TRIGGER_LEVELS.get(cls, 3) > 1:
        char["subclass"] = ""

    char["level"]      = 1
    char["experience"] = 0

    hp1 = max(1, die_max + con_mod)
    char["hp"]["max"]     = hp1
    char["hp"]["current"] = hp1
    char["hp"]["temp"]    = 0

    char["hit_dice"]["total"] = 1
    char["hit_dice"]["used"]  = 0

    char["conditions"]   = []
    char["inspiration"]  = False
    char["death_saves"]  = {"successes": 0, "failures": 0}

    for slot in char.get("spellcasting", {}).get("slots", {}).values():
        slot["used"] = 0

    char["feature_uses"] = {}
    for name, info in CLASS_FEATURE_CHARGES.get(cls, {}).items():
        if info.get("min_level", 1) <= 1:
            max_uses = current_max_uses(name, cls, 1, char)
            char["feature_uses"][name] = {"current": max_uses, "max": max_uses}

    return char


# ── Display ───────────────────────────────────────────────────────────────────

def summary(char: dict) -> str:
    """Return a plain-text character sheet summary for debugging or the console."""
    pb = proficiency_bonus(char["level"])
    ab = char["abilities"]
    lines = [
        f"{'='*50}",
        f"  {char['name']}  |  {char['race']} {char['class']} {char.get('subclass','')}  |  Level {char['level']}",
        f"  Background: {char['background']}  |  Alignment: {char['alignment']}",
        f"{'='*50}",
        f"  HP: {char['hp']['current']}/{char['hp']['max']}"
        + (f"  (Temp: {char['hp']['temp']})" if char["hp"]["temp"] else "")
        + (f"  [UNCONSCIOUS]" if is_unconscious(char) else ""),
        f"  AC: {char['armor_class']}  |  Speed: {char['speed']}ft",
        f"  Proficiency Bonus: +{pb}  |  Passive Perception: {passive_perception(char)}",
    ]
    lines.append(f"{'='*50}")
    return "\n".join(lines)
