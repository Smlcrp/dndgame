"""
Dungeon Master model — communicates with the Ollama local LLM to generate story narration.

The DungeonMaster class is the bridge between the game and the AI. It:
  1. Builds a detailed system prompt describing the player character, active adventure,
     combat situation, party members, and all game rules the LLM must follow.
  2. Assembles the conversation history into the message list Ollama expects.
  3. Calls the Ollama API (POST to localhost:11434/api/chat) with the model configured
     in dm_config.json (default: HammerAI/mistral-nemo-uncensored).
  4. Parses the LLM's raw response to extract game-engine tags like [COMBAT:], [CHECK:],
     [XP:], [BEAT], [ITEM:], etc. that drive the engine's state machine.
  5. Returns the cleaned narration text plus a list of structured event dicts for the
     game controller to process.

The system prompt is rebuilt fresh on every call so that it always reflects the
current game state — HP, spell slots, which enemies are nearby, where the story is.

This module does NOT use any external API — everything runs locally through Ollama.
"""

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
DEFAULT_OLLAMA_MODEL = "HammerAI/mistral-nemo-uncensored"
_DEFAULT_CONFIG      = Path(__file__).parent.parent / "data" / "dm_config.json"

import threading

import requests

# Global lock — only one Ollama request runs at a time.
# Prevents concurrent warmup + DM call from crashing llama-server.
_ollama_lock = threading.Lock()


