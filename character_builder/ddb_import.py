"""
D&D Beyond Character Importer
Fetches a character from D&D Beyond's internal API and maps it to our format.

Public characters work with no auth.
Private characters require a CobaltSession token from your browser.
"""

import json
import re
import sys
import urllib.request
import urllib.error
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))
from models.character import empty_character, save_character

DDB_API = "https://character-service.dndbeyond.com/character/v5/character/{id}"

# ── Alignment map ─────────────────────────────────────────────────────────────

ALIGNMENTS = {
    1: "Lawful Good",
    2: "Neutral Good",
    3: "Chaotic Good",
    4: "Lawful Neutral",
    5: "True Neutral",
    6: "Chaotic Neutral",
    7: "Lawful Evil",
    8: "Neutral Evil",
    9: "Chaotic Evil",
}

# ── Ability score ID map (DDB uses 1–6) ───────────────────────────────────────

ABILITY_IDS = {
    1: "strength",
    2: "dexterity",
    3: "constitution",
    4: "intelligence",
    5: "wisdom",
    6: "charisma",
}

# ── Skill subtype → our key map ───────────────────────────────────────────────

SKILL_MAP = {
    "acrobatics":        "Acrobatics",
    "animal-handling":   "Animal Handling",
    "arcana":            "Arcana",
    "athletics":         "Athletics",
    "deception":         "Deception",
    "history":           "History",
    "insight":           "Insight",
    "intimidation":      "Intimidation",
    "investigation":     "Investigation",
    "medicine":          "Medicine",
    "nature":            "Nature",
    "perception":        "Perception",
    "performance":       "Performance",
    "persuasion":        "Persuasion",
    "religion":          "Religion",
    "sleight-of-hand":   "Sleight of Hand",
    "stealth":           "Stealth",
    "survival":          "Survival",
}

SAVE_MAP = {
    "strength-saving-throws":     "strength",
    "dexterity-saving-throws":    "dexterity",
    "constitution-saving-throws": "constitution",
    "intelligence-saving-throws": "intelligence",
    "wisdom-saving-throws":       "wisdom",
    "charisma-saving-throws":     "charisma",
}

SPELLCASTING_ABILITY = {
    "artificer":  "intelligence",
    "bard":       "charisma",
    "cleric":     "wisdom",
    "druid":      "wisdom",
    "paladin":    "charisma",
    "ranger":     "wisdom",
    "sorcerer":   "charisma",
    "warlock":    "charisma",
    "wizard":     "intelligence",
}

# Standard spell slots by total spellcaster level (full casters)
FULL_CASTER_SLOTS = {
    1:  [2,0,0,0,0,0,0,0,0],
    2:  [3,0,0,0,0,0,0,0,0],
    3:  [4,2,0,0,0,0,0,0,0],
    4:  [4,3,0,0,0,0,0,0,0],
    5:  [4,3,2,0,0,0,0,0,0],
    6:  [4,3,3,0,0,0,0,0,0],
    7:  [4,3,3,1,0,0,0,0,0],
    8:  [4,3,3,2,0,0,0,0,0],
    9:  [4,3,3,3,1,0,0,0,0],
    10: [4,3,3,3,2,0,0,0,0],
    11: [4,3,3,3,2,1,0,0,0],
    12: [4,3,3,3,2,1,0,0,0],
    13: [4,3,3,3,2,1,1,0,0],
    14: [4,3,3,3,2,1,1,0,0],
    15: [4,3,3,3,2,1,1,1,0],
    16: [4,3,3,3,2,1,1,1,0],
    17: [4,3,3,3,2,1,1,1,1],
    18: [4,3,3,3,3,1,1,1,1],
    19: [4,3,3,3,3,2,1,1,1],
    20: [4,3,3,3,3,2,2,1,1],
}

WARLOCK_SLOTS = {
    1:  [1,0,0,0,0], 2: [2,0,0,0,0], 3: [0,2,0,0,0], 4: [0,2,0,0,0],
    5:  [0,0,2,0,0], 6: [0,0,2,0,0], 7: [0,0,0,2,0], 8: [0,0,0,2,0],
    9:  [0,0,0,0,2], 10:[0,0,0,0,2], 11:[0,0,0,0,3], 12:[0,0,0,0,3],
    13: [0,0,0,0,3], 14:[0,0,0,0,3], 15:[0,0,0,0,3], 16:[0,0,0,0,3],
    17: [0,0,0,0,4], 18:[0,0,0,0,4], 19:[0,0,0,0,4], 20:[0,0,0,0,4],
}


