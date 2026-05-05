from langchain_ollama import ChatOllama
from pydantic import BaseModel, Field
from langchain.tools import tool
from langgraph.graph import StateGraph, START, END
from langgraph.graph import MessagesState
from langchain.messages import SystemMessage, HumanMessage, ToolMessage
from assets import get_asset

llm = ChatOllama(model="llama3.2")

USER_QUERY = "Consider a strong Dungeons and Dragons character that excels at physical combat. Call the tool to decider its modifiers."

#Only point buy and race affect the character's scores
#The idea here would be to have two llm functions both modify the one Character object
#The first will be in the tool for the point buy and the second will be in a second function 
#that will determine the race, and do point calculations for race. Both will modify character object.
#Then we call the aggregation function to combine them.

class Scores():
    def __init__(self, scores: list[int]):
        self.stg = scores[0]
        self.dex = scores[1]
        self.con = scores[2]
        self.inte = scores[3]
        self.wis = scores[4]
        self.cha = scores[5]

class PointBuy():
    def __init__(self):
        self.pb_scores = None
    def set_pb_scores(self, pb_scores: Scores):
        self.pb_scores = pb_scores
    def get_pb_scores(self):
        return self.pb_scores

class Character():
    def __init__(self):
        self.final_scores = None
        self.walking_speed = None
    def set_final_scores(self, final_scores: Scores):
        self.final_scores = final_scores
    def set_walking_speed(self, speed: int):
        self.walking_speed = speed
    

class Ability():
    def __init__(self, ID: int, description: str, priority: int, points: int):
        self.ID = ID
        self.description = description
        self.priority = priority
        self.points = points
        self.modifier = 0
        self.buy_penalty = 1
    def get_ID(self):
        return self.ID
    def get_desc(self):
        return self.description
    def get_priority(self):
        return self.priority
    def get_points(self):
        return self.points
    def get_buy_penalty(self):
        return self.buy_penalty
    def set_priority(self, priority):
        self.priority = priority
    def set_points(self, points):
        self.points = points
    def set_modifier(self, modifier):
        self.modifier = modifier
    def add_point(self):
        self.points = self.points + 1
    def update_buy_penalty(self):
        if self.points >= 13:
            self.buy_penalty = 2


def total_points(abilities: list[Ability]) -> int:
    total = 0
    for ability in abilities:
        curr_points = ability.get_points()
        total += curr_points
    return total

def set_modifiers(abilities: list[Ability]) -> list[Ability]:
    modifier = 0
    for ability in abilities:
        points = ability.get_points()
        if points == 8 or points == 9:
            modifier = -1
        elif points == 10 or points == 11:
            modifier = 0
        elif points == 12 or points == 13:
            modifier = 1
        else:
            modifier = 2
        ability.set_modifier(modifier)
        
    return abilities

myPointBuy = PointBuy()

myCharacter = {
    "race": "",
    "subrace": "",
    "abilities": [],
    "speed": 0,
    "vision": 0,
    "HP": 0,
    "tools": [],
    "spells": [],
    "skills": [],
    "languages": [],
    "combat": [],
    "misc": [],
}

class CharacterBasics(BaseModel):
    Race: str = Field("low", description="Race - must be one of: Dwarf, Elf, Halfling, Human, Gnome, Half-Elf, Half-Orc or Tiefling.")
    Class: str = Field("low", description="Class - must be one of: Barbarian, Bard, Cleric, Druid, Fighter, Monk, Paladin, Ranger, Rogue, Sorcerer, Warlock or Wizard.")

