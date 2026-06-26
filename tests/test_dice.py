"""Tests for models/dice.py — rolling, crits, advantage/disadvantage."""

from unittest.mock import patch
import pytest
from models.dice import (
    roll, roll_dice, d20_check, damage, critical_damage,
    hit_die, death_save, initiative,
)


class TestRoll:
    def test_result_in_range(self):
        for sides in (4, 6, 8, 10, 12, 20, 100):
            r = roll(sides)
            assert 1 <= r <= sides

    def test_invalid_die_raises(self):
        with pytest.raises(ValueError):
            roll(7)

    def test_die_3_raises(self):
        with pytest.raises(ValueError):
            roll(3)


class TestRollDice:
    def test_parses_notation(self):
        r = roll_dice("2d6")
        assert len(r["rolls"]) == 2
        assert r["modifier"] == 0

    def test_modifier_added(self):
        with patch("random.randint", return_value=3):
            r = roll_dice("1d6+4")
        assert r["total"] == 7
        assert r["modifier"] == 4

    def test_negative_modifier(self):
        with patch("random.randint", return_value=5):
            r = roll_dice("1d8-2")
        assert r["total"] == 3

    def test_implicit_one_die(self):
        r = roll_dice("d20")
        assert len(r["rolls"]) == 1

    def test_invalid_notation_raises(self):
        with pytest.raises(ValueError):
            roll_dice("garbage")

    def test_invalid_die_sides_raises(self):
        with pytest.raises(ValueError):
            roll_dice("1d7")

    def test_count_zero_raises(self):
        with pytest.raises(ValueError):
            roll_dice("0d6")

    def test_notation_preserved_in_result(self):
        r = roll_dice("2d6+3")
        assert "2d6+3" in r["notation"]


class TestD20Check:
    def test_result_shape(self):
        r = d20_check(modifier=3)
        assert "rolls" in r and "kept" in r and "total" in r
        assert "nat20" in r and "nat1" in r
        assert r["modifier"] == 3
        assert r["total"] == r["kept"] + 3

    def test_advantage_picks_higher(self):
        with patch("random.randint", side_effect=[5, 15]):
            r = d20_check(advantage=True)
        assert r["kept"] == 15
        assert len(r["rolls"]) == 2

    def test_disadvantage_picks_lower(self):
        with patch("random.randint", side_effect=[15, 5]):
            r = d20_check(disadvantage=True)
        assert r["kept"] == 5

    def test_both_cancel_to_normal(self):
        with patch("random.randint", return_value=10):
            r = d20_check(advantage=True, disadvantage=True)
        assert len(r["rolls"]) == 1

    def test_nat20(self):
        with patch("random.randint", return_value=20):
            r = d20_check()
        assert r["nat20"] is True
        assert r["nat1"] is False

    def test_nat1(self):
        with patch("random.randint", return_value=1):
            r = d20_check()
        assert r["nat1"] is True
        assert r["nat20"] is False


class TestCriticalDamage:
    def test_doubles_dice_count(self):
        with patch("random.randint", return_value=4):
            r = critical_damage("2d6+3")
        assert len(r["rolls"]) == 4
        assert r["critical"] is True
        assert r["modifier"] == 3

    def test_single_die_doubled(self):
        with patch("random.randint", return_value=1):
            r = critical_damage("1d8")
        assert len(r["rolls"]) == 2

    def test_negative_modifier_preserved(self):
        with patch("random.randint", return_value=1):
            r = critical_damage("1d8-1")
        assert r["modifier"] == -1


class TestHitDie:
    def test_result_in_range(self):
        r = hit_die("d8")
        assert r["total"] >= 1

    def test_minimum_result_is_1(self):
        with patch("random.randint", return_value=1):
            r = hit_die("d8", con_mod=-5)
        assert r["total"] == 1

    def test_con_mod_added(self):
        with patch("random.randint", return_value=4):
            r = hit_die("d8", con_mod=2)
        assert r["total"] == 6

    def test_1d8_notation_accepted(self):
        r = hit_die("1d8")
        assert r["total"] >= 1

    def test_invalid_die_raises(self):
        with pytest.raises(ValueError):
            hit_die("d7")

    def test_invalid_notation_raises(self):
        with pytest.raises(ValueError):
            hit_die("2d8")  # only single hit die allowed


class TestDeathSave:
    def test_shape(self):
        r = death_save()
        assert "roll" in r
        assert "success" in r
        assert "critical" in r
        assert "double_fail" in r

    def test_10_is_success(self):
        with patch("random.randint", return_value=10):
            r = death_save()
        assert r["success"] is True
        assert r["critical"] is False
        assert r["double_fail"] is False

    def test_9_is_failure(self):
        with patch("random.randint", return_value=9):
            r = death_save()
        assert r["success"] is False

    def test_nat20_is_critical(self):
        with patch("random.randint", return_value=20):
            r = death_save()
        assert r["critical"] is True
        assert r["success"] is True

    def test_nat1_is_double_fail(self):
        with patch("random.randint", return_value=1):
            r = death_save()
        assert r["double_fail"] is True
        assert r["success"] is False


class TestInitiative:
    def test_total_includes_mod(self):
        with patch("random.randint", return_value=12):
            r = initiative(dex_mod=3)
        assert r["total"] == 15
        assert r["roll"] == 12
        assert r["modifier"] == 3

    def test_negative_mod(self):
        with patch("random.randint", return_value=10):
            r = initiative(dex_mod=-2)
        assert r["total"] == 8
