"""
Valid D&D 5e options for character creation (PHB + common supplements).
"""

RACES = [
    "Dragonborn",
    "Dwarf (Hill)",
    "Dwarf (Mountain)",
    "Elf (Drow / Dark)",
    "Elf (High)",
    "Elf (Wood)",
    "Gnome (Forest)",
    "Gnome (Rock)",
    "Half-Elf",
    "Half-Orc",
    "Halfling (Lightfoot)",
    "Halfling (Stout)",
    "Human",
    "Human (Variant)",
    "Tiefling",
    "Aasimar",
    "Firbolg",
    "Genasi (Air)",
    "Genasi (Earth)",
    "Genasi (Fire)",
    "Genasi (Water)",
    "Goblin",
    "Goliath",
    "Kenku",
    "Lizardfolk",
    "Tabaxi",
    "Triton",
    "Yuan-ti Pureblood",
]

CLASSES = [
    "Artificer",
    "Barbarian",
    "Bard",
    "Cleric",
    "Druid",
    "Fighter",
    "Monk",
    "Paladin",
    "Ranger",
    "Rogue",
    "Sorcerer",
    "Warlock",
    "Wizard",
]

SUBCLASSES = {
    "Artificer": [
        "Alchemist",
        "Armorer",
        "Artillerist",
        "Battle Smith",
    ],
    "Barbarian": [
        "Path of the Ancestral Guardian",
        "Path of the Battlerager",
        "Path of the Beast",
        "Path of the Berserker",
        "Path of the Storm Herald",
        "Path of the Totem Warrior",
        "Path of the Wild Magic",
        "Path of the Zealot",
    ],
    "Bard": [
        "College of Creation",
        "College of Eloquence",
        "College of Glamour",
        "College of Lore",
        "College of Spirits",
        "College of Swords",
        "College of Valor",
        "College of Whispers",
    ],
    "Cleric": [
        "Arcana Domain",
        "Death Domain",
        "Forge Domain",
        "Grave Domain",
        "Knowledge Domain",
        "Life Domain",
        "Light Domain",
        "Nature Domain",
        "Order Domain",
        "Peace Domain",
        "Tempest Domain",
        "Trickery Domain",
        "Twilight Domain",
        "War Domain",
    ],
    "Druid": [
        "Circle of Dreams",
        "Circle of Spores",
        "Circle of Stars",
        "Circle of the Land",
        "Circle of the Moon",
        "Circle of the Shepherd",
        "Circle of Wildfire",
    ],
    "Fighter": [
        "Arcane Archer",
        "Banneret",
        "Battle Master",
        "Cavalier",
        "Champion",
        "Echo Knight",
        "Eldritch Knight",
        "Psi Warrior",
        "Rune Knight",
        "Samurai",
    ],
    "Monk": [
        "Way of Mercy",
        "Way of Shadow",
        "Way of the Ascendant Dragon",
        "Way of the Astral Self",
        "Way of the Drunken Master",
        "Way of the Four Elements",
        "Way of the Kensei",
        "Way of the Long Death",
        "Way of the Open Hand",
        "Way of the Sun Soul",
    ],
    "Paladin": [
        "Oath of Conquest",
        "Oath of Devotion",
        "Oath of Glory",
        "Oath of Redemption",
        "Oath of the Ancients",
        "Oath of the Crown",
        "Oath of Vengeance",
        "Oath of the Watchers",
        "Oathbreaker",
    ],
    "Ranger": [
        "Beast Master",
        "Drakewarden",
        "Fey Wanderer",
        "Gloom Stalker",
        "Horizon Walker",
        "Hunter",
        "Monster Slayer",
        "Swarmkeeper",
    ],
    "Rogue": [
        "Arcane Trickster",
        "Assassin",
        "Inquisitive",
        "Mastermind",
        "Phantom",
        "Scout",
        "Soulknife",
        "Swashbuckler",
        "Thief",
    ],
    "Sorcerer": [
        "Aberrant Mind",
        "Clockwork Soul",
        "Divine Soul",
        "Draconic Bloodline",
        "Shadow Magic",
        "Storm Sorcery",
        "Wild Magic",
    ],
    "Warlock": [
        "The Archfey",
        "The Celestial",
        "The Fathomless",
        "The Fiend",
        "The Genie",
        "The Great Old One",
        "The Hexblade",
        "The Undead",
        "The Undying",
    ],
    "Wizard": [
        "School of Abjuration",
        "School of Bladesinging",
        "School of Chronurgy",
        "School of Conjuration",
        "School of Divination",
        "School of Enchantment",
        "School of Evocation",
        "School of Graviturgy",
        "School of Illusion",
        "School of Necromancy",
        "School of Order of Scribes",
        "School of Transmutation",
        "School of War Magic",
    ],
}

BACKGROUNDS = [
    "Acolyte",
    "Anthropologist",
    "Archaeologist",
    "Athlete",
    "Charlatan",
    "City Watch",
    "Clan Crafter",
    "Cloistered Scholar",
    "Courtier",
    "Criminal",
    "Entertainer",
    "Faction Agent",
    "Far Traveler",
    "Fisher",
    "Folk Hero",
    "Gladiator",
    "Guild Artisan",
    "Guild Merchant",
    "Haunted One",
    "Hermit",
    "Inheritor",
    "Investigator",
    "Knight",
    "Knight of the Order",
    "Marine",
    "Mercenary Veteran",
    "Noble",
    "Outlander",
    "Pirate",
    "Sage",
    "Sailor",
    "Soldier",
    "Spy",
    "Urban Bounty Hunter",
    "Urchin",
    "Uthgardt Tribe Member",
    "Waterdhavian Noble",
]

ALIGNMENTS = [
    "Lawful Good",
    "Neutral Good",
    "Chaotic Good",
    "Lawful Neutral",
    "True Neutral",
    "Chaotic Neutral",
    "Lawful Evil",
    "Neutral Evil",
    "Chaotic Evil",
]

# Racial ability score bonuses.
# "fixed"    → {ability: bonus} always applied
# "flexible" → player chooses which stats get bonuses
#   count  : how many stats to pick
#   amount : bonus per pick
#   exclude: stats that can't be chosen (already covered by fixed)
RACIAL_BONUSES = {
    "Dragonborn":        {"fixed": {"strength": 2, "charisma": 1},           "flexible": None},
    "Dwarf (Hill)":      {"fixed": {"constitution": 2, "wisdom": 1},         "flexible": None},
    "Dwarf (Mountain)":  {"fixed": {"strength": 2, "constitution": 2},       "flexible": None},
    "Elf (Drow / Dark)": {"fixed": {"dexterity": 2, "charisma": 1},          "flexible": None},
    "Elf (High)":        {"fixed": {"dexterity": 2, "intelligence": 1},      "flexible": None},
    "Elf (Wood)":        {"fixed": {"dexterity": 2, "wisdom": 1},            "flexible": None},
    "Gnome (Forest)":    {"fixed": {"intelligence": 2, "dexterity": 1},      "flexible": None},
    "Gnome (Rock)":      {"fixed": {"intelligence": 2, "constitution": 1},   "flexible": None},
    "Half-Elf":          {"fixed": {"charisma": 2},
                          "flexible": {"count": 2, "amount": 1, "exclude": ["charisma"]}},
    "Half-Orc":          {"fixed": {"strength": 2, "constitution": 1},       "flexible": None},
    "Halfling (Lightfoot)": {"fixed": {"dexterity": 2, "charisma": 1},       "flexible": None},
    "Halfling (Stout)":  {"fixed": {"dexterity": 2, "constitution": 1},      "flexible": None},
    "Human":             {"fixed": {"strength": 1, "dexterity": 1, "constitution": 1,
                                    "intelligence": 1, "wisdom": 1, "charisma": 1},
                          "flexible": None},
    "Human (Variant)":   {"fixed": {},
                          "flexible": {"count": 2, "amount": 1, "exclude": []}},
    "Tiefling":          {"fixed": {"intelligence": 1, "charisma": 2},       "flexible": None},
    "Aasimar":           {"fixed": {"wisdom": 1, "charisma": 2},             "flexible": None},
    "Firbolg":           {"fixed": {"wisdom": 2, "strength": 1},             "flexible": None},
    "Genasi (Air)":      {"fixed": {"constitution": 2, "dexterity": 1},      "flexible": None},
    "Genasi (Earth)":    {"fixed": {"constitution": 2, "strength": 1},       "flexible": None},
    "Genasi (Fire)":     {"fixed": {"constitution": 2, "intelligence": 1},   "flexible": None},
    "Genasi (Water)":    {"fixed": {"constitution": 2, "wisdom": 1},         "flexible": None},
    "Goblin":            {"fixed": {"dexterity": 2, "constitution": 1},      "flexible": None},
    "Goliath":           {"fixed": {"strength": 2, "constitution": 1},       "flexible": None},
    "Kenku":             {"fixed": {"dexterity": 2, "wisdom": 1},            "flexible": None},
    "Lizardfolk":        {"fixed": {"constitution": 2, "wisdom": 1},         "flexible": None},
    "Tabaxi":            {"fixed": {"dexterity": 2, "charisma": 1},          "flexible": None},
    "Triton":            {"fixed": {"strength": 1, "constitution": 1, "charisma": 1}, "flexible": None},
    "Yuan-ti Pureblood": {"fixed": {"intelligence": 1, "charisma": 2},       "flexible": None},
}

STANDARD_ARRAY = [15, 14, 13, 12, 10, 8]

# Point Buy cost per score value
POINT_BUY_COSTS = {8: 0, 9: 1, 10: 2, 11: 3, 12: 4, 13: 5, 14: 7, 15: 9}
POINT_BUY_BUDGET = 27

ABILITIES = ["strength", "dexterity", "constitution", "intelligence", "wisdom", "charisma"]
ABILITY_LABELS = {"strength": "STR", "dexterity": "DEX", "constitution": "CON",
                  "intelligence": "INT", "wisdom": "WIS", "charisma": "CHA"}

# Primary ability scores for each class — what to prioritize at character creation
# ── Tool / language option lists ──────────────────────────────────────────────

ARTISAN_TOOLS = [
    "Alchemist's supplies", "Brewer's supplies", "Calligrapher's supplies",
    "Carpenter's tools",    "Cartographer's tools", "Cobbler's tools",
    "Cook's utensils",      "Glassblower's tools",  "Jeweler's tools",
    "Leatherworker's tools","Mason's tools",         "Painter's supplies",
    "Potter's tools",       "Smith's tools",         "Tinker's tools",
    "Weaver's tools",       "Woodcarver's tools",
]
GAMING_SETS = [
    "Dice set", "Dragonchess set", "Playing card set", "Three-Dragon Ante set",
]
MUSICAL_INSTRUMENTS = [
    "Bagpipes", "Drum", "Dulcimer", "Flute", "Horn",
    "Lute", "Lyre", "Pan flute", "Shawm", "Viol",
]
ALL_STANDARD_LANGUAGES = [
    "Common", "Dwarvish", "Elvish", "Giant", "Gnomish", "Goblin", "Halfling", "Orcish",
]
ALL_EXOTIC_LANGUAGES = [
    "Abyssal", "Celestial", "Draconic", "Deep Speech",
    "Infernal", "Primordial", "Sylvan", "Undercommon",
]
ALL_LANGUAGES = ALL_STANDARD_LANGUAGES + ALL_EXOTIC_LANGUAGES
ALL_SKILLS = [
    "Acrobatics", "Animal Handling", "Arcana", "Athletics", "Deception",
    "History", "Insight", "Intimidation", "Investigation", "Medicine",
    "Nature", "Perception", "Performance", "Persuasion", "Religion",
    "Sleight of Hand", "Stealth", "Survival",
]

