from langchain_ollama import ChatOllama
from pydantic import BaseModel, Field
from langchain.tools import tool
from typing_extensions import TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.graph import MessagesState
from langchain.messages import SystemMessage, HumanMessage, ToolMessage

llm = ChatOllama(model="llama3.2")

# class State(TypedDict):
#     strength: int
#     dexterity: int
#     constitution: int
#     intelligence: int
#     wisdom: int
#     charisma: int

# class AbilityScores(BaseModel):
#     strength: str = Field("low", description="Strength score")
#     dexterity: str = Field("low", description="Dexterity score")
#     constitution: str = Field("low", description="Constitution score")
#     intelligence: str = Field("low", description="Intelligence score")
#     wisdom: str = Field("low", description="Wisdom score")
#     charisma: str = Field("low", description="Charisma score")

# ability_llm = llm.with_structured_output(AbilityScores)
# ability_decision = ability_llm.invoke("Consider a Dungeons and Dragons character that excels at physical combat. Rate the importance its six abilities (strength, dexterity, constitution, wisdom, intelligence and charisma) as 'high', 'medium' or 'low'.")

# print(ability_decision)

class Ability():
    def __init__(self, description, priority, points):
        self.description = description
        self.priority = priority
        self.points = points
    def get_desc(self):
        return self.description
    def set_points(self, points):
        self.points = points
    def set_priority(self, priority):
        self.priority = priority


class CharacterBasics(BaseModel):
    Race: str = Field("low", description="Race - must be one of: Dwarf, Elf, Halfling, Human, Dragonborn, Gnome, Half-Elf, Half-Orc or Tiefling.")
    Class: str = Field("low", description="Class - must be one of: Barbarian, Bard, Cleric, Druid, Fighter, Monk, Paladin, Ranger, Rogue, Sorcerer, Warlock or Wizard.")

@tool
def quantitative_scores(stg: str, dex: str, con: str, inte: str, wis: str, cha: str, distribution: str) -> list[int]:
    """Create quantitative scores for these abilities: strength, dexterity, constitution, intelligence, wisdom and charisma. Also define how the ability points should be spread, evenly or unevenly.

    Args:
        stg: the character's strength rating; one of 'high', 'medium', or 'low'
        dex: the character's dexterity rating; one of 'high', 'medium', or 'low'
        con: the character's constitution rating; one of 'high', 'medium', or 'low'
        int: the character's intelligence rating; one of 'high', 'medium', or 'low'
        wis: the character's wisdom rating; one of 'high', 'medium', or 'low'
        cha: the character's charisma rating; one of 'high', 'medium', or 'low'
        distribution: how the character's ability points should be distributed; either 'balanced' or 'focused'
    """

    print("This is the weight: ", distribution)
    abilities_str = [stg, dex, con, inte, wis, cha]
    print("These are the ability inputs: ", abilities_str)
    abilities_int = [0, 0, 0, 0, 0, 0]

    strength = Ability(str, 0, 8)
    dexterity = Ability(dex, 0, 8)
    constitution = Ability(con, 0, 8)
    intelligence = Ability(inte, 0, 8)
    wisdom = Ability(wis, 0, 8)
    charisma = Ability(cha, 0, 8)

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

    # For unbalanced, or 'focused' we start by min-maxing the "high" level skills, then move to medium, checking 
    #the threshold at each time.

    # Should result in somthing like tool_result, where the numbers appear
    # only once, but can be in any order; showing priority of skills.

    print("Here are the results of the tool being called: ", abilities_int)
    return abilities_int

# Augment the LLM with tools
tools = [quantitative_scores]
llm_with_tools = llm.bind_tools([quantitative_scores])
tools_by_name = {tool.name: tool for tool in tools}



def llm_call(state: MessagesState):
    """LLM decides whether to call a tool or not"""

    return {
        "messages": [
            llm_with_tools.invoke(
                [
                    SystemMessage(
                        content="You are a helpful assistant. Your input is a qualitative description of a characters' abilities and you must call a tool to get corresponding quantitative ability scores."
                    )
                ]
                + state["messages"]
            )
        ]
    }


def tool_node(state: dict):
    """Performs the tool call"""

    tool_calls = state["messages"][-1].tool_calls
    if not tool_calls:
        observation = "Err: no tool calls made"
        print(observation)
        result = [ToolMessage(content=observation, tool_call_id=tool_call["id"])]
        return {"messages": result}
    else:
        tool_call = tool_calls[0]    
        tool = tools_by_name[tool_call["name"]]
        observation = tool.invoke(tool_call["args"])
        result = [ToolMessage(content=observation, tool_call_id=tool_call["id"])]
        return {"messages": result}
    
def register_basics(state: dict):
    basics_llm = llm.with_structured_output(CharacterBasics)
    basics_decision = basics_llm.invoke("Consider a strong Dungeons and Dragons character that excels at physical combat. Choose its race and class.")
    print("Here are the basics: ", basics_decision)

agent_builder = StateGraph(MessagesState)

agent_builder.add_node("llm_call", llm_call)
agent_builder.add_node("tool_node", tool_node)
agent_builder.add_node("register_basics", register_basics)

agent_builder.add_edge(START, "llm_call")
#Add parallel execution for character basics (i.e. race, class)
agent_builder.add_edge(START, "register_basics")
agent_builder.add_edge("llm_call", "tool_node")
agent_builder.add_edge("tool_node", END)
agent_builder.add_edge("register_basics", END)

agent = agent_builder.compile()

messages = [HumanMessage(content="strength='low' dexterity='high' constitution='high' intelligence='low' wisdom='medium' charisma='medium'")]
messages = agent.invoke({"messages": messages})
for m in messages["messages"]:
    m.pretty_print()
