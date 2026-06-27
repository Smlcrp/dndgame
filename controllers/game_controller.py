import sys
from pathlib import Path
_root = Path(__file__).parent.parent
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))

from models import dice
from models import game_state as gs
from models import combat as cb
from models.character import modifier, proficiency_bonus
from models.progression import (
    level_from_xp, xp_for_level, xp_to_next_level,
    features_gained_at, feature_charges_gained_at,
    current_max_uses, recharges_on_short_rest,
)
from models.enemies import ENEMIES, enemy_list_for_dm
from models.adventure import generate_adventure, advance_beat as _adv_advance_beat

SKILL_ABILITIES = {
    "Acrobatics": "dexterity",    "Animal Handling": "wisdom",
    "Arcana": "intelligence",     "Athletics": "strength",
    "Deception": "charisma",      "History": "intelligence",
    "Insight": "wisdom",          "Intimidation": "charisma",
    "Investigation": "intelligence","Medicine": "wisdom",
    "Nature": "intelligence",     "Perception": "wisdom",
    "Performance": "charisma",    "Persuasion": "charisma",
    "Religion": "intelligence",   "Sleight of Hand": "dexterity",
    "Stealth": "dexterity",       "Survival": "wisdom",
    "Strength": "strength",       "Dexterity": "dexterity",
    "Constitution": "constitution","Intelligence": "intelligence",
    "Wisdom": "wisdom",           "Charisma": "charisma",
    "Thieves Tools": "dexterity", "Thieves' Tools": "dexterity",
}


