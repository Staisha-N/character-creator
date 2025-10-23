from langchain_ollama import ChatOllama
from pydantic import BaseModel, Field
from typing_extensions import TypedDict
from langchain.tools import tool

llm = ChatOllama(model="llama3.1")

class AbilityScores(BaseModel):
    strength: int = Field(None, description="Strength score")
    dexterity: int = Field(None, description="Dexterity score")
    constitution: int = Field(None, description="Constitution score")
    intelligence: int = Field(None, description="Intelligence score")
    wisdom: int = Field(None, description="Wisdom score")
    charisma: int = Field(None, description="Charisma score")

@tool
def rate(stg: str, dex: str, con: str, inte: str, wis: str, cha: str) -> list[str]:
    """Rate the importance of stg, dex, con, int, wis and cha.

    Args:
        stg: strength
        dex: dexterity
        con: constitution
        int: intelligence
        wis: wisdom
        cha: charisma
    """
    decision = [stg, dex, con, inte, wis, cha]
    print(decision)
    return decision

tools = [rate]
llm_with_tools = llm.bind_tools(tools)

# Invoke the augmented LLM
output = llm_with_tools.invoke("Consider a character that excels at combat. Rate the importance its six abilities (strength, dexterity, constitution, wisdom, intelligence and charisma) as high, medium or low.")
