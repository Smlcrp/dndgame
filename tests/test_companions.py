"""Tests for the companion system — models/companions.py, dm.py, game_state.py."""

import sys
import os
from pathlib import Path

# Ensure project root is on path
_root = Path(__file__).parent.parent
sys.path.insert(0, str(_root))

import unittest
import models.companions as comp_mod
import models.game_state as gs
import models.dm as dm_mod

# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def _session_with_combat(player_hp=30, enemy_hp=7, companion=None):
    s = gs.empty_session()
    s["current_hp"] = player_hp
    s["in_combat"]  = True
    s["initiative_order"] = [
        {"name": "Player", "hp": player_hp, "max_hp": 30,
         "initiative": 18, "is_player": True, "conditions": []},
        {"name": "Goblin", "hp": enemy_hp, "max_hp": 7,
         "initiative": 8, "is_player": False, "conditions": []},
    ]
    if companion:
        s["companions"] = [companion]
        s["initiative_order"].insert(1, {
            "name": companion["name"], "hp": companion["hp"]["current"],
            "max_hp": companion["hp"]["max"], "initiative": 12,
            "is_player": False, "is_companion": True, "conditions": [],
        })
    return s


# ─────────────────────────────────────────────────────────────────────────────
# 1. Roster & lookup
# ─────────────────────────────────────────────────────────────────────────────

class TestRoster(unittest.TestCase):

    def test_roster_count(self):
        """Exactly 10 companion templates."""
        self.assertEqual(len(comp_mod.get_roster()), 10)

    def test_roster_all_have_names(self):
        for t in comp_mod.get_roster():
            self.assertTrue(t.get("first_name"), f"{t['id']} missing first_name")
            self.assertTrue(t.get("last_name"),  f"{t['id']} missing last_name")

    def test_roster_classes_unique(self):
        classes = [t["class"] for t in comp_mod.get_roster()]
        self.assertEqual(len(classes), len(set(classes)), "Duplicate classes in roster")

    def test_find_by_full_name_case_insensitive(self):
        t = comp_mod.find_companion_template("elara voss")
        self.assertIsNotNone(t)
        self.assertEqual(t["class"], "Cleric")

    def test_find_missing_returns_none(self):
        self.assertIsNone(comp_mod.find_companion_template("Nobody Here"))

    def test_find_all_10_templates(self):
        names = [f"{t['first_name']} {t['last_name']}" for t in comp_mod.get_roster()]
        for name in names:
            self.assertIsNotNone(comp_mod.find_companion_template(name), f"{name} not found")


# ─────────────────────────────────────────────────────────────────────────────
# 2. build_companion_at_level
# ─────────────────────────────────────────────────────────────────────────────

