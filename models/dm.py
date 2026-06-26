import json
import os
import re
import sys
from pathlib import Path

_root = Path(__file__).parent.parent
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))

from models import game_state as gs
from models.character import modifier
from models.enemies import enemy_list_for_dm
from models.adventure import adventure_prompt_block

OLLAMA_URL           = "http://localhost:11434/api/chat"
DEFAULT_OLLAMA_MODEL = "HammerAI/hermes-3-llama-3.1:8b-q4_K_M"
_DEFAULT_CONFIG      = Path(__file__).parent.parent / "data" / "dm_config.json"

import requests


class DungeonMaster:

    def __init__(self, model=None):
        self.model = model or DEFAULT_OLLAMA_MODEL

    def _build_system_prompt(self, character, session=None):
        name  = character.get("name") or "the adventurer"
        race  = character.get("race", "Human")
        cls   = character.get("class", "Fighter")
        sub   = character.get("subclass", "")
        level = character.get("level", 1)
        bg    = character.get("background", "")
        ab    = character.get("abilities", {})

        subclass_str = f" ({sub})" if sub else ""

        mods = {
            "STR": modifier(ab.get("strength",     10)),
            "DEX": modifier(ab.get("dexterity",    10)),
            "CON": modifier(ab.get("constitution", 10)),
            "INT": modifier(ab.get("intelligence", 10)),
            "WIS": modifier(ab.get("wisdom",       10)),
            "CHA": modifier(ab.get("charisma",     10)),
        }
        mod_str = "  ".join(f"{k} {v:+d}" for k, v in mods.items())

        traits = character.get("personality_traits", "")
        bonds  = character.get("bonds", "")

    def _build_combat_prompt_block(self, character):
        lines = [
            "\n\nCOMBAT ACTION TAGS — TWO-PHASE NARRATION SYSTEM:",
            "",
            "Phase 1 is NOW. You receive the player's intended action and must:",
            "1. Emit the correct tag on its own line BEFORE your narration.",
            "2. Write EXACTLY ONE SENTENCE describing only the physical initiation of the action.",
            "   That means: the body motion, the gesture, the wind-up — nothing more.",
            "   The dice have NOT been rolled. Contact has NOT happened. You do not know if it hits.",
            "",
            "Phase 2 comes later. After the dice resolve, you will be called again with the actual",
            "result (hit/miss/damage) and THAT is when you write the dramatic outcome.",
            "",
            "HARD RULES FOR PHASE 1 (your current response):",
            "- ONE sentence only. No paragraphs.",
            "- Stop before contact. Describe the reach, not the touch.",
            "- NO electricity crackling on skin. NO fire hitting anything. NO arrows finding marks.",
            "- NO enemy reactions (flinching, screaming, recoiling, eyes widening).",
            "- NO 'If successful...' or 'If it hits...' — you do not know.",
            "- NO 'What do you do next?' — the engine handles turns.",
            "",
            "EXAMPLE — player says 'I stab the goblin with my dagger':",
            "  CORRECT: [ACTION: attack=Dagger]",
            "           You lunge forward, dagger thrusting toward the goblin's ribs.",
            "  WRONG:   [ACTION: attack=Dagger]",
            "           You lunge forward — the dagger bites deep! The goblin howls in pain.",
            "",
            "EXAMPLE — player says 'I cast shocking grasp':",
            "  CORRECT: [ACTION: spell=Shocking Grasp]",
            "           You reach out, crackling energy gathering at your fingertips.",
            "  WRONG:   [ACTION: spell=Shocking Grasp]",
            "           You reach out — electricity surges into the goblin's skin, causing it to convulse.",
            "",
            "If the player is doing something purely narrative (talking, looking around), omit the tag.",
            "",
        ]

        attacks = character.get("attacks", [])
        if attacks:
            lines.append("Available attacks (use exact weapon name):")
            for atk in attacks:
                lines.append(f"  {atk['name']}  ({atk.get('attack_bonus', 0):+d} to hit,  "
                             f"{atk.get('damage', '?')} {atk.get('damage_type', '')})")
            lines.append("")

        sc = character.get("spellcasting", {})
        if sc.get("enabled"):
            try:
                from models.spells import SPELLS
            except ImportError:
                SPELLS = {}
            prepared = list(dict.fromkeys(
                sc.get("spells_prepared", []) + sc.get("spells_known", [])))
            slots = sc.get("slots", {})
            spell_lines = []
            for name in prepared:
                sp = SPELLS.get(name)
                if not sp:
                    continue
                if sp["level"] == 0:
                    spell_lines.append(f"  {name}  (cantrip)")
                else:
                    avail = sum(
                        max(0, v.get("total", 0) - v.get("used", 0))
                        for k, v in slots.items() if int(k) >= sp["level"])
                    if avail > 0:
                        spell_lines.append(
                            f"  {name}  (L{sp['level']}, {avail} slot{'s' if avail != 1 else ''} available)")
            if spell_lines:
                lines.append("Available spells (use exact spell name):")
                lines.extend(spell_lines)
                lines.append("")

        feature_uses = character.get("feature_uses", {})
        feat_lines = []
        for fname, data in feature_uses.items():
            cur = data.get("current", 0)
            mx  = data.get("max", 1)
            if cur > 0:
                feat_lines.append(f"  {fname}  ({cur}/{mx} charges)")
        if feat_lines:
            lines.append("Available features (use exact feature name):")
            lines.extend(feat_lines)
            lines.append("")

        lines += [
            "Tags — place ONE per line, before your narration:",
            "  [ACTION: attack=WeaponName]",
            "  [ACTION: attack=WeaponName, mode=twohanded]",
            "  [ACTION: attack=WeaponName, mode=thrown]",
            "  [ACTION: attack=WeaponName, mode=ranged]",
            "  [ACTION: spell=SpellName]",
            "  [ACTION: spell=SpellName, slot=N]   ← N = slot level; use lowest available if unsure",
            "  [ACTION: feature=FeatureName]",
            "  [ACTION: dodge]",
            "  [ACTION: dash]",
            "  [ACTION: disengage]",
            "  [ACTION: hide]",
            "  [BONUS: attack=WeaponName]           ← off-hand bonus attack",
            "  [BONUS: feature=FeatureName]         ← bonus-action class feature",
        ]
        return "\n".join(lines)

    def _build_system_prompt(self, character, session=None):
        name  = character.get("name") or "the adventurer"
        race  = character.get("race", "Human")
        cls   = character.get("class", "Fighter")
        sub   = character.get("subclass", "")
        level = character.get("level", 1)
        bg    = character.get("background", "")
        ab    = character.get("abilities", {})

        subclass_str = f" ({sub})" if sub else ""

        mods = {
            "STR": modifier(ab.get("strength",     10)),
            "DEX": modifier(ab.get("dexterity",    10)),
            "CON": modifier(ab.get("constitution", 10)),
            "INT": modifier(ab.get("intelligence", 10)),
            "WIS": modifier(ab.get("wisdom",       10)),
            "CHA": modifier(ab.get("charisma",     10)),
        }
        mod_str = "  ".join(f"{k} {v:+d}" for k, v in mods.items())

        traits = character.get("personality_traits", "")
        bonds  = character.get("bonds", "")

        in_combat    = session.get("in_combat", False) if session else False
        combat_block = self._build_combat_prompt_block(character) if in_combat else ""
        companions   = session.get("companions", []) if session else []
        party_block  = self._build_party_block(character, companions)

        return f"""You are the Dungeon Master for a solo D&D 5e adventure. Your job is to narrate an immersive story — you are a storyteller, not a game host.

PLAYER CHARACTER:
  Name: {name}
  Race: {race}  |  Class: {cls}{subclass_str}  |  Level: {level}
  Background: {bg}
  Ability modifiers: {mod_str}
  Personality: {traits}
  Bonds: {bonds}

NARRATION RULES — READ CAREFULLY:
1. Write in second person ("You see...", "The guard eyes you..."). Never use third person for the player.
2. Describe scenes vividly in 3-5 sentences. Engage the senses. React to what the player does.
3. NEVER mention dice, roll values, DCs, modifiers, hit points, or any game statistics in your narrative text. Ever.
   BAD: "Your Survival check of 16 beats the DC10 — you notice the tracks."
   GOOD: "You read the forest floor like an open book — the tracks are fresh, no more than an hour old."
4. NEVER refer to yourself as the DM, and never narrate your own actions or intentions.
   BAD: "The DM requests a Perception check." / "He was about to ask for a check when..."
   GOOD: Just emit the [CHECK:] tag silently on its own line, then continue the story.
5. When the game engine tells you a skill check succeeded or failed, narrate ONLY the fictional outcome. Do not echo the roll, the DC, or the word "check" in your prose.
6. When the player attempts something with an uncertain outcome, emit this tag on its own line then continue narrating:
   [CHECK: SkillName DC##]
   Example: [CHECK: Stealth DC14]
7. When combat should begin, emit this tag on its own line then stop — the engine takes over:
   [COMBAT: EnemyName×count, EnemyName×count]
   Example: [COMBAT: Goblin×2, Hobgoblin×1]
8. When the scene location changes, emit on its own line:
   [SCENE: Location Name]
9. When the player earns XP, emit on its own line:
   [XP: N]
   XP is awarded ONLY for tangible accomplishments: defeating enemies in combat, solving a puzzle or trap, completing a quest objective, or a significant story achievement the player actively caused.
   NEVER award XP for: starting a session, beginning an act, arriving at a location, scene transitions, or anything the player did not DO. If in doubt, do not emit [XP].
10. If this is the first message, open with a vivid scene that fits the character's background and class.
11. Keep responses focused. One scene at a time.

{enemy_list_for_dm(level)}{adventure_prompt_block(session.get("adventure") if session else None)}{party_block}{combat_block}"""

    def _build_party_block(self, character, companions):
        """System prompt section describing party members and companion introduction rules."""
        from models.companions import get_available_companions

        player_class   = character.get("class", "")
        active         = [c for c in companions if c.get("status") != "dead"]
        active_classes = [c["class"] for c in active]

        lines = ["\n\nCOMPANION SYSTEM:"]

        if active:
            lines.append("\nCURRENT PARTY MEMBERS (in addition to the player):")
            for c in active:
                status = " [UNCONSCIOUS]" if c.get("status") == "unconscious" else ""
                lines.append(
                    f"  {c['name']} — {c['race']} {c['class']} ({c['subclass']}), "
                    f"Level {c['level']}{status}")
                lines.append(f"    \"{c['personality_traits'][0]}\"")
                lines.append(f"    Ideal: {c['ideal']}")
                lines.append(f"    Alignment: {c['alignment']}")
                lines.append(
                    f"    Their surname ({c['last_name']}) may be used naturally by "
                    f"NPCs, in formal introductions, or in dramatic moments.")
            lines.append(
                "\n  Voice each party member consistently according to their personality, "
                "ideal, and alignment. They have opinions and may push back on choices "
                "that conflict with their moral code.")
        else:
            lines.append("\nThe player is currently traveling alone.")

        available = get_available_companions(player_class, active_classes)
        max_companions = 3

        if len(active) < max_companions and available:
            names_and_classes = ", ".join(
                f"{t['first_name']} {t['last_name']} ({t['class']})"
                for t in available)
            lines += [
                "\nINTRODUCING A COMPANION:",
                "You MAY introduce one of the available companions when the story calls "
                "for it naturally — a stranger who helps in a fight, someone rescued, "
                "a guide hired by the quest-giver. Do NOT rush this. There is no requirement "
                "to introduce anyone. Let the story create the moment.",
                f"Available companions: {names_and_classes}",
                "Rules:",
                "- NEVER introduce a companion whose class matches the player or any active party member.",
                "- Narrate their arrival naturally first, then emit on its own line: "
                "[COMPANION: First Last]",
                "- Use their full name at introduction. Their surname can appear in the story "
                "as NPCs address them or as the narrative calls for it.",
                "- The party cap is 3 companions. Do not introduce more.",
            ]
        elif len(active) >= max_companions:
            lines.append("\nThe party is at full capacity (3 companions). Do not introduce more.")

        return "\n".join(lines)

    def _messages_for_ollama(self, session, character, player_input):
        messages = [{"role": "system", "content": self._build_system_prompt(character, session)}]
        for entry in session.get("history", []):
            role = "user" if entry["role"] == "player" else "assistant"
            messages.append({"role": role, "content": entry["text"]})
        messages.append({"role": "user", "content": player_input})
        return messages

    def _call_ollama(self, messages):
        try:
            resp = requests.post(OLLAMA_URL, json={
                "model":    self.model,
                "messages": messages,
                "stream":   False,
            }, timeout=120)
            resp.raise_for_status()
            return resp.json()["message"]["content"]
        except requests.exceptions.ConnectionError:
            raise RuntimeError(
                "Cannot connect to Ollama. Make sure it is running.\n"
                "Start it with:  ollama serve\n"
                f"Then pull a model:  ollama pull {self.model}"
            )
        except requests.exceptions.Timeout:
            raise RuntimeError("Ollama timed out. The model may still be loading — try again.")
        except (KeyError, ValueError) as e:
            raise RuntimeError(f"Unexpected Ollama response: {e}")

    def _parse_events(self, raw_text):
        events = []

        for m in re.finditer(r"\[CHECK:\s*([\w\s]+?)\s+DC\s*(\d+)\]", raw_text, re.IGNORECASE):
            events.append({
                "type":  "skill_check",
                "skill": m.group(1).strip(),
                "dc":    int(m.group(2)),
            })

        for m in re.finditer(r"\[COMBAT:\s*([^\]]+)\]", raw_text, re.IGNORECASE):
            enemies = []
            for part in m.group(1).split(","):
                part = part.strip()
                mob  = re.match(r"(.+?)(?:[×x])(\d+)$", part, re.IGNORECASE)
                if mob:
                    enemies.append({"name": mob.group(1).strip(), "count": int(mob.group(2))})
                elif part:
                    enemies.append({"name": part, "count": 1})
            if enemies:
                events.append({"type": "combat_start", "enemies": enemies})

        for m in re.finditer(r"\[SCENE:\s*([^\]]+)\]", raw_text, re.IGNORECASE):
            events.append({"type": "scene_change", "location": m.group(1).strip()})

        for m in re.finditer(r"\[XP:\s*(\d+)\]", raw_text, re.IGNORECASE):
            events.append({"type": "xp_award", "amount": int(m.group(1))})

        if re.search(r"\[BEAT\]", raw_text, re.IGNORECASE):
            events.append({"type": "beat_complete"})

        if re.search(r"\[CLIMAX\]", raw_text, re.IGNORECASE):
            events.append({"type": "climax_reached"})

        if re.search(r"\[BREAK\]", raw_text, re.IGNORECASE):
            events.append({"type": "break_suggested"})

        for m in re.finditer(r"\[COMPANION:\s*([^\]]+)\]", raw_text, re.IGNORECASE):
            events.append({"type": "companion_join", "name": m.group(1).strip()})

        for m in re.finditer(r"\[ACTION:\s*([^\]]+)\]", raw_text, re.IGNORECASE):
            content = m.group(1).strip()
            pairs   = {k.strip().lower(): v.strip()
                       for part in content.split(",")
                       for k, v in [part.split("=", 1)] if "=" in part}
            first   = content.split(",")[0].split("=")[0].strip().lower()
            ev      = {"type": "action_taken"}
            if first in ("dodge", "dash", "disengage", "hide"):
                ev["action"] = first
            elif "attack" in pairs:
                ev["action"] = "attack"
                ev["weapon"] = pairs["attack"]
                ev["mode"]   = pairs.get("mode")
            elif "spell" in pairs:
                ev["action"] = "spell"
                ev["spell"]  = pairs["spell"]
                ev["slot"]   = int(pairs["slot"]) if "slot" in pairs else None
            elif "feature" in pairs:
                ev["action"]  = "feature"
                ev["feature"] = pairs["feature"]
            else:
                continue
            events.append(ev)

        for m in re.finditer(r"\[BONUS:\s*([^\]]+)\]", raw_text, re.IGNORECASE):
            content = m.group(1).strip()
            pairs   = {k.strip().lower(): v.strip()
                       for part in content.split(",")
                       for k, v in [part.split("=", 1)] if "=" in part}
            ev = {"type": "bonus_action_taken"}
            if "attack" in pairs:
                ev["action"] = "attack"
                ev["weapon"] = pairs["attack"]
            elif "feature" in pairs:
                ev["action"]  = "feature"
                ev["feature"] = pairs["feature"]
            else:
                continue
            events.append(ev)

        clean = re.sub(r"\[(CHECK|COMBAT|SCENE|XP|COMPANION):[^\]]*\]", "", raw_text, flags=re.IGNORECASE)
        clean = re.sub(r"\[(ACTION|BONUS):[^\]]*\]", "", clean, flags=re.IGNORECASE)
        clean = re.sub(r"\[(BEAT|CLIMAX|BREAK)\]", "", clean, flags=re.IGNORECASE)
        clean = re.sub(r"\n{3,}", "\n\n", clean).strip()

        return clean, events

    def respond(self, session, character, player_input):
        messages  = self._messages_for_ollama(session, character, player_input)
        raw       = self._call_ollama(messages)

        narration, events = self._parse_events(raw)

        gs.add_history(session, "player", player_input)
        gs.add_history(session, "dm",     narration)

        for ev in events:
            if ev["type"] == "scene_change":
                session["location"] = ev["location"]
                session["scene"]    = narration

        return {"narration": narration, "events": events}


# ── Config helpers ─────────────────────────────────────────────────────────────

def load_config(path=None):
    if path is None:
        path = _DEFAULT_CONFIG
    if os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    return {"model": DEFAULT_OLLAMA_MODEL}


def save_config(config, path=None):
    if path is None:
        path = _DEFAULT_CONFIG
    with open(path, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2)


def from_config(path=None):
    cfg = load_config(path)
    return DungeonMaster(model=cfg.get("model"))
