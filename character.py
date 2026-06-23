"""
D&D 5e Character System
Handles loading, saving, and manipulating character sheets.
"""

import json
import os
from pathlib import Path

CHARACTERS_DIR = Path(__file__).parent / "characters"


# ── Ability score modifier ────────────────────────────────────────────────────

def modifier(score: int) -> int:
    return (score - 10) // 2


def modifier_str(score: int) -> str:
    m = modifier(score)
    return f"+{m}" if m >= 0 else str(m)


# ── Proficiency bonus by level ────────────────────────────────────────────────

def proficiency_bonus(level: int) -> int:
    return (level - 1) // 4 + 2


# ── Default empty character ───────────────────────────────────────────────────

def empty_character() -> dict:
    return {
        "name": "",
        "race": "",
        "class": "",
        "subclass": "",
        "background": "",
        "level": 1,
        "experience": 0,
        "alignment": "",

        # Ability scores
        "abilities": {
            "strength":     10,
            "dexterity":    10,
            "constitution": 10,
            "intelligence": 10,
            "wisdom":       10,
            "charisma":     10,
        },

        # Hit points
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

        # Combat
        "armor_class":    10,
        "initiative":     0,   # override; normally dex mod
        "speed":          30,
        "death_saves": {
            "successes": 0,
            "failures":  0,
        },

        # Proficiencies
        "saving_throw_proficiencies": [],   # list of ability names
        "skill_proficiencies":        [],   # list of skill names
        "skill_expertises":           [],   # double proficiency
        "armor_proficiencies":        [],
        "weapon_proficiencies":       [],
        "tool_proficiencies":         [],
        "languages":                  [],

        # Skills (computed on the fly but stored for overrides)
        "skill_overrides": {},

        # Attacks
        "attacks": [],
        # Each: {"name": str, "attack_bonus": int, "damage": str, "damage_type": str, "notes": str}

        # Spellcasting
        "spellcasting": {
            "enabled":      False,
            "ability":      "",       # e.g. "wisdom"
            "spell_save_dc": 0,       # computed or overridden
            "attack_bonus":  0,       # computed or overridden
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
            # Each spell: {"name": str, "level": int, "school": str, "description": str}
        },

        # Equipment
        "equipment": [],
        # Each: {"name": str, "quantity": int, "weight": float, "notes": str}

        "currency": {
            "cp": 0,
            "sp": 0,
            "ep": 0,
            "gp": 0,
            "pp": 0,
        },

        # Features & Traits
        "features": [],
        # Each: {"name": str, "source": str, "description": str, "uses": null | {"max": int, "used": int}}

        # Conditions
        "conditions": [],   # e.g. ["poisoned", "prone"]

        # Inspiration
        "inspiration": False,

        # Personality
        "personality_traits": "",
        "ideals":             "",
        "bonds":              "",
        "flaws":              "",
        "backstory":          "",

        # Notes
        "notes": "",
    }


# ── Derived stats ─────────────────────────────────────────────────────────────

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
    if skill in char.get("skill_overrides", {}):
        return char["skill_overrides"][skill]
    ability = SKILLS.get(skill)
    if not ability:
        return 0
    base = modifier(char["abilities"][ability])
    pb = proficiency_bonus(char["level"])
    if skill in char.get("skill_expertises", []):
        return base + pb * 2
    if skill in char.get("skill_proficiencies", []):
        return base + pb
    return base


def saving_throw_bonus(char: dict, ability: str) -> int:
    base = modifier(char["abilities"][ability])
    pb = proficiency_bonus(char["level"])
    if ability in char.get("saving_throw_proficiencies", []):
        return base + pb
    return base


def passive_perception(char: dict) -> int:
    return 10 + skill_bonus(char, "perception")


def computed_spell_stats(char: dict) -> tuple[int, int]:
    """Returns (spell_save_dc, spell_attack_bonus)."""
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

def list_characters() -> list[str]:
    CHARACTERS_DIR.mkdir(exist_ok=True)
    return [f.stem for f in CHARACTERS_DIR.glob("*.json")]


def save_character(char: dict) -> Path:
    CHARACTERS_DIR.mkdir(exist_ok=True)
    path = CHARACTERS_DIR / f"{char['name']}.json"
    with open(path, "w") as f:
        json.dump(char, f, indent=2)
    return path


def load_character(name: str) -> dict:
    path = CHARACTERS_DIR / f"{name}.json"
    if not path.exists():
        raise FileNotFoundError(f"No character named '{name}' found.")
    with open(path) as f:
        return json.load(f)