class TestBuildCompanion(unittest.TestCase):

    def setUp(self):
        self.cleric_t = comp_mod.find_companion_template("Elara Voss")
        self.fighter_t = comp_mod.find_companion_template("Varen Ashcloak")
        self.wizard_t  = comp_mod.find_companion_template("Zephyra Coldwell")
        self.ranger_t  = comp_mod.find_companion_template("Sable Nightwhisper")
        self.monk_t    = comp_mod.find_companion_template("Petra Stonehaven")

    def test_name_assembled(self):
        c = comp_mod.build_companion_at_level(self.cleric_t, 1)
        self.assertEqual(c["name"], "Elara Voss")
        self.assertEqual(c["first_name"], "Elara")
        self.assertEqual(c["last_name"],  "Voss")

    def test_hp_positive(self):
        for t in comp_mod.get_roster():
            c = comp_mod.build_companion_at_level(t, 1)
            self.assertGreater(c["hp"]["max"], 0, f"{t['id']} HP ≤ 0")
            self.assertEqual(c["hp"]["current"], c["hp"]["max"])

    def test_hp_grows_with_level(self):
        c1 = comp_mod.build_companion_at_level(self.fighter_t, 1)
        c5 = comp_mod.build_companion_at_level(self.fighter_t, 5)
        self.assertGreater(c5["hp"]["max"], c1["hp"]["max"])

    def test_ac_reasonable(self):
        for t in comp_mod.get_roster():
            c = comp_mod.build_companion_at_level(t, 1)
            self.assertGreaterEqual(c["ac"], 10, f"{t['id']} AC < 10")
            self.assertLessEqual(c["ac"], 22, f"{t['id']} AC > 22")

    def test_cleric_has_spell_slots(self):
        c = comp_mod.build_companion_at_level(self.cleric_t, 3)
        slots = c["spell_slots"]
        self.assertIn("1", slots)
        self.assertIn("2", slots)
        self.assertGreater(slots["1"]["total"], 0)

    def test_wizard_has_more_slots_at_higher_level(self):
        c5  = comp_mod.build_companion_at_level(self.wizard_t, 5)
        c10 = comp_mod.build_companion_at_level(self.wizard_t, 10)
        total_5  = sum(d["total"] for d in c5["spell_slots"].values())
        total_10 = sum(d["total"] for d in c10["spell_slots"].values())
        self.assertGreater(total_10, total_5)

    def test_ranger_half_caster_slots(self):
        c1 = comp_mod.build_companion_at_level(self.ranger_t, 1)
        c5 = comp_mod.build_companion_at_level(self.ranger_t, 5)
        self.assertEqual(len(c1["spell_slots"]), 0)  # rangers get slots at L2
        self.assertGreater(len(c5["spell_slots"]), 0)

    def test_fighter_no_spell_slots(self):
        c = comp_mod.build_companion_at_level(self.fighter_t, 5)
        self.assertEqual(len(c["spell_slots"]), 0)

    def test_monk_no_spell_slots(self):
        c = comp_mod.build_companion_at_level(self.monk_t, 5)
        self.assertEqual(len(c["spell_slots"]), 0)

    def test_fighter_second_wind(self):
        c = comp_mod.build_companion_at_level(self.fighter_t, 1)
        self.assertIn("Second Wind", c["feature_uses"])

    def test_fighter_action_surge_at_level_2(self):
        c1 = comp_mod.build_companion_at_level(self.fighter_t, 1)
        c2 = comp_mod.build_companion_at_level(self.fighter_t, 2)
        self.assertNotIn("Action Surge", c1["feature_uses"])
        self.assertIn("Action Surge", c2["feature_uses"])

    def test_status_active(self):
        c = comp_mod.build_companion_at_level(self.cleric_t, 1)
        self.assertEqual(c["status"], "active")
        self.assertEqual(c["death_saves"], {"successes": 0, "failures": 0})
        self.assertIsNone(c["dead_at_scene"])

    def test_personality_fields_present(self):
        for t in comp_mod.get_roster():
            c = comp_mod.build_companion_at_level(t, 1)
            self.assertEqual(len(c["personality_traits"]), 2, t["id"])
            self.assertTrue(c["ideal"])
            self.assertTrue(c["bond"])
            self.assertTrue(c["flaw"])

    def test_attack_bonus_reasonable(self):
        for t in comp_mod.get_roster():
            c = comp_mod.build_companion_at_level(t, 5)
            bonus = c["attack"]["bonus"]
            self.assertGreaterEqual(bonus, 2, f"{t['id']} attack bonus < 2")
            self.assertLessEqual(bonus, 12, f"{t['id']} attack bonus > 12")

    def test_monk_ac_uses_wis(self):
        c = comp_mod.build_companion_at_level(self.monk_t, 1)
        # Petra: DEX 17 (+3), WIS 16 (+3) → AC = 10 + 3 + 3 = 16
        self.assertEqual(c["ac"], 16)


# ─────────────────────────────────────────────────────────────────────────────
# 3. level_up_companion
# ─────────────────────────────────────────────────────────────────────────────

class TestLevelUp(unittest.TestCase):

    def test_hp_max_increases(self):
        t = comp_mod.find_companion_template("Varen Ashcloak")
        c = comp_mod.build_companion_at_level(t, 1)
        old_max = c["hp"]["max"]
        comp_mod.level_up_companion(c, 5)
        self.assertGreater(c["hp"]["max"], old_max)

    def test_current_hp_preserves_ratio(self):
        t = comp_mod.find_companion_template("Elara Voss")
        c = comp_mod.build_companion_at_level(t, 3)
        # Damage to 50%
        c["hp"]["current"] = c["hp"]["max"] // 2
        comp_mod.level_up_companion(c, 5)
        ratio = c["hp"]["current"] / c["hp"]["max"]
        self.assertAlmostEqual(ratio, 0.5, delta=0.15)

    def test_spell_slots_increase(self):
        t = comp_mod.find_companion_template("Zephyra Coldwell")
        c = comp_mod.build_companion_at_level(t, 3)
        old_total = sum(d["total"] for d in c["spell_slots"].values())
        comp_mod.level_up_companion(c, 7)
        new_total = sum(d["total"] for d in c["spell_slots"].values())
        self.assertGreater(new_total, old_total)

    def test_status_preserved(self):
        t = comp_mod.find_companion_template("Mira Swifthand")
        c = comp_mod.build_companion_at_level(t, 1)
        c["status"] = "unconscious"
        comp_mod.level_up_companion(c, 3)
        self.assertEqual(c["status"], "unconscious")

    def test_dead_at_scene_preserved(self):
        t = comp_mod.find_companion_template("Mira Swifthand")
        c = comp_mod.build_companion_at_level(t, 1)
        c["dead_at_scene"] = "Old Mill"
        comp_mod.level_up_companion(c, 3)
        self.assertEqual(c["dead_at_scene"], "Old Mill")

    def test_new_feature_unlocked(self):
        t = comp_mod.find_companion_template("Varen Ashcloak")
        c = comp_mod.build_companion_at_level(t, 1)
        self.assertNotIn("Action Surge", c["feature_uses"])
        comp_mod.level_up_companion(c, 2)
        self.assertIn("Action Surge", c["feature_uses"])


