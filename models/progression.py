XP_THRESHOLDS = [
    0, 300, 900, 2700, 6500, 14000, 23000, 34000, 48000, 64000,
    83000, 100000, 120000, 140000, 165000, 195000, 225000, 265000, 305000, 355000,
]

# Per-class levels that grant an ASI or Feat choice
ASI_LEVELS = {
    "Artificer": [4, 8, 12, 16, 19],
    "Barbarian": [4, 8, 12, 16, 19],
    "Bard":      [4, 8, 12, 16, 19],
    "Cleric":    [4, 8, 12, 16, 19],
    "Druid":     [4, 8, 12, 16, 19],
    "Fighter":   [4, 6, 8, 12, 14, 16, 19],
    "Monk":      [4, 8, 12, 16, 19],
    "Paladin":   [4, 8, 12, 16, 19],
    "Ranger":    [4, 8, 12, 16, 19],
    "Rogue":     [4, 8, 10, 12, 16, 19],
    "Sorcerer":  [4, 8, 12, 16, 19],
    "Warlock":   [4, 8, 12, 16, 19],
    "Wizard":    [4, 8, 12, 16, 19],
}

# Level at which each class first chooses a subclass
SUBCLASS_TRIGGER_LEVELS = {
    "Artificer": 3,
    "Barbarian": 3,
    "Bard":      3,
    "Cleric":    1,
    "Druid":     2,
    "Fighter":   3,
    "Monk":      3,
    "Paladin":   3,
    "Ranger":    3,
    "Rogue":     3,
    "Sorcerer":  1,
    "Warlock":   1,
    "Wizard":    2,
}

# Limited-use features per class.
# max_uses values:
#   int          — fixed number of uses
#   "level"      — uses = character level
#   "cha_mod"    — uses = CHA modifier (min 1)
#   "int_mod"    — uses = INT modifier (min 1)
#   "5x_level"   — pool = 5 × character level (Lay on Hands)
CLASS_FEATURE_CHARGES = {
    "Artificer": {
        "Flash of Genius": {
            "max_uses": "int_mod",
            "recharge": "short_rest",
            "desc": "Add INT modifier to a saving throw or ability check you can see fail",
            "min_level": 7,
        },
    },
    "Barbarian": {
        "Rage": {
            "max_uses": 2,
            "recharge": "long_rest",
            "desc": "Enter a rage for 1 minute: bonus damage, resistance to physical damage, advantage on STR checks/saves",
            "min_level": 1,
            "scaling": {9: 3, 12: 3, 17: 4, 20: 6},
        },
    },
    "Bard": {
        "Bardic Inspiration": {
            "max_uses": "cha_mod",
            "recharge": "long_rest",
            "desc": "Grant a creature a Bardic Inspiration die to add to one roll",
            "min_level": 1,
            "short_rest_at": 5,
        },
    },
    "Cleric": {
        "Channel Divinity": {
            "max_uses": 1,
            "recharge": "short_rest",
            "desc": "Channel divine energy for Turn Undead or a domain-specific effect",
            "min_level": 2,
            "scaling": {6: 2, 18: 3},
        },
    },
    "Druid": {
        "Wild Shape": {
            "max_uses": 2,
            "recharge": "short_rest",
            "desc": "Magically assume the shape of a beast you have seen",
            "min_level": 2,
        },
    },
    "Fighter": {
        "Second Wind": {
            "max_uses": 1,
            "recharge": "short_rest",
            "desc": "Regain 1d10 + Fighter level HP as a bonus action",
            "min_level": 1,
        },
        "Action Surge": {
            "max_uses": 1,
            "recharge": "short_rest",
            "desc": "Take one additional action on your turn",
            "min_level": 2,
            "scaling": {17: 2},
        },
        "Indomitable": {
            "max_uses": 1,
            "recharge": "long_rest",
            "desc": "Reroll a failed saving throw",
            "min_level": 9,
            "scaling": {13: 2, 17: 3},
        },
    },
    "Monk": {
        "Ki Points": {
            "max_uses": "level",
            "recharge": "short_rest",
            "desc": "Spend ki points to fuel Flurry of Blows, Patient Defense, Step of the Wind, and other monk features",
            "min_level": 2,
        },
    },
    "Paladin": {
        "Lay on Hands": {
            "max_uses": "5x_level",
            "recharge": "long_rest",
            "desc": "Restore HP from a healing pool equal to 5 × Paladin level (spend 5 to cure a disease/poison)",
            "min_level": 1,
        },
        "Cleansing Touch": {
            "max_uses": "cha_mod",
            "recharge": "long_rest",
            "desc": "End one spell on yourself or a willing creature you touch",
            "min_level": 14,
        },
    },
    "Ranger": {},
    "Rogue": {
        "Stroke of Luck": {
            "max_uses": 1,
            "recharge": "short_rest",
            "desc": "Turn a missed attack into a hit, or a failed ability check into a 20",
            "min_level": 20,
        },
    },
    "Sorcerer": {
        "Sorcery Points": {
            "max_uses": "level",
            "recharge": "long_rest",
            "desc": "Spend sorcery points to create spell slots or power Metamagic options",
            "min_level": 2,
        },
    },
    "Warlock": {
        "Eldritch Master": {
            "max_uses": 1,
            "recharge": "long_rest",
            "desc": "Spend 1 minute entreating your patron to regain all Pact Magic spell slots",
            "min_level": 20,
        },
    },
    "Wizard": {
        "Arcane Recovery": {
            "max_uses": 1,
            "recharge": "long_rest",
            "desc": "Recover spell slots totalling up to half your Wizard level (rounded up) on a short rest",
            "min_level": 1,
        },
    },
}

