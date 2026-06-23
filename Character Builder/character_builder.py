"""
Interactive CLI for creating and editing a D&D 5e character sheet.
Run this script to build or update your character.
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from character import (
    empty_character, save_character, load_character, list_characters,
    summary, SKILLS, modifier, proficiency_bonus
)


def prompt(label: str, default: str = "") -> str:
    result = input(f"  {label}" + (f" [{default}]" if default else "") + ": ").strip()
    return result if result else default


def prompt_int(label: str, default: int = 0) -> int:
    while True:
        val = input(f"  {label} [{default}]: ").strip()
        if not val:
            return default
        try:
            return int(val)
        except ValueError:
            print("  Please enter a number.")


def prompt_list(label: str, existing: list) -> list:
    print(f"  {label} (comma-separated, blank to keep current)")
    if existing:
        print(f"    Current: {', '.join(existing)}")
    val = input("  > ").strip()
    if not val:
        return existing
    return [x.strip() for x in val.split(",") if x.strip()]


def section(title: str):
    print(f"\n{'─'*50}")
    print(f"  {title}")
    print(f"{'─'*50}")


def build_basic_info(char: dict) -> dict:
    section("BASIC INFORMATION")
    char["name"]       = prompt("Character name", char["name"])
    char["race"]       = prompt("Race", char["race"])
    char["class"]      = prompt("Class", char["class"])
    char["subclass"]   = prompt("Subclass (optional)", char["subclass"])
    char["background"] = prompt("Background", char["background"])
    char["level"]      = prompt_int("Level", char["level"])
    char["experience"] = prompt_int("Experience points", char["experience"])
    char["alignment"]  = prompt("Alignment", char["alignment"])
    return char


def build_ability_scores(char: dict) -> dict:
    section("ABILITY SCORES")
    abilities = ["strength", "dexterity", "constitution", "intelligence", "wisdom", "charisma"]
    for ability in abilities:
        char["abilities"][ability] = prompt_int(
            ability.capitalize(), char["abilities"][ability]
        )
    return char


def build_combat(char: dict) -> dict:
    section("COMBAT STATS")
    char["hp"]["max"]     = prompt_int("Max HP", char["hp"]["max"])
    char["hp"]["current"] = prompt_int("Current HP", char["hp"]["current"])
    char["hp"]["temp"]    = prompt_int("Temp HP", char["hp"]["temp"])
    char["armor_class"]   = prompt_int("Armor Class", char["armor_class"])
    char["speed"]         = prompt_int("Speed (ft)", char["speed"])
    char["hit_dice"]["type"]  = prompt("Hit die type (e.g. d8)", char["hit_dice"]["type"])
    char["hit_dice"]["total"] = prompt_int("Total hit dice", char["hit_dice"]["total"] or char["level"])
    char["hit_dice"]["used"]  = prompt_int("Used hit dice", char["hit_dice"]["used"])
    return char


def build_proficiencies(char: dict) -> dict:
    section("PROFICIENCIES & SAVES")
    print(f"  Abilities: strength, dexterity, constitution, intelligence, wisdom, charisma")
    char["saving_throw_proficiencies"] = prompt_list(
        "Saving throw proficiencies", char["saving_throw_proficiencies"]
    )
    print(f"\n  Skills: {', '.join(SKILLS.keys())}")
    char["skill_proficiencies"] = prompt_list("Skill proficiencies", char["skill_proficiencies"])
    char["skill_expertises"]    = prompt_list("Skill expertises (double proficiency)", char["skill_expertises"])
    char["languages"]           = prompt_list("Languages", char["languages"])
    char["armor_proficiencies"] = prompt_list("Armor proficiencies", char["armor_proficiencies"])
    char["weapon_proficiencies"]= prompt_list("Weapon proficiencies", char["weapon_proficiencies"])
    char["tool_proficiencies"]  = prompt_list("Tool proficiencies", char["tool_proficiencies"])
    return char


def build_attacks(char: dict) -> dict:
    section("ATTACKS")
    print(f"  Current attacks: {len(char['attacks'])}")
    for i, atk in enumerate(char["attacks"]):
        print(f"    {i+1}. {atk['name']}  +{atk['attack_bonus']} to hit  {atk['damage']} {atk['damage_type']}")

    while True:
        action = input("\n  [a]dd attack, [d]elete attack, or [enter] to skip: ").strip().lower()
        if not action:
            break
        if action == "a":
            atk = {
                "name":         prompt("Attack name"),
                "attack_bonus": prompt_int("Attack bonus"),
                "damage":       prompt("Damage (e.g. 1d6+3)"),
                "damage_type":  prompt("Damage type (e.g. slashing)"),
                "notes":        prompt("Notes (optional)"),
            }
            char["attacks"].append(atk)
        elif action == "d":
            idx = prompt_int("Delete attack number", 1) - 1
            if 0 <= idx < len(char["attacks"]):
                removed = char["attacks"].pop(idx)
                print(f"  Removed: {removed['name']}")
    return char


def build_spellcasting(char: dict) -> dict:
    section("SPELLCASTING")
    sc = char["spellcasting"]
    enabled = input("  Does this character cast spells? [y/N]: ").strip().lower()
    sc["enabled"] = enabled == "y"

    if not sc["enabled"]:
        return char

    print("  Spellcasting ability: strength/dexterity/constitution/intelligence/wisdom/charisma")
    sc["ability"] = prompt("Spellcasting ability", sc["ability"])

    override = input("  Override spell save DC and attack bonus? [y/N]: ").strip().lower()
    if override == "y":
        sc["spell_save_dc"] = prompt_int("Spell save DC", sc["spell_save_dc"])
        sc["attack_bonus"]  = prompt_int("Spell attack bonus", sc["attack_bonus"])

    section("SPELL SLOTS")
    for lvl in range(1, 10):
        key = str(lvl)
        current = sc["slots"][key]["total"]
        total = prompt_int(f"Level {lvl} slot total", current)
        used  = prompt_int(f"Level {lvl} slots used", sc["slots"][key]["used"]) if total else 0
        sc["slots"][key] = {"total": total, "used": used}

    section("SPELLS")
    print("  Add spells one at a time. Press enter with blank name to stop.")
    while True:
        name = input("  Spell name (blank to stop): ").strip()
        if not name:
            break
        spell = {
            "name":        name,
            "level":       prompt_int("  Spell level (0 for cantrip)", 1),
            "school":      prompt("  School of magic"),
            "description": prompt("  Brief description"),
        }
        char["spellcasting"]["spells_known"].append(spell)

    return char


def build_equipment(char: dict) -> dict:
    section("EQUIPMENT & CURRENCY")
    while True:
        action = input("  [a]dd item, [d]elete item, [enter] to skip: ").strip().lower()
        if not action:
            break
        if action == "a":
            item = {
                "name":     prompt("Item name"),
                "quantity": prompt_int("Quantity", 1),
                "weight":   float(prompt("Weight (lbs)", "0")),
                "notes":    prompt("Notes"),
            }
            char["equipment"].append(item)
        elif action == "d":
            for i, it in enumerate(char["equipment"]):
                print(f"    {i+1}. {it['name']} x{it['quantity']}")
            idx = prompt_int("Delete item number", 1) - 1
            if 0 <= idx < len(char["equipment"]):
                char["equipment"].pop(idx)

    section("CURRENCY")
    for coin in ["cp", "sp", "ep", "gp", "pp"]:
        char["currency"][coin] = prompt_int(coin.upper(), char["currency"][coin])

    return char


def build_features(char: dict) -> dict:
    section("FEATURES & TRAITS")
    print("  Add class features, racial traits, feats, etc.")
    while True:
        action = input("  [a]dd feature, [enter] to skip: ").strip().lower()
        if not action:
            break
        if action == "a":
            has_uses = input("  Does this feature have limited uses? [y/N]: ").strip().lower() == "y"
            feature = {
                "name":        prompt("Feature name"),
                "source":      prompt("Source (e.g. 'Rogue 2', 'Half-Elf')"),
                "description": prompt("Description"),
                "uses": {
                    "max":  prompt_int("Max uses per rest", 1),
                    "used": prompt_int("Currently used", 0),
                } if has_uses else None,
            }
            char["features"].append(feature)
    return char


def build_personality(char: dict) -> dict:
    section("PERSONALITY")
    char["personality_traits"] = prompt("Personality traits", char["personality_traits"])
    char["ideals"]             = prompt("Ideals", char["ideals"])
    char["bonds"]              = prompt("Bonds", char["bonds"])
    char["flaws"]              = prompt("Flaws", char["flaws"])
    char["backstory"]          = prompt("Backstory summary", char["backstory"])
    return char


def main():
    print("\n" + "="*50)
    print("  D&D 5e CHARACTER BUILDER")
    print("="*50)

    existing = list_characters()
    if existing:
        print(f"\n  Existing characters: {', '.join(existing)}")
        choice = input("  Load existing character to edit? [name or blank for new]: ").strip()
        if choice and choice in existing:
            char = load_character(choice)
            print(f"  Loaded: {char['name']}")
        else:
            char = empty_character()
    else:
        char = empty_character()

    sections = [
        ("Basic Information",    build_basic_info),
        ("Ability Scores",       build_ability_scores),
        ("Combat Stats",         build_combat),
        ("Proficiencies",        build_proficiencies),
        ("Attacks",              build_attacks),
        ("Spellcasting",         build_spellcasting),
        ("Equipment",            build_equipment),
        ("Features & Traits",    build_features),
        ("Personality",          build_personality),
    ]

    print("\n  You can fill in all sections or skip any (press enter to skip a section).")
    for title, fn in sections:
        skip = input(f"\n  Fill in [{title}]? [Y/n]: ").strip().lower()
        if skip != "n":
            char = fn(char)

    print("\n" + summary(char))

    if char["name"]:
        save = input("\n  Save this character? [Y/n]: ").strip().lower()
        if save != "n":
            path = save_character(char)
            print(f"  Saved to: {path}")
    else:
        print("  Character needs a name to be saved.")


if __name__ == "__main__":
    main()