# ── Background proficiencies ───────────────────────────────────────────────────
# skills_fixed:     always granted
# skills_choose:    None | {"count": N, "from": list-or-"any"}
# tools_fixed:      always granted
# tools_choose:     None | {"count": N, "from": list, "label": str}
# languages:        int  — number of free language picks
# languages_exotic: bool — True = pick from exotic list only
BACKGROUND_PROFICIENCIES = {
    "Acolyte":              {"skills_fixed": ["Insight", "Religion"],                          "skills_choose": None,
                             "tools_fixed": [],                                                 "tools_choose": None,
                             "languages": 2, "languages_exotic": False},
    "Anthropologist":       {"skills_fixed": ["Insight", "Religion"],                          "skills_choose": None,
                             "tools_fixed": [],                                                 "tools_choose": None,
                             "languages": 2, "languages_exotic": False},
    "Archaeologist":        {"skills_fixed": ["History", "Survival"],                           "skills_choose": None,
                             "tools_fixed": [],
                             "tools_choose": {"count": 1, "from": ["Cartographer's tools", "Navigator's tools"], "label": "Choose a tool"},
                             "languages": 0, "languages_exotic": False},
    "Athlete":              {"skills_fixed": ["Acrobatics", "Athletics"],                       "skills_choose": None,
                             "tools_fixed": [],                                                 "tools_choose": None,
                             "languages": 1, "languages_exotic": False},
    "Charlatan":            {"skills_fixed": ["Deception", "Sleight of Hand"],                 "skills_choose": None,
                             "tools_fixed": ["Disguise kit", "Forgery kit"],                   "tools_choose": None,
                             "languages": 0, "languages_exotic": False},
    "City Watch":           {"skills_fixed": ["Athletics", "Insight"],                         "skills_choose": None,
                             "tools_fixed": [],                                                 "tools_choose": None,
                             "languages": 2, "languages_exotic": False},
    "Clan Crafter":         {"skills_fixed": ["History", "Insight"],                           "skills_choose": None,
                             "tools_fixed": [],
                             "tools_choose": {"count": 1, "from": ARTISAN_TOOLS, "label": "Choose an artisan's tool"},
                             "languages": 1, "languages_exotic": False},
    "Cloistered Scholar":   {"skills_fixed": ["History"],
                             "skills_choose": {"count": 1, "from": ["Arcana", "Nature", "Religion"]},
                             "tools_fixed": [],                                                 "tools_choose": None,
                             "languages": 2, "languages_exotic": False},
    "Courtier":             {"skills_fixed": ["Insight", "Persuasion"],                        "skills_choose": None,
                             "tools_fixed": [],                                                 "tools_choose": None,
                             "languages": 2, "languages_exotic": False},
    "Criminal":             {"skills_fixed": ["Deception", "Stealth"],                         "skills_choose": None,
                             "tools_fixed": ["Thieves' tools"],
                             "tools_choose": {"count": 1, "from": GAMING_SETS, "label": "Choose a gaming set"},
                             "languages": 0, "languages_exotic": False},
    "Entertainer":          {"skills_fixed": ["Acrobatics", "Performance"],                    "skills_choose": None,
                             "tools_fixed": ["Disguise kit"],
                             "tools_choose": {"count": 1, "from": MUSICAL_INSTRUMENTS, "label": "Choose a musical instrument"},
                             "languages": 0, "languages_exotic": False},
    "Faction Agent":        {"skills_fixed": ["Insight"],
                             "skills_choose": {"count": 1, "from": "any"},
                             "tools_fixed": [],                                                 "tools_choose": None,
                             "languages": 2, "languages_exotic": False},
    "Far Traveler":         {"skills_fixed": ["Insight", "Perception"],                        "skills_choose": None,
                             "tools_fixed": [],
                             "tools_choose": {"count": 1, "from": MUSICAL_INSTRUMENTS + GAMING_SETS, "label": "Choose an instrument or gaming set"},
                             "languages": 1, "languages_exotic": False},
    "Fisher":               {"skills_fixed": ["History", "Survival"],                          "skills_choose": None,
                             "tools_fixed": [],                                                 "tools_choose": None,
                             "languages": 1, "languages_exotic": False},
    "Folk Hero":            {"skills_fixed": ["Animal Handling", "Survival"],                  "skills_choose": None,
                             "tools_fixed": ["Vehicles (land)"],
                             "tools_choose": {"count": 1, "from": ARTISAN_TOOLS, "label": "Choose an artisan's tool"},
                             "languages": 0, "languages_exotic": False},
    "Gladiator":            {"skills_fixed": ["Acrobatics", "Performance"],                    "skills_choose": None,
                             "tools_fixed": ["Disguise kit"],
                             "tools_choose": {"count": 1, "from": MUSICAL_INSTRUMENTS, "label": "Choose a musical instrument"},
                             "languages": 0, "languages_exotic": False},
    "Guild Artisan":        {"skills_fixed": ["Insight", "Persuasion"],                        "skills_choose": None,
                             "tools_fixed": [],
                             "tools_choose": {"count": 1, "from": ARTISAN_TOOLS, "label": "Choose an artisan's tool"},
                             "languages": 1, "languages_exotic": False},
    "Guild Merchant":       {"skills_fixed": ["Insight", "Persuasion"],                        "skills_choose": None,
                             "tools_fixed": [],
                             "tools_choose": {"count": 1, "from": ["Navigator's tools"] + ARTISAN_TOOLS, "label": "Choose a tool"},
                             "languages": 1, "languages_exotic": False},
    "Haunted One":          {"skills_fixed": [],
                             "skills_choose": {"count": 2, "from": ["Arcana", "Investigation", "Religion", "Survival"]},
                             "tools_fixed": [],                                                 "tools_choose": None,
                             "languages": 1, "languages_exotic": True},
    "Hermit":               {"skills_fixed": ["Medicine", "Religion"],                         "skills_choose": None,
                             "tools_fixed": ["Herbalism kit"],                                 "tools_choose": None,
                             "languages": 1, "languages_exotic": False},
    "Inheritor":            {"skills_fixed": ["Survival"],
                             "skills_choose": {"count": 1, "from": ["Arcana", "History", "Religion"]},
                             "tools_fixed": [],
                             "tools_choose": {"count": 1, "from": GAMING_SETS + MUSICAL_INSTRUMENTS, "label": "Choose a gaming set or instrument"},
                             "languages": 1, "languages_exotic": False},
    "Investigator":         {"skills_fixed": ["Insight", "Investigation"],                     "skills_choose": None,
                             "tools_fixed": [],                                                 "tools_choose": None,
                             "languages": 2, "languages_exotic": False},
    "Knight":               {"skills_fixed": ["History", "Persuasion"],                        "skills_choose": None,
                             "tools_fixed": [],
                             "tools_choose": {"count": 1, "from": GAMING_SETS, "label": "Choose a gaming set"},
                             "languages": 1, "languages_exotic": False},
    "Knight of the Order":  {"skills_fixed": ["Persuasion"],
                             "skills_choose": {"count": 1, "from": ["Arcana", "History", "Nature", "Religion"]},
                             "tools_fixed": [],
                             "tools_choose": {"count": 1, "from": GAMING_SETS + MUSICAL_INSTRUMENTS, "label": "Choose a gaming set or instrument"},
                             "languages": 1, "languages_exotic": False},
    "Marine":               {"skills_fixed": ["Athletics", "Survival"],                        "skills_choose": None,
                             "tools_fixed": ["Vehicles (land)", "Vehicles (water)"],           "tools_choose": None,
                             "languages": 0, "languages_exotic": False},
    "Mercenary Veteran":    {"skills_fixed": ["Athletics", "Persuasion"],                      "skills_choose": None,
                             "tools_fixed": ["Vehicles (land)"],
                             "tools_choose": {"count": 1, "from": GAMING_SETS, "label": "Choose a gaming set"},
                             "languages": 0, "languages_exotic": False},
    "Noble":                {"skills_fixed": ["History", "Persuasion"],                        "skills_choose": None,
                             "tools_fixed": [],
                             "tools_choose": {"count": 1, "from": GAMING_SETS, "label": "Choose a gaming set"},
                             "languages": 1, "languages_exotic": False},
    "Outlander":            {"skills_fixed": ["Athletics", "Survival"],                        "skills_choose": None,
                             "tools_fixed": [],
                             "tools_choose": {"count": 1, "from": MUSICAL_INSTRUMENTS, "label": "Choose a musical instrument"},
                             "languages": 1, "languages_exotic": False},
    "Pirate":               {"skills_fixed": ["Athletics", "Perception"],                      "skills_choose": None,
                             "tools_fixed": ["Navigator's tools", "Vehicles (water)"],         "tools_choose": None,
                             "languages": 0, "languages_exotic": False},
    "Sage":                 {"skills_fixed": ["Arcana", "History"],                            "skills_choose": None,
                             "tools_fixed": [],                                                 "tools_choose": None,
                             "languages": 2, "languages_exotic": False},
    "Sailor":               {"skills_fixed": ["Athletics", "Perception"],                      "skills_choose": None,
                             "tools_fixed": ["Navigator's tools", "Vehicles (water)"],         "tools_choose": None,
                             "languages": 0, "languages_exotic": False},
    "Soldier":              {"skills_fixed": ["Athletics", "Intimidation"],                    "skills_choose": None,
                             "tools_fixed": ["Vehicles (land)"],
                             "tools_choose": {"count": 1, "from": GAMING_SETS, "label": "Choose a gaming set"},
                             "languages": 0, "languages_exotic": False},
    "Spy":                  {"skills_fixed": ["Deception", "Stealth"],                         "skills_choose": None,
                             "tools_fixed": ["Thieves' tools"],
                             "tools_choose": {"count": 1, "from": GAMING_SETS, "label": "Choose a gaming set"},
                             "languages": 0, "languages_exotic": False},
    "Urban Bounty Hunter":  {"skills_fixed": [],
                             "skills_choose": {"count": 2, "from": ["Deception", "Insight", "Persuasion", "Stealth"]},
                             "tools_fixed": [],
                             "tools_choose": {"count": 2, "from": GAMING_SETS + MUSICAL_INSTRUMENTS + ["Thieves' tools"], "label": "Choose two tool proficiencies"},
                             "languages": 0, "languages_exotic": False},
    "Urchin":               {"skills_fixed": ["Sleight of Hand", "Stealth"],                   "skills_choose": None,
                             "tools_fixed": ["Disguise kit", "Thieves' tools"],                "tools_choose": None,
                             "languages": 0, "languages_exotic": False},
    "Uthgardt Tribe Member":{"skills_fixed": ["Athletics", "Survival"],                        "skills_choose": None,
                             "tools_fixed": [],
                             "tools_choose": {"count": 1, "from": MUSICAL_INSTRUMENTS + ARTISAN_TOOLS, "label": "Choose an instrument or artisan's tool"},
                             "languages": 1, "languages_exotic": False},
    "Waterdhavian Noble":   {"skills_fixed": ["History", "Persuasion"],                        "skills_choose": None,
                             "tools_fixed": [],
                             "tools_choose": {"count": 1, "from": GAMING_SETS + MUSICAL_INSTRUMENTS, "label": "Choose a gaming set or instrument"},
                             "languages": 1, "languages_exotic": False},
}

# ── Combat data ───────────────────────────────────────────────────────────────

CLASS_HIT_DICE = {
    "Artificer": "d8",  "Barbarian": "d12", "Bard":    "d8",
    "Cleric":    "d8",  "Druid":     "d8",  "Fighter": "d10",
    "Monk":      "d8",  "Paladin":   "d10", "Ranger":  "d10",
    "Rogue":     "d8",  "Sorcerer":  "d6",  "Warlock": "d8",
    "Wizard":    "d6",
}

HIT_DIE_AVERAGES = {"d6": 4, "d8": 5, "d10": 6, "d12": 7}

RACE_SPEED = {
    "Dragonborn": 30, "Dwarf (Hill)": 25, "Dwarf (Mountain)": 25,
    "Elf (Drow / Dark)": 30, "Elf (High)": 30, "Elf (Wood)": 35,
    "Gnome (Forest)": 25, "Gnome (Rock)": 25, "Half-Elf": 30,
    "Half-Orc": 30, "Halfling (Lightfoot)": 25, "Halfling (Stout)": 25,
    "Human": 30, "Human (Variant)": 30, "Tiefling": 30,
    "Aasimar": 30, "Firbolg": 30, "Genasi (Air)": 30, "Genasi (Earth)": 30,
    "Genasi (Fire)": 30, "Genasi (Water)": 30, "Goblin": 30, "Goliath": 30,
    "Kenku": 30, "Lizardfolk": 30, "Tabaxi": 30, "Triton": 30,
    "Yuan-ti Pureblood": 30,
}

# Armor: ac_base, max_dex (None = unlimited), stealth disadvantage, type
ARMOR_TABLE = {
    "None (unarmored)":   {"ac_base": 10, "max_dex": None, "stealth_dis": False, "type": "none"},
    "Padded":             {"ac_base": 11, "max_dex": None, "stealth_dis": True,  "type": "light"},
    "Leather":            {"ac_base": 11, "max_dex": None, "stealth_dis": False, "type": "light"},
    "Studded Leather":    {"ac_base": 12, "max_dex": None, "stealth_dis": False, "type": "light"},
    "Hide":               {"ac_base": 12, "max_dex": 2,    "stealth_dis": False, "type": "medium"},
    "Chain Shirt":        {"ac_base": 13, "max_dex": 2,    "stealth_dis": False, "type": "medium"},
    "Scale Mail":         {"ac_base": 14, "max_dex": 2,    "stealth_dis": True,  "type": "medium"},
    "Breastplate":        {"ac_base": 14, "max_dex": 2,    "stealth_dis": False, "type": "medium"},
    "Half Plate":         {"ac_base": 15, "max_dex": 2,    "stealth_dis": True,  "type": "medium"},
    "Ring Mail":          {"ac_base": 14, "max_dex": 0,    "stealth_dis": True,  "type": "heavy"},
    "Chain Mail":         {"ac_base": 16, "max_dex": 0,    "stealth_dis": True,  "type": "heavy"},
    "Splint":             {"ac_base": 17, "max_dex": 0,    "stealth_dis": True,  "type": "heavy"},
    "Plate":              {"ac_base": 18, "max_dex": 0,    "stealth_dis": True,  "type": "heavy"},
}

# ── Proficiency data ───────────────────────────────────────────────────────────

CLASS_SKILLS = {
    "Artificer": {"count": 2, "from": ["Arcana","History","Investigation","Medicine","Nature","Perception","Sleight of Hand"]},
    "Barbarian": {"count": 2, "from": ["Animal Handling","Athletics","Intimidation","Nature","Perception","Survival"]},
    "Bard":      {"count": 3, "from": "any"},
    "Cleric":    {"count": 2, "from": ["History","Insight","Medicine","Persuasion","Religion"]},
    "Druid":     {"count": 2, "from": ["Arcana","Animal Handling","Insight","Medicine","Nature","Perception","Religion","Survival"]},
    "Fighter":   {"count": 2, "from": ["Acrobatics","Animal Handling","Athletics","History","Insight","Intimidation","Perception","Survival"]},
    "Monk":      {"count": 2, "from": ["Acrobatics","Athletics","History","Insight","Religion","Stealth"]},
    "Paladin":   {"count": 2, "from": ["Athletics","Insight","Intimidation","Medicine","Persuasion","Religion"]},
    "Ranger":    {"count": 3, "from": ["Animal Handling","Athletics","Insight","Investigation","Nature","Perception","Stealth","Survival"]},
    "Rogue":     {"count": 4, "from": ["Acrobatics","Athletics","Deception","Insight","Intimidation","Investigation","Perception","Performance","Persuasion","Sleight of Hand","Stealth"]},
    "Sorcerer":  {"count": 2, "from": ["Arcana","Deception","Insight","Intimidation","Persuasion","Religion"]},
    "Warlock":   {"count": 2, "from": ["Arcana","Deception","History","Intimidation","Investigation","Nature","Religion"]},
    "Wizard":    {"count": 2, "from": ["Arcana","History","Insight","Investigation","Medicine","Religion"]},
}