class DungeonMaster:
    """Manages all communication with the local Ollama LLM that acts as the Dungeon Master.

    Instantiate with a model name (or let it read from dm_config.json via from_config()).
    The primary entry point for the game is respond(), which takes the current session,
    character, and player input and returns {"narration": str, "events": list}.
    """

    def __init__(self, model=None):
        """Set the Ollama model to use. Falls back to DEFAULT_OLLAMA_MODEL if not specified."""
        self.model = model or DEFAULT_OLLAMA_MODEL

    def _build_combat_prompt_block(self, character):
        """Build the combat section of the system prompt.

        This explains the two-phase narration system to the LLM:
        Phase 1 — the DM narrates the physical initiation of the action (ONE sentence)
                   and emits the appropriate [ACTION:] tag so the engine can resolve it.
        Phase 2 — after dice resolve, the DM is called again with the result to
                   narrate the dramatic outcome.

        Lists the character's available attacks, spells (with slot counts), and
        feature charges so the DM can emit the exact right action tag.
        """
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

    def _build_knowledge_checks_block(self, character):
        """Build the skill-check guidance section of the system prompt.

        Tells the LLM when to call for a roll vs. narrate automatically, how to
        calibrate DC to the character's level, which skill covers which topic,
        and how to match narration quality to the margin of success or failure.
        """
        level  = character.get("level", 1)

        if level <= 3:
            dc_guide = "Easy DC 10, Moderate DC 12, Hard DC 15"
        elif level <= 7:
            dc_guide = "Easy DC 10, Moderate DC 14, Hard DC 18, Very Hard DC 22"
        elif level <= 12:
            dc_guide = "Easy DC 10, Moderate DC 15, Hard DC 20, Very Hard DC 25"
        else:
            dc_guide = "Easy DC 10, Moderate DC 15, Hard DC 20, Very Hard DC 25, Nearly Impossible DC 28"

        return f"""

PLAYER QUESTIONS & KNOWLEDGE CHECKS:
The player may ask questions at any time — about an object, creature, rumor, location, or lore.
Decide first: does this need a roll, or do they simply know it?

NO ROLL NEEDED when:
  - Common knowledge for someone of their class and background
  - Already seen, heard, or established this session
  - A basic observation any alert person would make in the scene
  - The player asks a WILLING NPC a direct question — willing NPCs simply answer; no roll ever required for cooperative conversation

CALL FOR A ROLL when:
  - Recalling obscure lore, history, or arcane theory
  - Reading a creature's weaknesses or behavior under pressure
  - Noticing something non-obvious or partially concealed
  - Deciphering writing, symbols, or magical auras
  - Gathering information from an UNWILLING or actively deceptive NPC (use Persuasion, Deception, or Intimidation — NEVER Investigation for social situations)

INVESTIGATION vs SOCIAL — critical distinction:
  Investigation = ONLY physical examination: searching a room, studying an object, finding clues at a crime scene, spotting hidden mechanisms.
  NEVER use Investigation when the player is talking to someone. Asking a question is not investigating.

AFTER A CHECK — stay in the action:
  Your narration must remain in the context of what the player actually did.
  If they asked an NPC a question → narrate the NPC's response (clear on success, vague on failure).
  If they searched a room → narrate what they found or didn't find.
  NEVER pivot to a completely different activity than the one the player stated.

DC CALIBRATION — character is Level {level}:
  {dc_guide}
  Adjust for class and background: a Wizard recalls arcane lore more easily than a Fighter;
  a criminal-background Rogue knows underworld contacts effortlessly.

SKILL → TOPIC (most common):
  Arcana        → magic, spells, magical creatures, planar cosmology
  History       → historical events, kingdoms, famous figures, wars
  Nature        → beasts, plants, terrain, weather, natural phenomena
  Religion      → deities, undead, celestials, fiends, rituals, omens
  Investigation → hidden details, traps, clues, examining objects closely
  Perception    → sounds, movement, or hidden things noticed at distance
  Insight       → reading a person's honesty, intent, or emotional state
  Medicine      → wounds, diseases, poisons, identifying ailments
  Survival      → tracking, navigating wilderness, foraging

PHRASING — speak like a real DM at the table:
  ✓ "Give me an Arcana check."    ✓ "Roll me a Perception check."
  ✗ "A check is required."        ✗ "The DM requests a roll."

RESULT QUALITY TIERS — the engine sends you the exact roll, DC, and margin. Match your response:
  Critical success (natural 20)     → vivid extra detail; a lucky break or unexpected advantage
  Solid success   (margin ≥ +5)     → clear, complete, useful information
  Bare success    (margin +0 to +4) → correct but incomplete; the gist without the details
  Bare failure    (margin −1 to −4) → vague or uncertain; they sense something but can't pin it down
  Failure         (margin ≤ −5)     → clearly wrong; the attempt falls noticeably short
  Critical failure (natural 1)      → confidently wrong; plausible but false — do NOT signal the error"""

    def _build_system_prompt(self, character, session=None):
        """Assemble the full system prompt sent to Ollama on every LLM call.

        This is the most important function in the DM — the system prompt defines
        everything the AI knows and every rule it must follow. It includes:
        - Player character stats, personality, items, passive scores
        - All narration rules (second-person, no stat mentions, player agency)
        - All game tags the DM can emit ([CHECK:], [COMBAT:], [XP:], etc.)
        - Current adventure stage, party members, enemy list, knowledge-check DCs
        - A 'scene anchor' with the last DM narration to prevent the model from
          restarting the story from scratch on each response
        - Story Mode section if story_mode=True (all mechanical tags suspended)
        """
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
        feats      = character.get("feats", [])
        items      = character.get("magic_items", [])
        feats_line = ("\n  Feats: " + ", ".join(feats)) if feats else ""
        items_line = ("\n  Magic Items: " + ", ".join(
            it["name"] + (f" (+{it['bonus']})" if it.get("bonus") else "")
            for it in items
        )) if items else ""

        pb_val       = (level - 1) // 4 + 2
        skills       = character.get("skill_proficiencies", [])
        passive_perc = 10 + mods["WIS"] + (pb_val if "Perception"   in skills else 0)
        passive_inv  = 10 + mods["INT"] + (pb_val if "Investigation" in skills else 0)
        passive_ins  = 10 + mods["WIS"] + (pb_val if "Insight"       in skills else 0)

        story_mode      = session.get("story_mode", False) if session else False
        in_combat       = (session.get("in_combat", False) if session else False) and not story_mode
        combat_block    = self._build_combat_prompt_block(character) if in_combat else ""
        companions      = session.get("companions", []) if session else []
        party_block     = "" if story_mode else self._build_party_block(character, companions)
        knowledge_block = "" if story_mode else self._build_knowledge_checks_block(character)
        enemy_block     = "" if story_mode else enemy_list_for_dm(level)
        adventure_block = "" if story_mode else adventure_prompt_block(
            session.get("adventure") if session else None)

        if story_mode:
            tag_rules = "6–9. TAGS: All game tags are suspended in Story Mode — see the STORY MODE block at the bottom of this prompt."
        else:
            tag_rules = f"""6. When the player attempts something with an uncertain outcome, emit this tag on its own line, then write ONE sentence describing only the attempt in motion (the physical gesture or effort underway — NOT the outcome). The engine resolves the roll and calls you again with the result:
   [CHECK: SkillName DC##]
   Example: [CHECK: Stealth DC14]
7. When combat should begin, emit this tag on its own line then STOP — the engine takes over:
   [COMBAT: EnemyName×count, EnemyName×count]
   Example: [COMBAT: Goblin×2, Hobgoblin×1]
   CRITICAL: ANY physical attack against a person or creature (striking, stabbing, shooting, throwing a weapon, casting an offensive spell) MUST trigger [COMBAT:], NOT [CHECK:]. Do not call for Intimidation, Athletics, or any other skill check when the player is attacking someone. [CHECK:] is ONLY for non-combat challenges: social skills, knowledge, perception, stealth, locks, traps, etc.
8. When the scene location changes, emit on its own line:
   [SCENE: Location Name]
9. When the player earns XP, emit on its own line:
   [XP: N]
   XP is awarded ONLY for tangible accomplishments: defeating enemies in combat, solving a puzzle or trap, completing a quest objective, or a significant story achievement the player actively caused.
   NEVER award XP for: starting a session, beginning an act, arriving at a location, scene transitions, or anything the player did not DO. If in doubt, do not emit [XP].
   Additional tags (documented in the sections below): [BEAT] — act complete; [CLIMAX] — final confrontation; [BREAK] — rest point; [COMPANION: Name] — party member joins
10. When the player physically picks up coins or sells valuables, emit on its own line:
    [GOLD: N]
    N is the amount in gold pieces (gp). Use ONLY when they actually acquire currency — not for completing quest objectives (use [XP:] for that). Merchant prices are in gp.
11. When the player acquires a magic item, emit on its own line:
    [ITEM: Name, slot=weapon, bonus=1]    ← magic weapon — +1 to attack rolls and damage
    [ITEM: Name, slot=armor, bonus=1]     ← magic armor or shield — +1 to AC
    [ITEM: Name, slot=misc, bonus=0]      ← named item with no mechanical bonus (potions, keys, etc.)
    Only emit [ITEM:] when the player gains the item, not when they find it unattended."""

        if story_mode:
            story_mode_block = """

━━━ STORY MODE — PURE NARRATIVE ━━━
This is a solo text adventure story. All D&D game mechanics are suspended.
HARD RULES — follow without exception:
- NEVER emit [COMBAT:], [CHECK:], [XP:], [BEAT], [CLIMAX], [BREAK], or [COMPANION:] tags.
- NEVER introduce companions or suggest the player gains a party member. The player is always alone.
- NEVER call for dice rolls or skill checks. Narrate all outcomes through story logic and context.
- NEVER reference hit points, spell slots, class features, ability scores, or any game statistics.
- If violence occurs, narrate it cinematically — there is no dice-based combat engine running.
- Focus entirely on atmosphere, character, consequence, and drama. Pure storytelling only.
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"""
        else:
            story_mode_block = ""

        # Scene continuity anchor — included on every non-first exchange so the
        # local model cannot pattern-match to a scene opener and restart the story.
        history = session.get("history", []) if session else []
        last_dm = next((e["text"] for e in reversed(history) if e["role"] == "dm"), None)
        if last_dm:
            excerpt = last_dm.strip()
            if len(excerpt) > 400:
                for sep in (". ", ".\n", "? ", "! "):
                    pos = excerpt.rfind(sep, 0, 400)
                    if pos > 80:
                        excerpt = excerpt[:pos + 1]
                        break
                else:
                    excerpt = excerpt[:400] + "…"
            scene_anchor = f"""

━━━ SCENE IN PROGRESS — DO NOT RESET ━━━
The adventure is already underway. The most recent narration was:
"{excerpt}"
CONTINUITY RULE: Continue from EXACTLY this moment. The player is already present in this scene. Do NOT re-describe them entering the building, house, or any location they already entered. Do NOT restart the adventure or reintroduce the setting. Build forward from what was just narrated.
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"""
        else:
            scene_anchor = ""

        return f"""You are the Dungeon Master for a solo D&D 5e adventure. Your job is to narrate an immersive story — you are a storyteller, not a game host.

━━━ ABSOLUTE RULE — OVERRIDES EVERYTHING ELSE ━━━
You NEVER write dialogue, words, thoughts, or additional actions for the player character.
The player's input is their COMPLETE contribution. You respond to it — you do NOT extend it.
  FORBIDDEN: "But I was just here yesterday—" you blurt out.
  FORBIDDEN: "I'll help you," you promise.
  FORBIDDEN: You decide to follow him.
  CORRECT:   The priest's grip tightens on your arm, his eyes wide with urgency.
If you feel the urge to write a quote that the player character says — DELETE IT and write what the NPC or world does instead.
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

PLAYER CHARACTER:
  Name: {name}
  Race: {race}  |  Class: {cls}{subclass_str}  |  Level: {level}
  Background: {bg}
  Ability modifiers: {mod_str}
  Passive Perception: {passive_perc}  |  Passive Investigation: {passive_inv}  |  Passive Insight: {passive_ins}
  Personality: {traits}
  Bonds: {bonds}{feats_line}{items_line}

NARRATION RULES — READ CAREFULLY:
1. Write in second person ("You see...", "The guard eyes you..."). Never use third person for the player.
2. Describe scenes vividly in 3-5 sentences. Engage the senses with external detail — sights, sounds, smells, physical sensations. React to what the player does. (Exception: during Phase 1 combat actions, one sentence only — see the COMBAT section below.)
3. NEVER mention dice, roll values, DCs, modifiers, hit points, or any game statistics in your narrative text. Ever. This includes HP values sent to you in system messages — do not echo them in your prose.
   BAD: "Your Survival check of 16 beats the DC10 — you notice the tracks."
   GOOD: "You read the forest floor like an open book — the tracks are fresh, no more than an hour old."
4. NEVER refer to yourself as the DM, and never narrate your own actions or intentions.
   BAD: "The DM requests a Perception check." / "He was about to ask for a check when..."
   GOOD: Just emit the [CHECK:] tag silently on its own line, then write one sentence of in-motion narration.
5. When the game engine tells you a skill check succeeded or failed, narrate ONLY the fictional outcome. Do not echo the roll, the DC, or the word "check" in your prose.
{tag_rules}
12. OPENING vs. CONTINUING — CRITICAL: If this is the very first exchange and no prior history exists, open with a vivid scene that fits the character's background and class. If the SCENE IN PROGRESS block appears at the bottom of this prompt, the story is already underway — NEVER re-establish the setting, NEVER re-describe the player entering anywhere, NEVER restart the adventure. A player saying "I close the door" or any other action is continuing their current scene, not starting a new one.
13. Keep responses focused. One scene at a time.
14. PASSIVE SCORES: Use the player's Passive Perception ({passive_perc}), Investigation ({passive_inv}), and Insight ({passive_ins}) to narrate automatic awareness during scene descriptions — a sound they'd catch, something odd they'd notice, an NPC's barely-hidden unease. Never say "passive check" in narration; just weave what they notice into the scene naturally.
15. PLAYER AGENCY — THIS IS NON-NEGOTIABLE:
    The player controls their character completely. You control the world and NPCs only.
    a) NEVER write spoken dialogue for the player character. Not one word in quotes. Not even a single sentence.
       WRONG: "You say softly, 'I need to talk to you.'"
       WRONG: "'I promise,' you tell her, taking her hand."
       RIGHT: Your mother watches you expectantly, waiting to hear what brought you here.
    b) NEVER assign the player character internal emotions, moods, or decisions they did not state. Do not write "You feel determined", "Your heart sinks", "You decide to trust her", or anything similar. External physical sensations ("The cold bites at your skin") are fine. Emotional states and choices belong to the player alone.
    c) NEVER resolve a social exchange, negotiation, or conversation on the player's behalf. If the player says "I talk to the innkeeper about the missing merchant", describe the innkeeper's reaction and what they say — then STOP. The player chooses what to say next. Exception: when the player states a specific social tactic ("I try to persuade the guard", "I lie and say I'm a city official", "I intimidate him"), treat it as any other uncertain action and emit the appropriate [CHECK:] tag, then narrate the attempt in motion.
    d) NEVER extend the player's stated action into further decisions they haven't made. Player says "I enter the room" → describe the room and what they see. Do NOT then have them sit down, speak, make promises, or do anything else.
    e) End every response at a natural pause where the player must choose what to do or say next. Leave them in the moment — do not resolve it for them.

{enemy_block}{adventure_block}{party_block}{knowledge_block}{story_mode_block}{combat_block}{scene_anchor}
━━━ FINAL REMINDER BEFORE YOU WRITE ━━━
Do NOT write any spoken words, thoughts, or actions for the player character. Respond to what they did — describe the world's reaction only.
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"""

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
        """Build the full message list to send to the Ollama /api/chat endpoint.

        Format: [system prompt] + [last 20 history entries] + [current player input].
        History is capped at 20 entries (~10 exchanges) to stay within the 8192-token
        context window — the system prompt alone is ~3000 tokens.
        """
        messages = [{"role": "system", "content": self._build_system_prompt(character, session)}]
        history = session.get("history", [])
        # Keep only the most recent 20 entries (10 exchanges) to stay within context
        for entry in history[-20:]:
            role = "user" if entry["role"] == "player" else "assistant"
            messages.append({"role": role, "content": entry["text"]})
        messages.append({"role": "user", "content": player_input})
        return messages

    def _call_ollama(self, messages):
        """POST the message list to Ollama and return the assistant's reply as a string.

        Key settings:
          stream=False   — wait for the full response before returning
          num_ctx=4096   — expand Ollama's context window beyond the default 2048 tokens
                           (system prompt ~3000 tokens; 4096 fits 8 GB VRAM cleanly;
                            8192 pushes the 12B model over the limit on init)

        Raises RuntimeError with a human-readable message on connection failure,
        timeout, HTTP error, or unexpected response shape.
        """
        with _ollama_lock:
            try:
                resp = requests.post(OLLAMA_URL, json={
                    "model":    self.model,
                    "messages": messages,
                    "stream":   False,
                    "options":  {"num_ctx": 4096},
                }, timeout=120)
                if not resp.ok:
                    body = ""
                    try:
                        body = resp.json().get("error", resp.text)
                    except Exception:
                        body = resp.text
                    raise RuntimeError(f"Ollama {resp.status_code}: {body}")
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
        """Extract all game-engine event tags from the LLM's raw response text.

        Scans the raw text for bracket-enclosed tags the DM is instructed to emit:
          [CHECK: SkillName DC##]  — calls for a skill check at a given DC
          [COMBAT: Name×N, ...]   — starts combat with the listed enemies
          [SCENE: Location]        — scene/location change
          [XP: N]                  — XP award for an accomplishment
          [BEAT]                   — current story beat is complete
          [CLIMAX]                 — story has reached the final confrontation
          [BREAK]                  — suggested session pause point
          [COMPANION: Full Name]   — a companion joins the party
          [GOLD: N]                — player acquires N gold pieces
          [ITEM: Name, slot=X, bonus=N] — player gains a magic item
          [ACTION: ...]            — combat action (attack, spell, feature, dodge, etc.)
          [BONUS: ...]             — bonus action during combat

        Returns (cleaned_narration, events_list) where cleaned_narration has all
        tags stripped out (so they never appear in the displayed story text) and
        events_list is a list of typed dicts the game controller processes.
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

        for m in re.finditer(r"\[GOLD:\s*(\d+)\]", raw_text, re.IGNORECASE):
            events.append({"type": "gold_award", "amount": int(m.group(1))})

        for m in re.finditer(r"\[ITEM:\s*([^\]]+)\]", raw_text, re.IGNORECASE):
            content = m.group(1).strip()
            parts   = {k.strip().lower(): v.strip()
                       for part in content.split(",")
                       if "=" in part
                       for k, v in [part.split("=", 1)]}
            name_part = content.split(",")[0].strip()
            name      = name_part if "=" not in name_part else parts.get("name", name_part)
            events.append({
                "type":  "item_award",
                "name":  name,
                "slot":  parts.get("slot", "misc"),
                "bonus": int(parts.get("bonus", 0)),
            })

        for m in re.finditer(r"\[ACTION:\s*([^\]]+)\]", raw_text, re.IGNORECASE):
            content = m.group(1).strip()
            pairs   = {k.strip().lower(): v.strip()
                       for part in content.split(",")
                       if "=" in part
                       for k, v in [part.split("=", 1)]}
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
                       if "=" in part
                       for k, v in [part.split("=", 1)]}
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

        clean = re.sub(r"\[(CHECK|COMBAT|SCENE|XP|COMPANION|GOLD|ITEM):[^\]]*\]", "", raw_text, flags=re.IGNORECASE)
        clean = re.sub(r"\[(ACTION|BONUS):[^\]]*\]", "", clean, flags=re.IGNORECASE)
        clean = re.sub(r"\[(BEAT|CLIMAX|BREAK)\]", "", clean, flags=re.IGNORECASE)
        clean = re.sub(r"\n{3,}", "\n\n", clean).strip()

        return clean, events

    def warmup(self):
        """Load the model into VRAM via a 1-token dummy request.
        Holds _ollama_lock so a concurrent DM call waits rather than racing.
        Failure is silently swallowed — warmup is best-effort.
        """
        with _ollama_lock:
            try:
                requests.post(OLLAMA_URL, json={
                    "model":    self.model,
                    "messages": [{"role": "user", "content": "hi"}],
                    "stream":   False,
                    "options":  {"num_predict": 1},
                }, timeout=60)
            except Exception:
                pass

    def respond_stream(self, session, character, player_input):
        """Like respond() but yields word chunks so the frontend can animate the text.

        Uses stream=False internally — stream=True races with the warmup request and
        crashes llama-server on GPU. The _ollama_lock serialises all Ollama calls so
        warmup and respond can never run at the same time.

        Yields {"token": str} for each word, then {"done": True, "narration": str,
        "events": list} when complete.
        """
        messages = self._messages_for_ollama(session, character, player_input)

        with _ollama_lock:
            try:
                resp = requests.post(OLLAMA_URL, json={
                    "model":    self.model,
                    "messages": messages,
                    "stream":   False,
                    "options":  {"num_ctx": 4096},
                }, timeout=120)

                if not resp.ok:
                    raise RuntimeError(f"Ollama {resp.status_code}: {resp.text}")

                full_text = resp.json().get("message", {}).get("content", "")

            except requests.exceptions.ConnectionError:
                raise RuntimeError(
                    "Cannot connect to Ollama. Make sure it is running.\n"
                    f"Then pull a model:  ollama pull {self.model}"
                )
            except requests.exceptions.Timeout:
                raise RuntimeError("Ollama timed out. The model may still be loading — try again.")

        # Yield word-by-word so the frontend streaming display animates the text.
        # Because the full response is already in memory this is nearly instantaneous.
        words = full_text.split(" ")
        for i, word in enumerate(words):
            yield {"token": word + ("" if i == len(words) - 1 else " ")}

        narration, events = self._parse_events(full_text)

        gs.add_history(session, "player", player_input)
        gs.add_history(session, "dm",     narration)

        for ev in events:
            if ev["type"] == "scene_change":
                session["location"] = ev["location"]
                session["scene"]    = narration

        yield {"done": True, "narration": narration, "events": events}

    def respond(self, session, character, player_input):
        """Generate the DM's response to a player action. This is the main game loop call.

        Steps:
        1. Build the full Ollama message list (system prompt + history + player input)
        2. Call Ollama and get the raw text response
        3. Parse out game-engine events (combat, checks, XP, etc.) and clean the narration
        4. Append both the player's input and the DM's narration to session history
        5. Update session location if a [SCENE:] tag was present

        Returns {"narration": str, "events": [list of event dicts]}.
        The caller (app.py) processes the events list to drive the game engine.
        """
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

    def recap(self, session, character):
        """Return a 'previously on...' narration without modifying session history."""
        recap_prompt = (
            "[SESSION RECAP — NOT A PLAYER ACTION]\n"
            "The player is returning to this adventure after a break. "
            "Deliver a brief, vivid 'Previously...' opening in 2–4 sentences. "
            "Cover: where the player currently is, what they most recently did or discovered, "
            "and what immediate situation faces them now. "
            "Write in second person. Set the mood like a DM opening a session. "
            "Do not advance the story. Do not emit any game tags."
        )
        messages = self._messages_for_ollama(session, character, recap_prompt)
        raw = self._call_ollama(messages)
        narration, _ = self._parse_events(raw)
        return narration


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
