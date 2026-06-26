"""Tests for models/combat.py — attack resolution, death saves, XP, summaries."""

import pytest
from models.combat import (
    build_enemy, setup_combat, resolve_attack, player_attack,
    enemy_attack, handle_death_save, xp_from_combat, combat_summary,
)
from models.game_state import empty_session, start_combat
from models.character import empty_character


def _char(name="Hero", hp=10, ac=14, dex=12, level=1):
    c = empty_character()
    c["name"] = name
    c["level"] = level
    c["hp"] = {"max": hp, "current": hp, "temp": 0}
    c["armor_class"] = ac
    c["abilities"]["dexterity"] = dex
    c["attacks"] = [{"name": "Longsword", "damage": "1d8+3", "attack_bonus": 5}]
    return c


def _enemy_dict(name="Goblin", hp=7, ac=13, xp=50):
    return build_enemy(name, hp, ac,
                       [{"name": "Scimitar", "damage": "1d6+2", "bonus": 4}],
                       xp=xp)


def _ready_session(char, enemies):
    s = empty_session(char["name"])
    s["current_hp"] = char["hp"]["current"]
    setup_combat(s, char, enemies)
    return s


class TestBuildEnemy:
    def test_shape(self):
        e = _enemy_dict()
        assert e["name"] == "Goblin"
        assert e["hp"] == 7
        assert e["max_hp"] == 7
        assert e["ac"] == 13
        assert e["xp"] == 50
        assert e["is_player"] is False
        assert e["conditions"] == []

    def test_no_xp_defaults_zero(self):
        e = build_enemy("Rat", 2, 10, [])
        assert e["xp"] == 0


class TestResolveAttack:
    def _session(self):
        c = _char()
        enemies = [_enemy_dict()]
        return _ready_session(c, enemies), c

    def test_nat20_always_hits(self):
        s, _ = self._session()
        r = resolve_attack(s, "Hero", "Goblin", 0, "1d6", d20_override=20)
        assert r["hit"] is True
        assert r["critical"] is True

    def test_nat1_always_misses(self):
        s, _ = self._session()
        r = resolve_attack(s, "Hero", "Goblin", 100, "1d6", d20_override=1)
        assert r["hit"] is False
        assert r["damage"] is None

    def test_hit_above_ac(self):
        s, _ = self._session()
        # Goblin AC=13, roll+bonus=15 → hit
        r = resolve_attack(s, "Hero", "Goblin", 0, "1d6", d20_override=15)
        assert r["hit"] is True

    def test_miss_below_ac(self):
        s, _ = self._session()
        # Goblin AC=13, roll=5+0=5 → miss
        r = resolve_attack(s, "Hero", "Goblin", 0, "1d6", d20_override=5)
        assert r["hit"] is False

    def test_hit_deals_pre_damage(self):
        s, _ = self._session()
        pre = {"total": 4, "rolls": [4], "modifier": 0}
        r = resolve_attack(s, "Hero", "Goblin", 5, "1d6",
                           d20_override=15, pre_damage=pre)
        assert r["hit"] is True
        assert r["new_hp"] == 3  # 7 - 4

    def test_overkill_sets_killed(self):
        s, _ = self._session()
        pre = {"total": 20, "rolls": [20], "modifier": 0}
        r = resolve_attack(s, "Hero", "Goblin", 5, "1d6",
                           d20_override=15, pre_damage=pre)
        assert r["killed"] is True
        assert r["new_hp"] == 0

    def test_unknown_target_returns_error(self):
        s = empty_session()
        s["initiative_order"] = []
        r = resolve_attack(s, "Hero", "Nobody", 0, "1d6")
        assert "error" in r

    def test_result_shape(self):
        s, _ = self._session()
        r = resolve_attack(s, "Hero", "Goblin", 0, "1d6", d20_override=5)
        for key in ("attacker", "target", "target_ac", "roll", "hit",
                    "damage", "new_hp", "killed", "critical"):
            assert key in r, f"Missing result key: {key}"


class TestPlayerAttack:
    def test_weapon_not_found_returns_error(self):
        c = _char()
        s = _ready_session(c, [_enemy_dict()])
        r = player_attack(s, c, "NonexistentWeapon", "Goblin")
        assert "error" in r

    def test_valid_attack(self):
        c = _char()
        s = _ready_session(c, [_enemy_dict()])
        r = player_attack(s, c, "Longsword", "Goblin",
                          d20_override=18,
                          pre_damage={"total": 5, "rolls": [2], "modifier": 3})
        assert r["weapon"] == "Longsword"
        assert r["hit"] is True


