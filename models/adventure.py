import random
import sys
from pathlib import Path
_root = Path(__file__).parent.parent
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))

_TEMPLATES = [
    {
        "title": "The Missing Merchant",
        "setting": "town",
        "hook": (
            "A wealthy merchant has vanished three days before a vital trade deal. "
            "The town council is desperate — and offering a reward."
        ),
        "antagonist": {
            "name": "Aldric Vane",
            "role": "Smuggling Ring Leader",
            "motivation": "Greed. He runs a shadow trade in stolen goods and silences anyone who gets too close.",
            "plan": "He has the merchant locked in a cellar while negotiating ransom, planning to flee the region once paid.",
        },
        "beats": [
            "Investigate the merchant's last known location. Clues in the warehouse district and a shady contact who saw something point the way.",
            "The contact leads to a guarded warehouse. Breaking in reveals the smuggling records and the merchant's whereabouts.",
            "Race to the hidden cellar before Aldric's men move the prisoner. Aldric is there — cornered and dangerous.",
        ],
        "climax": "Confront Aldric Vane directly. He has armed guards and will not surrender without a fight.",
        "resolution": "The merchant is freed and the town pays the reward. Aldric faces justice or flees the region for good.",
    },
    {
        "title": "The Haunted Mill",
        "setting": "wilderness",
        "hook": (
            "The old mill on the edge of town has gone dark. Workers refuse to enter "
            "after one was found dead with no visible wounds. The miller's family begs for help."
        ),
        "antagonist": {
            "name": "The Wrathful Miller",
            "role": "Restless Spirit",
            "motivation": "Murdered by his business partner for the deed to the mill, his spirit cannot rest until the truth is exposed.",
            "plan": "He haunts the mill with increasing violence, unable to communicate what happened — only to lash out at intruders.",
        },
        "beats": [
            "Explore the mill and survive the initial haunting. Strange visions reveal the miller's final moments and hint at betrayal.",
            "Investigate the business partner — find the forged deed hidden in his home. He realises the trail is closing and tries to flee.",
            "Return to the mill with the evidence. The spirit manifests fully — it can be put to rest with proof, or fought.",
        ],
        "climax": "Face the wrathful spirit at full power. Reason with it using the evidence, or fight it to a standstill.",
        "resolution": "The spirit passes on. The partner faces justice. The miller's family inherits what's theirs.",
    },
    {
        "title": "Raiders at the Crossroads",
        "setting": "wilderness",
        "hook": (
            "A farming village has been raided twice this month — livestock stolen, a barn burned. "
            "The raiders strike at night and vanish into the forest. The village elder asks for help."
        ),
        "antagonist": {
            "name": "Sergeant Brynn",
            "role": "Deserter-turned-Bandit Captain",
            "motivation": "A disgraced soldier who led his unit into desertion. He believes the world owes him and takes what he needs.",
            "plan": "He runs a disciplined bandit camp in the forest, scouts targets carefully, and will not hesitate to make examples.",
        },
        "beats": [
            "Track the raiders from the last attack site into the forest. A survivor or captive reveals the camp's general location.",
            "Scout the bandit camp — it's fortified and well-organised. Brynn's second-in-command is brutal and will harm hostages.",
            "Assault the camp or lure Brynn out. He fights tactically and has a backup escape route through the forest.",
        ],
        "climax": "Face Sergeant Brynn in a direct confrontation. He's a hardened veteran who fights dirty and knows every shadow of this forest.",
        "resolution": "The camp is broken up and the village is safe. Brynn is killed, captured, or driven off for good.",
    },
    {
        "title": "The Stolen Relic",
        "setting": "urban",
        "hook": (
            "A sacred relic has been taken from the city's main temple. "
            "The priests are in crisis — a dark ritual requires it. Time is running out."
        ),
        "antagonist": {
            "name": "Sister Morvaine",
            "role": "Fallen Cleric",
            "motivation": "She lost her faith after the temple failed her in her hour of need. Now she seeks to curse the city that abandoned her.",
            "plan": "She stole the relic and plans to corrupt it during the next new moon — three nights away. Cultists guard her sanctum.",
        },
        "beats": [
            "Investigate the theft at the temple. Witnesses point to someone with inside knowledge — a former temple initiate.",
            "Follow the trail into the city's underside. A cult safehouse, a skirmish, and a map to the sanctum beneath the city.",
            "Enter the sanctum. Guards are fanatical and the ritual has already begun — there is no time to waste.",
        ],
        "climax": "Confront Sister Morvaine mid-ritual. Stopping her means destroying the corrupted relic or breaking her concentration.",
        "resolution": "The ritual is stopped and the city is spared. Morvaine faces justice or death. The temple offers healing and reward.",
    },
    {
        "title": "Depths of the Old Keep",
        "setting": "dungeon",
        "hook": (
            "Treasure hunters entered the abandoned keep a week ago. Only one returned — raving about what woke up down there. "
            "The keep's cellars are said to hold a vault worth a fortune."
        ),
        "antagonist": {
            "name": "The Warden",
            "role": "Ancient Guardian Construct",
            "motivation": "Bound to protect the vault for an empire long dead. It follows its last orders with merciless precision.",
            "plan": "It has sealed the lower levels and is systematically eliminating intruders, setting traps and herding prey.",
        },
        "beats": [
            "Descend into the upper level. Traps and the surviving hunters' notes reveal the layout and warn of what waits below.",
            "Navigate the warded middle level. The Warden is active — it can be avoided or fought. Old carvings hint at a command word.",
            "Reach the vault level. The Warden is in full defensive mode. Clues found above may offer a way to deactivate it.",
        ],
        "climax": "Face the Warden at the vault door. It must be defeated or deactivated using the command word hidden in the keep's history.",
        "resolution": "The vault is opened and the treasure is real. The Warden, deactivated or destroyed, rests after centuries of empty duty.",
    },
    {
        "title": "The Plague Wind",
        "setting": "wilderness",
        "hook": (
            "A village is afflicted with a creeping sickness — not natural disease. "
            "Livestock die, crops blacken, people weaken. A hedge witch says something foul lurks in the bog to the north."
        ),
        "antagonist": {
            "name": "Malgrath",
            "role": "Green Hag",
            "motivation": "Driven from the bog by the village's founders generations ago, she has waited patiently for revenge.",
            "plan": "She has been poisoning the water source with a slow-acting hex. The curse becomes permanent within a week.",
        },
        "beats": [
            "Investigate the village and trace the contamination to the well. Purifying it buys time but does not break the curse.",
            "Enter the bog. Malgrath's minions — blights and ensorcelled animals — watch every path. A corrupted shrine must be destroyed.",
            "Find Malgrath's sanctum deep in the bog. She is aware the adventurer is coming and has prepared her most powerful hex.",
        ],
        "climax": "Face Malgrath in her sanctum. She uses the terrain, illusions, and fear. Killing her or shattering her staff ends the curse.",
        "resolution": "The curse lifts and the village recovers. The hag's sanctum crumbles into the bog.",
    },
    {
        "title": "The Assassin's Mark",
        "setting": "urban",
        "hook": (
            "A city official has received a death threat — and their usual guards were found unconscious this morning. "
            "They have hired protection quietly, not wanting to cause a panic."
        ),
        "antagonist": {
            "name": "The Whisper",
            "role": "Guild Assassin",
            "motivation": "A professional contract. The Whisper will complete the job regardless of who stands in the way.",
            "plan": "Three attempts planned, each more direct than the last. The Whisper has informants and has already studied the target's schedule.",
        },
        "beats": [
            "Protect the official through the first attempt — a poisoning at a dinner event. Neutralising it reveals a cipher note from the guild.",
            "Decode the cipher to find a guild safehouse. It reveals who hired the Whisper and when the next attempt is planned.",
            "The second attempt is a street ambush. Surviving it and capturing a contact reveals the Whisper's final approach.",
        ],
        "climax": "Face the Whisper directly on their final, personal attempt. They have studied the adventurer's style and fight with cold precision.",
        "resolution": "The Whisper is stopped and the contractor is exposed. The official survives and the city owes a significant favour.",
    },
    {
        "title": "Blood and Salt",
        "setting": "coastal",
        "hook": (
            "Ships have been disappearing off the headland. The latest carried a merchant's entire fortune. "
            "A coastal town is in economic crisis and the harbormaster suspects something unnatural."
        ),
        "antagonist": {
            "name": "Captain Dravek",
            "role": "Wrecking Crew Leader and Warlock",
            "motivation": "He made a pact with something in the depths for power over the sea. In return he feeds it — treasure and souls.",
            "plan": "His crew uses a sea-cave on the headland to lure ships onto rocks with false lights, then strip the wreck.",
        },
        "beats": [
            "Investigate the docks and talk to survivors. Evidence points to the headland and a hidden path along the cliffs.",
            "Find the sea-cave entrance — guarded and trapped. Inside: stolen cargo, captives, and signs of the pact ritual.",
            "Confront Dravek's crew in the cave. His pact lets him call a water elemental or summon fog to cover retreat.",
        ],
        "climax": "Face Captain Dravek. He invokes his pact for one final edge — but the thing in the depths does not rescue its pawns.",
        "resolution": "The wrecking stops and the captives go free. The stolen cargo is partly recovered. Something deep below stirs, then goes quiet.",
    },
]

