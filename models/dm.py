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

OLLAMA_URL           = "http://localhost:11434/api/chat"
DEFAULT_OLLAMA_MODEL = "llama3.1"
_DEFAULT_CONFIG      = Path(__file__).parent.parent / "data" / "dm_config.json"

import requests


class DungeonMaster:

    def __init__(self, model=None):
        self.model = model or DEFAULT_OLLAMA_MODEL

    def _build_system_prompt(self, character):
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
9. If this is the first message, open with a vivid scene that fits the character's background and class.
10. Keep responses focused. One scene at a time."""

    def _messages_for_ollama(self, session, character, player_input):
        messages = [{"role": "system", "content": self._build_system_prompt(character)}]
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

        clean = re.sub(r"\[(CHECK|COMBAT|SCENE):[^\]]*\]", "", raw_text, flags=re.IGNORECASE)
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