@tool
def point_buy_calculator(stg: str = "default", dex: str = "default", con: str = "default", inte: str = "default", wis: str = "default", cha: str = "default", distribution: str = "default") -> list[int]:
    """Choose descriptions for these abilities: strength, dexterity, constitution, intelligence, wisdom and charisma. Also define how the ability points should be spread, either 'balanced' or 'focused'.

    Args:
        stg: the character's strength rating; either 'high', 'medium', or 'low'
        dex: the character's dexterity rating; either 'high', 'medium', or 'low'
        con: the character's constitution rating; either 'high', 'medium', or 'low'
        int: the character's intelligence rating; either 'high', 'medium', or 'low'
        wis: the character's wisdom rating; either 'high', 'medium', or 'low'
        cha: the character's charisma rating; either 'high', 'medium', or 'low'
        distribution: how the character's ability points should be distributed; either 'balanced' or 'focused'
    """

    print("This is the weight: ", distribution)
    abilities_str = [stg, dex, con, inte, wis, cha]
    print("These are the ability inputs: ", abilities_str)

    strength = Ability(1, stg, 0, 8)
    dexterity = Ability(2, dex, 0, 8)
    constitution = Ability(3, con, 0, 8)
    intelligence = Ability(4, inte, 0, 8)
    wisdom = Ability(5, wis, 0, 8)
    charisma = Ability(6, cha, 0, 8)

    abilities = [strength, dexterity, constitution, intelligence, wisdom, charisma]

    ability_count = 0

    for ability in abilities:
        if "high" in ability.get_desc():
            ability.set_priority(ability_count + 1) 
            ability_count += 1

    for ability in abilities:
        if "medium" in ability.get_desc():
            ability.set_priority(ability_count + 1) 
            ability_count += 1

    for ability in abilities:
        if "high" not in ability.get_desc() and "medium" not in ability.get_desc():
            ability.set_priority(ability_count + 1) 
            ability_count += 1

    # order the abilities array by priority, then increment the abilities one by one (if balanced)
    # and check at each increment if we exceed the total point allowance.
    # At the end, we will iterate over the abilities and translate the points to scores (+1, -1, etc.)

    if "balanced" not in distribution and "focused" not in distribution:
        print("Error: distribution not balanced or focused")

    sorted_abilities = sorted(abilities, key=lambda this_ability: this_ability.get_priority())

    point_allowance = 27

    if "balanced" in distribution:
        while point_allowance > 0:
            for ability in sorted_abilities:
                if point_allowance <= 0:
                    break
                ability.add_point()
                penalty = ability.get_buy_penalty()
                point_allowance = point_allowance - penalty
                ability.update_buy_penalty()
    else: #focused distribution
        for ability in sorted_abilities:
            while ability.get_points() < 15 and point_allowance > 0:
                ability.add_point()
                penalty = ability.get_buy_penalty()
                point_allowance = point_allowance - penalty
                ability.update_buy_penalty()
            if point_allowance <= 0:
                break

    for ability in sorted_abilities:
        this_point = ability.get_points()
        print(ability.ID, " has this many points: ", this_point)

    sorted_abilities_by_ID = sorted(sorted_abilities, key=lambda this_ability: this_ability.get_ID())

    final_scores = []
    for i in range(6):
        final_scores.append(sorted_abilities_by_ID[i].get_points())

    print("Final scores: ",final_scores)
    
    pb_scores = Scores(final_scores)
    myPointBuy.set_pb_scores(pb_scores)

    return final_scores

def generateExample(quantity: int):
    example = "option1"
    for i in range(2, quantity+1):
        example += f"#option{i}"
    return example

def choose(topic: str, options: list[str], quantity: int=1):
    example = generateExample(quantity)
    if quantity == 1:
        llm_decision = llm.invoke(f"I am trying to build this character: {USER_QUERY}. I get to pick one extra {topic}. Reply with one option from this list: {options}. Do not respond with any other text.")
    else:
        llm_decision = llm.invoke(f"I am trying to build this character: {USER_QUERY}. I get to pick {quantity} extra {topic}. Reply with {quantity} options from this list: {options}. Return each answer separated by hashtags. Do not add any other text. Do not start with a hashtag, only use them between options. Your response should be in this exact format: '{example}'")
        
    print(f"Here is what the llm decided for you: {llm_decision.content}. Here was the topic: {topic} and the options presented: {options}")
    return llm_decision.content

