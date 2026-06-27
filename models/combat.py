"""
Combat model — resolves all attack, damage, and death save mechanics.

This module handles the mathematical rules of combat: rolling attacks,
checking hit/miss against AC, rolling damage, handling conditions, spell attacks,
and death saves. It works directly on session and character dicts.

The game controller (controllers/game_controller.py) calls these functions when
a player or enemy acts. The app (views/desktop/app.py) calls the controller,
never this module directly.
"""

import sys
from pathlib import Path
_root = Path(__file__).parent.parent
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))

from models import dice
from models import game_state as gs
from models.character import modifier, proficiency_bonus

# Conditions that grant advantage to attackers against the afflicted combatant
CONDITIONS_WITH_ADVANTAGE_VS = {"Prone", "Paralyzed", "Stunned", "Unconscious", "Blinded"}
# Conditions that impose disadvantage on the afflicted combatant's own attack rolls
CONDITIONS_WITH_DISADVANTAGE  = {"Prone", "Blinded", "Poisoned", "Frightened", "Restrained", "Exhaustion"}


# ── Setup ──────────────────────────────────────────────────────────────────────

def build_enemy(name, hp, ac, attacks, initiative_mod=0, xp=0):
    """Create an enemy combatant dict from basic stats.

    Returns a dict ready to be added to the initiative order. attacks is a list
    of dicts with 'name', 'bonus' (to-hit), and 'damage' (notation like '1d6+2').
    """
    return {
        "name":           name,
        "hp":             hp,
        "max_hp":         hp,
        "ac":             ac,
        "initiative_mod": initiative_mod,
        "attacks":        attacks,
        "is_player":      False,
        "conditions":     [],
        "xp":             xp,
    }


def setup_combat(session, character, enemies, player_initiative=None):
    """Build the initiative order and store it in the session, then return it.

    If player_initiative is provided (a pre-rolled d20+DEX result), it is used
    directly; otherwise a fresh initiative roll is made. Enemy initiatives are
    always rolled fresh. Returns the ordered list of combatant dicts.
    """
    dex_mod = modifier(character["abilities"].get("dexterity", 10))
    player_init = player_initiative if player_initiative is not None else dice.initiative(dex_mod)["total"]

    combatants = [{
        "name":       character["name"] or "Player",
        "initiative": player_init,
        "hp":         session["current_hp"],
        "max_hp":     character["hp"].get("max", 1),
        "ac":         character.get("armor_class", 10),
        "is_player":  True,
        "conditions": list(session.get("conditions", [])),
    }]

    for enemy in enemies:
        init_roll = dice.initiative(enemy.get("initiative_mod", 0))["total"]
        combatants.append({
            "name":       enemy["name"],
            "initiative": init_roll,
            "hp":         enemy["hp"],
            "max_hp":     enemy["max_hp"],
            "ac":         enemy["ac"],
            "attacks":    enemy.get("attacks", []),
            "is_player":  False,
            "conditions": list(enemy.get("conditions", [])),
            "xp":         enemy.get("xp", 0),
        })

    gs.start_combat(session, combatants)
    return session["initiative_order"]


# ── Core attack resolution ─────────────────────────────────────────────────────

def _has_condition(session, combatant_name, condition):
    """Check whether a combatant currently has a specific status condition."""
    for c in session["initiative_order"]:
        if c["name"] == combatant_name:
            return condition in c.get("conditions", [])
    return False


def _get_combatant(session, name):
    """Look up a combatant dict by name in the initiative order. Returns None if not found."""
    for c in session["initiative_order"]:
        if c["name"] == name:
            return c
    return None