CLASS_ARMOR_PROFS = {
    "Artificer": ["Light","Medium","Shields"],
    "Barbarian": ["Light","Medium","Shields"],
    "Bard":      ["Light"],
    "Cleric":    ["Light","Medium","Shields"],
    "Druid":     ["Light","Medium","Shields (non-metal)"],
    "Fighter":   ["Light","Medium","Heavy","Shields"],
    "Monk":      [],
    "Paladin":   ["Light","Medium","Heavy","Shields"],
    "Ranger":    ["Light","Medium","Shields"],
    "Rogue":     ["Light"],
    "Sorcerer":  [],
    "Warlock":   ["Light"],
    "Wizard":    [],
}

CLASS_WEAPON_PROFS = {
    "Artificer": ["Simple weapons","Hand crossbow","Heavy crossbow","Light crossbow"],
    "Barbarian": ["Simple weapons","Martial weapons"],
    "Bard":      ["Simple weapons","Hand crossbow","Longsword","Rapier","Shortsword"],
    "Cleric":    ["Simple weapons"],
    "Druid":     ["Clubs","Daggers","Darts","Javelins","Maces","Quarterstaffs","Scimitars","Sickles","Slings","Spears"],
    "Fighter":   ["Simple weapons","Martial weapons"],
    "Monk":      ["Simple weapons","Shortsword"],
    "Paladin":   ["Simple weapons","Martial weapons"],
    "Ranger":    ["Simple weapons","Martial weapons"],
    "Rogue":     ["Simple weapons","Hand crossbow","Longsword","Rapier","Shortsword"],
    "Sorcerer":  ["Daggers","Darts","Slings","Quarterstaffs","Light crossbows"],
    "Warlock":   ["Simple weapons"],
    "Wizard":    ["Daggers","Darts","Slings","Quarterstaffs","Light crossbows"],
}

RACE_LANGUAGES = {
    "Dragonborn":          ["Common","Draconic"],
    "Dwarf (Hill)":        ["Common","Dwarvish"],
    "Dwarf (Mountain)":    ["Common","Dwarvish"],
    "Elf (Drow / Dark)":   ["Common","Elvish","Undercommon"],
    "Elf (High)":          ["Common","Elvish"],
    "Elf (Wood)":          ["Common","Elvish"],
    "Gnome (Forest)":      ["Common","Gnomish"],
    "Gnome (Rock)":        ["Common","Gnomish"],
    "Half-Elf":            ["Common","Elvish"],
    "Half-Orc":            ["Common","Orcish"],
    "Halfling (Lightfoot)":["Common","Halfling"],
    "Halfling (Stout)":    ["Common","Halfling"],
    "Human":               ["Common"],
    "Human (Variant)":     ["Common"],
    "Tiefling":            ["Common","Infernal"],
    "Aasimar":             ["Common","Celestial"],
    "Firbolg":             ["Common","Elvish","Giant"],
    "Genasi (Air)":        ["Common","Primordial"],
    "Genasi (Earth)":      ["Common","Primordial"],
    "Genasi (Fire)":       ["Common","Primordial"],
    "Genasi (Water)":      ["Common","Primordial"],
    "Goblin":              ["Common","Goblin"],
    "Goliath":             ["Common","Giant"],
    "Kenku":               ["Common","Auran"],
    "Lizardfolk":          ["Common","Draconic"],
    "Tabaxi":              ["Common"],
    "Triton":              ["Common","Primordial"],
    "Yuan-ti Pureblood":   ["Common","Abyssal","Draconic"],
}

# Number of extra language picks (beyond racial fixed ones)
RACE_EXTRA_LANGUAGES = {
    "Elf (High)": 1, "Half-Elf": 1, "Human": 1,
    "Human (Variant)": 1, "Tabaxi": 1,
}

# ── Spellcasting ───────────────────────────────────────────────────────────────

CLASS_SPELLCASTING = {
    "Artificer": {"type": "half",    "ability": "intelligence", "prepares": True},
    "Barbarian": None,
    "Bard":      {"type": "full",    "ability": "charisma",     "prepares": False},
    "Cleric":    {"type": "full",    "ability": "wisdom",       "prepares": True},
    "Druid":     {"type": "full",    "ability": "wisdom",       "prepares": True},
    "Fighter":   None,
    "Monk":      None,
    "Paladin":   {"type": "half",    "ability": "charisma",     "prepares": True},
    "Ranger":    {"type": "half",    "ability": "wisdom",       "prepares": False},
    "Rogue":     None,
    "Sorcerer":  {"type": "full",    "ability": "charisma",     "prepares": False},
    "Warlock":   {"type": "warlock", "ability": "charisma",     "prepares": False},
    "Wizard":    {"type": "full",    "ability": "intelligence", "prepares": True},
}

# Spell slots by class type and level
FULL_CASTER_SLOTS = {
    1:  [2,0,0,0,0,0,0,0,0], 2:  [3,0,0,0,0,0,0,0,0],
    3:  [4,2,0,0,0,0,0,0,0], 4:  [4,3,0,0,0,0,0,0,0],
    5:  [4,3,2,0,0,0,0,0,0], 6:  [4,3,3,0,0,0,0,0,0],
    7:  [4,3,3,1,0,0,0,0,0], 8:  [4,3,3,2,0,0,0,0,0],
    9:  [4,3,3,3,1,0,0,0,0], 10: [4,3,3,3,2,0,0,0,0],
    11: [4,3,3,3,2,1,0,0,0], 12: [4,3,3,3,2,1,0,0,0],
    13: [4,3,3,3,2,1,1,0,0], 14: [4,3,3,3,2,1,1,0,0],
    15: [4,3,3,3,2,1,1,1,0], 16: [4,3,3,3,2,1,1,1,0],
    17: [4,3,3,3,2,1,1,1,1], 18: [4,3,3,3,3,1,1,1,1],
    19: [4,3,3,3,3,2,1,1,1], 20: [4,3,3,3,3,2,2,1,1],
}
HALF_CASTER_SLOTS = {
    1:  [0,0,0,0,0,0,0,0,0], 2:  [2,0,0,0,0,0,0,0,0],
    3:  [3,0,0,0,0,0,0,0,0], 4:  [3,0,0,0,0,0,0,0,0],
    5:  [4,2,0,0,0,0,0,0,0], 6:  [4,2,0,0,0,0,0,0,0],
    7:  [4,3,0,0,0,0,0,0,0], 8:  [4,3,0,0,0,0,0,0,0],
    9:  [4,3,2,0,0,0,0,0,0], 10: [4,3,2,0,0,0,0,0,0],
    11: [4,3,3,0,0,0,0,0,0], 12: [4,3,3,0,0,0,0,0,0],
    13: [4,3,3,1,0,0,0,0,0], 14: [4,3,3,1,0,0,0,0,0],
    15: [4,3,3,2,0,0,0,0,0], 16: [4,3,3,2,0,0,0,0,0],
    17: [4,3,3,3,1,0,0,0,0], 18: [4,3,3,3,1,0,0,0,0],
    19: [4,3,3,3,2,0,0,0,0], 20: [4,3,3,3,2,0,0,0,0],
}
WARLOCK_SLOTS = {
    1: (1,1), 2: (2,1), 3: (2,2), 4: (2,2), 5: (3,3),
    6: (2,3), 7: (2,4), 8: (2,4), 9: (2,5), 10: (2,5),
    11: (3,5), 12: (2,5), 13: (3,5), 14: (2,5), 15: (3,5),
    16: (2,5), 17: (4,5), 18: (4,5), 19: (4,5), 20: (4,5),
}

# Cantrips known by level for each type
CANTRIPS_KNOWN = {
    "full":    {1:2,4:3,10:4},
    "half":    {1:0},
    "warlock": {1:2,4:3,10:4},
    "wizard":  {1:3,4:4,10:5},
}

# ── Weapons ───────────────────────────────────────────────────────────────────

WEAPONS = {
    # Simple Melee
    "Club":           {"damage":"1d4",  "type":"bludgeoning","props":["light"],               "cat":"Simple Melee"},
    "Dagger":         {"damage":"1d4",  "type":"piercing",   "props":["finesse","light","thrown (20/60)"],"cat":"Simple Melee"},
    "Greatclub":      {"damage":"1d8",  "type":"bludgeoning","props":["two-handed"],           "cat":"Simple Melee"},
    "Handaxe":        {"damage":"1d6",  "type":"slashing",   "props":["light","thrown (20/60)"],"cat":"Simple Melee"},
    "Javelin":        {"damage":"1d6",  "type":"piercing",   "props":["thrown (30/120)"],      "cat":"Simple Melee"},
    "Light Hammer":   {"damage":"1d4",  "type":"bludgeoning","props":["light","thrown (20/60)"],"cat":"Simple Melee"},
    "Mace":           {"damage":"1d6",  "type":"bludgeoning","props":[],                       "cat":"Simple Melee"},
    "Quarterstaff":   {"damage":"1d6",  "type":"bludgeoning","props":["versatile (1d8)"],      "cat":"Simple Melee"},
    "Sickle":         {"damage":"1d4",  "type":"slashing",   "props":["light"],               "cat":"Simple Melee"},
    "Spear":          {"damage":"1d6",  "type":"piercing",   "props":["thrown (20/60)","versatile (1d8)"],"cat":"Simple Melee"},
    # Simple Ranged
    "Light Crossbow": {"damage":"1d8",  "type":"piercing",   "props":["ammunition (80/320)","loading","two-handed"],"cat":"Simple Ranged"},
    "Dart":           {"damage":"1d4",  "type":"piercing",   "props":["finesse","thrown (20/60)"],"cat":"Simple Ranged"},
    "Shortbow":       {"damage":"1d6",  "type":"piercing",   "props":["ammunition (80/320)","two-handed"],"cat":"Simple Ranged"},
    "Sling":          {"damage":"1d4",  "type":"bludgeoning","props":["ammunition (30/120)"],  "cat":"Simple Ranged"},
    # Martial Melee
    "Battleaxe":      {"damage":"1d8",  "type":"slashing",   "props":["versatile (1d10)"],     "cat":"Martial Melee"},
    "Flail":          {"damage":"1d8",  "type":"bludgeoning","props":[],                       "cat":"Martial Melee"},
    "Glaive":         {"damage":"1d10", "type":"slashing",   "props":["heavy","reach","two-handed"],"cat":"Martial Melee"},
    "Greataxe":       {"damage":"1d12", "type":"slashing",   "props":["heavy","two-handed"],   "cat":"Martial Melee"},
    "Greatsword":     {"damage":"2d6",  "type":"slashing",   "props":["heavy","two-handed"],   "cat":"Martial Melee"},
    "Halberd":        {"damage":"1d10", "type":"slashing",   "props":["heavy","reach","two-handed"],"cat":"Martial Melee"},
    "Lance":          {"damage":"1d12", "type":"piercing",   "props":["reach"],                "cat":"Martial Melee"},
    "Longsword":      {"damage":"1d8",  "type":"slashing",   "props":["versatile (1d10)"],     "cat":"Martial Melee"},
    "Maul":           {"damage":"2d6",  "type":"bludgeoning","props":["heavy","two-handed"],   "cat":"Martial Melee"},
    "Morningstar":    {"damage":"1d8",  "type":"piercing",   "props":[],                       "cat":"Martial Melee"},
    "Pike":           {"damage":"1d10", "type":"piercing",   "props":["heavy","reach","two-handed"],"cat":"Martial Melee"},
    "Rapier":         {"damage":"1d8",  "type":"piercing",   "props":["finesse"],              "cat":"Martial Melee"},
    "Scimitar":       {"damage":"1d6",  "type":"slashing",   "props":["finesse","light"],      "cat":"Martial Melee"},
    "Shortsword":     {"damage":"1d6",  "type":"piercing",   "props":["finesse","light"],      "cat":"Martial Melee"},
    "Trident":        {"damage":"1d6",  "type":"piercing",   "props":["thrown (20/60)","versatile (1d8)"],"cat":"Martial Melee"},
    "War Pick":       {"damage":"1d8",  "type":"piercing",   "props":[],                       "cat":"Martial Melee"},
    "Warhammer":      {"damage":"1d8",  "type":"bludgeoning","props":["versatile (1d10)"],     "cat":"Martial Melee"},
    "Whip":           {"damage":"1d4",  "type":"slashing",   "props":["finesse","reach"],      "cat":"Martial Melee"},
    # Martial Ranged
    "Hand Crossbow":  {"damage":"1d6",  "type":"piercing",   "props":["ammunition (30/120)","light","loading"],"cat":"Martial Ranged"},
    "Heavy Crossbow": {"damage":"1d10", "type":"piercing",   "props":["ammunition (100/400)","heavy","loading","two-handed"],"cat":"Martial Ranged"},
    "Longbow":        {"damage":"1d8",  "type":"piercing",   "props":["ammunition (150/600)","heavy","two-handed"],"cat":"Martial Ranged"},
    "Net":            {"damage":"—",    "type":"—",          "props":["thrown (5/15)"],        "cat":"Martial Ranged"},
}

WEAPON_CATEGORIES = ["Simple Melee","Simple Ranged","Martial Melee","Martial Ranged"]

# ── Equipment ─────────────────────────────────────────────────────────────────

CLASS_STARTING_GOLD = {
    "Artificer":10*5, "Barbarian":2*10, "Bard":5*10, "Cleric":5*10,
    "Druid":2*10, "Fighter":5*10, "Monk":5, "Paladin":5*10,
    "Ranger":5*10, "Rogue":4*10, "Sorcerer":3*10, "Warlock":4*10,
    "Wizard":4*10,
}