@tool
def race_calculator(race: str = "default", subrace: str = "default") -> list[int]:
    """Choose a race and subrace

    Args:
        race: the character's race; either Dwarf, Elf, Halfling, Human, Gnome, Half-Elf, Half-Orc or Tiefling
        subrace: the character's subrace if applicable. Only Dwarf, Elf, Halfling and Gnome can have a subrace. Dwarf can be Hill or Mountain, Elf and be High or Wood, Halfling can be Lightfoot or Stout and Gnome can be Forest or Rock.
    """
    
    strength = dexterity = constitution = intelligence = wisdom = charisma = speed = vision = HP = 0
    tools = spells = skills = languages = combat = misc = []

    if "Dwarf" in race:
        constitution += 2
        speed = 25
        vision = 60
        combat.extend(["battleaxe", "handaxe", "light hammer", "warhammer"])
        tool_decision = choose("tool proficiency", ["smith", "brewer", "mason"])
        tools.append(tool_decision)
        languages = ["Common", "Dwarvish"]
        if "Hill" in subrace:
            wisdom += 1
            HP += 1
        else: #Mountain Dwarf
            strength += 2
            combat.extend(["light armor", "medium armor"])
    elif "Elf" in race: 
        dexterity += 2
        speed = 30
        vision = 60
        combat.extend(["longsword", "shortsword", "shortbow", "longbow"])
        skills.append("Perception")
        languages = ["Common", "Elvish"]
        if "High" in subrace:
            intelligence += 1
            language_decision = choose("languge", ["Dwarvish", "Halfling", "Gnomish", "Giant", "Goblin", "Orc"])
            languages.append(language_decision)
            spell_decision = choose("spell", get_asset("wizard_cantrips"))
            spells.append(spell_decision)
        else: #Wood Elf
            wisdom += 1
            speed = 35
    elif "Halfling" in race:
        dexterity += 2
        speed = 25
        languages = ["Common", "Halfling"]
        misc.append("When you roll a 1 on the d20 for an attack roll, ability check, or saving throw, you can reroll the die and must use the new roll.")
        misc.append("You have advantage on saving throws against being frightened.")
        misc.append("You can move through the space of any creature that is of a size larger than yours.")
        if "Lightfoot" in subrace:
            charisma += 1
            misc.append("You can attempt to hide even when you are obscured only by a creature that is at least one size larger than you.")
        else: #Stout Halfling
            constitution += 1
            misc.append("You have advantage on saving throws against poison, and you have resistance against poison damage.")
    elif "Human" in race:    
        strength += 1
        dexterity += 1
        constitution += 1
        intelligence += 1
        wisdom += 1
        charisma += 1
        speed = 30
        languages = ["Common"]
        language_decision = choose("languge", ["Dwarvish", "Halfling", "Gnomish", "Giant", "Goblin", "Orc"])
        languages.append(language_decision)
    elif "Gnome" in race:   
        intelligence += 2
        speed = 25
        vision = 60
        languages.append(["Common", "Gnomish"])
        misc.append("You have advantage on all Intelligence, Wisdom, and Charisma saving throws against magic.")
        if "Rock" in subrace:
            constitution += 1
            misc.append("Whenever you make an Intelligence (History) check related to magic items, alchemical objects, or technological devices, you can add twice your proficiency bonus, instead of any proficiency bonus you normally apply.")
            misc.append("You have proficiency with artisan's tools (tinker's tools).")
        else: #Forest gnome
            dexterity += 1
            misc.append("You know the minor illusion cantrip. Intelligence is your spellcasting ability for it.")
            misc.append("Through sounds and gestures, you can communicate simple ideas with Small or smaller beasts.")
    elif "Half-Elf" in race:
        charisma += 2
        dexterity += 1
        wisdom += 1
        speed = 30
        vision = 60
        misc.append("You have advantage on saving throws against being charmed, and magic can't put you to sleep.")
        languages = ["Common", "Elvish"]
        language_decision = choose("languge", ["Dwarvish", "Halfling", "Gnomish", "Giant", "Goblin", "Orc"])
        languages.append(language_decision)
        skill_decision = choose("skills", get_asset("skills"), 2)
        skills.append(skill_decision)
    elif "Half-Orc" in race:     
        strength += 2
        constitution += 1
        speed = 30
        vision = 60
        languages = ["Common", "Orc"]
        skills.append("Intimidation")
        misc.append("Once per long rest, at 0 hit points but not dead, you can drop to 1 hit point instead.")
        misc.append("When you score a critical hit with a melee weapon attack, you can roll one of the weapon's damage dice one additional time and add it to the extra damage of the critical hit.")
    elif "Tiefling" in race:
        intelligence += 1
        charisma += 2
        speed = 30
        vision = 60
        misc.append("You have resistance to fire damage.")
        spells.append("thaumaturgy")
        languages =["Common", "Infernal"]
    else:
        print("ERROR: Identified a race outside of the options.")

    print("\nRACE: ", race, "\nSUBRACE:", subrace, "\n")

    final_scores = [strength, dexterity, constitution, intelligence, wisdom, charisma]
    print("Here are the scores: ", final_scores)
    
    myRaceDict = {
        "race": race,
        "subrace": subrace,
        "abilities": final_scores,
        "speed": speed,
        "vision": vision,
        "HP": HP,
        "tools": tools,
        "spells": spells,
        "skills": skills,
        "languages": languages,
        "combat": combat,
        "misc": misc,
    }

    myCharacter["abilities"] = final_scores

    print("Here is the full race dictionary object: ", myRaceDict)

    return final_scores