def resolve_attack(session, attacker_name, target_name, attack_bonus,
                   damage_notation, advantage=False, disadvantage=False,
                   d20_override=None, pre_damage=None):
    """Resolve a single attack roll against a target and return the full result dict.

    Steps:
    1. Check target conditions (Prone, Paralyzed, etc.) to grant the attacker advantage.
    2. Check attacker conditions (Blinded, Poisoned, etc.) to impose disadvantage.
    3. Roll a d20 (or use d20_override if the player already rolled via the UI).
    4. A natural 20 is always a hit (critical); a natural 1 always misses.
    5. On a hit, roll damage (double dice on a crit) unless pre_damage is provided.
    6. Apply the damage to the target in the session and return whether they were killed.

    pre_damage allows the caller to supply a pre-computed damage result (used when
    the UI rolls damage separately before calling this function).
    """
    target = _get_combatant(session, target_name)
    if not target:
        return {"error": f"Target '{target_name}' not found in combat."}

    target_ac = target.get("ac", 10)

    for cond in CONDITIONS_WITH_ADVANTAGE_VS:
        if _has_condition(session, target_name, cond):
            advantage = True
            break

    for cond in CONDITIONS_WITH_DISADVANTAGE:
        if _has_condition(session, attacker_name, cond):
            disadvantage = True
            break

    if d20_override is not None:
        d20 = d20_override
        roll = {"rolls": [d20], "kept": d20, "modifier": attack_bonus,
                "total": d20 + attack_bonus, "nat20": d20 == 20, "nat1": d20 == 1}
    else:
        roll = dice.d20_check(modifier=attack_bonus, advantage=advantage,
                              disadvantage=disadvantage)
    hit = roll["nat20"] or (not roll["nat1"] and roll["total"] >= target_ac)

    result = {
        "attacker":   attacker_name,
        "target":     target_name,
        "target_ac":  target_ac,
        "roll":       roll,
        "hit":        hit,
        "damage":     None,
        "new_hp":     target["hp"],
        "killed":     False,
        "critical":   roll["nat20"],
    }

    if hit:
        if pre_damage is not None:
            dmg = pre_damage
        else:
            dmg = (dice.critical_damage(damage_notation) if roll["nat20"]
                   else dice.damage(damage_notation))
        result["damage"] = dmg
        new_hp = gs.apply_combat_damage(session, target_name, dmg["total"])
        result["new_hp"] = new_hp
        result["killed"] = new_hp <= 0

    return result


# ── Player attack ──────────────────────────────────────────────────────────────

def player_attack(session, character, weapon_name, target_name,
                  advantage=False, disadvantage=False, d20_override=None,
                  damage_override=None, pre_damage=None):
    """Resolve a player's weapon attack.

    Looks up the weapon by name on the character sheet, applies any magic weapon
    bonus to both to-hit and damage, then delegates to resolve_attack().
    Returns an error dict if the weapon isn't found.
    """
    attacks = character.get("attacks", [])
    weapon  = next((a for a in attacks if a["name"].lower() == weapon_name.lower()), None)
    if not weapon:
        return {"error": f"No attack named '{weapon_name}' on character sheet."}

    attacker_name  = character["name"] or "Player"
    magic_bonus    = character.get("magic_weapon_bonus", 0)
    attack_bonus   = weapon.get("attack_bonus", 0) + magic_bonus
    base_damage    = damage_override if damage_override is not None else weapon["damage"]
    damage_note    = (f"{base_damage}+{magic_bonus}" if magic_bonus > 0
                      else base_damage)

    result = resolve_attack(session, attacker_name, target_name,
                            attack_bonus, damage_note, advantage, disadvantage,
                            d20_override=d20_override, pre_damage=pre_damage)
    result["weapon"] = weapon_name
    return result


# ── Enemy attack ───────────────────────────────────────────────────────────────