EQUIPMENT_PACKS = {
    "Burglar's Pack":   ["Backpack","1000 ball bearings","10 ft string","Bell","5 candles","Crowbar","Hammer","10 pitons","Hooded lantern","2 flasks of oil","5 days rations","Tinderbox","Waterskin","50 ft hempen rope"],
    "Diplomat's Pack":  ["Chest","2 cases for maps/scrolls","Fine clothes","Bottle of ink","Ink pen","Lamp","2 flasks of oil","5 sheets of paper","Vial of perfume","Sealing wax","Soap"],
    "Dungeoneer's Pack":["Backpack","Crowbar","Hammer","10 pitons","10 torches","Tinderbox","10 days rations","Waterskin","50 ft hempen rope"],
    "Entertainer's Pack":["Backpack","Bedroll","2 costumes","5 candles","5 days rations","Waterskin","Disguise kit"],
    "Explorer's Pack":  ["Backpack","Bedroll","Mess kit","Tinderbox","10 torches","10 days rations","Waterskin","50 ft hempen rope"],
    "Monster Hunter's Pack":["Chest","Crowbar","Hammer","3 wooden stakes","Holy symbol","Holy water","Manacles","Steel mirror","Vial of oil","Tinderbox","3 torches"],
    "Priest's Pack":    ["Backpack","Blanket","10 candles","Tinderbox","Alms box","2 blocks of incense","Censer","Vestments","2 days rations","Waterskin"],
    "Scholar's Pack":   ["Backpack","Book of lore","Bottle of ink","Ink pen","10 sheets of parchment","Little bag of sand","Small knife"],
}

# ── Background features ────────────────────────────────────────────────────────

BACKGROUND_FEATURES = {
    "Acolyte":             ("Shelter of the Faithful", "As an acolyte, you command the respect of those who share your faith. You and your companions can receive free healing and care at a temple of your faith, and you can call upon priests for assistance."),
    "Anthropologist":      ("Adept Linguist", "You can communicate with humanoids who don't share a language by picking up cues from body language, tone, and syntax. After 1 day of observation you can mimic simple phrases."),
    "Archaeologist":       ("Historical Knowledge", "When you enter a ruin or dungeon, you can correctly ascertain its original purpose and identify its builders, gaining a +5 bonus to relevant History checks."),
    "Athlete":             ("Echoes of Victory", "You have won fame in at least one athletic event. Fans recognize you and are eager to help. You can secure free lodging and meals in exchange for competing and signing autographs."),
    "Charlatan":           ("False Identity", "You have a second identity including documentation, established acquaintances, and disguises. You can also forge documents including official papers and personal letters."),
    "City Watch":          ("Watcher's Eye", "Your experience helps you spot criminals and illegal activities. You can find the local watch or criminal guilds in any city, gaining information about criminal networks."),
    "Clan Crafter":        ("Respect of the Stout Folk", "As a respected crafter, you have access to clan holds of your race. You can find lodging and food among dwarves, gnomes, or your own folk."),
    "Cloistered Scholar":  ("Library Access", "You have access to most libraries and scholarly collections. Nobles and wizards often lend you books or allow entry to restricted archives."),
    "Courtier":            ("Court Functionary", "Your knowledge of courts lets you gain audience with local nobles. You know the right etiquette and minor officials to get access to most seats of power."),
    "Criminal":            ("Criminal Contact", "You have a reliable contact who acts as liaison to your criminal network, passing along information and requests."),
    "Entertainer":         ("By Popular Demand", "You can always find a place to perform. You receive free lodging and food of modest quality as long as you perform each night. You also become known locally."),
    "Faction Agent":       ("Safe Haven", "As a faction agent, you can call on your faction for assistance — a safe house, passage, or information."),
    "Far Traveler":        ("All Eyes on You", "Your accent, mannerisms, and equipment mark you as foreign. Common folk are curious and helpful; criminals and nobles take notice."),
    "Fisher":              ("Harvest the Water", "You gain advantage on ability checks to find food and freshwater in coastal, riverside, or lakeside environments."),
    "Folk Hero":           ("Rustic Hospitality", "As a folk hero, common people will shelter and hide you. They will not risk their lives for you, but they will keep you safe from soldiers or a local lord."),
    "Gladiator":           ("By Popular Demand", "You can always find a place to perform. You receive free lodging and food as long as you perform nightly. You become known in entertainment venues."),
    "Guild Artisan":       ("Guild Membership", "Your guild will provide lodging, food, and a modest lifestyle between adventures. The guild will also intervene if you face legal trouble, within reason."),
    "Guild Merchant":      ("Guild Membership", "Your guild provides lodging, food, and resources. You can call on guild members for trade goods at favorable prices and assistance in cities with a guild presence."),
    "Haunted One":         ("Heart of Darkness", "Those who look into your eyes can sense the horrors you've witnessed. Common folk sense something is different about you and are simultaneously drawn to and repelled by you."),
    "Hermit":              ("Discovery", "The quiet of your isolated existence let you discover a unique truth. Work with your DM to determine the nature of your discovery and its impact."),
    "Inheritor":           ("Inheritance", "You are the rightful heir to something of great value — not mere coin, but a title, a blade, a secret, or knowledge that others would kill to possess."),
    "Investigator":        ("Unofficial Inquiry", "When you want information about a person, place, or activity, you know who to ask and how to be discreet. It usually takes 1d4+1 days to gather rumors."),
    "Knight":              ("Retainers", "You have three commoners who serve as your attendants on adventures. They are loyal and competent, not combatants."),
    "Knight of the Order": ("Knightly Regard", "You receive shelter and succor from members of your knightly order and your religious allies."),
    "Marine":              ("Steady", "You can move across and climb difficult terrain made of rubble, ice, or ship decks without spending extra movement. Difficult terrain doesn't impede your Concentration."),
    "Mercenary Veteran":   ("Mercenary Life", "You know the mercenary life well. You can find mercenary groups to work with, find their meeting places, and identify their members."),
    "Noble":               ("Position of Privilege", "People are inclined to think the best of you. You are welcome in high society and common people make every effort to accommodate you."),
    "Outlander":           ("Wanderer", "You have an excellent memory for maps and geography, and you can always recall the general layout of terrain and settlements. You can always find food and fresh water for yourself and up to 5 others."),
    "Pirate":              ("Bad Reputation", "No matter where you go, people are afraid of you. You can get away with minor criminal offenses, such as refusing to pay for food at a tavern or breaking down doors."),
    "Sage":                ("Researcher", "When you attempt to learn or recall a piece of lore, if you don't know the information you often know where to find it."),
    "Sailor":              ("Ship's Passage", "When you need to, you can secure free passage on a sailing ship for you and your companions in exchange for serving as crew."),
    "Soldier":             ("Military Rank", "You have a military rank from your career. Soldiers loyal to your former organization still recognize your authority. You can invoke your rank to exert influence and requisition equipment."),
    "Spy":                 ("Criminal Contact", "You have a reliable contact in criminal networks who passes information and requests to and from other criminals."),
    "Urban Bounty Hunter": ("Ear to the Ground", "You're in frequent contact with people in underground segments of society. You know where to go to gather information about individuals and activities the authorities would prefer to keep quiet."),
    "Urchin":              ("City Secrets", "You know the secret patterns and flow of cities. You can find passages others would miss: alleyways, back streets, and sewers. You can move at double speed when navigating urban environments."),
    "Uthgardt Tribe Member":("Uthgardt Heritage", "You have advantage on Survival checks to hunt and forage, and you know the burial sites, sacred stones, and shrines of your tribe."),
    "Waterdhavian Noble":  ("Kept in Style", "While in Waterdeep or any city of the North, you can live at a wealthy lifestyle for free by staying with your family or guild associates."),
}

# ── Race descriptions ──────────────────────────────────────────────────────────