# ── Fetch ─────────────────────────────────────────────────────────────────────

def extract_character_id(url_or_id: str) -> str:
    url_or_id = url_or_id.strip()
    match = re.search(r"/characters?/(\d+)", url_or_id)
    if match:
        return match.group(1)
    if url_or_id.isdigit():
        return url_or_id
    raise ValueError(f"Could not find a character ID in: {url_or_id!r}")


def fetch_ddb_json(character_id: str, cobalt_token: str = "") -> dict:
    url = DDB_API.format(id=character_id)
    headers = {
        "Accept":     "application/json",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
    }
    if cobalt_token:
        headers["Cookie"]        = f"CobaltSession={cobalt_token}"
        headers["Authorization"] = f"Bearer {cobalt_token}"

    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        if e.code == 401:
            raise PermissionError(
                "Character is private. Provide your CobaltSession token to import it."
            )
        if e.code == 404:
            raise ValueError("Character not found. Check the URL or ID.")
        raise ConnectionError(f"D&D Beyond returned HTTP {e.code}.")
    except urllib.error.URLError as e:
        raise ConnectionError(f"Could not reach D&D Beyond: {e.reason}")


# ── Modifier helpers ──────────────────────────────────────────────────────────

def collect_modifiers(data: dict) -> list[dict]:
    """Flatten all modifier arrays from every source into one list."""
    mods = []
    for source in data.get("modifiers", {}).values():
        if isinstance(source, list):
            mods.extend(source)
    return mods


def modifiers_of(mods: list[dict], mod_type: str, sub_type: str = None) -> list[dict]:
    return [
        m for m in mods
        if m.get("type") == mod_type
        and (sub_type is None or m.get("subType") == sub_type)
    ]


# ── Ability scores ────────────────────────────────────────────────────────────

def build_abilities(data: dict, mods: list[dict]) -> dict:
    base   = {m["id"]: m["value"] or 0 for m in data.get("stats", [])}
    bonus  = {m["id"]: m["value"] or 0 for m in data.get("bonusStats", [])}
    override = {m["id"]: m["value"] for m in data.get("overrideStats", []) if m.get("value")}

    abilities = {}
    for aid, name in ABILITY_IDS.items():
        if aid in override:
            abilities[name] = override[aid]
        else:
            abilities[name] = base.get(aid, 10) + bonus.get(aid, 0)

    for mod in mods:
        if mod.get("type") == "bonus" and mod.get("subType", "").endswith("-score"):
            sub = mod["subType"].replace("-score", "")
            ability_name = {
                "strength": "strength", "dexterity": "dexterity",
                "constitution": "constitution", "intelligence": "intelligence",
                "wisdom": "wisdom", "charisma": "charisma",
            }.get(sub)
            if ability_name and ability_name not in override.values():
                abilities[ability_name] = abilities.get(ability_name, 10) + (mod.get("value") or 0)

    return abilities


# ── HP ────────────────────────────────────────────────────────────────────────

def build_hp(data: dict, abilities: dict) -> dict:
    info = data.get("hitPointInfo", {})
    max_hp    = info.get("maximum") or info.get("constitutionHitPoints", 8)
    current   = info.get("remaining", max_hp)
    temp      = data.get("temporaryHitPoints") or 0
    return {"max": max_hp, "current": current, "temp": temp}


# ── Classes ───────────────────────────────────────────────────────────────────

def build_class_info(data: dict) -> tuple[str, str, str, int]:
    classes = data.get("classes", [])
    if not classes:
        return "", "", "", 1
    primary = classes[0]
    class_def    = primary.get("definition", {})
    subclass_def = primary.get("subclassDefinition") or {}
    class_name   = class_def.get("name", "")
    subclass     = subclass_def.get("name", "")
    level        = primary.get("level", 1)

    if len(classes) > 1:
        extras = " / ".join(
            f"{c.get('definition',{}).get('name','')} {c.get('level',1)}"
            for c in classes[1:]
        )
        class_name = f"{class_name} ({extras})"

    return class_name, subclass, class_def.get("hitDice", 8), level


