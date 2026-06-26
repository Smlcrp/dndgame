"""Tests for models/adventure.py — generation, beat progression, prompt block."""

import pytest
from models.adventure import generate_adventure, advance_beat, adventure_prompt_block
from models.character import empty_character


def _char(name="Hero"):
    c = empty_character()
    c["name"] = name
    return c


class TestGenerateAdventure:
    def test_has_required_keys(self):
        adv = generate_adventure(_char())
        required = ("title", "hook", "antagonist", "beats", "climax",
                    "resolution", "current_beat", "beat_xp", "climax_xp")
        for key in required:
            assert key in adv, f"Missing key: {key}"

    def test_starts_at_beat_zero(self):
        assert generate_adventure(_char())["current_beat"] == 0

    def test_beats_is_nonempty_list(self):
        adv = generate_adventure(_char())
        assert isinstance(adv["beats"], list)
        assert len(adv["beats"]) > 0

    def test_beat_xp_is_list_of_ints(self):
        adv = generate_adventure(_char())
        assert all(isinstance(x, int) for x in adv["beat_xp"])

    def test_climax_xp_is_positive(self):
        assert generate_adventure(_char())["climax_xp"] > 0

    def test_antagonist_has_required_keys(self):
        ant = generate_adventure(_char())["antagonist"]
        for key in ("name", "role", "motivation", "plan"):
            assert key in ant, f"Antagonist missing: {key}"

    def test_produces_different_adventures(self):
        # Runs multiple times; should not always be identical (probabilistic).
        results = {generate_adventure(_char())["title"] for _ in range(20)}
        assert len(results) > 1


class TestAdvanceBeat:
    def _adv(self, beat=0):
        adv = generate_adventure(_char())
        adv["current_beat"] = beat
        return adv

    def test_increments_beat(self):
        adv = self._adv(0)
        advance_beat(adv)
        assert adv["current_beat"] == 1

    def test_returns_positive_xp(self):
        adv = self._adv(0)
        xp = advance_beat(adv)
        assert xp > 0

    def test_second_beat_higher_xp(self):
        adv = generate_adventure(_char())
        xp0 = adv["beat_xp"][0]
        xp1 = adv["beat_xp"][1]
        assert xp1 >= xp0  # XP escalates with story progression

    def test_capped_at_beat_4(self):
        adv = self._adv(4)
        xp = advance_beat(adv)
        assert xp == 0
        assert adv["current_beat"] == 4

    def test_repeated_advance_at_cap_noop(self):
        adv = self._adv(4)
        for _ in range(5):
            advance_beat(adv)
        assert adv["current_beat"] == 4

    def test_full_arc_reaches_climax(self):
        adv = self._adv(0)
        total_xp = sum(advance_beat(adv) for _ in range(4))
        assert adv["current_beat"] == 4
        assert total_xp > 0


class TestAdventurePromptBlock:
    def test_none_returns_empty_string(self):
        assert adventure_prompt_block(None) == ""

    def test_includes_title(self):
        adv = generate_adventure(_char())
        block = adventure_prompt_block(adv)
        assert adv["title"] in block

    def test_includes_antagonist_name(self):
        adv = generate_adventure(_char())
        block = adventure_prompt_block(adv)
        assert adv["antagonist"]["name"] in block

    def test_hook_stage_label(self):
        adv = generate_adventure(_char())
        adv["current_beat"] = 0
        block = adventure_prompt_block(adv)
        assert "HOOK" in block

    def test_climax_stage_label(self):
        adv = generate_adventure(_char())
        adv["current_beat"] = 4
        block = adventure_prompt_block(adv)
        assert "CLIMAX" in block

    def test_resolution_stage_label(self):
        adv = generate_adventure(_char())
        adv["current_beat"] = 5
        block = adventure_prompt_block(adv)
        assert "RESOLUTION" in block

    def test_beat_tag_instructions_included(self):
        adv = generate_adventure(_char())
        block = adventure_prompt_block(adv)
        assert "[BEAT]" in block
        assert "[CLIMAX]" in block
        assert "[BREAK]" in block

    def test_returns_string(self):
        adv = generate_adventure(_char())
        assert isinstance(adventure_prompt_block(adv), str)