RACE_DESCRIPTIONS = {
    "Dragonborn": (
        "Dragonborn look very much like dragons standing erect in humanoid form, though they lack wings "
        "or a tail. Born of draconic gods or the descendants of dragons, they walk proudly through a world "
        "that greets them with fearful incomprehension. Their coloring — red, gold, bronze, blue, white, "
        "green, black, copper, brass, or silver — reflects their draconic bloodline. They prize skill "
        "and excellence above all else, and a dragonborn's clan is the most important thing in their life, "
        "even for those who have been cast out."
    ),
    "Dwarf (Hill)": (
        "Bold and hardy, hill dwarves are known as skilled warriors, miners, and workers of stone and metal. "
        "More commonly seen among surface folk than their mountain cousins, they have an innate toughness "
        "that lets them outlast almost any hardship. Hill dwarves hold their traditions close, value loyalty "
        "above almost anything else, and carry a deep-seated hatred of goblins and orcs — ancient enemies "
        "of their people. Their lifespan stretches past 400 years, giving them a long memory for both "
        "grudges and friendships."
    ),
    "Dwarf (Mountain)": (
        "Mountain dwarves are physically stronger and more martially disciplined than their hill-dwelling "
        "kin, bred over generations to defend the great stone halls carved from the highest peaks. They are "
        "stocky and powerful, with a natural aptitude for armor and combat. Mountain dwarves have made their "
        "strongholds in the deep places of the earth, often far from the surface world, and they carry the "
        "weight of centuries of tradition and war. Their stubbornness is legendary — a mountain dwarf does "
        "not abandon a cause, a friend, or a grudge."
    ),
    "Elf (Drow / Dark)": (
        "Drow are a subrace of elves who were driven underground thousands of years ago for following the "
        "spider goddess Lolth down the path of chaos and cruelty. In the Underdark, they built a society "
        "of brutal ambition and arcane mastery, surviving by turning on each other as much as outsiders. "
        "Drow who leave that world behind — whether by exile or choice — face deep suspicion on the surface, "
        "their black skin and white hair marking them immediately. Yet some drow carry within them a will "
        "to prove that destiny is not determined by birth."
    ),
    "Elf (High)": (
        "High elves are slender, graceful beings who have cultivated arcane arts and refined culture over "
        "millennia. They believe themselves to be among the most civilized and intellectually accomplished "
        "of all races, and their ancient cities — often hidden in magically protected valleys or built near "
        "ley lines — reflect centuries of accumulated wisdom and artistic achievement. High elves see "
        "themselves as stewards of magical knowledge, and they carry an innate connection to the weave of "
        "magic that gives every high elf at least one cantrip."
    ),
    "Elf (Wood)": (
        "Wood elves are more primal and feral than their high elf kin, choosing the deep wilderness over "
        "towers of scholarship. Quick, perceptive, and fiercely independent, they live in close communion "
        "with the oldest forests of the world and guard those places jealously from intrusion. A wood elf "
        "moves through the trees faster than most creatures can move on open ground, and their ability to "
        "blend into natural surroundings makes them among the most elusive hunters and scouts in any world."
    ),
    "Gnome (Forest)": (
        "Forest gnomes are small, curious beings with a natural affinity for the living world and a love "
        "of minor illusion magic. They live in tight-knit communities hidden beneath old-growth forest "
        "canopies, using their ability to communicate with small animals and weave illusions to stay safe "
        "from larger predators and careless travellers. Cheerful and inventive, forest gnomes find wonder "
        "in everything, and their small hidden villages are places of laughter, tinkering, and celebration "
        "of nature's endless variety."
    ),
    "Gnome (Rock)": (
        "Rock gnomes are the most commonly encountered gnomes in the wider world — energetic, inventive, "
        "and perpetually tinkering. They have a deep love of gems, clockwork mechanisms, and the thrill "
        "of discovery, and their communities often resemble workshops more than towns. Rock gnomes have "
        "an innate talent for history and artifice, and their Gnome Cunning gives them a remarkable "
        "resistance to magical manipulation. They tend to be talkative, enthusiastic, and occasionally "
        "exhausting to keep up with."
    ),
    "Half-Elf": (
        "Half-elves combine the ambition and adaptability of their human heritage with the grace, "
        "perception, and longevity of their elven side. They tend to be curious, creative, and possessed "
        "of a natural charisma that makes them gifted diplomats and storytellers. Half-elves have no "
        "true homeland — neither fully accepted in elven communities nor entirely at home among humans — "
        "and this sense of living between worlds gives them a unique perspective. Most half-elves are "
        "wanderers by nature, building connections across cultures with ease."
    ),
    "Half-Orc": (
        "Half-orcs inherit a powerful physique and a fierce determination from their orcish lineage, "
        "combined with human flexibility and drive. They bear the physical marks of that heritage — "
        "grayish skin, prominent lower canines, and a powerful build — and often face prejudice in "
        "civilized lands. Half-orcs are rarely born into comfort; most have had to fight for their place "
        "in the world. This shapes them into driven, resilient individuals who push past limits that "
        "would stop others cold, and their orcish stubbornness means they are extraordinarily hard to kill."
    ),
    "Halfling (Lightfoot)": (
        "Lightfoot halflings are small, cheerful wanderers with a surprising talent for going unnoticed. "
        "They love the comforts of home — good food, warm fires, and the company of friends — but an "
        "adventurous streak runs through many of them. Lightfoot halflings are naturally lucky, brave "
        "despite their size, and possessed of a gift for blending into any crowd or background. They "
        "make natural rogues and scouts, and their easy-going charm means they rarely stay without friends "
        "for long wherever they travel."
    ),
    "Halfling (Stout)": (
        "Stout halflings are tougher than their lightfoot cousins, thought by some scholars to carry a "
        "thread of dwarven blood from ancient alliances. They share the halfling love of home and "
        "community but add to it a hardiness that shrugs off poisons and hardship with equal ease. "
        "Stout halflings are dependable, warm-hearted, and quietly courageous — the kind of companions "
        "who never abandon a friend in trouble and who never seem to stay down no matter how hard life "
        "knocks them."
    ),
    "Human": (
        "Humans are the most widespread, adaptable, and ambitious race in the multiverse. Their short "
        "lifespans drive them to heights of achievement that longer-lived races rarely match for sheer "
        "drive and urgency. Humans build empires, establish religions, found academies, and explore "
        "uncharted wilderness — all within what an elf would call a single lifetime. They are found in "
        "every corner of every world, in every climate and culture, and their extraordinary variety makes "
        "it nearly impossible to generalize about them beyond their boundless adaptability."
    ),
    "Human (Variant)": (
        "Some humans are born with an exceptional natural gift — an innate talent that sets them apart "
        "even as children. These variant humans learn faster than most, developing a notable skill or "
        "feat early in life that other adventurers only acquire through years of practice. Where standard "
        "humans excel through relentless effort, variant humans are defined by a particular brilliance "
        "that marks them as remarkable even among their already remarkable kind."
    ),
    "Tiefling": (
        "Tieflings are humans with an infernal bloodline — descendants of those who made pacts with "
        "devils in ages past, or who were touched by demonic power. They bear unmistakable physical "
        "marks: horns, a long tail, solid-colored eyes without whites, and skin tones ranging from "
        "deep red to purple and blue. Despite the suspicion this appearance invites, tieflings are "
        "not inherently evil — they are their own people, shaped by their choices rather than their "
        "heritage. Many tieflings carry a fierce determination to prove that blood is not destiny."
    ),
    "Aasimar": (
        "Aasimar are humans touched by celestial power, carrying the divine spark of angels, gods, "
        "or the Upper Planes in their blood. They often appear nearly human at first glance, but bear "
        "subtle signs of their heritage — luminous eyes, a faint glow to their skin, or an unearthly "
        "beauty. Most aasimar feel a calling toward good and justice, guided by a celestial spirit that "
        "whispers counsel in their dreams. That destiny is theirs to accept or reject, but the potential "
        "for greatness — and sacrifice — marks them from birth."
    ),
    "Firbolg": (
        "Firbolgs are large, reclusive humanoids deeply attuned to the natural world, preferring the "
        "quiet of ancient forests to the company of other races. Despite their imposing size, they are "
        "gentle, patient, and fundamentally peaceful — turning to violence only as a true last resort. "
        "Firbolgs can communicate with beasts and plants, turn invisible, and move with surprising "
        "subtlety for their size. Their forest homes are places of deep calm and ancient wisdom, and "
        "firbolgs who venture into the wider world do so with careful, measured purpose."
    ),
    "Genasi (Air)": (
        "Air genasi are touched by the Elemental Plane of Air, born of mortals with djinn blood or "
        "conceived during exposure to planar energy. They tend to be light-footed and free-spirited, "
        "with blue-gray or pale skin and hair that drifts as if in a constant breeze. Air genasi "
        "prize freedom above all else and find confinement — physical or social — deeply uncomfortable. "
        "They are drawn to open skies, high places, and the thrill of travel, and their connection to "
        "elemental air lets them hold their breath indefinitely and call on wind magic."
    ),
    "Genasi (Earth)": (
        "Earth genasi carry the solidity and endurance of the Elemental Plane of Earth in their very "
        "bones. They tend to be stocky and powerful, with skin that resembles stone — rough-textured, "
        "dark, or threaded with mineral veins of quartz or ore. Calm and deliberate by nature, earth "
        "genasi are as reliable as bedrock, moving through the world with steady, unhurried purpose. "
        "They walk across difficult rocky terrain without effort and draw upon the deep magic of stone "
        "to pass untracked through the wilderness."
    ),
    "Genasi (Fire)": (
        "Fire genasi are touched by elemental flame — most descended from efreeti or born near powerful "
        "fire nodes on the Material Plane. They run hot in every sense: their hair flickers like flame, "
        "their eyes glow, and their skin carries a reddish or coal-dark warmth. Passionate, fierce, and "
        "hard to ignore, fire genasi have a natural magnetism that draws others to them even as their "
        "intensity keeps some at a distance. They are drawn to leadership, conflict, and glory, their "
        "inner fire driving them toward the center of every storm."
    ),
    "Genasi (Water)": (
        "Water genasi are calm and fluid, touched by the Elemental Plane of Water through merfolk "
        "lineages, sea spirits, or planar crossings. Their skin carries blue-green or sea-gray tones, "
        "and their hair drifts as if perpetually submerged. Patient and adaptable, water genasi are at "
        "home in any environment but feel most themselves near the ocean. Their temperament tends toward "
        "deep contemplation and long memory, and their connection to elemental water lets them breathe "
        "beneath the waves and shape water with a touch."
    ),
    "Goblin": (
        "Goblins are small, nimble humanoids with a survival-driven cunning that larger races tend to "
        "underestimate. Long dismissed as vermin by the major civilizations of the world, individual "
        "goblins who find their own path are often surprisingly resourceful, quick-thinking, and tough. "
        "Their small size and explosive speed make them natural skirmishers, and their ability to "
        "disengage or hide at a moment's notice means they rarely stay in a losing fight. A goblin "
        "adventurer has usually left behind the chaos of their kin by choice — and usually has a very "
        "interesting story about why."
    ),
    "Goliath": (
        "Goliaths are towering humanoids who dwell in the highest mountain peaks, shaped by the brutal "
        "demands of survival at altitude. Their society prizes individual achievement, fairness, and "
        "contribution — a goliath who cannot pull their weight is a danger to the whole tribe. They "
        "compete constantly in tests of strength and endurance, not from cruelty but from a genuine "
        "belief that excellence keeps everyone alive. Goliaths carry a stone's endurance into battle, "
        "shrugging off damage that would fell a lesser warrior, and their competitive drive makes them "
        "relentless opponents."
    ),
    "Kenku": (
        "Kenku are cursed, flightless bird-folk who once soared the skies but lost their wings and "
        "their original voice in punishment for an ancient betrayal. They communicate entirely through "
        "mimicry — reproducing sounds, voices, and phrases they have heard, never speaking in their "
        "own words. This gives them an unsettling manner, but also extraordinary skill at copying "
        "sounds, handwriting, and craftsmanship. Kenku are survivors by nature, clever and opportunistic, "
        "and those who become adventurers often do so seeking to understand the curse that defines them."
    ),
    "Lizardfolk": (
        "Lizardfolk are cold-blooded reptilian humanoids who experience the world through a lens of "
        "pure pragmatism — survival is the only true value, and sentiment is a luxury they have never "
        "been able to afford. They do not understand sorrow, attachment, or mercy in the way mammalian "
        "races do, and what others call ruthlessness they simply call reason. Lizardfolk are formidable "
        "hunters and ingenious crafters, using every part of their environment and prey. Those who "
        "adventure among other races often find themselves genuinely baffled by emotions they observe "
        "but cannot share."
    ),
    "Tabaxi": (
        "Tabaxi are lithe, agile cat-folk from a distant jungle continent, driven by an insatiable "
        "curiosity that propels them to travel the world collecting stories, objects, and experiences. "
        "A tabaxi who has heard of something interesting cannot rest until they have seen it for "
        "themselves — which makes them natural wanderers and somewhat unpredictable companions. Their "
        "feline speed lets them burst into incredible movement when the need arises, and their climbing "
        "ability makes them at home in any environment with vertical surfaces. Tabaxi prize stories "
        "above gold; the greatest treasure is a tale no one else has heard."
    ),
    "Triton": (
        "Tritons are a proud aquatic race who have spent millennia guarding the deepest ocean trenches "
        "against horrors from the Elemental Plane of Water. They are humanoid in form, with blue-green "
        "skin, webbed hands and feet, and features that suggest the sea. Tritons see themselves as "
        "civilization's silent protectors — even when civilization has no idea it is being protected. "
        "This gives them a somewhat superior bearing that can read as arrogance, though their dedication "
        "to defending the innocent from dark-water threats is entirely genuine. They can breathe water "
        "and call on elemental magic of wind and wave."
    ),
    "Yuan-ti Pureblood": (
        "Yuan-ti purebloods are the most human-appearing of the serpent-blooded yuan-ti — the product "
        "of ancient rituals in which humans bound themselves to serpent gods, merging their bloodlines "
        "with those of snakes. To the casual eye they appear nearly human, but subtle scales around "
        "the neck, serpentine eyes, and an unnerving stillness betray their nature. Purebloods are "
        "valued by yuan-ti society as infiltrators and agents in the surface world, their human "
        "appearance making them ideal spies. Their magic resistance makes them extraordinarily "
        "difficult to control or manipulate with spells."
    ),
}

# ── Background descriptions ────────────────────────────────────────────────────

