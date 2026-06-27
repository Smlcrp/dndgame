"""Companion roster — pre-built party members with full D&D 5e class identity."""

import math
import sys
from pathlib import Path

_root = Path(__file__).parent.parent
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))

# ── Tables ─────────────────────────────────────────────────────────────────────

_HIT_DICE = {
    "Barbarian": 12, "Fighter": 10, "Paladin": 10, "Ranger": 10,
    "Bard": 8, "Cleric": 8, "Druid": 8, "Monk": 8, "Rogue": 8,
    "Sorcerer": 6, "Wizard": 6,
}

_FULL_CASTER  = {"Bard", "Cleric", "Druid", "Sorcerer", "Wizard"}
_HALF_CASTER  = {"Paladin", "Ranger"}

# Full caster slot table (index = character level)
_FULL_SLOTS = [
    {},
    {1: 2},
    {1: 3},
    {1: 4, 2: 2},
    {1: 4, 2: 3},
    {1: 4, 2: 3, 3: 2},
    {1: 4, 2: 3, 3: 3},
    {1: 4, 2: 3, 3: 3, 4: 1},
    {1: 4, 2: 3, 3: 3, 4: 2},
    {1: 4, 2: 3, 3: 3, 4: 3, 5: 1},
    {1: 4, 2: 3, 3: 3, 4: 3, 5: 2},
    {1: 4, 2: 3, 3: 3, 4: 3, 5: 2, 6: 1},
    {1: 4, 2: 3, 3: 3, 4: 3, 5: 2, 6: 1},
    {1: 4, 2: 3, 3: 3, 4: 3, 5: 2, 6: 1, 7: 1},
    {1: 4, 2: 3, 3: 3, 4: 3, 5: 2, 6: 1, 7: 1},
    {1: 4, 2: 3, 3: 3, 4: 3, 5: 2, 6: 1, 7: 1, 8: 1},
    {1: 4, 2: 3, 3: 3, 4: 3, 5: 2, 6: 1, 7: 1, 8: 1},
    {1: 4, 2: 3, 3: 3, 4: 3, 5: 2, 6: 1, 7: 1, 8: 1, 9: 1},
    {1: 4, 2: 3, 3: 3, 4: 3, 5: 3, 6: 1, 7: 1, 8: 1, 9: 1},
    {1: 4, 2: 3, 3: 3, 4: 3, 5: 3, 6: 2, 7: 1, 8: 1, 9: 1},
    {1: 4, 2: 3, 3: 3, 4: 3, 5: 3, 6: 2, 7: 2, 8: 1, 9: 1},
]

# Half caster slot table (Paladin, Ranger)
_HALF_SLOTS = [
    {}, {}, {1: 2}, {1: 3}, {1: 3},
    {1: 4, 2: 2}, {1: 4, 2: 2}, {1: 4, 2: 3}, {1: 4, 2: 3},
    {1: 4, 2: 3, 3: 2}, {1: 4, 2: 3, 3: 2}, {1: 4, 2: 3, 3: 3},
    {1: 4, 2: 3, 3: 3}, {1: 4, 2: 3, 3: 3, 4: 1}, {1: 4, 2: 3, 3: 3, 4: 1},
    {1: 4, 2: 3, 3: 3, 4: 2}, {1: 4, 2: 3, 3: 3, 4: 2},
    {1: 4, 2: 3, 3: 3, 4: 3, 5: 1}, {1: 4, 2: 3, 3: 3, 4: 3, 5: 1},
    {1: 4, 2: 3, 3: 3, 4: 3, 5: 2}, {1: 4, 2: 3, 3: 3, 4: 3, 5: 2},
]

# Spells that require a slot (non-cantrips by level)
_SPELL_LEVELS = {
    "Cure Wounds": 1, "Healing Word": 1, "Guiding Bolt": 1, "Bless": 1,
    "Shield of Faith": 1, "Divine Favor": 1, "Hunter's Mark": 1,
    "Burning Hands": 1, "Magic Missile": 1, "Fog Cloud": 1, "Entangle": 1,
    "Thunderwave": 1, "Mage Armor": 1, "Ensnaring Strike": 1, "Chromatic Orb": 1,
    "Faerie Fire": 1,
    "Spiritual Weapon": 2, "Lesser Restoration": 2, "Scorching Ray": 2,
    "Suggestion": 2, "Shatter": 2, "Misty Step": 2, "Moonbeam": 2,
    "Flaming Sphere": 2, "Pass Without Trace": 2, "Silence": 2,
    "Zone of Truth": 2, "Invisibility": 2,
    "Spirit Guardians": 3, "Fireball": 3, "Call Lightning": 3, "Conjure Animals": 3,
    "Counterspell": 3, "Fly": 3, "Hypnotic Pattern": 3,
    "Tasha's Hideous Laughter": 1,
    # cantrips
    "Sacred Flame": 0, "Fire Bolt": 0, "Vicious Mockery": 0,
    "Shillelagh": 0, "Chaos Bolt": 0,
}

