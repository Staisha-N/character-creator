from langchain_ollama import ChatOllama
from pydantic import BaseModel, Field
from langchain.tools import tool
from typing_extensions import TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.graph import MessagesState
from langchain.messages import SystemMessage, HumanMessage, ToolMessage

llm = ChatOllama(model="llama3.2")

class State(TypedDict):
    strength: int
    dexterity: int
    constitution: int
    intelligence: int
    wisdom: int
    charisma: int

class AbilityScores(BaseModel):
    strength: str = Field("low", description="Strength score")
    dexterity: str = Field("low", description="Dexterity score")
    constitution: str = Field("low", description="Constitution score")
    intelligence: str = Field("low", description="Intelligence score")
    wisdom: str = Field("low", description="Wisdom score")
    charisma: str = Field("low", description="Charisma score")

# Augment the LLM with schema for structured output
structured_llm = llm.with_structured_output(AbilityScores)

# Invoke the augmented LLM
output = structured_llm.invoke("Consider a Dungeons and Dragons character that excels at physical combat. Rate the importance its six abilities (strength, dexterity, constitution, wisdom, intelligence and charisma) as 'high', 'medium' or 'low'.")

print(output)

@tool
def quantitative_scores(stg: str, dex: str, con: str, inte: str, wis: str, cha: str) -> list[int]:
    """Create quantitative scores for these abilities: stg, dex, con, int, wis and cha.

    Args:
        stg: strength
        dex: dexterity
        con: constitution
        int: intelligence
        wis: wisdom
        cha: charisma
    """
    tool_result = [1,2,3,4,5,6]
    print("Here are the results of the tool being called: ", tool_result)
    return tool_result

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
    result = []
    for tool_call in state["messages"][-1].tool_calls:
        tool = tools_by_name[tool_call["name"]]
        observation = tool.invoke(tool_call["args"])
        result.append(ToolMessage(content=observation, tool_call_id=tool_call["id"]))
    return {"messages": result}

agent_builder = StateGraph(MessagesState)

agent_builder.add_node("llm_call", llm_call)
agent_builder.add_node("tool_node", tool_node)

agent_builder.add_edge(START, "llm_call")
agent_builder.add_edge("llm_call", "tool_node")
agent_builder.add_edge("tool_node", END)

agent = agent_builder.compile()

messages = [HumanMessage(content="strength='low' dexterity='high' constitution='high' intelligence='low' wisdom='medium' charisma='medium'")]
messages = agent.invoke({"messages": messages})
for m in messages["messages"]:
    m.pretty_print()
