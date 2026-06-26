"""Tests for models/game_state.py — session state, HP, combat, conditions."""

import pytest
from models.game_state import (
    empty_session, apply_damage, apply_healing,
    use_spell_slot, restore_spell_slot, long_rest, short_rest,
    start_combat, end_combat, advance_turn, current_combatant,
    apply_combat_damage, apply_combat_healing,
    add_condition, remove_condition,
    living_combatants, enemies_alive,
)
from models.character import empty_character


def _char(hp_max=10, level=1):
    c = empty_character()
    c["level"] = level
    c["hp"] = {"max": hp_max, "current": hp_max, "temp": 0}
    return c


def _combatants():
    return [
        {"name": "Player", "initiative": 5,  "hp": 10, "max_hp": 10, "is_player": True},
        {"name": "Goblin", "initiative": 15, "hp":  7, "max_hp":  7, "is_player": False},
        {"name": "Orc",    "initiative": 10, "hp": 15, "max_hp": 15, "is_player": False},
    ]


class TestEmptySession:
    def test_defaults(self):
        s = empty_session("Bob", "s1")
        assert s["character_name"] == "Bob"
        assert s["session_name"] == "s1"
        assert s["current_hp"] is None
        assert s["in_combat"] is False
        assert s["initiative_order"] == []
        assert s["round"] == 0


class TestApplyDamage:
    def _session(self, hp=10, temp=0):
        s = empty_session()
        s["current_hp"] = hp
        s["temp_hp"] = temp
        return s

    def test_reduces_hp(self):
        s = self._session(10)
        assert apply_damage(s, 4) == 6
        assert s["current_hp"] == 6

    def test_min_zero(self):
        s = self._session(3)
        assert apply_damage(s, 10) == 0

    def test_zero_damage_noop(self):
        s = self._session(10)
        assert apply_damage(s, 0) == 10

    def test_temp_fully_absorbs(self):
        s = self._session(10, temp=5)
        apply_damage(s, 3)
        assert s["temp_hp"] == 2
        assert s["current_hp"] == 10

    def test_damage_bleeds_through_temp(self):
        s = self._session(10, temp=2)
        apply_damage(s, 5)
        assert s["temp_hp"] == 0
        assert s["current_hp"] == 7

    def test_damage_exceeds_both(self):
        s = self._session(3, temp=2)
        apply_damage(s, 10)
        assert s["temp_hp"] == 0
        assert s["current_hp"] == 0


class TestApplyHealing:
    def _session(self, hp=5):
        s = empty_session()
        s["current_hp"] = hp
        return s

    def test_heals(self):
        assert apply_healing(self._session(5), 4, 10) == 9

    def test_caps_at_max(self):
        assert apply_healing(self._session(8), 10, 10) == 10


class TestSpellSlots:
    def test_use_increments(self):
        s = empty_session()
        use_spell_slot(s, 1)
        use_spell_slot(s, 1)
        assert s["spell_slots_used"]["1"] == 2

    def test_different_levels_tracked_separately(self):
        s = empty_session()
        use_spell_slot(s, 1)
        use_spell_slot(s, 2)
        assert s["spell_slots_used"]["1"] == 1
        assert s["spell_slots_used"]["2"] == 1

    def test_restore_decrements(self):
        s = empty_session()
        use_spell_slot(s, 2)
        restore_spell_slot(s, 2)
        assert s["spell_slots_used"]["2"] == 0

    def test_restore_when_zero_noop(self):
        s = empty_session()
        restore_spell_slot(s, 1)  # should not raise or go negative
        assert s["spell_slots_used"].get("1", 0) == 0


class TestLongRest:
    def test_restores_hp(self):
        c = _char(hp_max=10)
        s = empty_session()
        s["current_hp"] = 3
        long_rest(s, c)
        assert s["current_hp"] == 10

    def test_clears_spell_slots(self):
        c = _char()
        s = empty_session()
        s["current_hp"] = 10
        s["spell_slots_used"] = {"1": 2, "3": 1}
        long_rest(s, c)
        assert s["spell_slots_used"] == {}

    def test_clears_conditions(self):
        c = _char()
        s = empty_session()
        s["current_hp"] = 10
        s["conditions"] = ["Poisoned", "Blinded"]
        long_rest(s, c)
        assert s["conditions"] == []

    def test_resets_death_saves(self):
        c = _char()
        s = empty_session()
        s["current_hp"] = 10
        s["death_saves"] = {"successes": 1, "failures": 2}
        long_rest(s, c)
        assert s["death_saves"] == {"successes": 0, "failures": 0}

    def test_clears_temp_hp(self):
        c = _char()
        s = empty_session()
        s["current_hp"] = 10
        s["temp_hp"] = 8
        long_rest(s, c)
        assert s["temp_hp"] == 0


class TestShortRest:
    def test_heals_and_spends_die(self):
        s = empty_session()
        s["current_hp"] = 5
        s["hit_dice_spent"] = 0
        short_rest(s, hp_gained=4, max_hp=10)
        assert s["current_hp"] == 9
        assert s["hit_dice_spent"] == 1

    def test_caps_at_max_hp(self):
        s = empty_session()
        s["current_hp"] = 9
        short_rest(s, hp_gained=10, max_hp=10)
        assert s["current_hp"] == 10


