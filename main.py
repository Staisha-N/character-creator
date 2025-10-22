from langchain_ollama import ChatOllama
from pydantic import BaseModel, Field
from typing_extensions import TypedDict

llm = ChatOllama(model="gpt-oss:20b")

# Graph state
class State(TypedDict):
    strength: int
    dexterity: int
    constitution: int
    intelligence: int
    wisdom: int
    charisma: int

class AbilityScores(BaseModel):
    strength: int = Field(None, description="Strength score")
    dexterity: int = Field(None, description="Dexterity score")
    constitution: int = Field(None, description="Constitution score")
    intelligence: int = Field(None, description="Intelligence score")
    wisdom: int = Field(None, description="Wisdom score")
    charisma: int = Field(None, description="Charisma score")

# Augment the LLM with schema for structured output
structured_llm = llm.with_structured_output(AbilityScores)

# Invoke the augmented LLM
output = structured_llm.invoke("A character that wins all combats: rank their abilities from most to least important using numbers 1 to 6.")

print(output)