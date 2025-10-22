from langchain_ollama import ChatOllama
from pydantic import BaseModel, Field

llm = ChatOllama(model="gpt-oss:20b")

response = llm.invoke("What is the capital of France?")
print(response.content)

class SearchQuery(BaseModel):
    search_query: str = Field(None, description="Query that is optimized web search.")
    justification: str = Field(
        None, description="Why this query is relevant to the user's request."
    )


# Augment the LLM with schema for structured output
structured_llm = llm.with_structured_output(SearchQuery)

# Invoke the augmented LLM
output = structured_llm.invoke("How does Calcium CT score relate to high cholesterol?")

print(output)