# ─────────────────────────────────────────────────────────────────────────────
# 4. get_available_companions — class conflict filtering
# ─────────────────────────────────────────────────────────────────────────────

class TestAvailability(unittest.TestCase):

    def test_filters_player_class(self):
        avail = comp_mod.get_available_companions("Fighter", [])
        classes = [t["class"] for t in avail]
        self.assertNotIn("Fighter", classes)

    def test_filters_active_companion_classes(self):
        avail = comp_mod.get_available_companions("Fighter", ["Cleric", "Rogue"])
        classes = [t["class"] for t in avail]
        self.assertNotIn("Fighter", classes)
        self.assertNotIn("Cleric",  classes)
        self.assertNotIn("Rogue",   classes)

    def test_empty_party_returns_all_except_player(self):
        avail = comp_mod.get_available_companions("Paladin", [])
        self.assertEqual(len(avail), 9)

    def test_case_insensitive_filter(self):
        avail = comp_mod.get_available_companions("fighter", [])
        classes = [t["class"].lower() for t in avail]
        self.assertNotIn("fighter", classes)


# ─────────────────────────────────────────────────────────────────────────────
# 5. Slot helpers
# ─────────────────────────────────────────────────────────────────────────────

class TestSlotHelpers(unittest.TestCase):

    def setUp(self):
        t = comp_mod.find_companion_template("Elara Voss")
        self.cleric = comp_mod.build_companion_at_level(t, 5)

    def test_has_slot_true_when_available(self):
        self.assertTrue(comp_mod.has_slot(self.cleric, 1))

    def test_use_slot_returns_level(self):
        level = comp_mod.use_slot(self.cleric, 1)
        self.assertEqual(level, 1)

    def test_use_slot_increments_used(self):
        before = self.cleric["spell_slots"]["1"]["used"]
        comp_mod.use_slot(self.cleric, 1)
        after = self.cleric["spell_slots"]["1"]["used"]
        self.assertEqual(after, before + 1)

    def test_has_slot_false_when_exhausted(self):
        slots = self.cleric["spell_slots"]
        for lvl in list(slots.keys()):
            slots[lvl]["used"] = slots[lvl]["total"]
        self.assertFalse(comp_mod.has_slot(self.cleric, 1))

    def test_use_slot_returns_none_when_none_available(self):
        slots = self.cleric["spell_slots"]
        for lvl in list(slots.keys()):
            slots[lvl]["used"] = slots[lvl]["total"]
        result = comp_mod.use_slot(self.cleric, 1)
        self.assertIsNone(result)

    def test_use_slot_picks_minimum_level(self):
        # Exhaust L1, should use L2
        slots = self.cleric["spell_slots"]
        slots["1"]["used"] = slots["1"]["total"]
        level = comp_mod.use_slot(self.cleric, 1)
        self.assertEqual(level, 2)

    def test_non_caster_has_no_slots(self):
        t = comp_mod.find_companion_template("Varen Ashcloak")
        fighter = comp_mod.build_companion_at_level(t, 5)
        self.assertFalse(comp_mod.has_slot(fighter, 1))


# ─────────────────────────────────────────────────────────────────────────────
# 6. spell_damage & companion_sneak_attack_damage
# ─────────────────────────────────────────────────────────────────────────────

class TestDamageNotations(unittest.TestCase):

    def test_sacred_flame_is_string(self):
        result = comp_mod.spell_damage("Sacred Flame", 0, 1)
        self.assertIsInstance(result, str)
        self.assertIn("d", result)

    def test_fireball_has_more_dice_at_higher_slot(self):
        low  = comp_mod.spell_damage("Fireball", 3, 5)
        high = comp_mod.spell_damage("Fireball", 6, 5)
        # Low: 8d6, High: 11d6 — extract first number
        low_num  = int(low.split("d")[0])
        high_num = int(high.split("d")[0])
        self.assertGreater(high_num, low_num)

    def test_sneak_attack_scales(self):
        l1  = comp_mod.companion_sneak_attack_damage(1)
        l5  = comp_mod.companion_sneak_attack_damage(5)
        l11 = comp_mod.companion_sneak_attack_damage(11)
        # L1=1d6, L5=3d6, L11=6d6
        self.assertEqual(l1, "1d6")
        self.assertEqual(l5, "3d6")
        self.assertEqual(l11, "6d6")


