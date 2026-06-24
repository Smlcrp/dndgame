import random
import re

VALID_DICE = {4, 6, 8, 10, 12, 20, 100}


def roll(sides):
    if sides not in VALID_DICE:
        raise ValueError(f"Invalid die: d{sides}. Valid: {sorted(VALID_DICE)}")
    return random.randint(1, sides)


def roll_dice(notation):
    """Parse and roll a notation string like '2d6+3', '1d8', 'd20', '3d6-1'.
    Returns {notation, rolls, modifier, total}.
    """
    notation = notation.strip().lower()
    m = re.fullmatch(r"(\d*)d(\d+)\s*([+-]\s*\d+)?", notation)
    if not m:
        raise ValueError(f"Invalid dice notation: '{notation}'")

    count    = int(m.group(1)) if m.group(1) else 1
    sides    = int(m.group(2))
    mod_str  = (m.group(3) or "0").replace(" ", "")
    modifier = int(mod_str)

    if sides not in VALID_DICE:
        raise ValueError(f"Invalid die in '{notation}': d{sides}")
    if count < 1 or count > 100:
        raise ValueError(f"Dice count must be 1–100, got {count}")

    rolls = [random.randint(1, sides) for _ in range(count)]
    total = sum(rolls) + modifier
    return {"notation": notation, "rolls": rolls, "modifier": modifier, "total": total}


def d20_check(modifier=0, advantage=False, disadvantage=False):
    """Roll a d20 for an attack, save, or skill check.
    Advantage and disadvantage cancel out if both are True.
    Returns {rolls, kept, modifier, total, nat20, nat1}.
    """
    if advantage and not disadvantage:
        rolls = [random.randint(1, 20), random.randint(1, 20)]
        kept  = max(rolls)
    elif disadvantage and not advantage:
        rolls = [random.randint(1, 20), random.randint(1, 20)]
        kept  = min(rolls)
    else:
        kept  = random.randint(1, 20)
        rolls = [kept]

    total = kept + modifier
    return {
        "rolls":    rolls,
        "kept":     kept,
        "modifier": modifier,
        "total":    total,
        "nat20":    kept == 20,
        "nat1":     kept == 1,
    }


def damage(notation):
    """Roll damage dice. Thin alias for roll_dice for call-site clarity."""
    return roll_dice(notation)


def critical_damage(notation):
    """Roll critical hit damage: double the dice, keep same modifier.
    '2d6+3' becomes 4d6+3.
    Returns {notation, rolls, modifier, total, critical: True}.
    """
    notation = notation.strip().lower()
    m = re.fullmatch(r"(\d*)d(\d+)\s*([+-]\s*\d+)?", notation)
    if not m:
        raise ValueError(f"Invalid dice notation: '{notation}'")

    count    = int(m.group(1)) if m.group(1) else 1
    sides    = int(m.group(2))
    mod_str  = (m.group(3) or "0").replace(" ", "")
    modifier = int(mod_str)

    if sides not in VALID_DICE:
        raise ValueError(f"Invalid die in '{notation}': d{sides}")

    rolls = [random.randint(1, sides) for _ in range(count * 2)]
    total = sum(rolls) + modifier
    return {"notation": notation, "rolls": rolls, "modifier": modifier,
            "total": total, "critical": True}


def hit_die(die_str, con_mod=0):
    """Roll a hit die for short rest HP recovery.
    die_str is like 'd8' or '1d8'. Minimum result is 1.
    Returns {roll, con_mod, total}.
    """
    die_str = die_str.strip().lower().lstrip("1")
    if not die_str.startswith("d"):
        die_str = "d" + die_str
    sides = int(die_str[1:])
    if sides not in VALID_DICE:
        raise ValueError(f"Invalid hit die: {die_str}")
    result = random.randint(1, sides)
    total  = max(1, result + con_mod)
    return {"roll": result, "con_mod": con_mod, "total": total}


def death_save():
    """Roll a death saving throw. 10+ is a success; 20 is a critical (regain 1 HP).
    Returns {roll, success, critical}.
    """
    result = random.randint(1, 20)
    return {"roll": result, "success": result >= 10, "critical": result == 20}


def initiative(dex_mod=0):
    """Roll initiative (d20 + DEX modifier).
    Returns {roll, modifier, total}.
    """
    result = random.randint(1, 20)
    return {"roll": result, "modifier": dex_mod, "total": result + dex_mod}