BACKGROUND_DESCRIPTIONS = {
    "Acolyte": (
        "You have spent your life in the service of a temple, acting as an intermediary between the realm "
        "of the holy and the mortal world, performing sacred rites and offering sacrifices in honor of the "
        "gods. You are not necessarily a cleric — performing sacred rites is not the same thing as channeling "
        "divine power — but it is not uncommon for acolytes to awaken to a divine calling while serving at "
        "an altar."
    ),
    "Anthropologist": (
        "You have always been fascinated by other cultures, from the most ancient and primeval lost lands "
        "to the most modern civilizations. You have likely spent years living among peoples different from "
        "your birth culture, mastering their customs, adopting their superstitions, and learning their "
        "languages. By immersing yourself in the daily lives of these cultures you have gained insight into "
        "the bonds that hold civilizations together — and those that break them apart."
    ),
    "Archaeologist": (
        "An archaeologist digs into the distant past, often in search of long-lost civilizations and the "
        "treasures they left behind. Some work for academic institutions or well-funded patrons while others "
        "operate as lone treasure-hunters after glory, fame, and wealth. Regardless of motivation, "
        "archaeologists share a love of discovery and an ability to survive the dangers lurking in ancient, "
        "trap-laden ruins."
    ),
    "Athlete": (
        "You have trained your body to its limits, competing in grand games, famous tournaments, or seasonal "
        "festivals that draw the greatest competitors from across the land. The cheers of the crowd, the "
        "thrill of victory, and the sorrow of defeat have all shaped who you are. Your physical prowess "
        "is matched by a fiercely competitive spirit and the discipline born from years of rigorous training."
    ),
    "Charlatan": (
        "You have always had a way with people. You know what makes them tick, you can tease out their "
        "desires after a few minutes of conversation, and with a few leading questions you can read them "
        "like a children's book. It's a useful talent, and it has led you to make a living by exploiting "
        "others. You're confident, smooth, and adept at spinning elaborate schemes — though the line between "
        "a clever con and outright fraud is one you cross without hesitation."
    ),
    "City Watch": (
        "You have served the community where you grew up, standing as its first line of defense against "
        "crime. You aren't a soldier directing your gaze outward at possible enemies. Instead, your service "
        "was to help police the populace, protecting the townsfolk from lawbreakers and malefactors of "
        "every stripe. You are familiar with the criminal element of a city and have earned the respect — "
        "and occasional resentment — of those you have kept in line."
    ),
    "Clan Crafter": (
        "The Stout Folk are well known for their artisanship and the worth of their crafts, and you have "
        "been trained in that ancient dwarven tradition. For years you labored under a master of the craft, "
        "enduring long hours and honing your skills to a fine edge. You take pride in your work and in the "
        "heritage of your craft, keeping the traditions of your ancestors alive in every piece you create."
    ),
    "Cloistered Scholar": (
        "As a child, you were inquisitive when your playmates were possessive or raucous. In your formative "
        "years, you found your way to one of the great institutes of learning, where you were apprenticed "
        "and taught that knowledge is a more valuable treasure than gold or gems. Now you venture from the "
        "library into a world that holds far more secrets than any book — and you intend to document them all."
    ),
    "Courtier": (
        "In your earlier years, you devoted yourself to the workings of high courts and bureaucracies of "
        "noble houses. You might have been a tax collector, a lawyer, a herald at the court of a noble "
        "lord, or a diplomat in service to a city or kingdom. You have learned that words can be more "
        "powerful than swords, and that a well-placed favor or a carefully worded letter can change the "
        "course of history."
    ),
    "Criminal": (
        "You are an experienced criminal with a history of breaking the law. You have spent a lot of time "
        "among other criminals and still have contacts within the criminal underworld. You're far closer than "
        "most people to the world of murder, theft, and violence that pervades the underbelly of civilization, "
        "and you have used every trick in the book to stay one step ahead of the law."
    ),
    "Entertainer": (
        "You thrive in front of an audience. You know how to entrance them, entertain them, and even inspire "
        "them. Your poignant performances have touched the hearts of many listeners, and you have the fire "
        "of performance in your blood. From humble taverns to grand theaters, you have honed your act and "
        "learned to read a crowd — giving them what they want while leaving them wanting more."
    ),
    "Faction Agent": (
        "Many organizations throughout the Sword Coast and beyond are bound by a shared philosophy, a "
        "common religion, or a mutual commitment to a goal. You are an agent of one such faction, working "
        "clandestinely to advance your organization's goals and gather intelligence against its enemies. "
        "You know how to operate in the shadows and how to call on your faction's resources when you need "
        "help — but you also know how to disappear when that becomes necessary."
    ),
    "Far Traveler": (
        "You are from a distant place, one so remote that few of the common folk realize it even exists. "
        "You have crossed seas and survived climates most adventurers never encounter, learning to navigate "
        "unfamiliar cultures and languages through careful observation. Your exotic origins make you an "
        "object of curiosity to those you meet, and your unique perspective on the world around you has "
        "proved to be an unexpected advantage."
    ),
    "Fisher": (
        "You have spent your life working the waters of a lake, river, or sea, harvesting the bounty they "
        "offer. The life of a fisher is filled with hard work and routine — a cycle of tides, seasons, and "
        "the ebb and flow of fish populations. You've weathered storms that would terrify landlocked folk "
        "and learned the patience required to wait for fortune to find you on the open water."
    ),
    "Folk Hero": (
        "You come from a humble social rank, but you are destined for so much more. Already the people of "
        "your home village regard you as their champion, and your destiny calls you to stand against the "
        "tyrants and monsters that threaten the common folk everywhere. You grew up among working people "
        "and you share their values: fairness, hospitality, and the simple dignity of honest labor."
    ),
    "Gladiator": (
        "A gladiator is as much an entertainer as any minstrel or circus performer, trained to make the "
        "arts of combat into a spectacle the crowd can enjoy. You might have entered the arena as a "
        "prisoner, a slave, a criminal, or a willing thrill-seeker. Whatever brought you there, you "
        "survived — and you thrived. The roar of the crowd and the taste of victory in mortal combat "
        "have left marks on your soul that civilized life can never quite erase."
    ),
    "Guild Artisan": (
        "You are a member of an artisan's guild, skilled in a particular field and closely associated with "
        "other artisans. You are a well-established part of the mercantile world, freed from the constraints "
        "of a feudal social order. Your guild provides you with a social identity, a network of contacts, "
        "and the assurance that your skills will be recognized and fairly compensated wherever you travel."
    ),
    "Guild Merchant": (
        "Rather than mastering a craft, you have built your livelihood through the buying and selling of "
        "goods. As a member of a merchant guild you have the skills to evaluate quality, negotiate deals, "
        "and move merchandise across vast distances. You know how money flows through a city and how to "
        "find buyers and sellers for nearly anything — a talent that translates surprisingly well to "
        "the adventuring life."
    ),
    "Haunted One": (
        "You are haunted by something so terrible that you dare not speak of it. You've tried to bury it "
        "and run away from it, to no avail. Whatever this thing is that haunts you can't be fixed, and it "
        "can't be unseen. When you close your eyes, you see it. When you sleep, you dream of it. Perhaps "
        "someday you'll find a way to defeat it — but until then, you carry its shadow wherever you go."
    ),
    "Hermit": (
        "You lived in seclusion — either in a sheltered community such as a monastery, or entirely alone — "
        "for a formative part of your life. In your time apart from the clamor of society, you found quiet, "
        "solitude, and perhaps some of the answers you were looking for. The wisdom you gained through "
        "contemplation and simple living has proven far more valuable than anything you could have learned "
        "in a city, and you carry it with you as you return to the world."
    ),
    "Inheritor": (
        "You are the heir to something of great value — not merely money or physical wealth, but an object, "
        "piece of information, or a title that has been entrusted to you by a member of your family, a "
        "mentor, or a dying adventurer. The nature of this inheritance and its true significance may not "
        "yet be fully clear to you, but the responsibility it carries has set you on the path of adventure."
    ),
    "Investigator": (
        "As a city official or private investigator, you are trained — and authorized — to look into crimes "
        "and uncover the truth behind mysterious events. You pride yourself on your ability to get results "
        "where others have failed, often by following leads to dark and dangerous places. Logic, keen "
        "observation, and an instinct for knowing when someone is lying are your most reliable tools."
    ),
    "Knight": (
        "A knight is a member of the warrior elite, trained from youth in the arts of war and sworn to "
        "uphold an order of chivalry, a noble liege, or a personal code of conduct. Most knights serve a "
        "lord or king, but some travel as errant knights in search of quests to prove their valor. You "
        "carry a title bestowed upon you by a liege lord or earned in the field, and with it the obligation "
        "to act with honor, courage, and mercy."
    ),
    "Knight of the Order": (
        "You belong to an order of knights who have sworn oaths to achieve a certain goal — whether "
        "smashing a thieves' guild, establishing justice, or righting wrongs in a land where law is absent. "
        "The order's goals define your own, and the brotherhood of your fellow knights provides both "
        "support and a standard to live up to. You are more than a warrior; you are a symbol of your "
        "order's ideals made manifest."
    ),
    "Marine": (
        "You were trained for battle on sea and land alike. As a marine, you served aboard ships and "
        "slogged through swamps and jungles on raids, defending your vessel against pirates and claiming "
        "plunder of your own. The hardships of maritime combat — fighting on rolling decks, swimming in "
        "full armor, enduring weeks at sea without fresh food — have forged you into a supremely adaptable "
        "warrior."
    ),
    "Mercenary Veteran": (
        "As a sell-sword who fought battles for coin, you're well acquainted with risking life and limb "
        "for a chance at treasure. You've served in many companies and under many banners, and you've "
        "learned that loyalty lasts only as long as the gold does. Now you look for other opportunities "
        "to earn a living — ideally ones where you aren't being paid by someone who might decide you "
        "cost too much."
    ),
    "Noble": (
        "You understand wealth, power, and privilege. You carry a noble title, and your family owns land, "
        "collects taxes, and wields significant political influence. You might be a pampered aristocrat "
        "unfamiliar with work or discomfort, a former merchant who rose to nobility through wealth, or a "
        "disinherited scoundrel with a name but no fortune. Whatever the case, your noble bearing opens "
        "doors that remain closed to common folk — and creates enemies among those who resent your station."
    ),
    "Outlander": (
        "You grew up in the wilds, far from civilization and the comforts of town and technology. You've "
        "witnessed the migration of herds larger than forests, survived weather more extreme than any "
        "city-dweller could comprehend, and enjoyed the solitude of being the only thinking creature for "
        "miles in any direction. The city feels cramped and loud to you, but you've learned to navigate "
        "it just as you navigate trackless wilderness — by adapting."
    ),
    "Pirate": (
        "You spent your formative years under the sway of a dread pirate or among a crew of cutthroats, "
        "learning to survive in a world of robbers and rogues. You've indulged in larceny on the high "
        "seas, weathered storms that would splinter lesser ships, and sent more than one deserving soul "
        "to a watery grave. The open ocean is your home, and the horizon your ever-retreating destination."
    ),
    "Sage": (
        "You spent years learning the lore of the multiverse. You scoured manuscripts, studied scrolls, "
        "and listened to the greatest experts on subjects that fascinate you. Your efforts have made you "
        "a master of your chosen field. When you don't know an answer, you know where to find it — and "
        "you've learned that the most dangerous thing in the world is a question no one has yet thought "
        "to ask."
    ),
    "Sailor": (
        "You sailed on a seagoing vessel for years. In that time, you faced down mighty storms, monsters "
        "of the deep, and pirates who wanted to send your craft to the bottomless depths. Your first love "
        "is the distant horizon, but the time has come to try your hand at something new. The sea will "
        "always call you back — but for now, adventure on solid ground beckons."
    ),
    "Soldier": (
        "War has been your life for as long as you care to remember. You trained as a youth, studied the "
        "use of weapons and armor, and learned basic survival techniques, including how to stay alive on "
        "the battlefield. You might have been part of a standing national army, a mercenary company, or "
        "a local militia. Regardless, the discipline, camaraderie, and brutality of military life have "
        "left an indelible mark on who you are."
    ),
    "Spy": (
        "Although your capabilities are not much different from those of a criminal, you practiced them "
        "as an espionage agent of a government, noble house, or other organization. The clandestine nature "
        "of your work means your true employer may be unknown to most, even among your allies. You are "
        "adept at moving through society unnoticed, gathering secrets, and making sure that those who "
        "know too much don't remain a problem for long."
    ),
    "Urban Bounty Hunter": (
        "Before you became an adventurer, your life was already full of conflict and excitement, because "
        "you made a living tracking down people for pay. Unlike wilderness hunters, you are an urbanite — "
        "skilled at navigating the underbelly of city life and tracking quarry through the thick of "
        "civilization. Taverns, thieves' guilds, and shadowy alleyways are your hunting grounds, and "
        "you've learned that the city always gives up its secrets to someone patient enough to listen."
    ),
    "Urchin": (
        "You grew up on the streets alone, orphaned, and poor. You had no one to watch over you or "
        "provide for you, so you learned to provide for yourself. You fought fiercely over food and kept "
        "a constant watch out for other desperate souls who might steal from you. Sleep was a luxury, "
        "and every meal was hard-won. Despite everything, you survived — and that alone makes you "
        "tougher than most."
    ),
    "Uthgardt Tribe Member": (
        "You are a member — or former member — of one of the Uthgardt barbarian tribes of the North. "
        "Even if you've left your people behind to seek your fortune, you hold the traditions of the "
        "Uthgardt close to your heart. Your people are known for their fierce pride, their reverence "
        "for their totemic ancestors, and a deep suspicion of magic. The brutal nature of your upbringing "
        "has made you strong and honed your instincts for survival to a razor's edge."
    ),
    "Waterdhavian Noble": (
        "You are a scion of one of the great noble families of Waterdeep, the City of Splendors. "
        "Waterdhavian noble families jealously guard their bloodlines as well as the coffers of their "
        "banking houses, and they exert their influence throughout the North through commerce, politics, "
        "and carefully arranged marriages. You were raised on the finest food, educated by the best "
        "tutors, and dressed in the most fashionable clothes — but you've always suspected the real "
        "world holds something more interesting than ballrooms and ledgers."
    ),
}

# ── Racial traits ──────────────────────────────────────────────────────────────

RACIAL_TRAITS = {
    "Dragonborn":          [("Draconic Ancestry","Choose a dragon type; determines your breath weapon element."),("Breath Weapon","Action: exhale destructive energy in a 15 ft cone or 30 ft line. DEX/CON save. Damage = 2d6 at level 1."),("Damage Resistance","Resistance to the damage type of your breath weapon.")],
    "Dwarf (Hill)":        [("Darkvision","60 ft."),("Dwarven Resilience","Advantage on saves vs. poison; resistance to poison damage."),("Dwarven Combat Training","Proficiency with battleaxe, handaxe, light hammer, warhammer."),("Stonecunning","+2× proficiency bonus on History checks about stonework."),("Dwarven Toughness","HP maximum increases by 1 per level.")],
    "Dwarf (Mountain)":    [("Darkvision","60 ft."),("Dwarven Resilience","Advantage on saves vs. poison; resistance to poison damage."),("Dwarven Combat Training","Proficiency with battleaxe, handaxe, light hammer, warhammer."),("Stonecunning","+2× proficiency bonus on History checks about stonework."),("Dwarven Armor Training","Proficiency with light and medium armor.")],
    "Elf (Drow / Dark)":   [("Darkvision","120 ft."),("Keen Senses","Proficiency in Perception."),("Fey Ancestry","Advantage vs. charm; immune to magical sleep."),("Trance","Only need 4 hours of meditation instead of sleep."),("Sunlight Sensitivity","Disadvantage on attack rolls and Perception in sunlight."),("Drow Magic","Cantrips: Dancing Lights (level 1), Faerie Fire (level 3), Darkness (level 5).")],
    "Elf (High)":          [("Darkvision","60 ft."),("Keen Senses","Proficiency in Perception."),("Fey Ancestry","Advantage vs. charm; immune to magical sleep."),("Trance","Only need 4 hours of meditation."),("Elf Weapon Training","Proficiency with longsword, shortsword, shortbow, longbow."),("Cantrip","Know one wizard cantrip of your choice.")],
    "Elf (Wood)":          [("Darkvision","60 ft."),("Keen Senses","Proficiency in Perception."),("Fey Ancestry","Advantage vs. charm; immune to magical sleep."),("Trance","Only need 4 hours of meditation."),("Elf Weapon Training","Proficiency with longsword, shortsword, shortbow, longbow."),("Fleet of Foot","Base speed 35 ft."),("Mask of the Wild","Can hide when only lightly obscured by natural phenomena.")],
    "Gnome (Forest)":      [("Darkvision","60 ft."),("Gnome Cunning","Advantage on INT/WIS/CHA saves vs. magic."),("Natural Illusionist","Know Minor Illusion cantrip."),("Speak with Small Beasts","Communicate simple ideas with Small or smaller beasts.")],
    "Gnome (Rock)":        [("Darkvision","60 ft."),("Gnome Cunning","Advantage on INT/WIS/CHA saves vs. magic."),("Artificer's Lore","+2× proficiency bonus on History checks about magic items and tech."),("Tinker","Construct tiny clockwork devices.")],
    "Half-Elf":            [("Darkvision","60 ft."),("Fey Ancestry","Advantage vs. charm; immune to magical sleep."),("Skill Versatility","Gain proficiency in two skills of your choice.")],
    "Half-Orc":            [("Darkvision","60 ft."),("Menacing","Proficiency in Intimidation."),("Relentless Endurance","When reduced to 0 HP, drop to 1 HP instead (once per long rest)."),("Savage Attacks","On a critical hit with a melee weapon, add one extra weapon damage die.")],
    "Halfling (Lightfoot)":  [("Lucky","Reroll 1s on attack rolls, ability checks, and saves."),("Brave","Advantage on saves vs. being frightened."),("Halfling Nimbleness","Move through space of larger creatures."),("Naturally Stealthy","Can attempt to hide behind larger creatures.")],
    "Halfling (Stout)":    [("Lucky","Reroll 1s on attack rolls, ability checks, and saves."),("Brave","Advantage on saves vs. being frightened."),("Halfling Nimbleness","Move through space of larger creatures."),("Stout Resilience","Advantage on saves vs. poison; resistance to poison damage.")],
    "Human":               [("Extra Language","Speak one extra language of your choice.")],
    "Human (Variant)":     [("Feat","Choose one feat."),("Skill","Gain proficiency in one skill."),("Ability Bump","+1 to two different ability scores.")],
    "Tiefling":            [("Darkvision","60 ft."),("Hellish Resistance","Resistance to fire damage."),("Infernal Legacy","Know Thaumaturgy cantrip; Hellish Rebuke (level 3) as a 2nd-level spell; Darkness (level 5). CHA is the spellcasting ability.")],
    "Aasimar":             [("Darkvision","60 ft."),("Celestial Resistance","Resistance to necrotic and radiant damage."),("Healing Hands","Action: heal HP equal to your level (once per long rest)."),("Light Bearer","Know Light cantrip.")],
    "Firbolg":             [("Firbolg Magic","Cast Detect Magic and Disguise Self once each per short rest (WIS)."),("Hidden Step","Bonus action: turn invisible until next turn (once per short rest)."),("Powerful Build","Count as Large for carrying capacity."),("Speech of Beast and Leaf","Communicate simple ideas with beasts and plants.")],
    "Goblin":              [("Darkvision","60 ft."),("Fury of the Small","Once per rest, deal extra damage equal to your level when hitting a larger creature."),("Nimble Escape","Bonus action to Disengage or Hide.")],
    "Goliath":             [("Natural Athlete","Proficiency in Athletics."),("Stone's Endurance","Bonus action: reduce damage by 1d12 + CON modifier (once per rest)."),("Powerful Build","Count as Large for carrying capacity."),("Mountain Born","Adapted to cold and high altitude.")],
    "Kenku":               [("Expert Forgery","Advantage when creating forgeries and duplicating writing."),("Kenku Training","Proficiency in two of: Acrobatics, Deception, Stealth, Sleight of Hand."),("Mimicry","Mimic sounds and voices heard.")],
    "Lizardfolk":          [("Cunning Artisan","Craft simple items from slain creatures."),("Hold Breath","Hold breath for 15 minutes."),("Natural Armor","AC = 13 + DEX modifier when unarmored."),("Hungry Jaws","Bonus action: bite attack; gain temp HP on hit."),("Natural Weapons","Bite does 1d6 + STR piercing damage.")],
    "Tabaxi":              [("Darkvision","60 ft."),("Feline Agility","Double speed for one turn; recharges after not moving."),("Cat's Claws","Climb speed 20 ft; claws deal 1d4 slashing."),("Cat's Talent","Proficiency in Perception and Stealth.")],
    "Triton":              [("Amphibious","Breathe air and water."),("Control Air and Water","Cast Fog Cloud (level 1), Gust of Wind (level 3), Wall of Water (level 5). CHA is the spellcasting ability."),("Darkvision","60 ft."),("Emissary of the Sea","Communicate simple ideas with beasts that breathe water."),("Guardians of the Depths","Adapted to cold and deep pressure; resistance to cold damage.")],
    "Yuan-ti Pureblood":   [("Darkvision","60 ft."),("Innate Spellcasting","Poison Spray cantrip; Animal Friendship (snakes, at will); Suggestion (once per rest). CHA is spellcasting ability."),("Magic Resistance","Advantage on saves vs. spells and magical effects."),("Poison Immunity","Immune to poison damage and the poisoned condition.")],
    "Genasi (Air)":        [("Unending Breath","Hold breath indefinitely."),("Mingle with the Wind","Cast Levitate once per rest (CON)."),("Languages","Common and Primordial.")],
    "Genasi (Earth)":      [("Earth Walk","Move across difficult terrain of rock and earth without extra movement."),("Merge with Stone","Cast Pass without Trace once per rest (CON). ")],
    "Genasi (Fire)":       [("Darkvision","60 ft."),("Fire Resistance","Resistance to fire damage."),("Reach to the Blaze","Know Produce Flame cantrip; cast Burning Hands once per rest (CON).")],
    "Genasi (Water)":      [("Acid Resistance","Resistance to acid damage."),("Amphibious","Breathe air and water."),("Swim","Swim speed 30 ft."),("Call to the Wave","Know Shape Water cantrip; cast Create/Destroy Water once per rest (CON).")],
}

