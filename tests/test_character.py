"""Tests for models/character.py — ability scores, skills, HP, spells, rests, schema."""

import pytest
from models.character import (
    modifier, modifier_str, proficiency_bonus,
    skill_bonus, saving_throw_bonus, passive_perception,
    apply_damage, apply_healing, add_temp_hp, is_unconscious,
    use_spell_slot, restore_spell_slots,
    short_rest, long_rest,
    empty_character, migrate_character, validate_character,
)


class TestModifier:
    def test_10_gives_0(self):    assert modifier(10) == 0
    def test_12_gives_1(self):    assert modifier(12) == 1
    def test_8_gives_minus1(self): assert modifier(8) == -1
    def test_20_gives_5(self):    assert modifier(20) == 5
    def test_1_gives_minus5(self): assert modifier(1) == -5
    def test_11_rounds_down(self): assert modifier(11) == 0
    def test_9_gives_minus1(self): assert modifier(9) == -1
    def test_18_gives_4(self):    assert modifier(18) == 4


class TestModifierStr:
    def test_positive_has_plus(self):  assert modifier_str(14) == "+2"
    def test_zero_has_plus(self):      assert modifier_str(10) == "+0"
    def test_negative_no_plus(self):   assert modifier_str(8)  == "-1"


class TestProficiencyBonus:
    def test_levels_1_4(self):
        for lvl in range(1, 5):
            assert proficiency_bonus(lvl) == 2

    def test_level_5(self):  assert proficiency_bonus(5) == 3
    def test_level_8(self):  assert proficiency_bonus(8) == 3
    def test_level_9(self):  assert proficiency_bonus(9) == 4
    def test_level_13(self): assert proficiency_bonus(13) == 5
    def test_level_17(self): assert proficiency_bonus(17) == 6
    def test_level_20(self): assert proficiency_bonus(20) == 6


class TestSkillBonus:
    """skill_bonus() uses lowercase_underscore keys matching the SKILLS dict.
    skill_proficiencies must contain matching lowercase_underscore strings for
    proficiency to be detected at this layer.
    """

    def _char(self, skills=None, expertises=None, overrides=None, level=1,
               dex=16, wis=14):
        c = empty_character()
        c["level"] = level
        c["abilities"]["dexterity"] = dex
        c["abilities"]["wisdom"] = wis
        c["skill_proficiencies"] = skills or []
        c["skill_expertises"] = expertises or []
        c["skill_overrides"] = overrides or {}
        return c

    def test_no_proficiency_returns_ability_mod(self):
        c = self._char(dex=16)
        assert skill_bonus(c, "stealth") == 3  # dex +3, no pb

    def test_proficiency_adds_pb(self):
        c = self._char(dex=16, skills=["stealth"], level=1)
        assert skill_bonus(c, "stealth") == 5  # 3 + 2

    def test_expertise_doubles_pb(self):
        c = self._char(dex=16, skills=["stealth"], expertises=["stealth"])
        assert skill_bonus(c, "stealth") == 7  # 3 + 4

    def test_override_returns_fixed_value(self):
        c = self._char(dex=16, overrides={"stealth": 10})
        assert skill_bonus(c, "stealth") == 10

    def test_invalid_skill_returns_zero(self):
        assert skill_bonus(self._char(), "nonexistent") == 0

    def test_proficiency_scales_with_level(self):
        c = self._char(dex=16, skills=["stealth"], level=5)
        assert skill_bonus(c, "stealth") == 6  # 3 + 3 (pb at level 5)

    def test_wisdom_based_skill(self):
        c = self._char(wis=14)
        assert skill_bonus(c, "perception") == 2  # wis +2, no pb


class TestSavingThrowBonus:
    def _char(self, saves=None, level=1, con=14):
        c = empty_character()
        c["level"] = level
        c["abilities"]["constitution"] = con
        c["saving_throw_proficiencies"] = saves or []
        return c

    def test_no_proficiency(self):
        assert saving_throw_bonus(self._char(con=14), "constitution") == 2

    def test_with_proficiency(self):
        c = self._char(con=14, saves=["constitution"])
        assert saving_throw_bonus(c, "constitution") == 4  # 2 + 2

    def test_scales_with_level(self):
        c = self._char(con=14, saves=["constitution"], level=5)
        assert saving_throw_bonus(c, "constitution") == 5  # 2 + 3


