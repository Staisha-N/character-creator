from langchain_ollama import ChatOllama
from pydantic import BaseModel, Field

llm = ChatOllama(model="llama3.2")

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
output = structured_llm.invoke("Consider a character that excels at physical combat. Rate the importance its six abilities (strength, dexterity, constitution, wisdom, intelligence and charisma) as high, medium or low.")

print(output)