@tool
def class_calculator(dnd_class: str = "default") -> list[int]:
    """Choose my character's class

    Args:
        class: the character's class; either Barbarian, Bard, Cleric, Druid, Fighter, Monk, Paladin, Ranger, Rogue, Sorcerer, Warlock, or Wizard.
    """

    HP = proficiency_bonus = spellslots = 0
    hit_dice = ""
    abilities = myCharacter["abilities"]
    armour = weapons = tools = saving_throws = tools = features = skills = equipment = cantrips = spells = languages = []

    if "barbarian" in dnd_class:
        HP = 12 + abilities[2] #12 + constitution mod
        hit_dice = "1d12"
        armour = ["light armor", "medium armor", "shields"]
        weapons = ["simple weapons", "martial weapons"]
        saving_throws = ["strength", "constitution"]
        skills_decision = choose("skills", ["Animal Handling", "Athletics", "Intimidation", "Nature", "Perception", "Survival"], 2)
        skills.append(skills_decision)
        equipment.extend("greataxe", "two handaxes", "explorer’s pack", "four javelins")
        features.extend("Rage", "Unarmored Defense")
        proficiency_bonus = 2
    elif "bard" in dnd_class:
        HP = 8 + abilities[2]
        hit_dice = "1d8"
        armour = ["light armor"]
        weapons = ["Simple weapons", "hand crossbows", "longswords", "rapiers", "shortswords"]
        saving_throws = ["dexterity", "charisma"]
        skills_decision = choose("skills", get_asset("skills"), 3)
        skills.append(skills_decision)
        features.extend("Spellcasting", "Bardic Inspiration")
        pack_decision = choose("pack", ["entertainer's pack", "diplomat's pack"])
        equipment.append(pack_decision)
        instrument_decision = choose("instruments", get_asset("instruments"), 4)
        equipment.extend(instrument_decision)
        equipment.extend("rapier", "leather armour", "dagger")
        proficiency_bonus = 2
        cantrip_decision = choose("bard cantrips", get_asset("bard_cantrips"), 2)
        cantrips.extend(cantrip_decision)
        spell_decision = choose("bard spells", get_asset("bard_spells"), 4)
        spells.extend(spell_decision)
        spellslots = 2
    elif "cleric" in dnd_class:
        HP = 8 + abilities[2]
        hit_dice = "1d8"
        armour = ["light armor", "medium armor", "shields"]
        weapons = ["Simple weapons"]
        saving_throws = ["wisdom", "charisma"]
        skills_decision = choose("skills", ["History", "Insight", "Medicine", "Persuasion", "Religion"], 2)
        skills.append(skills_decision)
        features.extend("Spellcasting", "Divine Domain")
        pack_decision = choose("pack", ["priest's pack", "explorer's pack"])
        equipment.append(pack_decision)
        equipment.extend("mace", "scale mail", "light crossbow and 20 bolts", "shield")
        holy_item_decision = choose("holy item", ["prayer beads", "censer", "chalice", "bone", "cloth", "sacred text", "holy water", "sacred oil", "stone from holy site"])
        equipment.extend(holy_item_decision)
        proficiency_bonus = 2
        cantrip_decision = choose("cleric cantrips", get_asset("cleric_cantrips"), 3)
        cantrips.extend(cantrip_decision)
        # Knows all spells
        spellslots = 2
    elif "druid" in dnd_class:
        HP = 8 + abilities[2]
        hit_dice = "1d8"
        armour = ["light armor", "medium armor", "shields"]
        weapons = ["Clubs", "daggers", "darts", "javelins", "maces", "quarterstaffs", "scimitars", "sickles", "slings", "spears"]
        saving_throws = ["wisdom", "intelligence"]
        skills_decision = choose("skills", ["Arcana", "Animal Handling", "Insight", "Medicine", "Nature", "Perception", "Religion", "Survival"], 2)
        skills.append(skills_decision)
        features.extend("Spellcasting", "Druidic")
        equipment.extend("explorer's pack", "herbalism kit", "wooden shield", "scimitar", "leather armor")
        equipment.extend("mace", "scale mail", "light crossbow and 20 bolts", "shield")
        proficiency_bonus = 2
        cantrip_decision = choose("cleric cantrips", get_asset("cleric_cantrips"), 2)
        cantrips.extend(cantrip_decision)
        languages.append("druidic")
        # Knows all spells
        spellslots = 2
        


        
    print("Here is the class: ", dnd_class)

    return [0]
    

