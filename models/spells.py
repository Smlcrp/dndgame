import re as _re

# Spell combat data. Schema per entry:
#   level: int (0=cantrip)
#   delivery: "attack" | "save" | "auto"
#   save_ability: str|None  ("dex","con","wis","str","int","cha")
#   damage: str  (base notation; "0" if no damage)
#   damage_type: str
#   upcast_per_level: str|None  (extra dice per slot above base)
#   cantrip_scale: bool  (double/triple/quadruple die count at levels 5/11/17)
#   on_hit_effect: str|None
#   concentration: bool

SPELLS = {
    # ── Cantrips ──────────────────────────────────────────────────────────────
    "Acid Splash":      {"level":0,"delivery":"save","save_ability":"dex","damage":"1d6","damage_type":"acid","upcast_per_level":None,"cantrip_scale":True,"on_hit_effect":None,"concentration":False},
    "Chill Touch":      {"level":0,"delivery":"attack","save_ability":None,"damage":"1d8","damage_type":"necrotic","upcast_per_level":None,"cantrip_scale":True,"on_hit_effect":"Cannot regain HP until your next turn.","concentration":False},
    "Eldritch Blast":   {"level":0,"delivery":"attack","save_ability":None,"damage":"1d10","damage_type":"force","upcast_per_level":None,"cantrip_scale":True,"on_hit_effect":None,"concentration":False},
    "Fire Bolt":        {"level":0,"delivery":"attack","save_ability":None,"damage":"1d10","damage_type":"fire","upcast_per_level":None,"cantrip_scale":True,"on_hit_effect":None,"concentration":False},
    "Infestation":      {"level":0,"delivery":"save","save_ability":"con","damage":"1d6","damage_type":"poison","upcast_per_level":None,"cantrip_scale":True,"on_hit_effect":"Must use reaction to move 5 ft in a random direction.","concentration":False},
    "Poison Spray":     {"level":0,"delivery":"save","save_ability":"con","damage":"1d12","damage_type":"poison","upcast_per_level":None,"cantrip_scale":True,"on_hit_effect":None,"concentration":False},
    "Produce Flame":    {"level":0,"delivery":"attack","save_ability":None,"damage":"1d8","damage_type":"fire","upcast_per_level":None,"cantrip_scale":True,"on_hit_effect":None,"concentration":False},
    "Ray of Frost":     {"level":0,"delivery":"attack","save_ability":None,"damage":"1d8","damage_type":"cold","upcast_per_level":None,"cantrip_scale":True,"on_hit_effect":"Speed reduced by 10 ft until start of your next turn.","concentration":False},
    "Sacred Flame":     {"level":0,"delivery":"save","save_ability":"dex","damage":"1d8","damage_type":"radiant","upcast_per_level":None,"cantrip_scale":True,"on_hit_effect":None,"concentration":False},
    "Shocking Grasp":   {"level":0,"delivery":"attack","save_ability":None,"damage":"1d8","damage_type":"lightning","upcast_per_level":None,"cantrip_scale":True,"on_hit_effect":"Cannot take reactions until start of its next turn.","concentration":False},
    "Thorn Whip":       {"level":0,"delivery":"attack","save_ability":None,"damage":"1d6","damage_type":"piercing","upcast_per_level":None,"cantrip_scale":True,"on_hit_effect":"Pulls target 10 ft closer.","concentration":False},
    "Thunderclap":      {"level":0,"delivery":"save","save_ability":"con","damage":"1d6","damage_type":"thunder","upcast_per_level":None,"cantrip_scale":True,"on_hit_effect":None,"concentration":False},
    "Toll the Dead":    {"level":0,"delivery":"save","save_ability":"wis","damage":"1d8","damage_type":"necrotic","upcast_per_level":None,"cantrip_scale":True,"on_hit_effect":None,"concentration":False},
    "Vicious Mockery":  {"level":0,"delivery":"save","save_ability":"wis","damage":"1d4","damage_type":"psychic","upcast_per_level":None,"cantrip_scale":True,"on_hit_effect":"Disadvantage on next attack roll.","concentration":False},
    "Word of Radiance": {"level":0,"delivery":"save","save_ability":"con","damage":"1d6","damage_type":"radiant","upcast_per_level":None,"cantrip_scale":True,"on_hit_effect":None,"concentration":False},

    # ── Level 1 ───────────────────────────────────────────────────────────────
    "Burning Hands":   {"level":1,"delivery":"save","save_ability":"dex","damage":"3d6","damage_type":"fire","upcast_per_level":"1d6","cantrip_scale":False,"on_hit_effect":None,"concentration":False},
    "Catapult":        {"level":1,"delivery":"save","save_ability":"dex","damage":"3d8","damage_type":"bludgeoning","upcast_per_level":"1d8","cantrip_scale":False,"on_hit_effect":None,"concentration":False},
    "Chromatic Orb":   {"level":1,"delivery":"attack","save_ability":None,"damage":"3d8","damage_type":"chosen","upcast_per_level":"1d8","cantrip_scale":False,"on_hit_effect":None,"concentration":False},
    "Guiding Bolt":    {"level":1,"delivery":"attack","save_ability":None,"damage":"4d6","damage_type":"radiant","upcast_per_level":"1d6","cantrip_scale":False,"on_hit_effect":"Next attack against target has advantage.","concentration":False},
    "Ice Knife":       {"level":1,"delivery":"attack","save_ability":None,"damage":"1d10","damage_type":"piercing","upcast_per_level":None,"cantrip_scale":False,"on_hit_effect":"On hit: creatures within 5 ft take 2d6 cold (DEX save negates).","concentration":False},
    "Inflict Wounds":  {"level":1,"delivery":"attack","save_ability":None,"damage":"3d10","damage_type":"necrotic","upcast_per_level":"1d10","cantrip_scale":False,"on_hit_effect":None,"concentration":False},
    "Magic Missile":   {"level":1,"delivery":"auto","save_ability":None,"damage":"1d4+1","damage_type":"force","upcast_per_level":"1d4+1","cantrip_scale":False,"on_hit_effect":"3 missiles at base; +1 per slot above 1st. Each deals 1d4+1 force.","concentration":False},
    "Ray of Sickness": {"level":1,"delivery":"attack","save_ability":None,"damage":"2d8","damage_type":"poison","upcast_per_level":"1d8","cantrip_scale":False,"on_hit_effect":"CON save or Poisoned until end of its next turn.","concentration":False},
    "Thunderwave":     {"level":1,"delivery":"save","save_ability":"con","damage":"2d8","damage_type":"thunder","upcast_per_level":"1d8","cantrip_scale":False,"on_hit_effect":"Pushed 10 ft on failed save.","concentration":False},
    "Witch Bolt":      {"level":1,"delivery":"attack","save_ability":None,"damage":"1d12","damage_type":"lightning","upcast_per_level":"1d12","cantrip_scale":False,"on_hit_effect":"Concentration: deal 1d12 per bonus action on subsequent turns.","concentration":True},

    # ── Level 2 ───────────────────────────────────────────────────────────────
    "Acid Arrow":          {"level":2,"delivery":"attack","save_ability":None,"damage":"4d4","damage_type":"acid","upcast_per_level":"1d4","cantrip_scale":False,"on_hit_effect":"On hit: 2d4 acid at end of target's next turn.","concentration":False},
    "Blindness/Deafness":  {"level":2,"delivery":"save","save_ability":"con","damage":"0","damage_type":"—","upcast_per_level":None,"cantrip_scale":False,"on_hit_effect":"Blinded or Deafened for 1 minute (save each turn).","concentration":False},
    "Crown of Madness":    {"level":2,"delivery":"save","save_ability":"wis","damage":"0","damage_type":"—","upcast_per_level":None,"cantrip_scale":False,"on_hit_effect":"Charmed; attacks a creature of your choice each turn.","concentration":True},
    "Hold Person":         {"level":2,"delivery":"save","save_ability":"wis","damage":"0","damage_type":"—","upcast_per_level":None,"cantrip_scale":False,"on_hit_effect":"Paralyzed for 1 minute (save each turn to end).","concentration":True},
    "Phantasmal Force":    {"level":2,"delivery":"save","save_ability":"int","damage":"1d6","damage_type":"psychic","upcast_per_level":None,"cantrip_scale":False,"on_hit_effect":"Target believes illusion is real; 1d6 psychic each turn.","concentration":True},
    "Scorching Ray":       {"level":2,"delivery":"attack","save_ability":None,"damage":"2d6","damage_type":"fire","upcast_per_level":None,"cantrip_scale":False,"on_hit_effect":"3 rays, each a separate attack (+1 ray per slot above 2nd).","concentration":False},
    "Shatter":             {"level":2,"delivery":"save","save_ability":"con","damage":"3d8","damage_type":"thunder","upcast_per_level":"1d8","cantrip_scale":False,"on_hit_effect":None,"concentration":False},

    # ── Level 3 ───────────────────────────────────────────────────────────────
    "Call Lightning":   {"level":3,"delivery":"save","save_ability":"dex","damage":"3d10","damage_type":"lightning","upcast_per_level":"1d10","cantrip_scale":False,"on_hit_effect":"Concentration: additional bolts each turn.","concentration":True},
    "Fear":             {"level":3,"delivery":"save","save_ability":"wis","damage":"0","damage_type":"—","upcast_per_level":None,"cantrip_scale":False,"on_hit_effect":"Frightened; must move away. Saves at end of each turn.","concentration":True},
    "Fireball":         {"level":3,"delivery":"save","save_ability":"dex","damage":"8d6","damage_type":"fire","upcast_per_level":"1d6","cantrip_scale":False,"on_hit_effect":None,"concentration":False},
    "Hypnotic Pattern": {"level":3,"delivery":"save","save_ability":"wis","damage":"0","damage_type":"—","upcast_per_level":None,"cantrip_scale":False,"on_hit_effect":"Incapacitated and speed 0. Ends if damaged or shaken.","concentration":True},
    "Lightning Bolt":   {"level":3,"delivery":"save","save_ability":"dex","damage":"8d6","damage_type":"lightning","upcast_per_level":"1d6","cantrip_scale":False,"on_hit_effect":None,"concentration":False},
    "Vampiric Touch":   {"level":3,"delivery":"attack","save_ability":None,"damage":"3d6","damage_type":"necrotic","upcast_per_level":"1d6","cantrip_scale":False,"on_hit_effect":"Regain HP equal to half the damage dealt.","concentration":True},

    # ── Level 4 ───────────────────────────────────────────────────────────────
    "Banishment":        {"level":4,"delivery":"save","save_ability":"cha","damage":"0","damage_type":"—","upcast_per_level":None,"cantrip_scale":False,"on_hit_effect":"Banished. Returns when concentration ends (unless native plane).","concentration":True},
    "Blight":            {"level":4,"delivery":"save","save_ability":"con","damage":"8d8","damage_type":"necrotic","upcast_per_level":"1d8","cantrip_scale":False,"on_hit_effect":None,"concentration":False},
    "Ice Storm":         {"level":4,"delivery":"save","save_ability":"dex","damage":"2d8","damage_type":"bludgeoning","upcast_per_level":"1d8","cantrip_scale":False,"on_hit_effect":"Also 4d6 cold. Area becomes difficult terrain.","concentration":False},
    "Phantasmal Killer": {"level":4,"delivery":"save","save_ability":"wis","damage":"4d10","damage_type":"psychic","upcast_per_level":"1d10","cantrip_scale":False,"on_hit_effect":"Frightened; 4d10 psychic at start of each turn (save each turn).","concentration":True},
    "Vitriolic Sphere":  {"level":4,"delivery":"save","save_ability":"dex","damage":"10d4","damage_type":"acid","upcast_per_level":"2d4","cantrip_scale":False,"on_hit_effect":"On miss: 5d4 acid. On hit: 5d4 additional acid end of next turn.","concentration":False},

    # ── Level 5 ───────────────────────────────────────────────────────────────
    "Cloudkill":       {"level":5,"delivery":"save","save_ability":"con","damage":"5d8","damage_type":"poison","upcast_per_level":None,"cantrip_scale":False,"on_hit_effect":"Persistent cloud; reapplies each turn.","concentration":True},
    "Cone of Cold":    {"level":5,"delivery":"save","save_ability":"con","damage":"8d8","damage_type":"cold","upcast_per_level":"1d8","cantrip_scale":False,"on_hit_effect":None,"concentration":False},
    "Dominate Person": {"level":5,"delivery":"save","save_ability":"wis","damage":"0","damage_type":"—","upcast_per_level":None,"cantrip_scale":False,"on_hit_effect":"Charmed; you control its actions.","concentration":True},
    "Hold Monster":    {"level":5,"delivery":"save","save_ability":"wis","damage":"0","damage_type":"—","upcast_per_level":None,"cantrip_scale":False,"on_hit_effect":"Paralyzed for 1 minute (save each turn to end).","concentration":True},
    "Synaptic Static": {"level":5,"delivery":"save","save_ability":"int","damage":"8d6","damage_type":"psychic","upcast_per_level":None,"cantrip_scale":False,"on_hit_effect":"Subtract 1d6 from attack rolls, checks, and saves for 1 minute.","concentration":False},

    # ── Level 6 ───────────────────────────────────────────────────────────────
    "Chain Lightning":  {"level":6,"delivery":"save","save_ability":"dex","damage":"10d8","damage_type":"lightning","upcast_per_level":None,"cantrip_scale":False,"on_hit_effect":"Jumps to 3 additional targets.","concentration":False},
    "Circle of Death":  {"level":6,"delivery":"save","save_ability":"con","damage":"8d6","damage_type":"necrotic","upcast_per_level":"2d6","cantrip_scale":False,"on_hit_effect":None,"concentration":False},
    "Disintegrate":     {"level":6,"delivery":"save","save_ability":"dex","damage":"10d6+40","damage_type":"force","upcast_per_level":"3d6","cantrip_scale":False,"on_hit_effect":"Reduced to dust if dropped to 0 HP.","concentration":False},
    "Eyebite":          {"level":6,"delivery":"save","save_ability":"wis","damage":"0","damage_type":"—","upcast_per_level":None,"cantrip_scale":False,"on_hit_effect":"Frightened, Unconscious, or Sickened (your choice) each turn.","concentration":True},

    # ── Level 7 ───────────────────────────────────────────────────────────────
    "Finger of Death": {"level":7,"delivery":"save","save_ability":"con","damage":"7d8+30","damage_type":"necrotic","upcast_per_level":None,"cantrip_scale":False,"on_hit_effect":None,"concentration":False},
    "Prismatic Spray":  {"level":7,"delivery":"save","save_ability":"dex","damage":"10d6","damage_type":"varies","upcast_per_level":None,"cantrip_scale":False,"on_hit_effect":"Random color determines secondary effect.","concentration":False},

    # ── Level 8 ───────────────────────────────────────────────────────────────
    "Feeblemind": {"level":8,"delivery":"save","save_ability":"int","damage":"4d6","damage_type":"psychic","upcast_per_level":None,"cantrip_scale":False,"on_hit_effect":"INT and CHA drop to 1. Cannot cast spells.","concentration":False},
    "Sunburst":   {"level":8,"delivery":"save","save_ability":"con","damage":"12d6","damage_type":"radiant","upcast_per_level":None,"cantrip_scale":False,"on_hit_effect":"Blinded for 1 minute (save each turn to end).","concentration":False},

    # ── Level 9 ───────────────────────────────────────────────────────────────
    "Meteor Swarm":   {"level":9,"delivery":"save","save_ability":"dex","damage":"20d6","damage_type":"fire","upcast_per_level":None,"cantrip_scale":False,"on_hit_effect":"Also 20d6 bludgeoning. Four 40 ft spheres.","concentration":False},
    "Power Word Kill":{"level":9,"delivery":"auto","save_ability":None,"damage":"0","damage_type":"—","upcast_per_level":None,"cantrip_scale":False,"on_hit_effect":"Instantly kills a creature with 100 HP or fewer.","concentration":False},
    "Psychic Scream": {"level":9,"delivery":"save","save_ability":"int","damage":"14d6","damage_type":"psychic","upcast_per_level":None,"cantrip_scale":False,"on_hit_effect":"Stunned for 1 minute (save each turn to end).","concentration":False},
}