# ── Proficiencies ─────────────────────────────────────────────────────────────

def build_proficiencies(mods: list[dict]) -> tuple[list, list, list, list, list, list, list]:
    skill_profs    = []
    skill_experts  = []
    save_profs     = []
    armor_profs    = []
    weapon_profs   = []
    tool_profs     = []
    languages      = []

    for mod in mods:
        mtype = mod.get("type", "")
        sub   = mod.get("subType", "")
        fname = mod.get("friendlySubtypeName", "")

        if mtype in ("proficiency", "expertise"):
            if sub in SKILL_MAP:
                key = SKILL_MAP[sub]
                if mtype == "expertise":
                    if key not in skill_experts:
                        skill_experts.append(key)
                else:
                    if key not in skill_profs:
                        skill_profs.append(key)

            elif sub in SAVE_MAP:
                ab = SAVE_MAP[sub]
                if ab not in save_profs:
                    save_profs.append(ab)

            elif "armor" in sub or sub in ("light-armor","medium-armor","heavy-armor","shield"):
                if fname and fname not in armor_profs:
                    armor_profs.append(fname)

            elif "weapon" in sub or sub in ("simple-weapons","martial-weapons"):
                if fname and fname not in weapon_profs:
                    weapon_profs.append(fname)

            elif "tool" in sub or "instrument" in sub or "kit" in sub or "supplies" in sub:
                if fname and fname not in tool_profs:
                    tool_profs.append(fname)

        elif mtype == "language":
            if fname and fname not in languages:
                languages.append(fname)

    return save_profs, skill_profs, skill_experts, armor_profs, weapon_profs, tool_profs, languages


# ── AC ────────────────────────────────────────────────────────────────────────

def build_ac(data: dict, abilities: dict, mods: list[dict]) -> int:
    override = data.get("overrideArmorClass")
    if override:
        return override

    dex_mod = (abilities.get("dexterity", 10) - 10) // 2
    base_ac = 10 + dex_mod

    for item in data.get("inventory", []):
        defn = item.get("definition", {})
        if not item.get("equipped"):
            continue
        armor_type = defn.get("armorTypeId")
        if armor_type in (1, 2, 3):
            base = defn.get("armorClass", 10)
            if armor_type == 1:
                base_ac = base + dex_mod
            elif armor_type == 2:
                base_ac = base + min(dex_mod, 2)
            elif armor_type == 3:
                base_ac = base
        elif armor_type == 4:
            base_ac += 2

    for mod in mods:
        if mod.get("type") == "bonus" and mod.get("subType") == "armor-class":
            base_ac += mod.get("value") or 0

    bonus_ac = data.get("bonusArmorClass") or 0
    return base_ac + bonus_ac


# ── Speed ─────────────────────────────────────────────────────────────────────

def build_speed(data: dict, mods: list[dict]) -> int:
    race = data.get("race", {})
    speeds = race.get("weightSpeeds", {}).get("normal", {})
    base = speeds.get("walk", 30)
    for mod in mods:
        if mod.get("type") == "bonus" and mod.get("subType") == "speed":
            base += mod.get("value") or 0
    return base


# ── Attacks ───────────────────────────────────────────────────────────────────