# ── Class features by level ────────────────────────────────────────────────────

CLASS_FEATURES = {
    "Barbarian": {
        1: ["Rage (2/rest, +2 damage)","Unarmored Defense (AC = 10 + DEX + CON)"],
        2: ["Reckless Attack","Danger Sense (advantage on DEX saves vs. visible sources)"],
        3: ["Primal Path (subclass)","Primal Knowledge"],
        4: ["Ability Score Improvement"],
        5: ["Extra Attack","Fast Movement (+10 ft speed when not in heavy armor)"],
        6: ["Subclass Feature","Rage: +2 damage"],
        7: ["Feral Instinct (advantage on Initiative; can rage to un-surprise yourself)"],
        8: ["Ability Score Improvement"],
        9: ["Brutal Critical (1 extra die on crits)","Rage: 3/rest"],
        10: ["Subclass Feature"],
        11: ["Relentless Rage (when reduced to 0 HP during rage, roll DC 10 CON save to drop to 1 HP)"],
        12: ["Ability Score Improvement","Rage: +3 damage"],
        13: ["Brutal Critical (2 extra dice on crits)"],
        14: ["Subclass Feature"],
        15: ["Persistent Rage (rage only ends if you choose or fall unconscious)"],
        16: ["Ability Score Improvement","Brutal Critical (3 extra dice)"],
        17: ["Rage: 4/rest"],
        18: ["Indomitable Might (STR minimum equals STR score)"],
        19: ["Ability Score Improvement"],
        20: ["Primal Champion (+4 STR, +4 CON)","Rage: 6/rest, +4 damage"],
    },
    "Bard": {
        1: ["Bardic Inspiration (d6, CHA mod times/rest)","Spellcasting"],
        2: ["Jack of All Trades (half proficiency on untrained checks)","Song of Rest (d6 healing on short rest)"],
        3: ["Bard College (subclass)","Expertise (double proficiency in two skills)"],
        4: ["Ability Score Improvement"],
        5: ["Bardic Inspiration (d8)","Font of Inspiration (regain Bardic Inspiration on short rest)"],
        6: ["Countercharm","Subclass Feature"],
        7: ["Subclass Feature"],
        8: ["Ability Score Improvement"],
        9: ["Song of Rest (d8)"],
        10: ["Bardic Inspiration (d10)","Expertise (two more skills)","Magical Secrets (learn 2 spells from any class)"],
        11: ["Bardic Inspiration (d10)"],
        12: ["Ability Score Improvement"],
        13: ["Song of Rest (d10)"],
        14: ["Magical Secrets","Subclass Feature"],
        15: ["Bardic Inspiration (d12)"],
        16: ["Ability Score Improvement"],
        17: ["Song of Rest (d12)"],
        18: ["Magical Secrets"],
        19: ["Ability Score Improvement"],
        20: ["Superior Inspiration (regain at least 1 Bardic Inspiration on initiative)"],
    },
    "Cleric": {
        1: ["Divine Domain (subclass)","Spellcasting"],
        2: ["Channel Divinity (1/rest): Turn Undead","Subclass Feature"],
        3: ["Subclass Feature"],
        4: ["Ability Score Improvement"],
        5: ["Destroy Undead (CR 1/2)"],
        6: ["Channel Divinity: 2/rest","Subclass Feature"],
        7: ["Subclass Feature"],
        8: ["Ability Score Improvement","Destroy Undead (CR 1)","Subclass Feature"],
        9: [],
        10: ["Divine Intervention (call on deity, 1/week)"],
        11: ["Destroy Undead (CR 2)"],
        12: ["Ability Score Improvement"],
        13: [],
        14: ["Destroy Undead (CR 3)"],
        15: [],
        16: ["Ability Score Improvement"],
        17: ["Destroy Undead (CR 4)","Subclass Feature"],
        18: ["Channel Divinity: 3/rest"],
        19: ["Ability Score Improvement"],
        20: ["Divine Intervention improved (auto-succeeds)"],
    },
    "Druid": {
        1: ["Druidic (secret language)","Spellcasting"],
        2: ["Wild Shape (CR 1/4, no fly/swim)","Druid Circle (subclass)"],
        3: [],
        4: ["Wild Shape: CR 1/2 (swim)","Ability Score Improvement"],
        5: [],
        6: ["Subclass Feature"],
        7: [],
        8: ["Wild Shape: CR 1 (fly)","Ability Score Improvement"],
        9: [],
        10: ["Subclass Feature"],
        11: [],
        12: ["Ability Score Improvement"],
        13: [],
        14: ["Subclass Feature"],
        15: [],
        16: ["Ability Score Improvement"],
        17: [],
        18: ["Timeless Body (no aging effects)","Beast Spells (cast while Wild Shaped)"],
        19: ["Ability Score Improvement"],
        20: ["Archdruid (unlimited Wild Shape)"],
    },
    "Fighter": {
        1: ["Fighting Style","Second Wind (heal 1d10 + level, 1/rest)"],
        2: ["Action Surge (extra action, 1/rest)"],
        3: ["Martial Archetype (subclass)"],
        4: ["Ability Score Improvement"],
        5: ["Extra Attack (2 attacks)"],
        6: ["Ability Score Improvement"],
        7: ["Subclass Feature"],
        8: ["Ability Score Improvement"],
        9: ["Indomitable (reroll a failed save, 1/rest)"],
        10: ["Subclass Feature"],
        11: ["Extra Attack (3 attacks)"],
        12: ["Ability Score Improvement"],
        13: ["Indomitable (2 uses)"],
        14: ["Ability Score Improvement"],
        15: ["Subclass Feature"],
        16: ["Ability Score Improvement"],
        17: ["Action Surge (2/rest)","Indomitable (3 uses)"],
        18: ["Subclass Feature"],
        19: ["Ability Score Improvement"],
        20: ["Extra Attack (4 attacks)"],
    },
    "Monk": {
        1: ["Unarmored Defense (AC = 10 + DEX + WIS)","Martial Arts (d4, DEX attacks, bonus unarmed strike)"],
        2: ["Ki Points (= level)","Flurry of Blows / Patient Defense / Step of the Wind","Unarmored Movement (+10 ft)"],
        3: ["Monastic Tradition (subclass)","Deflect Missiles"],
        4: ["Ability Score Improvement","Slow Fall"],
        5: ["Extra Attack","Stunning Strike"],
        6: ["Ki-Empowered Strikes (unarmed = magical)","Subclass Feature"],
        7: ["Evasion","Stillness of Mind (remove charm/frighten as action)"],
        8: ["Ability Score Improvement"],
        9: ["Unarmored Movement (walk on water, up walls)"],
        10: ["Purity of Body (immune to disease and poison)"],
        11: ["Subclass Feature"],
        12: ["Ability Score Improvement"],
        13: ["Tongue of the Sun and Moon (speak any language)"],
        14: ["Diamond Soul (proficiency in all saves, reroll with ki)"],
        15: ["Timeless Body (no aging, no food/water needed)"],
        16: ["Ability Score Improvement"],
        17: ["Subclass Feature"],
        18: ["Empty Body (invisible + plane shift with ki)"],
        19: ["Ability Score Improvement"],
        20: ["Perfect Self (regain 4 ki on initiative if at 0)"],
    },
    "Paladin": {
        1: ["Divine Sense","Lay on Hands (HP pool = 5 × level)"],
        2: ["Fighting Style","Spellcasting","Divine Smite (expend spell slot for extra radiant damage on hit)"],
        3: ["Divine Health (immune to disease)","Sacred Oath (subclass)","Subclass Feature"],
        4: ["Ability Score Improvement"],
        5: ["Extra Attack","Subclass Feature"],
        6: ["Aura of Protection (+CHA mod to saves for allies within 10 ft)"],
        7: ["Subclass Feature"],
        8: ["Ability Score Improvement"],
        9: ["Subclass Feature"],
        10: ["Aura of Courage (allies within 10 ft immune to frightened)"],
        11: ["Improved Divine Smite (bonus 1d8 radiant on all melee hits)"],
        12: ["Ability Score Improvement"],
        13: [],
        14: ["Cleansing Touch (end spell on self/ally as action, CHA mod/rest)"],
        15: ["Subclass Feature"],
        16: ["Ability Score Improvement"],
        17: [],
        18: ["Aura Improvements (auras extend to 30 ft)"],
        19: ["Ability Score Improvement"],
        20: ["Subclass Feature (Sacred Oath capstone)"],
    },
    "Ranger": {
        1: ["Favored Enemy (advantage on track/recall about chosen type)","Natural Explorer (bonus in favored terrain)"],
        2: ["Fighting Style","Spellcasting"],
        3: ["Ranger Archetype (subclass)","Primeval Awareness"],
        4: ["Ability Score Improvement"],
        5: ["Extra Attack"],
        6: ["Favored Enemy (second choice)","Natural Explorer (second terrain)"],
        7: ["Subclass Feature"],
        8: ["Ability Score Improvement","Land's Stride (ignore difficult terrain, no damage from plants)"],
        9: [],
        10: ["Natural Explorer (third terrain)","Hide in Plain Sight (+10 to Stealth when camouflaged, stationary)"],
        11: ["Subclass Feature"],
        12: ["Ability Score Improvement"],
        13: [],
        14: ["Vanish (Hide as bonus action; can't be tracked nonmagically)"],
        15: ["Subclass Feature"],
        16: ["Ability Score Improvement"],
        17: [],
        18: ["Feral Senses (no disadvantage attacking invisible, detect invisible within 30 ft)"],
        19: ["Ability Score Improvement"],
        20: ["Foe Slayer (+CHA mod to one attack roll or damage roll vs. Favored Enemy per turn)"],
    },
    "Rogue": {
        1: ["Expertise (two skills)","Sneak Attack (1d6)","Thieves' Cant"],
        2: ["Cunning Action (bonus action: Dash/Disengage/Hide)"],
        3: ["Roguish Archetype (subclass)","Sneak Attack (2d6)"],
        4: ["Ability Score Improvement"],
        5: ["Sneak Attack (3d6)","Uncanny Dodge (reaction: halve an attack's damage)"],
        6: ["Expertise (two more skills)","Sneak Attack (3d6)"],
        7: ["Evasion","Sneak Attack (4d6)"],
        8: ["Ability Score Improvement","Sneak Attack (4d6)"],
        9: ["Subclass Feature","Sneak Attack (5d6)"],
        10: ["Ability Score Improvement","Sneak Attack (5d6)"],
        11: ["Reliable Talent (min 10 on proficient skill checks)","Sneak Attack (6d6)"],
        12: ["Ability Score Improvement","Sneak Attack (6d6)"],
        13: ["Subclass Feature","Sneak Attack (7d6)"],
        14: ["Blindsense (within 10 ft, sense invisible creatures if you can hear)","Sneak Attack (7d6)"],
        15: ["Slippery Mind (proficiency in WIS saves)","Sneak Attack (8d6)"],
        16: ["Ability Score Improvement","Sneak Attack (8d6)"],
        17: ["Subclass Feature","Sneak Attack (9d6)"],
        18: ["Elusive (no advantage against you while not incapacitated)","Sneak Attack (9d6)"],
        19: ["Ability Score Improvement","Sneak Attack (10d6)"],
        20: ["Stroke of Luck (turn miss into hit or failed check into 20, 1/rest)","Sneak Attack (10d6)"],
    },
    "Sorcerer": {
        1: ["Sorcerous Origin (subclass)","Spellcasting"],
        2: ["Font of Magic (Sorcery Points = level)"],
        3: ["Metamagic (choose 2: Careful, Distant, Empowered, Extended, Heightened, Quickened, Subtle, Twinned)"],
        4: ["Ability Score Improvement"],
        5: [],
        6: ["Subclass Feature"],
        7: [],
        8: ["Ability Score Improvement"],
        9: [],
        10: ["Metamagic (one more option)"],
        11: [],
        12: ["Ability Score Improvement"],
        13: [],
        14: ["Subclass Feature"],
        15: [],
        16: ["Ability Score Improvement","Metamagic (one more option)"],
        17: [],
        18: ["Subclass Feature"],
        19: ["Ability Score Improvement"],
        20: ["Sorcerous Restoration (regain 4 sorcery points on short rest)"],
    },
    "Warlock": {
        1: ["Otherworldly Patron (subclass)","Pact Magic (short-rest slots)","Spellcasting"],
        2: ["Eldritch Invocations (2 invocations)"],
        3: ["Pact Boon (Pact of the Blade / Chain / Tome / Talisman)"],
        4: ["Ability Score Improvement"],
        5: ["Eldritch Invocations (total 3)"],
        6: ["Subclass Feature"],
        7: ["Eldritch Invocations (total 4)"],
        8: ["Ability Score Improvement"],
        9: ["Eldritch Invocations (total 5)"],
        10: ["Subclass Feature"],
        11: ["Eldritch Invocations (total 5 + Mystic Arcanum L6)"],
        12: ["Ability Score Improvement","Eldritch Invocations (total 6)"],
        13: ["Mystic Arcanum: Level 7"],
        14: ["Subclass Feature"],
        15: ["Mystic Arcanum: Level 8","Eldritch Invocations (total 7)"],
        16: ["Ability Score Improvement"],
        17: ["Mystic Arcanum: Level 9","Eldritch Invocations (total 8)"],
        18: ["Eldritch Invocations (total 8)"],
        19: ["Ability Score Improvement","Eldritch Invocations (total 8)"],
        20: ["Eldritch Master (spend 1 min; regain all Pact Magic slots, 1/long rest)"],
    },
    "Wizard": {
        1: ["Arcane Recovery (regain spell slots on short rest, total ≤ half level)","Spellcasting"],
        2: ["Arcane Tradition (subclass)"],
        3: [],
        4: ["Ability Score Improvement"],
        5: [],
        6: ["Subclass Feature"],
        7: [],
        8: ["Ability Score Improvement"],
        9: [],
        10: ["Subclass Feature"],
        11: [],
        12: ["Ability Score Improvement"],
        13: [],
        14: ["Subclass Feature"],
        15: [],
        16: ["Ability Score Improvement"],
        17: [],
        18: ["Spell Mastery (cast a 1st and 2nd level spell at will without a slot)"],
        19: ["Ability Score Improvement"],
        20: ["Signature Spell (two 3rd-level spells always prepared, cast once each without a slot)"],
    },
    "Artificer": {
        1: ["Magical Tinkering","Spellcasting"],
        2: ["Infuse Item (2 infusions)"],
        3: ["Artificer Specialist (subclass)","The Right Tool for the Job (craft artisan's tool with 1 hr)"],
        4: ["Ability Score Improvement"],
        5: ["Subclass Feature"],
        6: ["Tool Expertise (double proficiency on tool checks)"],
        7: ["Flash of Genius (add INT mod to saves/checks near you, INT mod/rest)"],
        8: ["Ability Score Improvement","Magic Item Adept (attune 4 items; craft common/uncommon faster/cheaper)"],
        9: ["Subclass Feature"],
        10: ["Magic Item Savant (attune 5 items, ignore attunement requirements for class/race/spell/level)"],
        11: ["Subclass Feature"],
        12: ["Ability Score Improvement"],
        13: [],
        14: ["Magic Item Master (attune 6 items)"],
        15: ["Subclass Feature"],
        16: ["Ability Score Improvement"],
        17: [],
        18: ["Magic Item Master","Spell-Storing Item (store spell in an object for allies to use)"],
        19: ["Ability Score Improvement"],
        20: ["Soul of Artifice (+1 to all saves per attuned item; as reaction drop to 1 HP instead of 0)"],
    },
}