class TestStartCombat:
    def test_sorts_descending(self):
        s = empty_session()
        start_combat(s, _combatants())
        names = [c["name"] for c in s["initiative_order"]]
        assert names == ["Goblin", "Orc", "Player"]

    def test_sets_in_combat_true(self):
        s = empty_session()
        start_combat(s, _combatants())
        assert s["in_combat"] is True

    def test_round_starts_at_1(self):
        s = empty_session()
        start_combat(s, _combatants())
        assert s["round"] == 1

    def test_current_turn_starts_at_0(self):
        s = empty_session()
        start_combat(s, _combatants())
        assert s["current_turn"] == 0

    def test_conditions_initialized(self):
        s = empty_session()
        start_combat(s, [{"name": "X", "initiative": 1, "hp": 5,
                          "max_hp": 5, "is_player": False}])
        assert s["initiative_order"][0]["conditions"] == []


class TestEndCombat:
    def test_clears_state(self):
        s = empty_session()
        start_combat(s, _combatants())
        end_combat(s)
        assert s["in_combat"] is False
        assert s["round"] == 0
        assert s["initiative_order"] == []


class TestAdvanceTurn:
    def _combat(self):
        s = empty_session()
        start_combat(s, [
            {"name": "A", "initiative": 20, "hp": 10, "max_hp": 10, "is_player": True},
            {"name": "B", "initiative": 10, "hp":  7, "max_hp":  7, "is_player": False},
        ])
        return s

    def test_increments_turn(self):
        s = self._combat()
        advance_turn(s)
        assert s["current_turn"] == 1

    def test_wraps_and_increments_round(self):
        s = self._combat()
        advance_turn(s)
        advance_turn(s)  # wraps to turn 0, round 2
        assert s["current_turn"] == 0
        assert s["round"] == 2

    def test_current_combatant(self):
        s = self._combat()
        c = current_combatant(s)
        assert c["name"] == "A"  # highest initiative


class TestApplyCombatDamage:
    def _session(self):
        s = empty_session()
        s["initiative_order"] = [
            {"name": "Goblin", "hp": 7, "max_hp": 7, "is_player": False},
        ]
        return s

    def test_reduces_hp(self):
        s = self._session()
        result = apply_combat_damage(s, "Goblin", 4)
        assert result == 3
        assert s["initiative_order"][0]["hp"] == 3

    def test_min_zero(self):
        s = self._session()
        result = apply_combat_damage(s, "Goblin", 20)
        assert result == 0

    def test_unknown_combatant_returns_none(self):
        s = empty_session()
        s["initiative_order"] = []
        assert apply_combat_damage(s, "Nobody", 5) is None


class TestApplyCombatHealing:
    def test_heals(self):
        s = empty_session()
        s["initiative_order"] = [
            {"name": "Player", "hp": 5, "max_hp": 10, "is_player": True},
        ]
        result = apply_combat_healing(s, "Player", 3)
        assert result == 8

    def test_caps_at_max_hp(self):
        s = empty_session()
        s["initiative_order"] = [
            {"name": "Player", "hp": 9, "max_hp": 10, "is_player": True},
        ]
        result = apply_combat_healing(s, "Player", 5)
        assert result == 10


class TestConditions:
    def _session(self):
        s = empty_session()
        s["initiative_order"] = [{"name": "Player", "hp": 10, "conditions": []}]
        return s

    def test_add_condition(self):
        s = self._session()
        add_condition(s, "Player", "Poisoned")
        assert "Poisoned" in s["initiative_order"][0]["conditions"]

    def test_no_duplicate_conditions(self):
        s = self._session()
        add_condition(s, "Player", "Poisoned")
        add_condition(s, "Player", "Poisoned")
        assert s["initiative_order"][0]["conditions"].count("Poisoned") == 1

    def test_remove_condition(self):
        s = self._session()
        s["initiative_order"][0]["conditions"] = ["Poisoned", "Blinded"]
        remove_condition(s, "Player", "Poisoned")
        assert "Poisoned" not in s["initiative_order"][0]["conditions"]
        assert "Blinded" in s["initiative_order"][0]["conditions"]


class TestLivingCombatants:
    def test_excludes_dead(self):
        s = empty_session()
        s["initiative_order"] = [
            {"name": "A", "hp": 5},
            {"name": "B", "hp": 0},
        ]
        result = living_combatants(s)
        assert len(result) == 1
        assert result[0]["name"] == "A"


class TestEnemiesAlive:
    def test_living_enemy(self):
        s = empty_session()
        s["initiative_order"] = [
            {"name": "Goblin", "hp": 3, "is_player": False},
        ]
        assert enemies_alive(s) is True

    def test_dead_enemy(self):
        s = empty_session()
        s["initiative_order"] = [
            {"name": "Goblin", "hp": 0, "is_player": False},
        ]
        assert enemies_alive(s) is False

    def test_companion_not_counted(self):
        s = empty_session()
        s["initiative_order"] = [
            {"name": "Aria", "hp": 10, "is_player": False, "is_companion": True},
        ]
        assert enemies_alive(s) is False

    def test_player_not_counted(self):
        s = empty_session()
        s["initiative_order"] = [
            {"name": "Hero", "hp": 10, "is_player": True},
        ]
        assert enemies_alive(s) is False