def build_attacks(data: dict, abilities: dict) -> list[dict]:
    from models.character import proficiency_bonus, modifier
    level = sum(c.get("level", 0) for c in data.get("classes", []))
    pb = proficiency_bonus(level)
    attacks = []

    str_mod = modifier(abilities.get("strength", 10))
    dex_mod = modifier(abilities.get("dexterity", 10))

    for item in data.get("inventory", []):
        defn = item.get("definition", {})
        if not item.get("equipped"):
            continue
        if defn.get("filterType") != "Weapon":
            continue

        name     = defn.get("name", "Unknown")
        is_finesse = any(
            p.get("name") == "Finesse"
            for p in defn.get("properties", [])
        )
        is_ranged = defn.get("attackType") == 2

        if is_finesse:
            atk_mod = max(str_mod, dex_mod)
        elif is_ranged:
            atk_mod = dex_mod
        else:
            atk_mod = str_mod

        damage_dice = defn.get("damage", {}).get("diceString", "1d4")
        damage_type = (defn.get("damageType") or "").lower()

        attacks.append({
            "name":         name,
            "attack_bonus": pb + atk_mod,
            "damage":       f"{damage_dice}+{atk_mod}" if atk_mod >= 0 else f"{damage_dice}{atk_mod}",
            "damage_type":  damage_type,
            "notes":        "",
        })

    for action in data.get("actions", {}).get("race", []) + data.get("actions", {}).get("class", []):
        if not action.get("attackTypeRange"):
            continue
        damage = action.get("dice", {})
        dice_str = damage.get("diceString", "") if damage else ""
        if not dice_str:
            continue
        attacks.append({
            "name":         action.get("name", "Attack"),
            "attack_bonus": pb + str_mod,
            "damage":       dice_str,
            "damage_type":  "",
            "notes":        "from character actions",
        })

    return attacks


# ── Spellcasting ──────────────────────────────────────────────────────────────

def build_spellcasting(data: dict, abilities: dict) -> dict:
    from models.character import proficiency_bonus, modifier

    classes = data.get("classes", [])
    if not classes:
        return empty_character()["spellcasting"]

    level = sum(c.get("level", 0) for c in classes)
    pb    = proficiency_bonus(level)

    spell_class = None
    for c in classes:
        cname = c.get("definition", {}).get("name", "").lower()
        if cname in SPELLCASTING_ABILITY:
            spell_class = cname
            break

    if not spell_class:
        return {**empty_character()["spellcasting"], "enabled": False}

    sp_ability = SPELLCASTING_ABILITY[spell_class]
    sp_mod     = modifier(abilities.get(sp_ability, 10))
    dc         = 8 + pb + sp_mod
    atk        = pb + sp_mod

    if spell_class == "warlock":
        raw_slots = WARLOCK_SLOTS.get(level, [0]*9)
    else:
        raw_slots = FULL_CASTER_SLOTS.get(level, [0]*9)

    slots = {}
    for i, total in enumerate(raw_slots, start=1):
        slots[str(i)] = {"total": total, "used": 0}
    for i in range(len(raw_slots)+1, 10):
        slots[str(i)] = {"total": 0, "used": 0}

    spells_known = []
    seen = set()

    def add_spell(s: dict):
        defn  = s.get("definition", {})
        name  = defn.get("name", "")
        if not name or name in seen:
            return
        seen.add(name)
        spells_known.append({
            "name":        name,
            "level":       defn.get("level", 0),
            "school":      defn.get("school", ""),
            "description": defn.get("description", "")[:200] if defn.get("description") else "",
        })

    for spell in data.get("spells", {}).get("race", []):
        add_spell(spell)
    for spell in data.get("spells", {}).get("background", []):
        add_spell(spell)
    for class_spells in data.get("classSpells", []):
        for spell in class_spells.get("spells", []):
            add_spell(spell)

    return {
        "enabled":       True,
        "ability":       sp_ability,
        "spell_save_dc": dc,
        "attack_bonus":  atk,
        "slots":         slots,
        "spells_known":  sorted(spells_known, key=lambda s: (s["level"], s["name"])),
        "spells_prepared": [],
    }


# ── Equipment ─────────────────────────────────────────────────────────────────

def build_equipment(data: dict) -> tuple[list, dict]:
    equipment = []
    currency  = {"cp": 0, "sp": 0, "ep": 0, "gp": 0, "pp": 0}

    for item in data.get("inventory", []):
        defn = item.get("definition", {})
        equipment.append({
            "name":     defn.get("name", "Unknown"),
            "quantity": item.get("quantity", 1),
            "weight":   defn.get("weight") or 0.0,
            "notes":    "equipped" if item.get("equipped") else "",
        })

    currencies = data.get("currencies", {})
    currency["cp"] = currencies.get("cp", 0)
    currency["sp"] = currencies.get("sp", 0)
    currency["ep"] = currencies.get("ep", 0)
    currency["gp"] = currencies.get("gp", 0)
    currency["pp"] = currencies.get("pp", 0)

    return equipment, currency


# ── Features ──────────────────────────────────────────────────────────────────

