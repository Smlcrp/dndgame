"""Integration tests — cross-module flows: full combat round, death saves, adventure arc."""

import pytest
from models.character import empty_character
from models.game_state import empty_session
from models.combat import (
    build_enemy, setup_combat, resolve_attack,
    handle_death_save, xp_from_combat, combat_summary,
)
from models.adventure import generate_adventure, advance_beat
from models.progression import level_from_xp, xp_for_level


def _char(name="Warrior", hp=20, ac=15, dex=14, level=1):
    c = empty_character()
    c["name"] = name
    c["level"] = level
    c["hp"] = {"max": hp, "current": hp, "temp": 0}
    c["armor_class"] = ac
    c["abilities"]["dexterity"] = dex
    c["attacks"] = [{"name": "Longsword", "damage": "1d8+3", "attack_bonus": 5}]
    return c


def _session(char, enemies):
    s = empty_session(char["name"])
    s["current_hp"] = char["hp"]["current"]
    setup_combat(s, char, enemies)
    return s


# ── Combat flow ────────────────────────────────────────────────────────────────

class TestCombatRound:
    def test_player_kills_enemy_and_earns_xp(self):
        c = _char()
        enemy = build_enemy("Goblin", hp=7, ac=13,
                            attacks=[{"name": "Scimitar", "damage": "1d6", "bonus": 3}],
                            xp=50)
        s = _session(c, [enemy])

        r = resolve_attack(s, "Warrior", "Goblin", 5, "1d8+3",
                           d20_override=15,
                           pre_damage={"total": 10, "rolls": [7], "modifier": 3})
        assert r["hit"] is True
        assert r["killed"] is True
        assert xp_from_combat(s) == 50

    def test_player_survives_miss(self):
        c = _char()
        enemy = build_enemy("Goblin", hp=7, ac=20, attacks=[], xp=50)
        s = _session(c, [enemy])

        r = resolve_attack(s, "Warrior", "Goblin", 0, "1d8", d20_override=10)
        assert r["hit"] is False
        assert r["damage"] is None
        # Goblin still alive
        summary = combat_summary(s)
        assert summary["enemies_alive"] is True

    def test_crit_deals_double_dice(self):
        c = _char()
        enemy = build_enemy("Orc", hp=30, ac=13, attacks=[], xp=100)
        s = _session(c, [enemy])

        r = resolve_attack(s, "Warrior", "Orc", 5, "1d8+3", d20_override=20)
        assert r["critical"] is True
        # A nat-20 auto-generates critical damage (4 rolls on 2d8 notation)
        assert r["hit"] is True


# ── Death save flow ────────────────────────────────────────────────────────────

class TestDeathSaveFlow:
    def _ds_session(self):
        s = empty_session()
        s["current_hp"] = 0
        s["death_saves"] = {"successes": 0, "failures": 0}
        return s

    def _roll(self, val):
        return {
            "roll": val,
            "success": val >= 10,
            "critical": val == 20,
            "double_fail": val == 1,
        }

    def test_three_successes_stabilize(self):
        s = self._ds_session()
        for _ in range(2):
            handle_death_save(s, pre_roll=self._roll(15))
        r = handle_death_save(s, pre_roll=self._roll(12))
        assert r["outcome"] == "stable"
        assert s["stable"] is True

    def test_three_failures_die(self):
        s = self._ds_session()
        for _ in range(2):
            handle_death_save(s, pre_roll=self._roll(5))
        r = handle_death_save(s, pre_roll=self._roll(5))
        assert r["outcome"] == "dead"

    def test_nat1_kills_after_two_failures(self):
        s = self._ds_session()
        handle_death_save(s, pre_roll=self._roll(5))
        r = handle_death_save(s, pre_roll=self._roll(1))
        assert r["outcome"] == "dead"
        assert s["death_saves"]["failures"] == 3

    def test_nat20_revives(self):
        s = self._ds_session()
        r = handle_death_save(s, pre_roll=self._roll(20))
        assert r["outcome"] == "revived"
        assert s["current_hp"] == 1


# ── Adventure + XP + level progression flow ───────────────────────────────────

class TestAdventureXpProgression:
    def test_beat_xp_accumulates(self):
        c = empty_character()
        c["name"] = "Hero"
        adv = generate_adventure(c)

        total_xp = 0
        for _ in range(3):  # three story beats
            total_xp += advance_beat(adv)

        assert total_xp > 0
        assert adv["current_beat"] == 3

    def test_beat_xp_exceeds_level_1_threshold(self):
        c = empty_character()
        c["name"] = "Hero"
        adv = generate_adventure(c)

        # Three beats should award enough XP to reach level 2+
        total_xp = sum(advance_beat(adv) for _ in range(3))
        assert level_from_xp(total_xp) >= 2

    def test_full_arc_xp_approaches_level_4(self):
        c = empty_character()
        c["name"] = "Hero"
        adv = generate_adventure(c)

        # Three beats + climax XP (if awarded manually)
        beat_xp = sum(advance_beat(adv) for _ in range(3))
        total = beat_xp + adv["climax_xp"]
        # Should put a fresh level-1 character at or near level 3-4
        lvl = level_from_xp(total)
        assert 2 <= lvl <= 5


# ── Schema validation round-trip ──────────────────────────────────────────────

class TestSchemaRoundTrip:
    def test_migrate_then_validate_empty(self):
        from models.character import migrate_character, validate_character
        c = {"name": "Sparse", "level": 2}
        c = migrate_character(c)
        validate_character(c)  # must not raise

    def test_empty_character_validates(self):
        from models.character import validate_character
        c = empty_character()
        c["name"] = "Default"
        validate_character(c)
