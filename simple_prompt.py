from langchain_ollama import ChatOllama
from pydantic import BaseModel, Field

llm = ChatOllama(model="llama3.2")

class AbilityScores(BaseModel):
    strength: str = Field(None, description="Strength score")
    dexterity: str = Field(None, description="Dexterity score")
    constitution: str = Field(None, description="Constitution score")
    intelligence: str = Field(None, description="Intelligence score")
    wisdom: str = Field(None, description="Wisdom score")
    charisma: str = Field(None, description="Charisma score")

# Augment the LLM with schema for structured output
structured_llm = llm.with_structured_output(AbilityScores)

# Invoke the augmented LLM
output = structured_llm.invoke("Consider a character that excels at physical combat. Rate the importance its six abilities (strength, dexterity, constitution, wisdom, intelligence and charisma) as high, medium or low.")

print(output)