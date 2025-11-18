from langchain_ollama import ChatOllama
from pydantic import BaseModel, Field
from langchain.tools import tool
from typing_extensions import TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.graph import MessagesState
from langchain.messages import SystemMessage, HumanMessage, ToolMessage
from langgraph.prebuilt import ToolNode

llm = ChatOllama(model="llama3.2")

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

class Character():
    def __init__(self):
        self.pb_scores = None
        self.race_scores = None
    def set_pb_scores(self, pb_scores: Scores):
        self.pb_scores = pb_scores
    def set_race_scores(self, race_scores: Scores):
        self.race_scores = race_scores
    

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

myCharacter = Character()

class CharacterBasics(BaseModel):
    Race: str = Field("low", description="Race - must be one of: Dwarf, Elf, Halfling, Human, Dragonborn, Gnome, Half-Elf, Half-Orc or Tiefling.")
    Class: str = Field("low", description="Class - must be one of: Barbarian, Bard, Cleric, Druid, Fighter, Monk, Paladin, Ranger, Rogue, Sorcerer, Warlock or Wizard.")

@tool
def choose_modifiers(stg: str = "default", dex: str = "default", con: str = "default", inte: str = "default", wis: str = "default", cha: str = "default", distribution: str = "default") -> list[int]:
    """Choose modifiers for these abilities: strength, dexterity, constitution, intelligence, wisdom and charisma. Also define how the ability points should be spread, either 'balanced' or 'focused'.

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

    temp_index = 1
    for ability in sorted_abilities:
        print("My ", ability.ID, " is number ", temp_index)
        temp_index += 1

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

    for ability in sorted_abilities_by_ID:
        print("ID=", ability.ID)

    final_scores = []
    for i in range(6):
        final_scores.append(sorted_abilities_by_ID[i].get_points())

    print("Final scores: ",final_scores)
    
    pb_scores = Scores(final_scores)
    myCharacter.set_pb_scores(pb_scores)


    return [0,0,0,0,0,0]


llm_with_tools = llm.bind_tools([choose_modifiers])

def llm_call(state: MessagesState):
    """Calls tool"""

    return {"messages": [llm_with_tools.invoke(state["messages"])]}
    
# def register_basics(state: dict):
#     basics_llm = llm.with_structured_output(CharacterBasics)
#     basics_decision = basics_llm.invoke("Consider a strong Dungeons and Dragons character that excels at physical combat. Choose its race and class.")
#     print("Here are the basics: ", basics_decision)

tool_node = ToolNode([choose_modifiers])

agent_builder = StateGraph(MessagesState)

agent_builder.add_node("llm_call", llm_call)
agent_builder.add_node("tools", tool_node)
#agent_builder.add_node("register_basics", register_basics)

agent_builder.add_edge(START, "llm_call")
#Add parallel execution for character basics (i.e. race, class)
#agent_builder.add_edge(START, "register_basics")
agent_builder.add_edge("llm_call", "tools")
agent_builder.add_edge("tools", END)
#agent_builder.add_edge("register_basics", END)

agent = agent_builder.compile()

result = agent.invoke({"messages": [{"role": "user", "content": "Consider a strong Dungeons and Dragons character that excels at physical combat. Call the tool to decider its modifiers."}]})
print(result["messages"][-1].content)
