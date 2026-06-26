"""Tests for models/dm.py — tag parsing and narration cleaning."""

import pytest
from models.dm import DungeonMaster


@pytest.fixture
def dm():
    return DungeonMaster()


def parse(dm, text):
    """Convenience: return (clean_text, events) for a raw DM response."""
    return dm._parse_events(text)


class TestCheckTag:
    def test_basic(self, dm):
        _, events = parse(dm, "[CHECK: Perception DC15]\nYou glance around.")
        ev = next(e for e in events if e["type"] == "skill_check")
        assert ev["skill"] == "Perception"
        assert ev["dc"] == 15

    def test_case_insensitive(self, dm):
        _, events = parse(dm, "[check: stealth DC12]")
        assert events[0]["dc"] == 12

    def test_multi_word_skill(self, dm):
        _, events = parse(dm, "[CHECK: Sleight of Hand DC14]")
        ev = next(e for e in events if e["type"] == "skill_check")
        assert "Sleight" in ev["skill"]
        assert ev["dc"] == 14

    def test_stripped_from_narration(self, dm):
        clean, _ = parse(dm, "[CHECK: Perception DC15]\nYou look around.")
        assert "[CHECK:" not in clean
        assert "You look around." in clean


class TestCombatTag:
    def test_single_enemy_with_count(self, dm):
        _, events = parse(dm, "[COMBAT: Goblin×3]")
        ev = next(e for e in events if e["type"] == "combat_start")
        assert ev["enemies"] == [{"name": "Goblin", "count": 3}]

    def test_multiple_enemies(self, dm):
        _, events = parse(dm, "[COMBAT: Goblin×2, Hobgoblin×1]")
        ev = next(e for e in events if e["type"] == "combat_start")
        assert len(ev["enemies"]) == 2
        assert {"name": "Hobgoblin", "count": 1} in ev["enemies"]

    def test_no_count_defaults_one(self, dm):
        _, events = parse(dm, "[COMBAT: Orc]")
        ev = next(e for e in events if e["type"] == "combat_start")
        assert ev["enemies"][0] == {"name": "Orc", "count": 1}

    def test_latin_x_separator(self, dm):
        _, events = parse(dm, "[COMBAT: Wolf×2]")
        ev = next(e for e in events if e["type"] == "combat_start")
        assert ev["enemies"][0]["count"] == 2

    def test_stripped_from_narration(self, dm):
        clean, _ = parse(dm, "[COMBAT: Goblin×1]\nThe goblin charges!")
        assert "[COMBAT:" not in clean
        assert "The goblin charges!" in clean


class TestSceneTag:
    def test_basic(self, dm):
        _, events = parse(dm, "[SCENE: The Dark Forest]")
        ev = next(e for e in events if e["type"] == "scene_change")
        assert ev["location"] == "The Dark Forest"

    def test_stripped_from_narration(self, dm):
        clean, _ = parse(dm, "[SCENE: Tavern]\nYou enter.")
        assert "[SCENE:" not in clean
        assert "You enter." in clean


class TestXpTag:
    def test_basic(self, dm):
        _, events = parse(dm, "[XP: 150]")
        ev = next(e for e in events if e["type"] == "xp_award")
        assert ev["amount"] == 150

    def test_large_value(self, dm):
        _, events = parse(dm, "[XP: 2700]")
        ev = next(e for e in events if e["type"] == "xp_award")
        assert ev["amount"] == 2700

    def test_stripped_from_narration(self, dm):
        clean, _ = parse(dm, "You win!\n[XP: 50]")
        assert "[XP:" not in clean
        assert "You win!" in clean


class TestBeatClimaxBreak:
    def test_beat_tag(self, dm):
        _, events = parse(dm, "[BEAT]")
        assert any(e["type"] == "beat_complete" for e in events)

    def test_climax_tag(self, dm):
        _, events = parse(dm, "[CLIMAX]")
        assert any(e["type"] == "climax_reached" for e in events)

    def test_break_tag(self, dm):
        _, events = parse(dm, "[BREAK]")
        assert any(e["type"] == "break_suggested" for e in events)

    def test_beat_stripped(self, dm):
        clean, _ = parse(dm, "Great work!\n[BEAT]")
        assert "[BEAT]" not in clean
        assert "Great work!" in clean

    def test_case_insensitive(self, dm):
        _, events = parse(dm, "[beat]")
        assert any(e["type"] == "beat_complete" for e in events)


class TestCompanionTag:
    def test_basic(self, dm):
        _, events = parse(dm, "[COMPANION: Aria Windfall]")
        ev = next(e for e in events if e["type"] == "companion_join")
        assert ev["name"] == "Aria Windfall"

    def test_stripped_from_narration(self, dm):
        clean, _ = parse(dm, "She joins you.\n[COMPANION: Aria Windfall]")
        assert "[COMPANION:" not in clean
        assert "She joins you." in clean