def _enemy_defaults(name, level):
    hp  = max(5, level * 7)
    ac  = 10 + max(0, level // 3)
    atk = max(2, level // 2 + 1)
    dmg = f"1d{'6' if level < 5 else '8'}+{max(1, level//3)}"
    return {"hp": hp, "ac": ac, "xp": level * 50, "initiative_mod": 1,
            "attacks": [{"name": "Attack", "bonus": atk, "damage": dmg,
                         "damage_type": "slashing"}]}


# ── Public controller API ──────────────────────────────────────────────────────

def build_enemy_list(enemy_specs, player_level):
    """Build a list of enemy dicts from DM event specs."""
    enemies = []
    for spec in enemy_specs:
        data  = ENEMIES.get(spec["name"])
        base  = data if data is not None else _enemy_defaults(spec["name"], player_level)
        count = spec.get("count", 1)
        for i in range(count):
            label = spec["name"] if count == 1 else f"{spec['name']} {i+1}"
            enemies.append(cb.build_enemy(
                label, base["hp"], base["ac"], base["attacks"],
                base["initiative_mod"], base["xp"]))
    return enemies


def setup_combat(session, char, enemy_specs, d20_initiative):
    """Set up combat with a pre-rolled initiative value.
    Returns {"order": list, "display": str}.
    """
    enemies = build_enemy_list(enemy_specs, char.get("level", 1))
    order   = cb.setup_combat(session, char, enemies, player_initiative=d20_initiative)
    lines   = []
    for c in order:
        marker = "▶" if c["is_player"] else "·"
        lines.append(f"  {marker} {c['name']} (HP {c['hp']}/{c['max_hp']}) — init {c['initiative']}")
    return {"order": order, "display": "\n".join(lines)}


def get_skill_modifier(char, skill):
    """Return the total modifier for a skill check (ability mod + proficiency if applicable)."""
    ability    = SKILL_ABILITIES.get(skill, "")
    ab_mod     = modifier(char.get("abilities", {}).get(ability, 10)) if ability else 0
    prof_b     = proficiency_bonus(char.get("level", 1))
    proficient = skill in char.get("skill_proficiencies", [])
    total_mod  = ab_mod + (prof_b if proficient else 0)
    return {
        "modifier":  total_mod,
        "ab_mod":    ab_mod,
        "prof_b":    prof_b,
        "proficient": proficient,
    }


def process_skill_check(char, skill, dc, d20_value):
    """Resolve a skill check against DC with a pre-rolled d20.
    Returns result dict including success flag and narrative outcome string.
    """
    info    = get_skill_modifier(char, skill)
    total   = d20_value + info["modifier"]
    success = d20_value == 20 or (d20_value != 1 and total >= dc)
    return {
        "d20":        d20_value,
        "modifier":   info["modifier"],
        "total":      total,
        "dc":         dc,
        "success":    success,
        "proficient": info["proficient"],
        "prof_bonus": info["prof_b"],
        "outcome_text": (
            f"I attempted a {skill} check (DC {dc}) and "
            f"{'succeeded' if success else 'failed'} with a roll of {total}."
        ),
    }


def process_attack(session, char, weapon_name, target_name, d20_value,
                   damage_override=None):
    """Resolve a player attack with a pre-rolled d20.
    damage_override replaces the weapon's base damage (used for versatile
    two-handed, thrown, and off-hand variants where damage dice differ).
    Returns the combat.player_attack result dict.
    """
    return cb.player_attack(session, char, weapon_name, target_name,
                            d20_override=d20_value,
                            damage_override=damage_override)


def process_enemy_turn(session):
    """Resolve the current enemy's attack against the player.
    Returns the combat result dict, or None if the current combatant is the player.
    """
    current = gs.current_combatant(session)
    if not current or current["is_player"]:
        return None
    if current["hp"] <= 0:
        return {"skip": True, "name": current["name"]}
    return cb.enemy_attack(session, current["name"])


def process_death_save(session):
    """Roll a death save and update session.
    Returns the combat.handle_death_save result dict.
    """
    return cb.handle_death_save(session)


def process_xp_award(session, char, amount):
    """Add XP to character, detect level-up, return result dict."""
    old_xp    = char.get("experience", 0)
    old_level = char.get("level", 1)
    new_xp    = old_xp + amount
    new_level = min(20, level_from_xp(new_xp))

    char["experience"] = new_xp
    leveled_up = new_level > old_level

    if leveled_up:
        char["level"] = new_level
        new_features  = features_gained_at(char["class"], new_level)
        new_charges   = feature_charges_gained_at(char["class"], new_level)
        # Backfill any feature charges from prior levels not yet in feature_uses
        for lvl in range(1, new_level + 1):
            for charge in feature_charges_gained_at(char["class"], lvl):
                name = charge["name"]
                if name not in char["feature_uses"]:
                    max_uses = current_max_uses(name, char["class"], new_level, char)
                    char["feature_uses"][name] = {"current": max_uses, "max": max_uses}
        # Update scaling on existing features (e.g. Rage going from 2→3 uses at level 9)
        for name in list(char["feature_uses"].keys()):
            max_uses = current_max_uses(name, char["class"], new_level, char)
            existing = char["feature_uses"][name]
            existing["max"] = max_uses
            existing["current"] = min(existing["current"], max_uses)
    else:
        new_features = []
        new_charges  = []

    return {
        "xp_gained":    amount,
        "total_xp":     new_xp,
        "leveled_up":   leveled_up,
        "old_level":    old_level,
        "new_level":    new_level,
        "new_features": new_features,
        "new_charges":  new_charges,
        "xp_to_next":   xp_to_next_level(new_xp, new_level),
    }


def process_short_rest(session, char, dice_spent, rolls):
    """Resolve a short rest: spend hit dice, recharge short-rest features.
    rolls — list of raw die results (e.g. [5, 3] for two d8s rolled).
    Returns result dict with hp_recovered and features_recharged.
    """
    from models.character import short_rest as char_short_rest
    old_hp = char["hp"]["current"]
    char_short_rest(char, dice_spent, rolls)
    hp_recovered = char["hp"]["current"] - old_hp

    recharged = []
    cls   = char.get("class", "")
    level = char.get("level", 1)
    for name, uses in char.get("feature_uses", {}).items():
        if recharges_on_short_rest(name, cls, level):
            max_uses = current_max_uses(name, cls, level, char)
            char["feature_uses"][name] = {"current": max_uses, "max": max_uses}
            recharged.append(name)

    if session.get("current_hp") is not None:
        session["current_hp"] = char["hp"]["current"]
        session["hit_dice_spent"] = char["hit_dice"]["used"]

    return {
        "dice_spent":         dice_spent,
        "hp_recovered":       hp_recovered,
        "features_recharged": recharged,
    }


def process_long_rest(session, char):
    """Resolve a long rest: restore HP, spell slots, and all features.
    Returns result dict with hp_recovered, slots_recovered, features_recharged.
    """
    from models.character import long_rest as char_long_rest
    old_hp = char["hp"]["current"]
    char_long_rest(char)
    hp_recovered = char["hp"]["current"] - old_hp

    recharged = []
    cls   = char.get("class", "")
    level = char.get("level", 1)
    for name in list(char.get("feature_uses", {}).keys()):
        max_uses = current_max_uses(name, cls, level, char)
        char["feature_uses"][name] = {"current": max_uses, "max": max_uses}
        recharged.append(name)

    slots_recovered = {
        lvl: data["total"]
        for lvl, data in char.get("spellcasting", {}).get("slots", {}).items()
        if data["total"] > 0
    }

    gs.long_rest(session, char)

    return {
        "hp_recovered":       hp_recovered,
        "slots_recovered":    slots_recovered,
        "features_recharged": recharged,
    }


def process_spell_cast(session, char, spell_name, target_name, slot_level,
                       d20_override=None, pre_damage=None):
    """Resolve a spell. Does NOT consume slots — caller must do that first.
    Returns a result dict from the appropriate combat.player_cast_* function.
    """
    from models.spells import SPELLS
    spell_data = SPELLS.get(spell_name)
    if not spell_data:
        return {"error": f"No combat data for '{spell_name}'."}
    delivery = spell_data.get("delivery", "auto")
    if delivery == "attack":
        return cb.player_cast_attack_spell(session, char, spell_name, spell_data,
                                           target_name, slot_level,
                                           d20_override=d20_override, pre_damage=pre_damage)
    if delivery == "save":
        return cb.player_cast_save_spell(session, char, spell_name, spell_data,
                                          target_name, slot_level)
    return cb.player_cast_auto_spell(session, char, spell_name, spell_data,
                                      target_name, slot_level)


def process_gold_award(char, amount):
    """Add gold pieces to the character's currency. Returns new gp total."""
    char.setdefault("currency", {"cp": 0, "sp": 0, "ep": 0, "gp": 0, "pp": 0})
    char["currency"]["gp"] = char["currency"].get("gp", 0) + amount
    return char["currency"]["gp"]


def process_item_award(char, name, slot="misc", bonus=0):
    """Add a magic item to the character. Applies mechanical bonus where relevant.
    slot: 'weapon' | 'armor' | 'misc'
    bonus: integer bonus applied to attack+damage (weapon) or AC (armor).
    Returns the added item dict.
    """
    item = {"name": name, "slot": slot, "bonus": bonus}
    char.setdefault("magic_items", [])
    char["magic_items"].append(item)
    if slot == "weapon" and bonus > 0:
        char["magic_weapon_bonus"] = char.get("magic_weapon_bonus", 0) + bonus
    elif slot == "armor" and bonus > 0:
        char["magic_armor_bonus"] = char.get("magic_armor_bonus", 0) + bonus
    return item


def get_available_combat_spells(char):
    from models.spells import get_combat_spells
    return get_combat_spells(char)


def start_adventure(session, char, preset="Quest"):
    """Generate and store a fresh adventure in the session. Returns the adventure dict."""
    adv = generate_adventure(char, preset=preset)
    session["adventure"] = adv
    return adv


def advance_beat(session):
    """Advance the session's adventure to the next beat. Returns XP awarded (0 if none)."""
    adv = session.get("adventure")
    if not adv:
        return 0
    return _adv_advance_beat(adv)