# Simplified companion spell damage (slot_level → damage notation)
def _spell_dmg(spell, slot_level, char_level):
    extra = max(0, slot_level - 1)
    char_extra = max(0, (char_level - 1) // 5)
    d = {
        "Sacred Flame":    f"{1+char_extra}d8",
        "Fire Bolt":       f"{1+char_extra}d10",
        "Vicious Mockery": f"{1+char_extra}d4",
        "Shillelagh":      f"1d8",
        "Guiding Bolt":    f"{3+extra}d6",
        "Magic Missile":   f"{2+slot_level}d4+{2+slot_level}",
        "Burning Hands":   f"{2+extra}d6",
        "Thunderwave":     f"{2+extra}d8",
        "Chromatic Orb":   f"{3+extra}d8",
        "Chaos Bolt":      f"2d8+1d6",
        "Scorching Ray":   f"{2+extra}d6",
        "Shatter":         f"{3+extra}d8",
        "Moonbeam":        f"{2+extra}d10",
        "Flaming Sphere":  f"{2+extra}d6",
        "Fireball":        f"{8+extra}d6",
        "Call Lightning":  f"{3+extra}d10",
        "Spirit Guardians":f"{3+extra}d8",
        "Conjure Animals": f"0",
        "Faerie Fire":     f"0",
        "Entangle":        f"0",
        "Hypnotic Pattern":f"0",
    }
    return d.get(spell, "1d6")


# ── Helpers ────────────────────────────────────────────────────────────────────

def _mod(score):
    return (score - 10) // 2


def _prof(level):
    return math.ceil(level / 4) + 1


def _calc_ac(template, ab):
    armor  = template["equipment"]["armor"]
    shield = template["equipment"].get("shield", False)
    dex    = _mod(ab["dexterity"])
    wis    = _mod(ab["wisdom"])
    con    = _mod(ab["constitution"])
    cls    = template["class"]

    if armor == "plate":          base = 18
    elif armor == "chain_mail":   base = 16
    elif armor == "half_plate":   base = 15 + min(dex, 2)
    elif armor == "breastplate":  base = 14 + min(dex, 2)
    elif armor == "chain_shirt":  base = 13 + min(dex, 2)
    elif armor == "studded":      base = 12 + dex
    elif armor == "leather":      base = 11 + dex
    elif armor == "mage_armor":   base = 13 + dex
    elif armor == "none":
        if cls == "Monk":         base = 10 + dex + wis
        elif cls == "Barbarian":  base = 10 + dex + con
        else:                     base = 10 + dex
    else:                         base = 10 + dex

    return base + (2 if shield else 0)


def _monk_die(level):
    if level >= 17: return 10
    if level >= 11: return 8
    if level >= 5:  return 6
    return 4


def _weapon_damage(template, level, ab):
    equip = template["equipment"]
    die   = equip["weapon_die"]
    ability = equip["weapon_ability"]
    amod  = _mod(ab[ability])
    if template["class"] == "Monk":
        die = _monk_die(level)
    return f"1d{die}{amod:+d}"


def _calc_spell_slots(cls, level):
    if cls in _FULL_CASTER:
        raw = _FULL_SLOTS[min(level, 20)]
    elif cls in _HALF_CASTER:
        raw = _HALF_SLOTS[min(level, 20)]
    else:
        return {}
    return {str(k): {"total": v, "used": 0} for k, v in raw.items()}


def _calc_features(template, level, ab):
    cls      = template["class"]
    cha_mod  = _mod(ab["charisma"])
    features = {}

    if cls == "Fighter":
        features["Second Wind"] = {"current": 1, "max": 1, "recharge": "short"}
        if level >= 2:
            cap = 2 if level >= 17 else 1
            features["Action Surge"] = {"current": cap, "max": cap, "recharge": "short"}

    elif cls == "Rogue":
        if level >= 2:
            features["Cunning Action"] = {"current": 1, "max": 1, "recharge": "turn"}

    elif cls == "Cleric":
        charges = 1 + (1 if level >= 6 else 0) + (1 if level >= 18 else 0)
        features["Channel Divinity"] = {"current": charges, "max": charges,
                                         "recharge": "short"}

    elif cls == "Paladin":
        pool = 5 * level
        features["Lay on Hands"] = {"current": pool, "max": pool, "recharge": "long"}
        if level >= 3:
            features["Channel Divinity"] = {"current": 1, "max": 1, "recharge": "short"}

    elif cls == "Bard":
        charges = max(1, cha_mod)
        recharge = "short" if level >= 5 else "long"
        features["Bardic Inspiration"] = {"current": charges, "max": charges,
                                           "recharge": recharge}

    elif cls == "Wizard":
        features["Arcane Recovery"] = {"current": 1, "max": 1, "recharge": "long"}

    elif cls == "Sorcerer":
        features["Sorcery Points"] = {"current": level, "max": level, "recharge": "long"}
        features["Tides of Chaos"] = {"current": 1, "max": 1, "recharge": "long"}

    elif cls == "Druid":
        features["Wild Shape"] = {"current": 2, "max": 2, "recharge": "short"}

    elif cls == "Monk":
        features["Ki Points"] = {"current": level, "max": level, "recharge": "short"}

    return features


# ── Companion roster ───────────────────────────────────────────────────────────

_TEMPLATES = [
    {
        "id": "varen_ashcloak",
        "first_name": "Varen", "last_name": "Ashcloak",
        "race": "Human", "class": "Fighter", "subclass": "Battle Master",
        "alignment": "Lawful Neutral", "background": "Soldier",
        "abilities": {"strength": 17, "dexterity": 13, "constitution": 15,
                      "intelligence": 11, "wisdom": 12, "charisma": 10},
        "equipment": {"weapon": "Longsword", "weapon_die": 8, "weapon_ability": "strength",
                      "weapon_type": "slashing", "armor": "chain_mail", "shield": True},
        "spells": [],
        "personality_traits": [
            "I approach every problem methodically — emotion clouds judgement.",
            "I keep my equipment spotless and my plans tighter.",
        ],
        "ideal":  "Duty. I fight for those who cannot fight for themselves, and I expect nothing in return.",
        "bond":   "My unit was everything to me. I carry their memory into every battle.",
        "flaw":   "I struggle to follow orders from those I don't respect.",
        "combat_role": "striker",
    },
    {
        "id": "mira_swifthand",
        "first_name": "Mira", "last_name": "Swifthand",
        "race": "Halfling", "class": "Rogue", "subclass": "Thief",
        "alignment": "Chaotic Neutral", "background": "Charlatan",
        "abilities": {"strength": 8, "dexterity": 18, "constitution": 13,
                      "intelligence": 14, "wisdom": 12, "charisma": 14},
        "equipment": {"weapon": "Short Sword", "weapon_die": 6, "weapon_ability": "dexterity",
                      "weapon_type": "piercing", "armor": "leather", "shield": False},
        "spells": [],
        "personality_traits": [
            "I always have an exit strategy, even at the dinner table.",
            "I collect debts the way other people collect coins.",
        ],
        "ideal":  "Freedom. Nobody owns me, and I return the favour by not owning anyone else.",
        "bond":   "I owe a life debt to someone who sheltered me when I had nothing. I haven't paid it back yet.",
        "flaw":   "I can't walk past something valuable without mentally calculating how I'd take it.",
        "combat_role": "striker",
    },
    {
        "id": "elara_voss",
        "first_name": "Elara", "last_name": "Voss",
        "race": "Half-Elf", "class": "Cleric", "subclass": "Life Domain",
        "deity": "Lathander",
        "alignment": "Neutral Good", "background": "Acolyte",
        "abilities": {"strength": 12, "dexterity": 10, "constitution": 14,
                      "intelligence": 13, "wisdom": 17, "charisma": 14},
        "equipment": {"weapon": "Mace", "weapon_die": 6, "weapon_ability": "strength",
                      "weapon_type": "bludgeoning", "armor": "chain_mail", "shield": True},
        "spells": ["Sacred Flame", "Cure Wounds", "Healing Word", "Guiding Bolt",
                   "Bless", "Spiritual Weapon", "Spirit Guardians", "Mass Cure Wounds"],
        "personality_traits": [
            "I have seen too much death to fear it, but never enough to accept it.",
            "I remember every person I have failed to save.",
        ],
        "ideal":  "Compassion. No one should face their darkest moment alone.",
        "bond":   "The temple that raised me was burned to ash. I seek to rebuild what was lost.",
        "flaw":   "I offer forgiveness too freely, even when it hasn't been earned.",
        "combat_role": "healer",
    },
    {
        "id": "torben_ironwall",
        "first_name": "Torben", "last_name": "Ironwall",
        "race": "Dwarf", "class": "Paladin", "subclass": "Oath of Devotion",
        "deity": "Tyr",
        "alignment": "Lawful Good", "background": "Noble",
        "abilities": {"strength": 18, "dexterity": 8, "constitution": 16,
                      "intelligence": 10, "wisdom": 14, "charisma": 13},
        "equipment": {"weapon": "Warhammer", "weapon_die": 8, "weapon_ability": "strength",
                      "weapon_type": "bludgeoning", "armor": "plate", "shield": True},
        "spells": ["Bless", "Cure Wounds", "Divine Favor", "Shield of Faith",
                   "Lesser Restoration", "Zone of Truth"],
        "personality_traits": [
            "I speak my mind, and I mean every word.",
            "I have no patience for cowardice or compromise with evil.",
        ],
        "ideal":  "Honor. My word is my bond. I would sooner die than break a sworn oath.",
        "bond":   "I swore to a dying lord to see his daughter safely to the capital. I have not reached it yet.",
        "flaw":   "I hold myself and others to an impossibly high standard and am slow to forgive failure.",
        "combat_role": "support",
    },
    {
        "id": "sable_nightwhisper",
        "first_name": "Sable", "last_name": "Nightwhisper",
        "race": "Wood Elf", "class": "Ranger", "subclass": "Hunter",
        "alignment": "True Neutral", "background": "Outlander",
        "abilities": {"strength": 12, "dexterity": 17, "constitution": 13,
                      "intelligence": 11, "wisdom": 16, "charisma": 10},
        "equipment": {"weapon": "Longbow", "weapon_die": 8, "weapon_ability": "dexterity",
                      "weapon_type": "piercing", "armor": "leather", "shield": False},
        "spells": ["Hunter's Mark", "Cure Wounds", "Ensnaring Strike",
                   "Fog Cloud", "Pass Without Trace", "Silence"],
        "personality_traits": [
            "I listen more than I speak, and I see more than I say.",
            "I read terrain better than any map.",
        ],
        "ideal":  "The Hunt. Every predator leaves a trail. I follow it to the end, however long it takes.",
        "bond":   "A creature of the deep forest sheltered me as a child when I had no one. I protect the wild in return.",
        "flaw":   "I am more comfortable with animals than people, and I can't always hide it.",
        "combat_role": "striker",
    },
    {
        "id": "zephyra_coldwell",
        "first_name": "Zephyra", "last_name": "Coldwell",
        "race": "Human", "class": "Wizard", "subclass": "School of Evocation",
        "alignment": "Lawful Neutral", "background": "Sage",
        "abilities": {"strength": 8, "dexterity": 14, "constitution": 13,
                      "intelligence": 18, "wisdom": 12, "charisma": 11},
        "equipment": {"weapon": "Quarterstaff", "weapon_die": 6, "weapon_ability": "strength",
                      "weapon_type": "bludgeoning", "armor": "mage_armor", "shield": False},
        "spells": ["Fire Bolt", "Mage Armor", "Magic Missile", "Burning Hands",
                   "Misty Step", "Scorching Ray", "Fireball", "Counterspell"],
        "personality_traits": [
            "I work through problems out loud. Others find this annoying. I find their annoyance inefficient.",
            "I remember every detail I have read and most of what I have observed.",
        ],
        "ideal":  "Knowledge. To understand a thing fully is the only way to truly master it.",
        "bond":   "My mentor vanished chasing a theory I once dismissed as impossible. I need to know what happened.",
        "flaw":   "I treat people like interesting puzzles, which they find off-putting.",
        "combat_role": "controller",
    },
    {
        "id": "bryn_foxfire",
        "first_name": "Bryn", "last_name": "Foxfire",
        "race": "Tiefling", "class": "Sorcerer", "subclass": "Wild Magic",
        "alignment": "Chaotic Neutral", "background": "Entertainer",
        "abilities": {"strength": 9, "dexterity": 14, "constitution": 13,
                      "intelligence": 13, "wisdom": 10, "charisma": 17},
        "equipment": {"weapon": "Dagger", "weapon_die": 4, "weapon_ability": "dexterity",
                      "weapon_type": "piercing", "armor": "mage_armor", "shield": False},
        "spells": ["Fire Bolt", "Mage Armor", "Chromatic Orb", "Thunderwave",
                   "Scorching Ray", "Tasha's Hideous Laughter", "Fireball", "Fly"],
        "personality_traits": [
            "I say what I think, when I think it. People can adjust.",
            "I find rules interesting primarily as things to break.",
        ],
        "ideal":  "Chaos. The best moments happen when you throw out the plan.",
        "bond":   "My magic surged when I was young and hurt someone I loved. I'm still trying to make it right.",
        "flaw":   "I act first and think second, which has occasionally been catastrophic.",
        "combat_role": "striker",
    },
    {
        "id": "oswin_merryweather",
        "first_name": "Oswin", "last_name": "Merryweather",
        "race": "Gnome", "class": "Bard", "subclass": "College of Lore",
        "alignment": "Chaotic Good", "background": "Entertainer",
        "abilities": {"strength": 8, "dexterity": 14, "constitution": 12,
                      "intelligence": 15, "wisdom": 11, "charisma": 17},
        "equipment": {"weapon": "Rapier", "weapon_die": 8, "weapon_ability": "dexterity",
                      "weapon_type": "piercing", "armor": "leather", "shield": False},
        "spells": ["Vicious Mockery", "Healing Word", "Faerie Fire", "Thunderwave",
                   "Suggestion", "Shatter", "Hypnotic Pattern", "Invisibility"],
        "personality_traits": [
            "I have a story for every situation, and I am not afraid to tell all of them.",
            "I am brave to the point of recklessness when someone else is in danger.",
        ],
        "ideal":  "Stories. Every person carries a story worth hearing. I want to hear them all.",
        "bond":   "I wrote a ballad about a village that burned. I have never performed it. I owe them a better ending.",
        "flaw":   "I cannot keep a secret if there is a good story in it.",
        "combat_role": "support",
    },
    {
        "id": "dusk_ashveil",
        "first_name": "Dusk", "last_name": "Ashveil",
        "race": "Half-Orc", "class": "Druid", "subclass": "Circle of the Moon",
        "alignment": "True Neutral", "background": "Hermit",
        "abilities": {"strength": 14, "dexterity": 11, "constitution": 15,
                      "intelligence": 11, "wisdom": 17, "charisma": 10},
        "equipment": {"weapon": "Quarterstaff", "weapon_die": 6, "weapon_ability": "strength",
                      "weapon_type": "bludgeoning", "armor": "leather", "shield": True},
        "spells": ["Shillelagh", "Cure Wounds", "Entangle", "Thunderwave",
                   "Moonbeam", "Flaming Sphere", "Call Lightning", "Conjure Animals"],
        "personality_traits": [
            "I do not rush to judgment. The forest does not rush.",
            "I speak plainly and expect the same in return.",
        ],
        "ideal":  "Balance. Nothing in nature is purely good or evil. Everything has its season.",
        "bond":   "A sacred grove was corrupted while I was away. I failed it. I will not fail again.",
        "flaw":   "I find it easier to speak for the dying than to comfort the living.",
        "combat_role": "healer",
    },
    {
        "id": "petra_stonehaven",
        "first_name": "Petra", "last_name": "Stonehaven",
        "race": "Human", "class": "Monk", "subclass": "Way of the Open Hand",
        "alignment": "Lawful Neutral", "background": "Hermit",
        "abilities": {"strength": 13, "dexterity": 17, "constitution": 14,
                      "intelligence": 11, "wisdom": 16, "charisma": 10},
        "equipment": {"weapon": "Unarmed Strike", "weapon_die": 4, "weapon_ability": "dexterity",
                      "weapon_type": "bludgeoning", "armor": "none", "shield": False},
        "spells": [],
        "personality_traits": [
            "I say what I mean. Nothing more, nothing less.",
            "Every movement serves a purpose. Every word too.",
        ],
        "ideal":  "Discipline. The body and mind are one. Master both and you master anything.",
        "bond":   "My monastery was betrayed from within. I left to understand the outside world so it can never happen again.",
        "flaw":   "I struggle to understand why people fail to simply do what they know is right.",
        "combat_role": "striker",
    },
]


# ── Build helpers ──────────────────────────────────────────────────────────────

def build_companion_at_level(template, level):
    """Return a full companion state dict built at the given level."""
    ab      = template["abilities"]
    prof    = _prof(level)
    con_mod = _mod(ab["constitution"])
    hd      = _HIT_DICE[template["class"]]
    avg_hd  = hd // 2 + 1
    hp_max  = max(1, (hd + con_mod) + (avg_hd + con_mod) * max(0, level - 1))

    atk_ab   = template["equipment"]["weapon_ability"]
    atk_mod  = _mod(ab[atk_ab])
    # Druid Shillelagh upgrades to WIS
    if template["class"] == "Druid" and "Shillelagh" in template.get("spells", []):
        atk_mod = max(atk_mod, _mod(ab["wisdom"]))

    return {
        "id":          template["id"],
        "first_name":  template["first_name"],
        "last_name":   template["last_name"],
        "name":        f"{template['first_name']} {template['last_name']}",
        "race":        template["race"],
        "class":       template["class"],
        "subclass":    template["subclass"],
        "alignment":   template["alignment"],
        "background":  template["background"],
        "abilities":   dict(ab),
        "level":       level,
        "hp":          {"current": hp_max, "max": hp_max},
        "ac":          _calc_ac(template, ab),
        "attack": {
            "name":        template["equipment"]["weapon"],
            "bonus":       atk_mod + prof,
            "damage":      _weapon_damage(template, level, ab),
            "damage_type": template["equipment"]["weapon_type"],
        },
        "spells":       list(template.get("spells", [])),
        "spell_slots":  _calc_spell_slots(template["class"], level),
        "feature_uses": _calc_features(template, level, ab),
        "personality_traits": list(template["personality_traits"]),
        "ideal":        template["ideal"],
        "bond":         template["bond"],
        "flaw":         template["flaw"],
        "combat_role":  template["combat_role"],
        "status":       "active",
        "death_saves":  {"successes": 0, "failures": 0},
        "dead_at_scene": None,
    }


def level_up_companion(companion, new_level):
    """Rebuild companion features/HP for a new level. Preserves current HP ratio."""
    template = next((t for t in _TEMPLATES if t["id"] == companion["id"]), None)
    if not template:
        return
    old_max = companion["hp"]["max"]
    old_cur = companion["hp"]["current"]
    new     = build_companion_at_level(template, new_level)
    ratio   = old_cur / max(1, old_max)
    new["hp"]["current"] = max(1, round(new["hp"]["max"] * ratio))
    new["status"]        = companion["status"]
    new["death_saves"]   = dict(companion["death_saves"])
    new["dead_at_scene"] = companion["dead_at_scene"]
    companion.clear()
    companion.update(new)


# ── Roster queries ─────────────────────────────────────────────────────────────

def get_roster():
    return _TEMPLATES


def find_companion_template(name):
    """Look up by full name (case-insensitive)."""
    name_lower = name.strip().lower()
    for t in _TEMPLATES:
        if f"{t['first_name']} {t['last_name']}".lower() == name_lower:
            return t
    return None


def get_available_companions(player_class, active_classes):
    """Return templates whose class doesn't conflict with the current party."""
    taken = {c.lower() for c in ([player_class] + list(active_classes))}
    return [t for t in _TEMPLATES if t["class"].lower() not in taken]


# ── Slot helpers (used by app.py turn resolver) ────────────────────────────────

def has_slot(companion, min_level=1):
    for lvl_str, data in companion.get("spell_slots", {}).items():
        if int(lvl_str) >= min_level:
            if data.get("total", 0) - data.get("used", 0) > 0:
                return True
    return False


def use_slot(companion, min_level=1):
    """Use the lowest available slot at or above min_level. Returns slot level or None."""
    for lvl in sorted(companion.get("spell_slots", {}).keys(), key=int):
        if int(lvl) >= min_level:
            data = companion["spell_slots"][lvl]
            if data.get("total", 0) - data.get("used", 0) > 0:
                data["used"] += 1
                return int(lvl)
    return None


def spell_damage(spell, slot_level, char_level):
    return _spell_dmg(spell, slot_level, char_level)


def spell_level(spell_name):
    return _SPELL_LEVELS.get(spell_name, 1)


# ── Combat AI ─────────────────────────────────────────────────────────────────

def companion_ai(companion, session):
    """
    Return an action dict for the companion's turn.

    Possible return shapes:
      {"action": "attack",   "target": name}
      {"action": "spell",    "spell": name, "target": name,
       "slot_level": N,      "is_heal": bool, "damage": notation}
      {"action": "feature",  "feature": name, "target": name,
       "heal_amount": N}
      {"action": "none"}
    """
    if companion["status"] != "active" or companion["hp"]["current"] <= 0:
        return {"action": "none"}

    cls      = companion["class"]
    role     = companion["combat_role"]
    hp_pct   = companion["hp"]["current"] / max(1, companion["hp"]["max"])
    level    = companion["level"]

    order  = session.get("initiative_order", [])
    enemies = [c for c in order
               if not c["is_player"] and not c.get("is_companion") and c["hp"] > 0]
    allies  = [c for c in order
               if (c["is_player"] or c.get("is_companion")) and c["hp"] > 0]
    dying   = [c for c in order
               if (c["is_player"] or c.get("is_companion")) and c["hp"] <= 0]
    wounded = [c for c in allies
               if c["hp"] / max(1, c.get("max_hp", c["hp"])) < 0.35]

    if not enemies:
        return {"action": "none"}

    target = min(enemies, key=lambda e: e["hp"])["name"]

    # ── Healer role: Cleric, Druid ─────────────────────────────────────────────
    if role == "healer":
        if dying:
            heal_target = dying[0]["name"]
            if cls == "Cleric" and "Healing Word" in companion["spells"]:
                slot = use_slot(companion, 1)
                if slot:
                    return {"action": "spell", "spell": "Healing Word",
                            "target": heal_target, "slot_level": slot, "is_heal": True,
                            "damage": f"1d4+{_mod(companion['abilities']['wisdom'])}"}
            if cls == "Druid" and "Cure Wounds" in companion["spells"]:
                slot = use_slot(companion, 1)
                if slot:
                    return {"action": "spell", "spell": "Cure Wounds",
                            "target": heal_target, "slot_level": slot, "is_heal": True,
                            "damage": f"1d8+{_mod(companion['abilities']['wisdom'])}"}

        if wounded and hp_pct > 0.4:
            heal_target = min(wounded, key=lambda c: c["hp"])["name"]
            if cls == "Cleric":
                spell = "Healing Word" if "Healing Word" in companion["spells"] else "Cure Wounds"
                if spell in companion["spells"]:
                    slot = use_slot(companion, 1)
                    if slot:
                        wis = _mod(companion["abilities"]["wisdom"])
                        dmg = f"1d4+{wis}" if spell == "Healing Word" else f"1d8+{wis}"
                        return {"action": "spell", "spell": spell, "target": heal_target,
                                "slot_level": slot, "is_heal": True, "damage": dmg}
            if cls == "Druid" and "Cure Wounds" in companion["spells"]:
                slot = use_slot(companion, 1)
                if slot:
                    return {"action": "spell", "spell": "Cure Wounds",
                            "target": heal_target, "slot_level": slot, "is_heal": True,
                            "damage": f"1d8+{_mod(companion['abilities']['wisdom'])}"}

        # Attack with best offensive spell or weapon
        # Druid spells first, then Cleric — avoids iterating Cleric-only spells for Druid
        for sp in ["Moonbeam", "Call Lightning", "Flaming Sphere",
                   "Spirit Guardians", "Spiritual Weapon", "Guiding Bolt",
                   "Shatter", "Thunderwave", "Sacred Flame", "Shillelagh"]:
            if sp in companion["spells"]:
                slvl = _SPELL_LEVELS.get(sp, 0)
                if slvl == 0:  # cantrip
                    return {"action": "spell", "spell": sp, "target": target,
                            "slot_level": 0, "is_heal": False,
                            "damage": spell_damage(sp, 0, level)}
                slot = use_slot(companion, slvl)
                if slot:
                    return {"action": "spell", "spell": sp, "target": target,
                            "slot_level": slot, "is_heal": False,
                            "damage": spell_damage(sp, slot, level)}
        return {"action": "attack", "target": target}

    # ── Support role: Paladin, Bard ────────────────────────────────────────────
    if role == "support":
        if cls == "Paladin":
            # Use Lay on Hands for critically wounded or dying
            loh = companion["feature_uses"].get("Lay on Hands", {})
            if (dying or wounded) and loh.get("current", 0) >= 5:
                heal_t = dying[0]["name"] if dying else wounded[0]["name"]
                heal   = min(10, loh["current"])
                loh["current"] -= heal
                return {"action": "feature", "feature": "Lay on Hands",
                        "target": heal_t, "heal_amount": heal}
            # Offensive spell or attack
            for sp in ["Bless", "Divine Favor", "Cure Wounds"]:
                if sp in companion["spells"] and not dying and not wounded:
                    break
            return {"action": "attack", "target": target}

        if cls == "Bard":
            # Bardic Inspiration on player first round if available
            bi = companion["feature_uses"].get("Bardic Inspiration", {})
            player_c = next((c for c in order if c["is_player"] and c["hp"] > 0), None)
            if bi.get("current", 0) > 0 and player_c and session.get("round", 1) == 1:
                bi["current"] -= 1
                return {"action": "feature", "feature": "Bardic Inspiration",
                        "target": player_c["name"], "heal_amount": 0}
            # Heal if needed
            if (dying or wounded) and "Healing Word" in companion["spells"]:
                heal_t = (dying[0] if dying else wounded[0])["name"]
                slot = use_slot(companion, 1)
                if slot:
                    wis = _mod(companion["abilities"]["charisma"])
                    return {"action": "spell", "spell": "Healing Word",
                            "target": heal_t, "slot_level": slot, "is_heal": True,
                            "damage": f"1d4+{wis}"}
            # Offensive spell
            for sp in ["Hypnotic Pattern", "Shatter", "Thunderwave", "Vicious Mockery"]:
                if sp in companion["spells"]:
                    slvl = _SPELL_LEVELS.get(sp, 0)
                    if slvl == 0:
                        return {"action": "spell", "spell": sp, "target": target,
                                "slot_level": 0, "is_heal": False,
                                "damage": spell_damage(sp, 0, level)}
                    slot = use_slot(companion, slvl)
                    if slot:
                        return {"action": "spell", "spell": sp, "target": target,
                                "slot_level": slot, "is_heal": False,
                                "damage": spell_damage(sp, slot, level)}
            return {"action": "attack", "target": target}

    # ── Controller: Wizard ─────────────────────────────────────────────────────
    if role == "controller":
        # Fireball at 3+ enemies
        if len(enemies) >= 3 and "Fireball" in companion["spells"]:
            slot = use_slot(companion, 3)
            if slot:
                return {"action": "spell", "spell": "Fireball", "target": target,
                        "slot_level": slot, "is_heal": False,
                        "damage": spell_damage("Fireball", slot, level)}
        # Best single-target spell
        for sp in ["Scorching Ray", "Magic Missile", "Burning Hands",
                   "Chromatic Orb", "Fire Bolt"]:
            if sp in companion["spells"]:
                slvl = _SPELL_LEVELS.get(sp, 0)
                if slvl == 0:
                    return {"action": "spell", "spell": sp, "target": target,
                            "slot_level": 0, "is_heal": False,
                            "damage": spell_damage(sp, 0, level)}
                slot = use_slot(companion, slvl)
                if slot:
                    return {"action": "spell", "spell": sp, "target": target,
                            "slot_level": slot, "is_heal": False,
                            "damage": spell_damage(sp, slot, level)}
        return {"action": "attack", "target": target}

    # ── Striker: Fighter, Rogue, Ranger, Monk, Sorcerer ────────────────────────
    # Self-heal if Fighter and low HP
    if cls == "Fighter" and hp_pct < 0.4:
        sw = companion["feature_uses"].get("Second Wind", {})
        if sw.get("current", 0) > 0:
            sw["current"] -= 1
            return {"action": "feature", "feature": "Second Wind",
                    "target": companion["name"], "heal_amount": 0,
                    "damage": f"1d10+{companion['level']}"}

    # Sorcerer / Ranger may use spells
    if cls in ("Sorcerer", "Ranger"):
        for sp in ["Fireball", "Scorching Ray", "Thunderwave", "Chromatic Orb",
                   "Chaos Bolt", "Ensnaring Strike", "Fire Bolt"]:
            if sp in companion["spells"]:
                slvl = _SPELL_LEVELS.get(sp, 0)
                if slvl == 0:
                    return {"action": "spell", "spell": sp, "target": target,
                            "slot_level": 0, "is_heal": False,
                            "damage": spell_damage(sp, 0, level)}
                slot = use_slot(companion, slvl)
                if slot:
                    return {"action": "spell", "spell": sp, "target": target,
                            "slot_level": slot, "is_heal": False,
                            "damage": spell_damage(sp, slot, level)}

    return {"action": "attack", "target": target,
            "sneak_attack": cls == "Rogue"}


def companion_sneak_attack_damage(level):
    dice = math.ceil(level / 2)
    return f"{dice}d6"