# ── Personality suggestions by background ─────────────────────────────────────

PERSONALITY_SUGGESTIONS = {
    "Acolyte": {
        "traits":  ["I idolize a particular hero of my faith.","I can find common ground between the fiercest enemies.","I see omens in every event.","Nothing can shake my optimistic attitude."],
        "ideals":  ["Tradition: The ways of the old must be preserved.","Charity: I always try to help those in need.","Change: Change is natural and must be embraced.","Power: I hope to one day rise to the top of my faith."],
        "bonds":   ["I would die to recover an ancient relic of my faith.","I will someday get revenge on the corrupt temple hierarchy.","I owe my life to a priest who took me in when I was young.","I seek to preserve a sacred text that my enemies consider heretical."],
        "flaws":   ["I judge others harshly and myself even more severely.","I put too much trust in those in power of my faith.","My piety sometimes leads me to blindly trust others.","I am inflexible in my thinking."],
    },
    "Criminal": {
        "traits":  ["I always have a plan for when things go wrong.","I am always calm, no matter the situation.","The first thing I do is case the joint for an exit.","I would rather make a new friend than a new enemy."],
        "ideals":  ["Honor: I don't steal from others in my trade.","Freedom: Chains are meant to be broken.","Greed: I will do whatever it takes to become wealthy.","People: I'm loyal to my friends, not ideals."],
        "bonds":   ["I'm trying to pay off an old debt I owe a dangerous person.","My ill-gotten gains go to support my family.","Something important was taken from me and I aim to steal it back.","I will become the greatest thief who ever lived."],
        "flaws":   ["When I see something valuable I can't think about anything but how to steal it.","When faced with a choice between money and friends, I usually choose money.","I turn tail and run when things look bad.","An innocent person is in prison for a crime I committed."],
    },
    "Folk Hero": {
        "traits":  ["I judge people by their actions, not their words.","If someone is in trouble, I'm always ready to lend help.","When I set my mind to something I follow through.","I have a strong sense of fair play and hate seeing others get an unfair advantage."],
        "ideals":  ["Respect: Everyone deserves to be treated with dignity.","Fairness: No one should get preferential treatment.","Freedom: Tyrants must not be allowed to oppress the people.","Might: If I become strong, I can protect those who need it."],
        "bonds":   ["I have a family, but I have no idea where they are.","I protect those who cannot protect themselves.","I will face any challenge to win the approval of my family.","My honor is my life."],
        "flaws":   ["The tyrant who rules my land will stop at nothing to see me dead.","I'm convinced of the significance of my destiny and blind to my shortcomings.","The people who knew me when I was young know my shameful secret.","I have trouble trusting in my allies."],
    },
    "Noble": {
        "traits":  ["My eloquent flattery makes everyone I talk to feel like the most wonderful and important person in the world.","The common folk love me for my kindness and generosity.","No one could doubt by looking at my regal bearing that I am a cut above the unwashed masses.","I take great pains to always look my best and follow the latest fashions."],
        "ideals":  ["Respect: Respect is due to me because of my position, not the other way around.","Responsibility: I must protect those in my charge.","Independence: I must prove that I can handle myself without the coddling of my family.","Power: If I can attain more power, no one will tell me what to do."],
        "bonds":   ["I will face any challenge to win the approval of my family.","My house's alliance with another noble family must be sustained at all costs.","Nothing is more important than the other members of my family.","I am in love with a beautiful heir, and our families are enemies."],
        "flaws":   ["I secretly believe that everyone is beneath me.","I hide a truly scandalous secret.","I too often hear veiled insults and threats in every word addressed to me.","I have an insatiable desire for carnal pleasures."],
    },
    "Sage": {
        "traits":  ["I use polysyllabic words that convey the impression of great erudition.","I've read every book in the world's greatest libraries.","I'm used to helping out those who aren't as smart as I am.","There's nothing I like more than a good mystery."],
        "ideals":  ["Knowledge: The path to power and self-improvement is through knowledge.","Beauty: What is beautiful points us beyond itself toward what is true.","Logic: Emotions must not cloud our logical thinking.","No Limits: Nothing should fetter the infinite possibility inherent in all existence."],
        "bonds":   ["It is my duty to protect my students.","I have an ancient text that holds terrible secrets.","My life's work is a series of tomes related to a specific field of lore.","I've been searching my whole life for the answer to a certain question."],
        "flaws":   ["I am easily distracted by the promise of information.","Most people scream and run when they see a demon — I stop and take notes.","Unlocking an ancient mystery is worth the price of civilization.","I speak without thinking and often say things that offend."],
    },
    "Soldier": {
        "traits":  ["I'm always polite and respectful.","I'm haunted by memories of war.","I've lost too many friends and I'm slow to make new ones.","I'm full of inspiring and cautionary tales from my military experience."],
        "ideals":  ["Greater Good: Our lot is to lay down our lives for others.","Responsibility: I do what I must and obey just authority.","Independence: When people follow orders blindly, they embrace a kind of tyranny.","Live and Let Live: Ideals aren't worth killing for or going to war over."],
        "bonds":   ["I would still lay down my life for the people I served with.","Someone saved my life on the battlefield. To this day I will never leave a friend behind.","My honor is my life.","I'll never forget the crushing defeat my company suffered."],
        "flaws":   ["The monstrous enemy we faced in battle still leaves me shaken.","I have little respect for anyone who is not a proven warrior.","I made a terrible mistake in battle that cost many lives.","My hatred of my enemies is blinding and unreasonable."],
    },
    "Outlander": {
        "traits":  ["I'm driven by a wanderlust that led me away from home.","I watch over my friends as if they were a litter of newborn pups.","I once ran 25 miles without stopping to warn my clan of an approaching threat.","I have a lesson for every situation, drawn from observing nature."],
        "ideals":  ["Change: Life is like the seasons, in constant change.","Greater Good: It is each person's responsibility to make the most happiness for the tribe.","Honor: If I dishonor myself, I dishonor my whole clan.","Might: The strongest are meant to rule."],
        "bonds":   ["My family, clan, or tribe is the most important thing in my life.","An injury to the natural world is an injury to me.","I will bring terrible wrath down on the evildoers who destroyed my homeland.","I am the last of my tribe and must ensure their culture lives on."],
        "flaws":   ["I am too enamored of ale, wine, and other intoxicants.","There's no room for caution in a life lived to the fullest.","I remember every insult I've received and nurse a silent resentment toward anyone who's wronged me.","I am slow to trust members of other races."],
    },
    "Hermit": {
        "traits":  ["I've been isolated for so long that I rarely speak, preferring gestures and the occasional grunt.","I am utterly serene, even in the face of disaster.","I know a lot of esoteric lore about a very specific subject.","I connect everything that happens to me to a grand, cosmic plan."],
        "ideals":  ["Greater Good: My gifts are meant to be shared with all.","Logic: Emotions must not cloud our logical thinking.","Free Thinking: Inquiry and curiosity are the pillars of progress.","Self-Knowledge: If you know yourself, there's nothing left to know."],
        "bonds":   ["Nothing is more important than the other members of my hermitage.","I entered seclusion to hide from those who might still be hunting me.","I am still seeking the enlightenment I pursued in my seclusion.","I entered seclusion because I loved someone I could never have."],
        "flaws":   ["Now that I've returned to the world, I enjoy its delights a little too much.","I harbor dark, bloodthirsty thoughts that my isolation failed to quell.","I am dogmatic in my thoughts and philosophy.","I let my need to win arguments overshadow friendships and harmony."],
    },
}

# For backgrounds without specific suggestions, generate generic ones
_GENERIC_SUGGESTIONS = {
    "traits":  ["I always have a plan when things go wrong.","I face problems head-on.","I believe in hard work and fair play.","I always try to help those who are struggling."],
    "ideals":  ["Honesty: Truth is the foundation of trust.","Loyalty: My word is my bond.","Ambition: I will make something of myself.","Justice: Everyone deserves fair treatment."],
    "bonds":   ["My companions are my family now.","I owe a great debt to someone who helped me.","I will not rest until a wrong is made right.","Something important to me was lost or stolen."],
    "flaws":   ["I am too proud to admit when I am wrong.","My past mistakes haunt me.","I am quick to judge others.","I sometimes act before thinking."],
}

def get_personality_suggestions(background: str) -> dict:
    return PERSONALITY_SUGGESTIONS.get(background, _GENERIC_SUGGESTIONS)

CLASS_PRIMARY_STATS = {
    "Artificer": ["intelligence"],
    "Barbarian": ["strength", "constitution"],
    "Bard":      ["charisma"],
    "Cleric":    ["wisdom"],
    "Druid":     ["wisdom"],
    "Fighter":   ["strength", "dexterity", "constitution"],
    "Monk":      ["dexterity", "wisdom"],
    "Paladin":   ["strength", "charisma"],
    "Ranger":    ["dexterity", "wisdom"],
    "Rogue":     ["dexterity"],
    "Sorcerer":  ["charisma"],
    "Warlock":   ["charisma"],
    "Wizard":    ["intelligence"],
}

# Saving throw proficiencies granted by each class
CLASS_SAVING_THROWS = {
    "Artificer": ["constitution", "intelligence"],
    "Barbarian": ["strength", "constitution"],
    "Bard":      ["dexterity", "charisma"],
    "Cleric":    ["wisdom", "charisma"],
    "Druid":     ["intelligence", "wisdom"],
    "Fighter":   ["strength", "constitution"],
    "Monk":      ["strength", "dexterity"],
    "Paladin":   ["wisdom", "charisma"],
    "Ranger":    ["strength", "dexterity"],
    "Rogue":     ["dexterity", "intelligence"],
    "Sorcerer":  ["constitution", "charisma"],
    "Warlock":   ["wisdom", "charisma"],
    "Wizard":    ["intelligence", "wisdom"],
}