def cantrip_damage_notation(base: str, player_level: int) -> str:
    m = _re.match(r'^(\d*)d(\d+)([+-]\d+)?$', base)
    if not m:
        return base
    count    = int(m.group(1)) if m.group(1) else 1
    die      = m.group(2)
    modifier = m.group(3) or ""
    mult = 4 if player_level >= 17 else 3 if player_level >= 11 else 2 if player_level >= 5 else 1
    return f"{count * mult}d{die}{modifier}"


def upcast_damage_notation(base: str, upcast_per_level: str, extra_levels: int) -> str:
    if not upcast_per_level or extra_levels <= 0:
        return base
    b = _re.match(r'^(\d*)d(\d+)([+-]\d+)?$', base)
    u = _re.match(r'^(\d*)d(\d+)([+-]\d+)?$', upcast_per_level)
    if not b or not u or b.group(2) != u.group(2):
        return base
    b_count  = int(b.group(1)) if b.group(1) else 1
    u_count  = int(u.group(1)) if u.group(1) else 1
    die      = b.group(2)
    modifier = b.group(3) or ""
    return f"{b_count + u_count * extra_levels}d{die}{modifier}"


def spell_damage_notation(spell_name: str, spell_data: dict, slot_level: int,
                          player_level: int) -> str:
    base = spell_data.get("damage", "0")
    if base in ("0", "", "—"):
        return "0"
    if spell_data["level"] == 0 and spell_data.get("cantrip_scale"):
        return cantrip_damage_notation(base, player_level)
    if spell_data["level"] > 0:
        extra = slot_level - spell_data["level"]
        if extra > 0:
            upcast = spell_data.get("upcast_per_level")
            if upcast:
                return upcast_damage_notation(base, upcast, extra)
    return base


def get_combat_spells(char: dict) -> list:
    sc = char.get("spellcasting", {})
    if not sc.get("enabled", False):
        return []
    known  = set(sc.get("spells_known", []) + sc.get("spells_prepared", []))
    slots  = sc.get("slots", {})
    result = []
    for name in sorted(known):
        spell = SPELLS.get(name)
        if not spell:
            continue
        if spell["level"] == 0:
            result.append({"name": name, "level": 0, "spell": spell,
                           "available_slots": None, "slot_options": []})
        else:
            avail = {int(k): v.get("total", 0) - v.get("used", 0)
                     for k, v in slots.items()
                     if int(k) >= spell["level"]
                     and v.get("total", 0) - v.get("used", 0) > 0}
            if not avail:
                continue
            result.append({"name": name, "level": spell["level"], "spell": spell,
                           "available_slots": sum(avail.values()),
                           "slot_options": sorted(avail.keys())})
    result.sort(key=lambda s: (s["level"], s["name"]))
    return result
