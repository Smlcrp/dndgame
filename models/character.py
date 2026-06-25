import json
import os
from pathlib import Path

# Points two levels up from models/ to the project root, then into data/characters/
CHARACTERS_DIR = Path(__file__).parent.parent / "data" / "characters"


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


def computed_spell_stats(char: dict) -> tuple:
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
    CHARACTERS_DIR.mkdir(parents=True, exist_ok=True)
    return [f.stem for f in CHARACTERS_DIR.glob("*.json")]


def save_character(char: dict) -> Path:
    CHARACTERS_DIR.mkdir(parents=True, exist_ok=True)
    path = CHARACTERS_DIR / f"{char['name']}.json"
    with open(path, "w") as f:
        json.dump(char, f, indent=2)
    return path


def load_character(name: str) -> dict:
    path = CHARACTERS_DIR / f"{name}.json"
    if not path.exists():
        raise FileNotFoundError(f"No character named '{name}' found.")
    with open(path) as f:
        char = json.load(f)
    char.setdefault("feature_uses", {})
    char.setdefault("inspiration", False)
    return char


# ── HP helpers ────────────────────────────────────────────────────────────────

def apply_damage(char: dict, amount: int) -> dict:
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
    for slot in char["spellcasting"]["slots"].values():
        slot["used"] = 0
    return char


# ── Rest ──────────────────────────────────────────────────────────────────────

def short_rest(char: dict, hit_dice_spent: int, rolls: list) -> dict:
    con_mod = modifier(char["abilities"]["constitution"])
    available = char["hit_dice"]["total"] - char["hit_dice"]["used"]
    if hit_dice_spent > available:
        raise ValueError(f"Only {available} hit dice available.")
    healing = sum(max(1, r + con_mod) for r in rolls[:hit_dice_spent])
    char["hit_dice"]["used"] += hit_dice_spent
    return apply_healing(char, healing)


def long_rest(char: dict) -> dict:
    char["hp"]["current"] = char["hp"]["max"]
    char["hp"]["temp"] = 0
    total = char["hit_dice"]["total"]
    char["hit_dice"]["used"] = max(0, char["hit_dice"]["used"] - max(1, total // 2))
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