# ─────────────────────────────────────────────────────────────────────────────
# 7. companion_ai — decision logic
# ─────────────────────────────────────────────────────────────────────────────

class TestCompanionAI(unittest.TestCase):

    def _cleric(self, level=5):
        t = comp_mod.find_companion_template("Elara Voss")
        return comp_mod.build_companion_at_level(t, level)

    def _fighter(self, level=5):
        t = comp_mod.find_companion_template("Varen Ashcloak")
        return comp_mod.build_companion_at_level(t, level)

    def _wizard(self, level=5):
        t = comp_mod.find_companion_template("Zephyra Coldwell")
        return comp_mod.build_companion_at_level(t, level)

    def _bard(self, level=5):
        t = comp_mod.find_companion_template("Oswin Merryweather")
        return comp_mod.build_companion_at_level(t, level)

    def _paladin(self, level=5):
        t = comp_mod.find_companion_template("Torben Ironwall")
        return comp_mod.build_companion_at_level(t, level)

    def _rogue(self, level=5):
        t = comp_mod.find_companion_template("Mira Swifthand")
        return comp_mod.build_companion_at_level(t, level)

    def test_healer_targets_dying_player(self):
        cleric = self._cleric()
        session = _session_with_combat(player_hp=0, companion=cleric)
        session["current_turn"] = 0
        action = comp_mod.companion_ai(cleric, session)
        self.assertEqual(action["action"], "spell")
        self.assertTrue(action["is_heal"])
        self.assertEqual(action["target"], "Player")

    def test_healer_attacks_when_all_healthy(self):
        cleric = self._cleric()
        session = _session_with_combat(player_hp=30, companion=cleric)
        action = comp_mod.companion_ai(cleric, session)
        # Should attack with an offensive spell
        self.assertIn(action["action"], ("spell", "attack"))
        self.assertFalse(action.get("is_heal", False))

    def test_fighter_attacks_when_healthy(self):
        fighter = self._fighter()
        session = _session_with_combat(companion=fighter)
        action = comp_mod.companion_ai(fighter, session)
        self.assertEqual(action["action"], "attack")
        self.assertEqual(action["target"], "Goblin")

    def test_fighter_second_wind_when_low_hp(self):
        fighter = self._fighter()
        fighter["hp"]["current"] = 5  # very low
        session = _session_with_combat(companion=fighter)
        action = comp_mod.companion_ai(fighter, session)
        self.assertEqual(action["action"], "feature")
        self.assertEqual(action["feature"], "Second Wind")

    def test_fighter_no_second_wind_after_used(self):
        fighter = self._fighter()
        fighter["hp"]["current"] = 5
        fighter["feature_uses"]["Second Wind"]["current"] = 0
        session = _session_with_combat(companion=fighter)
        action = comp_mod.companion_ai(fighter, session)
        # Falls through to attack
        self.assertEqual(action["action"], "attack")

    def test_wizard_fireball_at_3_enemies(self):
        wizard = self._wizard()
        session = _session_with_combat(companion=wizard)
        session["initiative_order"] += [
            {"name": "Goblin2", "hp": 7, "max_hp": 7, "initiative": 6,
             "is_player": False, "conditions": []},
            {"name": "Goblin3", "hp": 7, "max_hp": 7, "initiative": 5,
             "is_player": False, "conditions": []},
        ]
        action = comp_mod.companion_ai(wizard, session)
        self.assertEqual(action["action"], "spell")
        self.assertEqual(action["spell"], "Fireball")

    def test_wizard_no_fireball_with_1_enemy(self):
        wizard = self._wizard()
        session = _session_with_combat(companion=wizard)
        action = comp_mod.companion_ai(wizard, session)
        self.assertNotEqual(action.get("spell"), "Fireball")

    def test_bard_inspiration_round_1(self):
        bard = self._bard()
        session = _session_with_combat(companion=bard)
        session["round"] = 1
        action = comp_mod.companion_ai(bard, session)
        self.assertEqual(action["action"], "feature")
        self.assertEqual(action["feature"], "Bardic Inspiration")
        self.assertEqual(action["target"], "Player")

    def test_paladin_lay_on_hands_for_dying(self):
        paladin = self._paladin()
        session = _session_with_combat(player_hp=0, companion=paladin)
        action = comp_mod.companion_ai(paladin, session)
        self.assertEqual(action["action"], "feature")
        self.assertEqual(action["feature"], "Lay on Hands")

    def test_rogue_sneak_attack_flag(self):
        rogue = self._rogue()
        session = _session_with_combat(companion=rogue)
        action = comp_mod.companion_ai(rogue, session)
        self.assertEqual(action["action"], "attack")
        self.assertTrue(action.get("sneak_attack"))

    def test_ai_returns_none_when_no_enemies(self):
        cleric = self._cleric()
        session = _session_with_combat(companion=cleric)
        # Kill the only enemy
        session["initiative_order"][-1]["hp"] = 0
        # Remove Goblin from list entirely
        session["initiative_order"] = [
            e for e in session["initiative_order"]
            if e.get("is_player") or e.get("is_companion")
        ]
        action = comp_mod.companion_ai(cleric, session)
        self.assertEqual(action["action"], "none")

    def test_ai_returns_none_when_companion_dead(self):
        cleric = self._cleric()
        cleric["status"] = "dead"
        session = _session_with_combat(companion=cleric)
        action = comp_mod.companion_ai(cleric, session)
        self.assertEqual(action["action"], "none")

    def test_spell_use_decrements_slot(self):
        cleric = self._cleric()
        session = _session_with_combat(player_hp=0, companion=cleric)
        before = cleric["spell_slots"]["1"]["used"]
        action = comp_mod.companion_ai(cleric, session)
        after = cleric["spell_slots"]["1"]["used"]
        if action["action"] == "spell" and action.get("slot_level", 0) >= 1:
            self.assertEqual(after, before + 1)