class TestEnemyAttack:
    def test_returns_result(self):
        c = _char()
        s = _ready_session(c, [_enemy_dict()])
        r = enemy_attack(s, "Goblin", attack_index=0)
        assert "hit" in r
        assert r["weapon"] == "Scimitar"

    def test_enemy_not_found(self):
        s = empty_session()
        s["initiative_order"] = []
        r = enemy_attack(s, "Nobody")
        assert "error" in r

    def test_enemy_no_attacks(self):
        s = empty_session()
        s["current_hp"] = 10
        s["initiative_order"] = [
            {"name": "Player", "initiative": 10, "hp": 10, "max_hp": 10,
             "ac": 14, "is_player": True, "conditions": []},
            {"name": "Rat",    "initiative":  5, "hp":  2, "max_hp":  2,
             "ac": 10, "attacks": [], "is_player": False, "conditions": [], "xp": 5},
        ]
        r = enemy_attack(s, "Rat")
        assert "error" in r


class TestHandleDeathSave:
    def _session(self):
        s = empty_session()
        s["current_hp"] = 0
        s["death_saves"] = {"successes": 0, "failures": 0}
        return s

    def _roll(self, value, success=None, critical=False, double_fail=False):
        if success is None:
            success = value >= 10
        return {"roll": value, "success": success,
                "critical": critical, "double_fail": double_fail}

    def test_critical_revives(self):
        s = self._session()
        r = handle_death_save(s, pre_roll=self._roll(20, critical=True))
        assert r["outcome"] == "revived"
        assert s["current_hp"] == 1
        assert s["death_saves"]["successes"] == 0

    def test_three_successes_stabilize(self):
        s = self._session()
        s["death_saves"]["successes"] = 2
        r = handle_death_save(s, pre_roll=self._roll(15))
        assert r["outcome"] == "stable"
        assert s["stable"] is True

    def test_three_failures_dead(self):
        s = self._session()
        s["death_saves"]["failures"] = 2
        r = handle_death_save(s, pre_roll=self._roll(5, success=False))
        assert r["outcome"] == "dead"

    def test_nat1_double_fail(self):
        s = self._session()
        s["death_saves"]["failures"] = 1
        r = handle_death_save(s, pre_roll=self._roll(1, success=False, double_fail=True))
        assert r["outcome"] == "dead"
        assert s["death_saves"]["failures"] == 3

    def test_ongoing_success(self):
        s = self._session()
        r = handle_death_save(s, pre_roll=self._roll(12))
        assert r["outcome"] == "ongoing"
        assert s["death_saves"]["successes"] == 1

    def test_ongoing_failure(self):
        s = self._session()
        r = handle_death_save(s, pre_roll=self._roll(5, success=False))
        assert r["outcome"] == "ongoing"
        assert s["death_saves"]["failures"] == 1


class TestXpFromCombat:
    def _session_with(self, combatants):
        s = empty_session()
        s["initiative_order"] = combatants
        return s

    def test_sums_dead_enemy_xp(self):
        s = self._session_with([
            {"name": "Player", "hp": 5,  "is_player": True,  "xp": 0},
            {"name": "Goblin", "hp": 0,  "is_player": False, "xp": 50},
            {"name": "Orc",    "hp": 15, "is_player": False, "xp": 100},
        ])
        assert xp_from_combat(s) == 50

    def test_player_not_counted(self):
        s = self._session_with([
            {"name": "Hero", "hp": 0, "is_player": True, "xp": 999},
        ])
        assert xp_from_combat(s) == 0

    def test_all_enemies_dead(self):
        s = self._session_with([
            {"name": "A", "hp": 0, "is_player": False, "xp": 25},
            {"name": "B", "hp": 0, "is_player": False, "xp": 75},
        ])
        assert xp_from_combat(s) == 100

    def test_no_enemies(self):
        s = self._session_with([])
        assert xp_from_combat(s) == 0


class TestCombatSummary:
    def test_shape(self):
        c = _char()
        s = _ready_session(c, [_enemy_dict()])
        summary = combat_summary(s)
        assert "round" in summary
        assert "current_turn" in summary
        assert "combatants" in summary
        assert "enemies_alive" in summary
        assert "player_alive" in summary

    def test_enemies_alive_flag(self):
        c = _char()
        s = _ready_session(c, [_enemy_dict(hp=7)])
        assert combat_summary(s)["enemies_alive"] is True

    def test_player_alive_flag(self):
        c = _char(hp=10)
        s = _ready_session(c, [_enemy_dict()])
        assert combat_summary(s)["player_alive"] is True