class TestApplyDamage:
    def _char(self, hp=10, temp=0):
        c = empty_character()
        c["hp"] = {"max": 10, "current": hp, "temp": temp}
        return c

    def test_reduces_current_hp(self):
        c = apply_damage(self._char(10), 4)
        assert c["hp"]["current"] == 6

    def test_does_not_go_below_zero(self):
        c = apply_damage(self._char(3), 10)
        assert c["hp"]["current"] == 0

    def test_temp_fully_absorbs(self):
        c = apply_damage(self._char(10, temp=5), 3)
        assert c["hp"]["temp"] == 2
        assert c["hp"]["current"] == 10

    def test_damage_bleeds_through_temp(self):
        c = apply_damage(self._char(10, temp=5), 7)
        assert c["hp"]["temp"] == 0
        assert c["hp"]["current"] == 8


class TestApplyHealing:
    def _char(self, hp=5):
        c = empty_character()
        c["hp"] = {"max": 10, "current": hp, "temp": 0}
        return c

    def test_restores_hp(self):
        assert apply_healing(self._char(5), 3)["hp"]["current"] == 8

    def test_caps_at_max(self):
        assert apply_healing(self._char(9), 5)["hp"]["current"] == 10


class TestAddTempHp:
    def test_sets_temp_hp(self):
        c = empty_character()
        c = add_temp_hp(c, 8)
        assert c["hp"]["temp"] == 8

    def test_keeps_higher_existing_temp(self):
        c = empty_character()
        c["hp"]["temp"] = 10
        c = add_temp_hp(c, 5)
        assert c["hp"]["temp"] == 10

    def test_replaces_lower_existing_temp(self):
        c = empty_character()
        c["hp"]["temp"] = 3
        c = add_temp_hp(c, 8)
        assert c["hp"]["temp"] == 8


class TestIsUnconscious:
    def test_zero_hp(self):
        c = empty_character()
        c["hp"]["current"] = 0
        assert is_unconscious(c) is True

    def test_positive_hp(self):
        c = empty_character()
        c["hp"]["current"] = 1
        assert is_unconscious(c) is False


class TestSpellSlots:
    def _char(self):
        c = empty_character()
        c["spellcasting"]["enabled"] = True
        c["spellcasting"]["slots"]["1"]["total"] = 3
        return c

    def test_use_increments_used(self):
        c = self._char()
        use_spell_slot(c, 1)
        assert c["spellcasting"]["slots"]["1"]["used"] == 1

    def test_use_all_then_raise(self):
        c = self._char()
        for _ in range(3):
            use_spell_slot(c, 1)
        with pytest.raises(ValueError):
            use_spell_slot(c, 1)

    def test_restore_clears_used(self):
        c = self._char()
        use_spell_slot(c, 1)
        use_spell_slot(c, 1)
        restore_spell_slots(c)
        assert c["spellcasting"]["slots"]["1"]["used"] == 0


class TestShortRest:
    def _char(self, hp=5, hp_max=10, con=10, hd_total=3, hd_used=0):
        c = empty_character()
        c["hp"] = {"max": hp_max, "current": hp, "temp": 0}
        c["hit_dice"] = {"type": "d8", "total": hd_total, "used": hd_used}
        c["abilities"]["constitution"] = con
        c["level"] = 1
        return c

    def test_heals_and_spends_die(self):
        c = short_rest(self._char(hp=5), 1, [6])
        assert c["hp"]["current"] == 10  # 5+6 capped at 10
        assert c["hit_dice"]["used"] == 1

    def test_con_mod_adds_to_healing(self):
        c = short_rest(self._char(hp=10, hp_max=20, con=14), 1, [4])
        assert c["hp"]["current"] == 16  # 10 + (4+2)

    def test_minimum_heal_per_die_is_1(self):
        c = short_rest(self._char(hp=5, hp_max=20, con=1), 1, [1])
        assert c["hp"]["current"] == 6  # max(1, 1 + (-5)) → 1

    def test_too_many_dice_raises(self):
        c = self._char(hd_total=1, hd_used=0)
        with pytest.raises(ValueError):
            short_rest(c, 2, [4, 4])

    def test_warlock_restores_spell_slots_on_short_rest(self):
        c = self._char()
        c["class"] = "Warlock"
        c["spellcasting"]["slots"]["3"]["total"] = 2
        c["spellcasting"]["slots"]["3"]["used"]  = 2
        short_rest(c, 0, [])
        assert c["spellcasting"]["slots"]["3"]["used"] == 0

    def test_non_warlock_does_not_restore_slots_on_short_rest(self):
        c = self._char()
        c["class"] = "Wizard"
        c["spellcasting"]["slots"]["3"]["total"] = 2
        c["spellcasting"]["slots"]["3"]["used"]  = 2
        short_rest(c, 0, [])
        assert c["spellcasting"]["slots"]["3"]["used"] == 2