# ─────────────────────────────────────────────────────────────────────────────
# 8. game_state.py — enemies_alive & empty_session
# ─────────────────────────────────────────────────────────────────────────────

class TestGameState(unittest.TestCase):

    def test_empty_session_has_companions(self):
        s = gs.empty_session()
        self.assertIn("companions", s)
        self.assertEqual(s["companions"], [])

    def test_enemies_alive_true_with_enemy(self):
        s = gs.empty_session()
        s["in_combat"] = True
        s["initiative_order"] = [
            {"name": "Player", "hp": 10, "is_player": True},
            {"name": "Goblin", "hp": 5,  "is_player": False},
        ]
        self.assertTrue(gs.enemies_alive(s))

    def test_enemies_alive_false_enemy_at_0(self):
        s = gs.empty_session()
        s["initiative_order"] = [
            {"name": "Player", "hp": 10, "is_player": True},
            {"name": "Goblin", "hp": 0,  "is_player": False},
        ]
        self.assertFalse(gs.enemies_alive(s))

    def test_enemies_alive_false_when_only_companion_alive(self):
        """Companions must not be counted as enemies."""
        s = gs.empty_session()
        s["initiative_order"] = [
            {"name": "Player",     "hp": 0,  "is_player": True},
            {"name": "Elara Voss", "hp": 20, "is_player": False, "is_companion": True},
            {"name": "Goblin",     "hp": 0,  "is_player": False},
        ]
        self.assertFalse(gs.enemies_alive(s))

    def test_enemies_alive_true_when_companion_and_enemy_alive(self):
        s = gs.empty_session()
        s["initiative_order"] = [
            {"name": "Player",     "hp": 10, "is_player": True},
            {"name": "Elara Voss", "hp": 20, "is_player": False, "is_companion": True},
            {"name": "Goblin",     "hp": 5,  "is_player": False},
        ]
        self.assertTrue(gs.enemies_alive(s))


# ─────────────────────────────────────────────────────────────────────────────
# 9. dm.py — COMPANION tag parsing & system prompt
# ─────────────────────────────────────────────────────────────────────────────

