"""Tests for models/progression.py — XP thresholds, ASI levels, feature charges."""

import pytest
from models.progression import (
    XP_THRESHOLDS, level_from_xp, xp_for_level, xp_to_next_level,
    is_asi_level, get_subclass_trigger, current_max_uses,
    recharges_on_short_rest, feature_charges_gained_at,
)
from models.character import empty_character


class TestLevelFromXp:
    def test_0_xp_is_level_1(self):
        assert level_from_xp(0) == 1

    def test_300_xp_is_level_2(self):
        assert level_from_xp(300) == 2

    def test_just_below_threshold(self):
        assert level_from_xp(299) == 1

    def test_6500_is_level_5(self):
        assert level_from_xp(6500) == 5

    def test_max_xp_is_level_20(self):
        assert level_from_xp(355000) == 20

    def test_beyond_max_xp_is_level_20(self):
        assert level_from_xp(999999) == 20

    def test_between_thresholds_gives_lower_level(self):
        assert level_from_xp(500) == 2

    def test_all_thresholds(self):
        for i, xp in enumerate(XP_THRESHOLDS):
            expected = i + 1
            assert level_from_xp(xp) == expected, f"level {expected} at {xp} XP failed"


class TestXpForLevel:
    def test_level_1(self):  assert xp_for_level(1) == 0
    def test_level_2(self):  assert xp_for_level(2) == 300
    def test_level_5(self):  assert xp_for_level(5) == 6500
    def test_level_20(self): assert xp_for_level(20) == 355000

    def test_clamps_below_1(self):
        assert xp_for_level(0) == xp_for_level(1)

    def test_clamps_above_20(self):
        assert xp_for_level(21) == xp_for_level(20)


class TestXpToNextLevel:
    def test_level_1_needs_300(self):
        assert xp_to_next_level(0, 1) == 300

    def test_partially_through_level(self):
        assert xp_to_next_level(100, 1) == 200

    def test_level_20_returns_zero(self):
        assert xp_to_next_level(355000, 20) == 0


class TestIsAsiLevel:
    def test_fighter_has_level_6(self):
        assert is_asi_level("Fighter", 6) is True

    def test_fighter_standard_levels(self):
        for lvl in (4, 6, 8, 12, 14, 16, 19):
            assert is_asi_level("Fighter", lvl) is True

    def test_fighter_non_asi_level(self):
        assert is_asi_level("Fighter", 5) is False

    def test_wizard_standard_levels(self):
        for lvl in (4, 8, 12, 16, 19):
            assert is_asi_level("Wizard", lvl) is True

    def test_unknown_class_always_false(self):
        assert is_asi_level("FakeClass", 4) is False


class TestGetSubclassTrigger:
    def test_cleric_level_1(self):   assert get_subclass_trigger("Cleric") == 1
    def test_sorcerer_level_1(self): assert get_subclass_trigger("Sorcerer") == 1
    def test_druid_level_2(self):    assert get_subclass_trigger("Druid") == 2
    def test_wizard_level_2(self):   assert get_subclass_trigger("Wizard") == 2
    def test_fighter_level_3(self):  assert get_subclass_trigger("Fighter") == 3
    def test_unknown_defaults_3(self): assert get_subclass_trigger("FakeClass") == 3


class TestCurrentMaxUses:
    def _char(self, cha=10, intel=10, level=1):
        c = empty_character()
        c["level"] = level
        c["abilities"]["charisma"] = cha
        c["abilities"]["intelligence"] = intel
        return c

    def test_fixed_int_barbarian_rage(self):
        c = self._char()
        assert current_max_uses("Rage", "Barbarian", 1, c) == 2

    def test_level_based_monk_ki(self):
        c = self._char()
        assert current_max_uses("Ki Points", "Monk", 5, c) == 5
        assert current_max_uses("Ki Points", "Monk", 10, c) == 10

    def test_cha_mod_bard_inspiration(self):
        c = self._char(cha=16)  # +3
        assert current_max_uses("Bardic Inspiration", "Bard", 1, c) == 3

    def test_cha_mod_min_1(self):
        c = self._char(cha=8)  # -1 → clamped to 1
        assert current_max_uses("Bardic Inspiration", "Bard", 1, c) == 1

    def test_int_mod_artificer(self):
        c = self._char(intel=16)  # +3
        assert current_max_uses("Flash of Genius", "Artificer", 7, c) == 3

    def test_5x_level_paladin(self):
        c = self._char()
        assert current_max_uses("Lay on Hands", "Paladin", 4, c) == 20

    def test_scaling_barbarian_rage(self):
        c = self._char()
        # SRD: Lv1-2=2, Lv3-5=3, Lv6-11=4, Lv12-16=5, Lv17-19=6, Lv20=unlimited(999)
        assert current_max_uses("Rage", "Barbarian", 2,  c) == 2
        assert current_max_uses("Rage", "Barbarian", 3,  c) == 3
        assert current_max_uses("Rage", "Barbarian", 6,  c) == 4
        assert current_max_uses("Rage", "Barbarian", 12, c) == 5
        assert current_max_uses("Rage", "Barbarian", 17, c) == 6
        assert current_max_uses("Rage", "Barbarian", 20, c) == 999

    def test_unknown_feature_returns_zero(self):
        c = self._char()
        assert current_max_uses("Nonexistent Feature", "Fighter", 1, c) == 0

    def test_unknown_class_returns_zero(self):
        c = self._char()
        assert current_max_uses("Second Wind", "FakeClass", 1, c) == 0


class TestRechargesOnShortRest:
    def test_second_wind_is_short_rest(self):
        assert recharges_on_short_rest("Second Wind", "Fighter", 1) is True

    def test_action_surge_is_short_rest(self):
        assert recharges_on_short_rest("Action Surge", "Fighter", 2) is True

    def test_wild_shape_is_short_rest(self):
        assert recharges_on_short_rest("Wild Shape", "Druid", 2) is True

    def test_rage_is_long_rest(self):
        assert recharges_on_short_rest("Rage", "Barbarian", 1) is False

    def test_arcane_recovery_is_long_rest(self):
        assert recharges_on_short_rest("Arcane Recovery", "Wizard", 1) is False

    def test_bardic_inspiration_short_at_level_5(self):
        assert recharges_on_short_rest("Bardic Inspiration", "Bard", 5) is True
        assert recharges_on_short_rest("Bardic Inspiration", "Bard", 4) is False

    def test_unknown_feature_returns_false(self):
        assert recharges_on_short_rest("Nonexistent", "Fighter", 1) is False


class TestFeatureChargesGainedAt:
    def test_fighter_second_wind_at_level_1(self):
        result = feature_charges_gained_at("Fighter", 1)
        names = [f["name"] for f in result]
        assert "Second Wind" in names

    def test_fighter_action_surge_at_level_2(self):
        result = feature_charges_gained_at("Fighter", 2)
        names = [f["name"] for f in result]
        assert "Action Surge" in names

    def test_no_features_at_wrong_level(self):
        result = feature_charges_gained_at("Fighter", 3)
        names = [f["name"] for f in result]
        assert "Second Wind" not in names

    def test_unknown_class_returns_empty(self):
        assert feature_charges_gained_at("FakeClass", 1) == []