tools = [point_buy_calculator, race_calculator, class_calculator]
tools_by_name = {tool.name: tool for tool in tools}
llm_with_tools = llm.bind_tools(tools)

# Nodes
def llm_call(state: MessagesState):
    """LLM decides whether to call a tool or not"""

    return {
        "messages": [
            llm_with_tools.invoke(
                [
                    SystemMessage(
                        content=(
                            "You are a helpful assistant that must ALWAYS call exactly three tools, "
                            "in this order: "
                            "1) point_buy_calculator "
                            "2) race_calculator "
                            "3) class_calculator"
                            "Do not provide a final answer until ALL THREE tool calls have been made. "
                            "If the user asks for a character build, always plan on calling all tools."
                        )
                    )
                ]
                + state["messages"]
            )
        ]
    }


def tool_node(state: dict):
    """Performs the tool call"""

    result = []
    for tool_call in state["messages"][-1].tool_calls:
        tool = tools_by_name[tool_call["name"]]
        observation = tool.invoke(tool_call["args"])
        result.append(ToolMessage(content=observation, tool_call_id=tool_call["id"]))
    return {"messages": result} #Stop here and add these two results to global class


# Conditional edge function to route to the tool node or end based upon whether the LLM made a tool call
def should_continue(state: MessagesState):
    """Decide if we should continue the loop or stop based upon whether the LLM made a tool call"""

    messages = state["messages"]
    last_message = messages[-1]

    # If the LLM makes a tool call, then perform an action
    if last_message.tool_calls:
        return "tool_node"

    # Otherwise, we stop (reply to the user)
    return END


# Build workflow
agent_builder = StateGraph(MessagesState)

# Add nodes
agent_builder.add_node("llm_call", llm_call)
agent_builder.add_node("tool_node", tool_node)

# Add edges to connect nodes
agent_builder.add_edge(START, "llm_call")
agent_builder.add_conditional_edges(
    "llm_call",
    should_continue,
    ["tool_node", END]
)
agent_builder.add_edge("tool_node", "llm_call")

# Compile the agent
agent = agent_builder.compile()

# Invoke
messages = [HumanMessage(content=USER_QUERY)]
messages = agent.invoke({"messages": messages})
# for m in messages["messages"]:
#     m.pretty_print()


#Website: https://5e.tools/races.html#gnome%20(forest)_phb