class TestActionTag:
    def test_attack(self, dm):
        _, events = parse(dm, "[ACTION: attack=Dagger]\nYou thrust.")
        ev = next(e for e in events if e["type"] == "action_taken")
        assert ev["action"] == "attack"
        assert ev["weapon"] == "Dagger"
        assert ev.get("mode") is None

    def test_attack_with_mode(self, dm):
        _, events = parse(dm, "[ACTION: attack=Longsword, mode=twohanded]")
        ev = next(e for e in events if e["type"] == "action_taken")
        assert ev["mode"] == "twohanded"

    def test_spell_with_slot(self, dm):
        _, events = parse(dm, "[ACTION: spell=Fireball, slot=3]")
        ev = next(e for e in events if e["type"] == "action_taken")
        assert ev["action"] == "spell"
        assert ev["spell"] == "Fireball"
        assert ev["slot"] == 3

    def test_spell_without_slot(self, dm):
        _, events = parse(dm, "[ACTION: spell=Shocking Grasp]")
        ev = next(e for e in events if e["type"] == "action_taken")
        assert ev["slot"] is None

    def test_feature(self, dm):
        _, events = parse(dm, "[ACTION: feature=Second Wind]")
        ev = next(e for e in events if e["type"] == "action_taken")
        assert ev["action"] == "feature"
        assert ev["feature"] == "Second Wind"

    def test_dodge(self, dm):
        _, events = parse(dm, "[ACTION: dodge]")
        ev = next(e for e in events if e["type"] == "action_taken")
        assert ev["action"] == "dodge"

    def test_dash(self, dm):
        _, events = parse(dm, "[ACTION: dash]")
        ev = next(e for e in events if e["type"] == "action_taken")
        assert ev["action"] == "dash"

    def test_disengage(self, dm):
        _, events = parse(dm, "[ACTION: disengage]")
        ev = next(e for e in events if e["type"] == "action_taken")
        assert ev["action"] == "disengage"

    def test_hide(self, dm):
        _, events = parse(dm, "[ACTION: hide]")
        ev = next(e for e in events if e["type"] == "action_taken")
        assert ev["action"] == "hide"

    def test_action_stripped_from_narration(self, dm):
        clean, _ = parse(dm, "[ACTION: attack=Dagger]\nYou lunge.")
        assert "[ACTION:" not in clean
        assert "You lunge." in clean


class TestBonusTag:
    def test_bonus_attack(self, dm):
        _, events = parse(dm, "[BONUS: attack=Dagger]")
        ev = next(e for e in events if e["type"] == "bonus_action_taken")
        assert ev["action"] == "attack"
        assert ev["weapon"] == "Dagger"

    def test_bonus_feature(self, dm):
        _, events = parse(dm, "[BONUS: feature=Cunning Action]")
        ev = next(e for e in events if e["type"] == "bonus_action_taken")
        assert ev["action"] == "feature"
        assert ev["feature"] == "Cunning Action"

    def test_bonus_stripped_from_narration(self, dm):
        clean, _ = parse(dm, "[BONUS: attack=Dagger]\nOffhand follows.")
        assert "[BONUS:" not in clean
        assert "Offhand follows." in clean


class TestNarrationCleaning:
    def test_no_tags_passthrough(self, dm):
        text = "The fire crackles warmly as you settle in."
        clean, events = parse(dm, text)
        assert events == []
        assert clean == text

    def test_multiple_tags_all_stripped(self, dm):
        text = "[SCENE: Tavern]\n[XP: 100]\nThe barkeep nods."
        clean, events = parse(dm, text)
        assert "[SCENE:" not in clean
        assert "[XP:" not in clean
        assert "The barkeep nods." in clean
        assert len(events) == 2

    def test_excessive_newlines_collapsed(self, dm):
        text = "Line one.\n\n\n\nLine two."
        clean, _ = parse(dm, text)
        assert "\n\n\n" not in clean

    def test_all_tag_types_stripped_together(self, dm):
        text = (
            "[CHECK: Perception DC12]\n"
            "[COMBAT: Goblin×1]\n"
            "[SCENE: Forest]\n"
            "[XP: 50]\n"
            "[BEAT]\n"
            "[COMPANION: Aria]\n"
            "[ACTION: attack=Sword]\n"
            "[BONUS: attack=Dagger]\n"
            "The dust settles."
        )
        clean, events = parse(dm, text)
        for tag in ("[CHECK:", "[COMBAT:", "[SCENE:", "[XP:", "[BEAT]",
                    "[COMPANION:", "[ACTION:", "[BONUS:"):
            assert tag not in clean
        assert "The dust settles." in clean