def enemy_attack(session, enemy_name, attack_index=0):
    """Resolve an enemy's attack against the player.

    attack_index selects which of the enemy's attacks to use (wraps around if
    the index exceeds the number of attacks). Always targets the first player
    combatant found in the initiative order.
    """
    enemy = _get_combatant(session, enemy_name)
    if not enemy:
        return {"error": f"Enemy '{enemy_name}' not in combat."}

    attacks = enemy.get("attacks", [])
    if not attacks:
        return {"error": f"Enemy '{enemy_name}' has no attacks defined."}

    attack = attacks[attack_index % len(attacks)]
    player = next((c for c in session["initiative_order"] if c["is_player"]), None)
    if not player:
        return {"error": "No player combatant found."}

    result = resolve_attack(session, enemy_name, player["name"],
                            attack.get("bonus", 0), attack["damage"])
    result["weapon"] = attack["name"]

    if result["hit"]:
        session["current_hp"] = max(0, player["hp"])

    return result


# ── Death saves ────────────────────────────────────────────────────────────────

def handle_death_save(session, pre_roll=None):
    """Roll (or accept) a death saving throw and update the session's death save counters.

    D&D 5e death save rules:
    - Natural 20 → immediately revive at 1 HP
    - 10 or higher → success; 3 successes = stable
    - 1 → two failures counted (not just one)
    - 3 failures → dead

    pre_roll lets the caller supply an already-computed roll dict (from dice.death_save())
    if the UI handled the roll display separately.
    """
    roll = pre_roll if pre_roll is not None else dice.death_save()
    ds   = session["death_saves"]

    if roll["critical"]:
        session["current_hp"] = 1
        ds["successes"] = 0
        ds["failures"]  = 0
        outcome = "revived"
    elif roll["success"]:
        ds["successes"] += 1
        outcome = "stable" if ds["successes"] >= 3 else "ongoing"
        if outcome == "stable":
            session["stable"] = True
    else:
        failures = 2 if roll["double_fail"] else 1
        ds["failures"] += failures
        outcome = "dead" if ds["failures"] >= 3 else "ongoing"

    return {**roll, "outcome": outcome, "death_saves": dict(ds)}


# ── Turn management ────────────────────────────────────────────────────────────

def end_turn(session):
    """Advance to the next living combatant and return them.

    Skips dead combatants (HP ≤ 0) automatically. Iterates at most len(order)
    times to prevent an infinite loop if somehow every combatant is dead.
    Returns None if there are no combatants or all are dead.
    """
    order = session["initiative_order"]
    if not order:
        return None

    for _ in range(len(order)):
        gs.advance_turn(session)
        current = gs.current_combatant(session)
        if current and current["hp"] > 0:
            return current

    return None


# ── Spell casting ─────────────────────────────────────────────────────────────

def player_cast_attack_spell(session, character, spell_name, spell_data,
                              target_name, slot_level,
                              d20_override=None, pre_damage=None):
    """Resolve a spell that requires a spell attack roll (e.g. Fire Bolt, Guiding Bolt).

    Uses the character's spell attack bonus. Damage scales with slot_level if the
    spell has upcast_per_level defined. Returns the resolve_attack result dict
    plus 'spell' and 'slot_level' fields.
    """
    from models.spells import spell_damage_notation
    sc           = character.get("spellcasting", {})
    atk_bonus    = sc.get("attack_bonus", 0)
    player_level = character.get("level", 1)
    dmg_note     = spell_damage_notation(spell_name, spell_data, slot_level, player_level)
    attacker     = character.get("name") or "Player"
    result = resolve_attack(session, attacker, target_name,
                            atk_bonus, dmg_note,
                            d20_override=d20_override, pre_damage=pre_damage)
    result["spell"]      = spell_name
    result["slot_level"] = slot_level
    return result