_CLIMAX_XP = 800

PRESETS = {
    "One Shot": {"beats": 1, "estimate": "~1–2h"},
    "Quest":    {"beats": 3, "estimate": "~3–4h"},
    "Epic":     {"beats": 5, "estimate": "~5–8h"},
}

def _build_beats(template, beat_count):
    base = list(template["beats"])   # always 3 entries per template
    ant  = template["antagonist"]["name"]
    if beat_count == 1:
        return [template["climax"]]
    if beat_count == 3:
        return base
    if beat_count == 5:
        return [
            base[0],
            f"Complications deepen. {ant}'s reach extends further than expected — new obstacles and unexpected discoveries reshape the path forward.",
            base[1],
            f"Crisis point. {ant} is fully aware of the pursuit and makes a decisive, dangerous move.",
            base[2],
        ]
    return base[:beat_count]

def _beat_xp_for_preset(preset):
    n = PRESETS.get(preset, PRESETS["Quest"])["beats"]
    if n == 1:
        return [600]
    if n == 3:
        return [150, 300, 500]
    if n == 5:
        return [100, 150, 200, 300, 450]
    return [150, 300, 500]

def _stage_labels(n_story_beats):
    labels = ["HOOK — establish the situation, introduce the threat, draw the player in"]
    for i in range(n_story_beats):
        idx = i + 1
        if idx == 1 and n_story_beats == 1:
            labels.append("FINAL ACT — the confrontation; everything hinges on this moment")
        elif idx == 1:
            labels.append("ACT 1 — first significant encounter; stakes become real")
        elif idx == n_story_beats:
            labels.append(f"ACT {idx} — crisis point; the finale is within reach but the cost is high")
        elif idx == n_story_beats - 1:
            labels.append(f"ACT {idx} — complication and rising tension; things get harder before they get better")
        else:
            labels.append(f"ACT {idx} — the story deepens; complications escalate")
    labels.append("CLIMAX — the final confrontation with the antagonist")
    labels.append("RESOLUTION — aftermath, reward, and closure")
    return labels


