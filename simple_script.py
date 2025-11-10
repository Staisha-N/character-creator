def simple_script(user_question):
    from langchain_ollama import OllamaLLM
    llm = OllamaLLM(model="llama3.2")
    
    answer = llm.invoke("Please answer this question: ", user_question)
    return answer