# Reference to CLASS_FEATURES from dnd_data — imported lazily to avoid circular deps
def _class_features():
    try:
        import sys
        from pathlib import Path
        _cb = Path(__file__).parent.parent / "views" / "desktop" / "character_builder"
        if str(_cb) not in sys.path:
            sys.path.insert(0, str(_cb))
        from dnd_data import CLASS_FEATURES
        return CLASS_FEATURES
    except Exception as _e:
        import sys as _sys
        print(f"WARNING: could not load CLASS_FEATURES from dnd_data: {_e}",
              file=_sys.stderr)
        return {}


# ── Helper functions ───────────────────────────────────────────────────────────

def level_from_xp(xp):
    level = 1
    for i, threshold in enumerate(XP_THRESHOLDS):
        if xp >= threshold:
            level = i + 1
    return level


def xp_for_level(level):
    return XP_THRESHOLDS[max(1, min(level, 20)) - 1]


def xp_to_next_level(xp, current_level):
    if current_level >= 20:
        return 0
    return XP_THRESHOLDS[current_level] - xp


def is_asi_level(cls, level):
    return level in ASI_LEVELS.get(cls, [])


def get_subclass_trigger(cls):
    return SUBCLASS_TRIGGER_LEVELS.get(cls, 3)


def features_gained_at(cls, level):
    cf = _class_features()
    return cf.get(cls, {}).get(level, [])


def feature_charges_gained_at(cls, level):
    """Return list of charge dicts for limited-use features first gained at this level."""
    charges = CLASS_FEATURE_CHARGES.get(cls, {})
    gained = []
    for name, info in charges.items():
        if info.get("min_level") == level:
            gained.append({"name": name, **info})
    return gained


def current_max_uses(feature_name, cls, level, char):
    """Resolve the actual max_uses integer for a feature given current level/character."""
    charges = CLASS_FEATURE_CHARGES.get(cls, {})
    info = charges.get(feature_name)
    if not info:
        return 0

    base = info["max_uses"]
    if base == "level":
        uses = level
    elif base == "cha_mod":
        from models.character import modifier
        uses = max(1, modifier(char.get("abilities", {}).get("charisma", 10)))
    elif base == "int_mod":
        from models.character import modifier
        uses = max(1, modifier(char.get("abilities", {}).get("intelligence", 10)))
    elif base == "5x_level":
        uses = 5 * level
    else:
        uses = int(base)

    scaling = info.get("scaling", {})
    for trigger_level in sorted(scaling.keys()):
        if level >= trigger_level:
            uses = scaling[trigger_level]

    return uses


def recharges_on_short_rest(feature_name, cls, level):
    """True if this feature recharges on short rest at the given level."""
    charges = CLASS_FEATURE_CHARGES.get(cls, {})
    info = charges.get(feature_name)
    if not info:
        return False
    if info["recharge"] == "short_rest":
        return True
    short_rest_at = info.get("short_rest_at")
    return short_rest_at is not None and level >= short_rest_at