class TestDMIntegration(unittest.TestCase):

    def setUp(self):
        self.dm = dm_mod.DungeonMaster()

    def _parse(self, text):
        """Return (narration, events) from _parse_events."""
        return self.dm._parse_events(text)

    def test_companion_tag_parsed(self):
        _, events = self._parse("A stranger steps forward. [COMPANION: Elara Voss]")
        types = [e["type"] for e in events]
        self.assertIn("companion_join", types)

    def test_companion_tag_name_extracted(self):
        _, events = self._parse("[COMPANION: Varen Ashcloak]")
        join = next(e for e in events if e["type"] == "companion_join")
        self.assertEqual(join["name"], "Varen Ashcloak")

    def test_companion_tag_stripped_from_narration(self):
        raw = "A figure approaches. [COMPANION: Mira Swifthand] She nods."
        narration, _ = self._parse(raw)
        self.assertNotIn("[COMPANION:", narration)

    def test_multiple_companion_tags(self):
        raw = "[COMPANION: Elara Voss] ... [COMPANION: Mira Swifthand]"
        _, events = self._parse(raw)
        joins = [e for e in events if e["type"] == "companion_join"]
        self.assertEqual(len(joins), 2)

    def test_companion_tag_case_insensitive(self):
        _, events = self._parse("[companion: Zephyra Coldwell]")
        joins = [e for e in events if e["type"] == "companion_join"]
        self.assertEqual(len(joins), 1)

    def test_system_prompt_has_companion_section(self):
        session = gs.empty_session()
        t = comp_mod.find_companion_template("Elara Voss")
        session["companions"] = [comp_mod.build_companion_at_level(t, 3)]
        char = {
            "name": "Aldric", "race": "Human", "class": "Fighter",
            "subclass": "", "level": 3, "background": "Soldier",
            "abilities": {k: 10 for k in
                          ["strength","dexterity","constitution",
                           "intelligence","wisdom","charisma"]},
            "personality_traits": "", "bonds": "",
        }
        prompt = self.dm._build_system_prompt(char, session)
        self.assertIn("COMPANION SYSTEM", prompt)
        self.assertIn("Elara Voss", prompt)
        self.assertIn("Voss", prompt)   # surname present

    def test_system_prompt_no_duplicates_rule(self):
        session = gs.empty_session()
        t = comp_mod.find_companion_template("Elara Voss")
        session["companions"] = [comp_mod.build_companion_at_level(t, 3)]
        char = {
            "name": "Aldric", "race": "Human", "class": "Fighter",
            "subclass": "", "level": 3, "background": "Soldier",
            "abilities": {k: 10 for k in
                          ["strength","dexterity","constitution",
                           "intelligence","wisdom","charisma"]},
            "personality_traits": "", "bonds": "",
        }
        prompt = self.dm._build_system_prompt(char, session)
        # Cleric should not appear in available list (already in party)
        # Fighter should not appear (player class)
        # Find the "Available companions" line
        self.assertIn("Available companions:", prompt)
        import re
        avail_line = re.search(r"Available companions: (.+)", prompt)
        self.assertIsNotNone(avail_line)
        avail_text = avail_line.group(1)
        self.assertNotIn("Fighter", avail_text)
        self.assertNotIn("Cleric",  avail_text)

    def test_system_prompt_no_companions_solo(self):
        session = gs.empty_session()
        char = {
            "name": "Aldric", "race": "Human", "class": "Fighter",
            "subclass": "", "level": 3, "background": "Soldier",
            "abilities": {k: 10 for k in
                          ["strength","dexterity","constitution",
                           "intelligence","wisdom","charisma"]},
            "personality_traits": "", "bonds": "",
        }
        prompt = self.dm._build_system_prompt(char, session)
        self.assertIn("traveling alone", prompt)

    def test_system_prompt_party_full_blocks_new(self):
        session = gs.empty_session()
        templates = ["Elara Voss", "Mira Swifthand", "Varen Ashcloak"]
        for name in templates:
            t = comp_mod.find_companion_template(name)
            session["companions"].append(comp_mod.build_companion_at_level(t, 3))
        char = {
            "name": "Z", "race": "Human", "class": "Wizard",
            "subclass": "", "level": 3, "background": "",
            "abilities": {k: 10 for k in
                          ["strength","dexterity","constitution",
                           "intelligence","wisdom","charisma"]},
            "personality_traits": "", "bonds": "",
        }
        prompt = self.dm._build_system_prompt(char, session)
        self.assertIn("full capacity", prompt)


# ─────────────────────────────────────────────────────────────────────────────
# 10. Integration: death save logic
# ─────────────────────────────────────────────────────────────────────────────

