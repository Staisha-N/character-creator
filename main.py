from langchain_community.chat_models import ChatOllama

llm = ChatOllama(model="llama3")

response = llm.invoke("What is the capital of France?")
print(response.content)

