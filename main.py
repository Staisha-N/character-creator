from langchain_ollama import ChatOllama
from pydantic import BaseModel, Field
from typing_extensions import TypedDict

llm = ChatOllama(model="gpt-oss:20b")

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
output = structured_llm.invoke("I want to build a character that wins all combats. Assign a level of importance to each of their abilities. 1 is most important and 6 is least. For example: strength=4, dexterity=3, consitution=2, intelligence=6, wisdom=1, charisma=5.")

print(output)