class TestDeathSaveLogic(unittest.TestCase):
    """Unit tests for the death save state machine (not the UI)."""

    def _process_save(self, comp, roll):
        """Simulate what _do_companion_death_save does to comp's death_saves."""
        ds = comp.setdefault("death_saves", {"successes": 0, "failures": 0})
        if roll == 20:
            comp["status"] = "active"
            comp["hp"]["current"] = 1
            ds["successes"] = 0
            ds["failures"]  = 0
        elif roll >= 10:
            ds["successes"] = min(3, ds["successes"] + 1)
            if ds["successes"] >= 3:
                comp["status"] = "active"
        elif roll == 1:
            ds["failures"] = min(3, ds["failures"] + 2)
            if ds["failures"] >= 3:
                comp["status"]        = "dead"
                comp["dead_at_scene"] = "Test"
        else:
            ds["failures"] = min(3, ds["failures"] + 1)
            if ds["failures"] >= 3:
                comp["status"]        = "dead"
                comp["dead_at_scene"] = "Test"

    def _make_comp(self):
        t = comp_mod.find_companion_template("Varen Ashcloak")
        c = comp_mod.build_companion_at_level(t, 3)
        c["hp"]["current"] = 0
        c["status"] = "unconscious"
        return c

    def test_three_successes_stabilize(self):
        c = self._make_comp()
        self._process_save(c, 15)
        self._process_save(c, 12)
        self._process_save(c, 14)
        self.assertEqual(c["status"], "active")

    def test_three_failures_kill(self):
        c = self._make_comp()
        self._process_save(c, 5)
        self._process_save(c, 3)
        self._process_save(c, 2)
        self.assertEqual(c["status"], "dead")
        self.assertIsNotNone(c["dead_at_scene"])

    def test_nat_20_revives_at_1_hp(self):
        c = self._make_comp()
        self._process_save(c, 20)
        self.assertEqual(c["status"], "active")
        self.assertEqual(c["hp"]["current"], 1)

    def test_nat_1_counts_as_two_failures(self):
        c = self._make_comp()
        self._process_save(c, 1)
        self.assertEqual(c["death_saves"]["failures"], 2)

    def test_nat_1_twice_kills(self):
        c = self._make_comp()
        self._process_save(c, 1)
        self._process_save(c, 1)
        self.assertEqual(c["status"], "dead")

    def test_successes_cap_at_3(self):
        c = self._make_comp()
        for _ in range(5):
            self._process_save(c, 15)
        self.assertLessEqual(c["death_saves"]["successes"], 3)

    def test_failures_cap_at_3(self):
        c = self._make_comp()
        for _ in range(5):
            self._process_save(c, 4)
        self.assertLessEqual(c["death_saves"]["failures"], 3)


# ─────────────────────────────────────────────────────────────────────────────
# 11. Scene change — dead card removal
# ─────────────────────────────────────────────────────────────────────────────

class TestSceneChange(unittest.TestCase):

    def _scene_change(self, session):
        """Replicate _on_scene_change dead-card cleanup logic from app.py."""
        companions = session.get("companions", [])
        session["companions"] = [
            c for c in companions
            if not (c.get("status") == "dead" and c.get("dead_at_scene") is not None)
        ]

    def test_dead_companion_removed_on_scene_change(self):
        session = gs.empty_session()
        t = comp_mod.find_companion_template("Varen Ashcloak")
        c = comp_mod.build_companion_at_level(t, 3)
        c["status"]        = "dead"
        c["dead_at_scene"] = "The Old Mill"
        session["companions"] = [c]
        self._scene_change(session)
        self.assertEqual(len(session["companions"]), 0)

    def test_alive_companion_not_removed(self):
        session = gs.empty_session()
        t = comp_mod.find_companion_template("Varen Ashcloak")
        c = comp_mod.build_companion_at_level(t, 3)
        session["companions"] = [c]
        self._scene_change(session)
        self.assertEqual(len(session["companions"]), 1)

    def test_dead_without_scene_not_removed(self):
        """Companion who just died (dead_at_scene not yet set) stays through the scene."""
        session = gs.empty_session()
        t = comp_mod.find_companion_template("Varen Ashcloak")
        c = comp_mod.build_companion_at_level(t, 3)
        c["status"]        = "dead"
        c["dead_at_scene"] = None   # not yet assigned
        session["companions"] = [c]
        self._scene_change(session)
        self.assertEqual(len(session["companions"]), 1)

    def test_mixed_party_only_removes_dead(self):
        session = gs.empty_session()
        t1 = comp_mod.find_companion_template("Varen Ashcloak")
        t2 = comp_mod.find_companion_template("Elara Voss")
        c1 = comp_mod.build_companion_at_level(t1, 3)
        c2 = comp_mod.build_companion_at_level(t2, 3)
        c1["status"]        = "dead"
        c1["dead_at_scene"] = "Tavern"
        session["companions"] = [c1, c2]
        self._scene_change(session)
        remaining = [c["name"] for c in session["companions"]]
        self.assertEqual(remaining, ["Elara Voss"])


# ─────────────────────────────────────────────────────────────────────────────
# 12. Rest recovery
# ─────────────────────────────────────────────────────────────────────────────