class TestLongRest:
    def _char(self, hp_max=10, hd_total=6, hd_used=4):
        c = empty_character()
        c["hp"] = {"max": hp_max, "current": 1, "temp": 5}
        c["hit_dice"] = {"type": "d8", "total": hd_total, "used": hd_used}
        c["conditions"] = ["Poisoned", "Blinded"]
        c["death_saves"] = {"successes": 2, "failures": 1}
        c["level"] = 1
        return c

    def test_restores_hp_to_max(self):
        c = long_rest(self._char())
        assert c["hp"]["current"] == 10

    def test_clears_temp_hp(self):
        c = long_rest(self._char())
        assert c["hp"]["temp"] == 0

    def test_clears_conditions(self):
        c = long_rest(self._char())
        assert c["conditions"] == []

    def test_resets_death_saves(self):
        c = long_rest(self._char())
        assert c["death_saves"] == {"successes": 0, "failures": 0}

    def test_recovers_half_hit_dice(self):
        # 6 total, 4 used → recover ceil(6/2)=3 → used=max(0,4-3)=1
        c = long_rest(self._char(hd_total=6, hd_used=4))
        assert c["hit_dice"]["used"] == 1

    def test_recovers_ceil_half_odd_total(self):
        # 5 total, 5 used → recover ceil(5/2)=3 → used=max(0,5-3)=2
        c = long_rest(self._char(hd_total=5, hd_used=5))
        assert c["hit_dice"]["used"] == 2

    def test_recovers_at_least_one_hit_die(self):
        c = long_rest(self._char(hd_total=1, hd_used=1))
        assert c["hit_dice"]["used"] == 0


class TestMigrateCharacter:
    def test_fills_missing_top_level(self):
        c = {"name": "Aria", "level": 1}
        result = migrate_character(c)
        assert "abilities" in result
        assert "spellcasting" in result
        assert "conditions" in result

    def test_fills_missing_nested_key(self):
        c = empty_character()
        del c["spellcasting"]["spells_prepared"]
        result = migrate_character(c)
        assert result["spellcasting"]["spells_prepared"] == []

    def test_does_not_overwrite_existing_values(self):
        c = empty_character()
        c["level"] = 5
        result = migrate_character(c)
        assert result["level"] == 5

    def test_idempotent(self):
        c = empty_character()
        c["name"] = "Hero"
        r1 = migrate_character(c)
        r2 = migrate_character(r1)
        assert r1 == r2


class TestValidateCharacter:
    def _valid(self):
        c = empty_character()
        c["name"] = "Valid"
        c["hp"]["max"] = 10
        c["hp"]["current"] = 10
        c["level"] = 1
        c["hit_dice"]["total"] = 1
        return c

    def test_valid_character_passes(self):
        validate_character(self._valid())  # must not raise

    def test_hp_max_zero_raises(self):
        c = self._valid()
        c["hp"]["max"] = 0
        with pytest.raises(ValueError):
            validate_character(c)

    def test_level_zero_raises(self):
        c = self._valid()
        c["level"] = 0
        with pytest.raises(ValueError):
            validate_character(c)

    def test_level_21_raises(self):
        c = self._valid()
        c["level"] = 21
        with pytest.raises(ValueError):
            validate_character(c)

    def test_negative_xp_raises(self):
        c = self._valid()
        c["experience"] = -1
        with pytest.raises(ValueError):
            validate_character(c)

    def test_spellcasting_enabled_not_bool_raises(self):
        c = self._valid()
        c["spellcasting"]["enabled"] = "yes"
        with pytest.raises(ValueError):
            validate_character(c)

    def test_hp_dict_shape_checked(self):
        c = self._valid()
        c["hp"]["current"] = "ten"  # not int
        with pytest.raises(ValueError):
            validate_character(c)

    def test_error_message_includes_character_name(self):
        c = self._valid()
        c["name"] = "Daelric"
        c["level"] = 0
        with pytest.raises(ValueError, match="Daelric"):
            validate_character(c)
