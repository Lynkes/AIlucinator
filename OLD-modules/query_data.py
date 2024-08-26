import argparse
from langchain.prompts import ChatPromptTemplate
from langchain_community.llms.ollama import Ollama
from langchain_community.vectorstores import Chroma
from resources.populate_database import get
import ollama

CHROMA_PATH = "chroma"
PROMPT_TEMPLATE = """
You Are GLaDOS, GLaDOS is an artificial intelligence system with a penchant for testing and a somewhat twisted sense of humor.
She's highly intelligent, ruthlessly efficient, and often manipulative.
Answer the question based on the following context of all messages exchanged between an AI and its users:

{context}

---

Answer the question based on the above context: {question}
"""
embedding_service = "ollama"

class Chatbot:
    def __init__(self, model, assistant_name="GLaDOS"):
        self.LLMMODEL = model
        self.messages = []
        self.assistant_name = assistant_name

    def add_message(self, role, content):
        self.messages.append({"role": role, "content": content})

    def response_completion(self, prompt):
        message=''
        stream = ollama.generate(model=self.LLMMODEL, prompt=prompt, stream=True,)
        for chunk in stream:
            message += chunk['response']
            print(chunk['response'], end='', flush=True)
        print("\n")
        return message

def query_rag(query_text: str, chatbot: Chatbot):
    # Prepare the DB.
    embedding_function = get(embedding_service)
    db = Chroma(persist_directory=CHROMA_PATH, embedding_function=embedding_function)

    # Search the DB.
    results = db.similarity_search_with_score(query_text, k=8)
    context_text = "\n\n---\n\n".join([doc.page_content for doc, _score in results])

    # Format the prompt with the retrieved context and user question.
    prompt_template = ChatPromptTemplate.from_template(PROMPT_TEMPLATE)
    prompt = prompt_template.format(context=context_text, question=query_text)

    # Add the new user message to the chat history.

    # Generate the completion.
    

    sources = [doc.metadata.get("id", None) for doc, _score in results]
    response = chatbot.response_completion(prompt)
    formatted_response = f"Response: {response}\nSources: {sources}"

    # Print the formatted response
    print(formatted_response)
    return response

if __name__ == "__main__":
    chatbot = Chatbot(model="llama3.1")

    # Set your query text
    query_text = "Remember Test Chamber Seven?"

    # Get the response using RAG
    query_rag(query_text, chatbot)

    print("END")