def generate_adventure(char, preset="Quest"):
    """Return a fresh adventure dict for the given character and preset."""
    template  = random.choice(_TEMPLATES)
    p         = PRESETS.get(preset, PRESETS["Quest"])
    beats     = _build_beats(template, p["beats"])
    beat_xp   = _beat_xp_for_preset(preset)
    return {
        "preset":       preset,
        "title":        template["title"],
        "setting":      template["setting"],
        "hook":         template["hook"],
        "antagonist":   dict(template["antagonist"]),
        "beats":        beats,
        "climax":       template["climax"],
        "resolution":   template["resolution"],
        "current_beat": 0,
        "beat_xp":      beat_xp,
        "climax_xp":    _CLIMAX_XP,
    }


def advance_beat(adventure):
    """Advance to the next beat. Returns the XP award for this beat (0 if capped)."""
    beat         = adventure.get("current_beat", 0)
    n_story_beats = len(adventure.get("beats", []))
    if beat > n_story_beats:
        return 0
    xp = adventure["beat_xp"][beat] if beat < len(adventure["beat_xp"]) else 0
    adventure["current_beat"] = beat + 1
    return xp


def adventure_prompt_block(adventure):
    """Return the adventure section injected into the DM system prompt."""
    if not adventure:
        return ""

    beat          = adventure.get("current_beat", 0)
    preset        = adventure.get("preset", "Quest")
    n_story_beats = len(adventure.get("beats", []))
    labels        = _stage_labels(n_story_beats)
    stage         = labels[min(beat, len(labels) - 1)]
    ant           = adventure["antagonist"]
    beats         = "\n".join(f"  Beat {i+1}: {b}" for i, b in enumerate(adventure["beats"]))

    scope_lines = {
        "One Shot": "SCOPE: One-shot — deliver a complete, satisfying confrontation in a single compact session. Reach the climax briskly; do not pad.",
        "Epic":     "SCOPE: Epic campaign — let each act breathe fully. Build subplots, deepen NPC relationships, and escalate tension gradually across multiple sessions.",
    }
    scope_block = f"\n{scope_lines[preset]}" if preset in scope_lines else ""

    return f"""
ADVENTURE: {adventure['title']}{scope_block}

Hook: {adventure['hook']}

Antagonist: {ant['name']} ({ant['role']})
  Motivation: {ant['motivation']}
  Plan in motion: {ant['plan']}

Story structure:
{beats}
  Climax: {adventure['climax']}
  Resolution: {adventure['resolution']}

CURRENT STAGE: {stage}
Steer the story toward this stage. Do not rush ahead — let each beat breathe and give the player time to engage.

BEAT RULES — read carefully:
- [BEAT] means the player has COMPLETED the current stage through their own actions and choices. It takes multiple back-and-forth exchanges before a stage is ever complete.
- NEVER emit [BEAT] in your opening scene or on the first response. The hook must actually play out.
- NEVER emit [BEAT] just because you narrated something. The player must have done something meaningful to resolve it.
- When the CURRENT STAGE is fully resolved (player has explored, fought, discovered, or decided their way through it) and a natural pause occurs, emit on its own line:
  [BEAT]    — this beat is complete, story moves to the next act
  [CLIMAX]  — the story has reached the final confrontation (use instead of [BEAT] for the last act)
When the scene reaches a natural resting point where a real player could comfortably stop, also emit:
  [BREAK]   — a suggested session pause; the story continues if the player wants to keep going"""