# ── HP helpers ────────────────────────────────────────────────────────────────

def apply_damage(char: dict, amount: int) -> dict:
    """Apply damage, consuming temp HP first."""
    temp = char["hp"]["temp"]
    if temp >= amount:
        char["hp"]["temp"] -= amount
        return char
    amount -= temp
    char["hp"]["temp"] = 0
    char["hp"]["current"] = max(0, char["hp"]["current"] - amount)
    return char


def apply_healing(char: dict, amount: int) -> dict:
    char["hp"]["current"] = min(char["hp"]["max"], char["hp"]["current"] + amount)
    return char


def add_temp_hp(char: dict, amount: int) -> dict:
    """Temp HP doesn't stack — take the higher value."""
    char["hp"]["temp"] = max(char["hp"]["temp"], amount)
    return char


def is_unconscious(char: dict) -> bool:
    return char["hp"]["current"] == 0


# ── Spell slot helpers ────────────────────────────────────────────────────────

def use_spell_slot(char: dict, level: int) -> dict:
    slots = char["spellcasting"]["slots"][str(level)]
    available = slots["total"] - slots["used"]
    if available <= 0:
        raise ValueError(f"No level {level} spell slots remaining.")
    slots["used"] += 1
    return char


def restore_spell_slots(char: dict) -> dict:
    """Full rest — restore all spell slots."""
    for slot in char["spellcasting"]["slots"].values():
        slot["used"] = 0
    return char


# ── Rest ──────────────────────────────────────────────────────────────────────

def short_rest(char: dict, hit_dice_spent: int, rolls: list[int]) -> dict:
    """Apply a short rest: spend hit dice to regain HP."""
    con_mod = modifier(char["abilities"]["constitution"])
    available = char["hit_dice"]["total"] - char["hit_dice"]["used"]
    if hit_dice_spent > available:
        raise ValueError(f"Only {available} hit dice available.")
    healing = sum(max(1, r + con_mod) for r in rolls[:hit_dice_spent])
    char["hit_dice"]["used"] += hit_dice_spent
    return apply_healing(char, healing)


def long_rest(char: dict) -> dict:
    """Full rest: restore HP, half hit dice, all spell slots, reset death saves."""
    char["hp"]["current"] = char["hp"]["max"]
    char["hp"]["temp"] = 0
    total = char["hit_dice"]["total"]
    char["hit_dice"]["used"] = max(0, char["hit_dice"]["used"] - max(1, total // 2))
    char["death_saves"] = {"successes": 0, "failures": 0}
    char["conditions"] = []
    restore_spell_slots(char)

    # Reset limited-use features
    for feature in char.get("features", []):
        if feature.get("uses"):
            feature["uses"]["used"] = 0

    return char


# ── Display ───────────────────────────────────────────────────────────────────

def summary(char: dict) -> str:
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
        f"  AC: {char['armor_class']}  |  Speed: {char['speed']}ft  |  Initiative: {modifier_str(ab['dexterity'])}",
        f"  Proficiency Bonus: +{pb}  |  Passive Perception: {passive_perception(char)}",
        f"  Inspiration: {'Yes' if char['inspiration'] else 'No'}",
        f"",
        f"  ABILITY SCORES",
        f"  STR {ab['strength']:>2} ({modifier_str(ab['strength'])})  "
        f"DEX {ab['dexterity']:>2} ({modifier_str(ab['dexterity'])})  "
        f"CON {ab['constitution']:>2} ({modifier_str(ab['constitution'])})",
        f"  INT {ab['intelligence']:>2} ({modifier_str(ab['intelligence'])})  "
        f"WIS {ab['wisdom']:>2} ({modifier_str(ab['wisdom'])})  "
        f"CHA {ab['charisma']:>2} ({modifier_str(ab['charisma'])})",
    ]

    if char["conditions"]:
        lines.append(f"\n  CONDITIONS: {', '.join(char['conditions'])}")

    if char["spellcasting"]["enabled"]:
        dc, atk = computed_spell_stats(char)
        lines.append(f"\n  SPELLCASTING  |  Save DC: {dc}  |  Attack: {modifier_str(atk)}")
        slot_str = "  Slots: "
        for lvl, s in char["spellcasting"]["slots"].items():
            if s["total"] > 0:
                slot_str += f"L{lvl}:{s['total']-s['used']}/{s['total']}  "
        lines.append(slot_str)

    lines.append(f"{'='*50}")
    return "\n".join(lines)
