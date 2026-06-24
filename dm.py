import json
import os
import re
import requests

import game_state as gs
from character import modifier

OLLAMA_URL         = "http://localhost:11434/api/chat"
GEMINI_URL         = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
DEFAULT_OLLAMA_MODEL = "llama3.1"
DEFAULT_GEMINI_MODEL = "gemini-1.5-flash"


class DungeonMaster:

    def __init__(self, backend="ollama", model=None, api_key=None):
        self.backend = backend.lower()
        self.api_key = api_key or os.environ.get("GEMINI_API_KEY", "")
        if self.backend == "ollama":
            self.model = model or DEFAULT_OLLAMA_MODEL
        elif self.backend == "gemini":
            self.model = model or DEFAULT_GEMINI_MODEL
        else:
            raise ValueError(f"Unknown backend '{backend}'. Use 'ollama' or 'gemini'.")

    # ── System prompt ──────────────────────────────────────────────────────────

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

        return f"""You are the Dungeon Master for a solo D&D 5e adventure. Run an immersive, story-driven game.

PLAYER CHARACTER:
  Name: {name}
  Race: {race}  |  Class: {cls}{subclass_str}  |  Level: {level}
  Background: {bg}
  Ability modifiers: {mod_str}
  Personality: {traits}
  Bonds: {bonds}

DM RULES:
1. Describe scenes vividly in 3-6 sentences. Engage the senses. React to what the player does.
2. When the player attempts something with an uncertain outcome, request a skill check on its own line:
   [CHECK: SkillName DC##]
   Example: [CHECK: Stealth DC14]
3. When combat should begin, list enemies on its own line:
   [COMBAT: EnemyName×count, EnemyName×count]
   Example: [COMBAT: Goblin×2, Hobgoblin×1]
   After writing this tag, stop — the game engine handles combat resolution. Resume narration when combat ends.
4. When the scene location changes, note it on its own line:
   [SCENE: Location Name]
5. Never break the fourth wall. Do not mention game mechanics, dice, or stats unprompted.
6. If this is the first message, open the adventure with a vivid scene that fits the character's background and class.
7. Keep responses focused. Do not write more than one scene at a time."""

    # ── Message builders ───────────────────────────────────────────────────────

    def _messages_for_ollama(self, session, character, player_input):
        messages = [{"role": "system", "content": self._build_system_prompt(character)}]
        for entry in session.get("history", []):
            role = "user" if entry["role"] == "player" else "assistant"
            messages.append({"role": role, "content": entry["text"]})
        messages.append({"role": "user", "content": player_input})
        return messages

    def _messages_for_gemini(self, session, character, player_input):
        contents = []
        for entry in session.get("history", []):
            role = "user" if entry["role"] == "player" else "model"
            contents.append({"role": role, "parts": [{"text": entry["text"]}]})
        contents.append({"role": "user", "parts": [{"text": player_input}]})
        # Gemini requires the first turn to be from the user
        if not contents or contents[0]["role"] != "user":
            contents.insert(0, {"role": "user",
                                 "parts": [{"text": "Begin the adventure."}]})
        return contents

    # ── Backend calls ──────────────────────────────────────────────────────────

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

    def _call_gemini(self, system_prompt, contents):
        if not self.api_key:
            raise RuntimeError(
                "No Gemini API key found.\n"
                "Set the GEMINI_API_KEY environment variable, or add it to dm_config.json."
            )
        url = GEMINI_URL.format(model=self.model)
        payload = {
            "systemInstruction": {"parts": [{"text": system_prompt}]},
            "contents":          contents,
            "generationConfig":  {"temperature": 0.9, "maxOutputTokens": 1024},
        }
        try:
            resp = requests.post(url, params={"key": self.api_key}, json=payload, timeout=60)
            resp.raise_for_status()
            data = resp.json()
            return data["candidates"][0]["content"]["parts"][0]["text"]
        except requests.exceptions.Timeout:
            raise RuntimeError("Gemini request timed out.")
        except requests.exceptions.HTTPError as e:
            raise RuntimeError(f"Gemini API error {resp.status_code}: {resp.text[:200]}")
        except (KeyError, IndexError):
            raise RuntimeError(f"Unexpected Gemini response format: {resp.text[:200]}")

    # ── Event parsing ──────────────────────────────────────────────────────────

    def _parse_events(self, raw_text):
        """Extract [CHECK:], [COMBAT:], [SCENE:] tags from the DM response.
        Returns (clean_narration, list_of_event_dicts).
        """
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

    # ── Main entry point ───────────────────────────────────────────────────────

    def respond(self, session, character, player_input):
        """Send a player action to the DM and return the response.

        Saves both turns to session history automatically.
        Returns:
            {
                "narration": str,       — text to display to the player
                "events":    list,      — parsed game events:
                    {"type": "skill_check",  "skill": str, "dc": int}
                    {"type": "combat_start", "enemies": [{name, count}]}
                    {"type": "scene_change", "location": str}
            }
        """
        if self.backend == "ollama":
            messages  = self._messages_for_ollama(session, character, player_input)
            raw       = self._call_ollama(messages)
        else:
            system   = self._build_system_prompt(character)
            contents = self._messages_for_gemini(session, character, player_input)
            raw      = self._call_gemini(system, contents)

        narration, events = self._parse_events(raw)

        gs.add_history(session, "player", player_input)
        gs.add_history(session, "dm",     narration)

        for ev in events:
            if ev["type"] == "scene_change":
                session["location"] = ev["location"]
                session["scene"]    = narration

        return {"narration": narration, "events": events}


# ── Config helpers ─────────────────────────────────────────────────────────────

def load_config(path="dm_config.json"):
    """Load backend config from dm_config.json. Falls back to Ollama defaults."""
    if os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    return {"backend": "ollama", "model": DEFAULT_OLLAMA_MODEL, "api_key": ""}


def save_config(config, path="dm_config.json"):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2)


def from_config(path="dm_config.json"):
    """Create a DungeonMaster from a dm_config.json file (or defaults)."""
    cfg = load_config(path)
    return DungeonMaster(
        backend = cfg.get("backend", "ollama"),
        model   = cfg.get("model"),
        api_key = cfg.get("api_key") or os.environ.get("GEMINI_API_KEY", ""),
    )