def player_cast_save_spell(session, character, spell_name, spell_data,
                            target_name, slot_level):
    """Resolve a spell that forces the target to make a saving throw (e.g. Fireball).

    The target rolls against the character's spell save DC. On a successful save,
    the target takes half damage (rounded down). On a failure, full damage applies.
    Returns a result dict with save roll, whether they saved, damage dealt, and HP remaining.
    """
    from models.spells import spell_damage_notation
    sc           = character.get("spellcasting", {})
    save_dc      = sc.get("spell_save_dc", 8)
    player_level = character.get("level", 1)
    dmg_note     = spell_damage_notation(spell_name, spell_data, slot_level, player_level)
    has_damage   = dmg_note not in ("0", "", "—")

    save_roll = dice.roll(20)
    saved     = save_roll >= save_dc

    dmg_result = None
    new_hp     = None
    killed     = False
    if has_damage:
        raw = dice.damage(dmg_note)
        total = max(0, raw["total"] // 2) if saved else raw["total"]
        dmg_result = {**raw, "total": total, "saved": saved}
        if total > 0:
            new_hp = gs.apply_combat_damage(session, target_name, total)
            killed = new_hp is not None and new_hp <= 0

    target = _get_combatant(session, target_name)
    return {
        "spell":        spell_name,
        "slot_level":   slot_level,
        "save_ability": spell_data.get("save_ability", ""),
        "save_dc":      save_dc,
        "save_roll":    save_roll,
        "saved":        saved,
        "damage":       dmg_result,
        "new_hp":       new_hp if new_hp is not None else (target["hp"] if target else 0),
        "killed":       killed,
        "effect":       spell_data.get("on_hit_effect") if not saved else None,
    }


def player_cast_auto_spell(session, character, spell_name, spell_data,
                            target_name, slot_level):
    """Resolve a spell that automatically hits with no attack roll or save (e.g. Magic Missile).

    Magic Missile is handled as a special case: it fires 3 + (slot_level - 1) missiles,
    each dealing 1d4+1. Other auto-hit spells simply roll their damage notation.
    """
    from models.spells import spell_damage_notation
    player_level = character.get("level", 1)
    dmg_note     = spell_damage_notation(spell_name, spell_data, slot_level, player_level)
    has_damage   = dmg_note not in ("0", "", "—")

    dmg_result = None
    new_hp     = None
    killed     = False
    if has_damage:
        if spell_name == "Magic Missile":
            num_missiles = 3 + max(0, slot_level - 1)
            total = sum(dice.roll(4) + 1 for _ in range(num_missiles))
            dmg_result = {"total": total, "missiles": num_missiles}
        else:
            dmg_result = dice.damage(dmg_note)
        target = _get_combatant(session, target_name)
        if target and dmg_result["total"] > 0:
            new_hp = gs.apply_combat_damage(session, target_name, dmg_result["total"])
            killed = new_hp <= 0

    target = _get_combatant(session, target_name)
    return {
        "spell":      spell_name,
        "slot_level": slot_level,
        "damage":     dmg_result,
        "new_hp":     new_hp if new_hp is not None else (target["hp"] if target else 0),
        "killed":     killed,
        "effect":     spell_data.get("on_hit_effect"),
    }


# ── Summary ────────────────────────────────────────────────────────────────────

def combat_summary(session):
    """Return a structured snapshot of the current combat state.

    Includes the round number, whose turn it is, the full combatant list with
    HP/conditions, and boolean flags for whether enemies and the player are still alive.
    Used by the UI to update the combat tracker panel.
    """
    order   = session["initiative_order"]
    current = gs.current_combatant(session)
    return {
        "round":        session["round"],
        "current_turn": current["name"] if current else None,
        "combatants": [
            {
                "name":       c["name"],
                "hp":         c["hp"],
                "max_hp":     c["max_hp"],
                "is_player":  c["is_player"],
                "conditions": c.get("conditions", []),
                "alive":      c["hp"] > 0,
            }
            for c in order
        ],
        "enemies_alive":  gs.enemies_alive(session),
        "player_alive":   any(c["hp"] > 0 for c in order if c["is_player"]),
    }


def xp_from_combat(session):
    """Return the total XP earned from all enemies defeated in this combat.
    Only counts enemies (not players or companions) with HP ≤ 0.
    """
    return sum(
        c.get("xp", 0)
        for c in session["initiative_order"]
        if not c["is_player"] and c["hp"] <= 0
    )