class TestCompanionRest(unittest.TestCase):
    """Replicate the _companion_long_rest and _companion_short_rest logic."""

    def _long_rest(self, session):
        for comp in session.get("companions", []):
            if comp.get("status") == "dead":
                continue
            comp["hp"]["current"] = comp["hp"]["max"]
            if comp.get("status") == "unconscious":
                comp["status"] = "active"
                comp["death_saves"] = {"successes": 0, "failures": 0}
            for data in comp.get("spell_slots", {}).values():
                data["used"] = 0
            for feat_data in comp.get("feature_uses", {}).values():
                if feat_data.get("recharge") in ("long", "short", "turn"):
                    feat_data["current"] = feat_data["max"]

    def _short_rest(self, session):
        import math
        from models.companions import _HIT_DICE, _mod
        for comp in session.get("companions", []):
            if comp.get("status") == "dead":
                continue
            for feat_data in comp.get("feature_uses", {}).values():
                if feat_data.get("recharge") == "short":
                    feat_data["current"] = feat_data["max"]
            hd      = _HIT_DICE.get(comp["class"], 8)
            con_mod = _mod(comp["abilities"].get("constitution", 10))
            gained  = max(1, hd // 2 + 1 + con_mod)
            comp["hp"]["current"] = min(comp["hp"]["max"],
                                        comp["hp"]["current"] + gained)

    def _build_wounded_cleric(self):
        t = comp_mod.find_companion_template("Elara Voss")
        c = comp_mod.build_companion_at_level(t, 5)
        c["hp"]["current"] = 5
        # Spend some slots
        c["spell_slots"]["1"]["used"] = 3
        c["spell_slots"]["2"]["used"] = 1
        c["feature_uses"]["Channel Divinity"]["current"] = 0
        return c

    def test_long_rest_restores_hp(self):
        session = gs.empty_session()
        c = self._build_wounded_cleric()
        session["companions"] = [c]
        self._long_rest(session)
        self.assertEqual(c["hp"]["current"], c["hp"]["max"])

    def test_long_rest_restores_spell_slots(self):
        session = gs.empty_session()
        c = self._build_wounded_cleric()
        session["companions"] = [c]
        self._long_rest(session)
        for lvl, data in c["spell_slots"].items():
            self.assertEqual(data["used"], 0, f"L{lvl} slots not restored")

    def test_long_rest_restores_features(self):
        session = gs.empty_session()
        c = self._build_wounded_cleric()
        session["companions"] = [c]
        self._long_rest(session)
        self.assertEqual(c["feature_uses"]["Channel Divinity"]["current"],
                         c["feature_uses"]["Channel Divinity"]["max"])

    def test_long_rest_revives_unconscious(self):
        session = gs.empty_session()
        c = self._build_wounded_cleric()
        c["status"] = "unconscious"
        c["death_saves"] = {"successes": 2, "failures": 1}
        session["companions"] = [c]
        self._long_rest(session)
        self.assertEqual(c["status"], "active")
        self.assertEqual(c["death_saves"]["successes"], 0)

    def test_long_rest_skips_dead_companion(self):
        session = gs.empty_session()
        c = self._build_wounded_cleric()
        c["status"] = "dead"
        old_hp = c["hp"]["current"]
        session["companions"] = [c]
        self._long_rest(session)
        self.assertEqual(c["hp"]["current"], old_hp)  # unchanged

    def test_short_rest_restores_short_rest_features(self):
        session = gs.empty_session()
        t = comp_mod.find_companion_template("Varen Ashcloak")
        c = comp_mod.build_companion_at_level(t, 5)
        c["feature_uses"]["Second Wind"]["current"] = 0
        session["companions"] = [c]
        self._short_rest(session)
        self.assertEqual(c["feature_uses"]["Second Wind"]["current"], 1)

    def test_short_rest_heals_some_hp(self):
        session = gs.empty_session()
        t = comp_mod.find_companion_template("Varen Ashcloak")
        c = comp_mod.build_companion_at_level(t, 5)
        c["hp"]["current"] = 1
        session["companions"] = [c]
        self._short_rest(session)
        self.assertGreater(c["hp"]["current"], 1)

    def test_short_rest_doesnt_overflow_max_hp(self):
        session = gs.empty_session()
        t = comp_mod.find_companion_template("Varen Ashcloak")
        c = comp_mod.build_companion_at_level(t, 5)
        c["hp"]["current"] = c["hp"]["max"]
        session["companions"] = [c]
        self._short_rest(session)
        self.assertLessEqual(c["hp"]["current"], c["hp"]["max"])


# ─────────────────────────────────────────────────────────────────────────────
# Run
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    unittest.main(verbosity=2)