def build_features(data: dict) -> list[dict]:
    features = []
    seen = set()

    def add(name, source, desc):
        if name in seen:
            return
        seen.add(name)
        features.append({
            "name":        name,
            "source":      source,
            "description": (desc or "")[:300],
            "uses":        None,
        })

    race = data.get("race", {})
    for trait in race.get("racialTraits", []):
        defn = trait.get("definition", {})
        add(defn.get("name",""), race.get("fullName","Race"), defn.get("description",""))

    for cls in data.get("classes", []):
        cname = cls.get("definition", {}).get("name", "Class")
        level = cls.get("level", 1)
        for feat in cls.get("classFeatures", []):
            defn = feat.get("definition", {})
            if defn.get("requiredLevel", 1) <= level:
                add(defn.get("name",""), f"{cname} {defn.get('requiredLevel',1)}", defn.get("description",""))

    for feat in data.get("feats", []):
        defn = feat.get("definition", {})
        add(defn.get("name",""), "Feat", defn.get("description",""))

    return features


# ── Hit dice ──────────────────────────────────────────────────────────────────

def build_hit_dice(data: dict, hit_die: int, level: int) -> dict:
    used = data.get("removedHitPoints", {})
    used_count = sum(used.values()) if isinstance(used, dict) else 0
    return {
        "type":  f"d{hit_die}",
        "total": level,
        "used":  used_count,
    }


# ── Main import function ──────────────────────────────────────────────────────

def import_from_ddb(url_or_id: str, cobalt_token: str = "") -> dict:
    """
    Fetch a D&D Beyond character and return it as our character dict.
    Raises ValueError / PermissionError / ConnectionError on failure.
    """
    character_id = extract_character_id(url_or_id)
    raw          = fetch_ddb_json(character_id, cobalt_token)
    data         = raw.get("data", raw)

    mods = collect_modifiers(data)

    class_name, subclass, hit_die, level = build_class_info(data)
    abilities = build_abilities(data, mods)
    hp        = build_hp(data, abilities)
    ac        = build_ac(data, abilities, mods)
    speed     = build_speed(data, mods)
    hit_dice  = build_hit_dice(data, hit_die, level)

    (save_profs, skill_profs, skill_experts,
     armor_profs, weapon_profs, tool_profs, languages) = build_proficiencies(mods)

    attacks      = build_attacks(data, abilities)
    spellcasting = build_spellcasting(data, abilities)
    equipment, currency = build_equipment(data)
    features     = build_features(data)

    race_name = data.get("race", {}).get("fullName", "")
    bg_def    = data.get("background", {})
    if isinstance(bg_def, dict):
        bg_name = bg_def.get("definition", {}).get("name", "") if bg_def.get("definition") else bg_def.get("name", "")
    else:
        bg_name = ""

    char = empty_character()
    char.update({
        "name":        data.get("name", ""),
        "race":        race_name,
        "class":       class_name,
        "subclass":    subclass,
        "background":  bg_name,
        "level":       level,
        "experience":  data.get("currentXp", 0),
        "alignment":   ALIGNMENTS.get(data.get("alignmentId"), ""),
        "abilities":   abilities,
        "hp":          hp,
        "armor_class": ac,
        "speed":       speed,
        "hit_dice":    hit_dice,
        "saving_throw_proficiencies": save_profs,
        "skill_proficiencies":        skill_profs,
        "skill_expertises":           skill_experts,
        "armor_proficiencies":        armor_profs,
        "weapon_proficiencies":       weapon_profs,
        "tool_proficiencies":         tool_profs,
        "languages":                  languages,
        "attacks":                    attacks,
        "spellcasting":               spellcasting,
        "equipment":                  equipment,
        "currency":                   currency,
        "features":                   features,
        "personality_traits": data.get("traits", {}).get("personalityTraits", "") or "",
        "ideals":             data.get("traits", {}).get("ideals", "") or "",
        "bonds":              data.get("traits", {}).get("bonds", "") or "",
        "flaws":              data.get("traits", {}).get("flaws", "") or "",
        "backstory":          data.get("backstory", {}).get("value", "") or "" if isinstance(data.get("backstory"), dict) else "",
        "inspiration":        bool(data.get("inspiration", False)),
    })

    return char
