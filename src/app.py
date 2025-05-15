# Adaptive LLM-Based Chatbot with Automatic Persona Detection and LangChain Memory

from fastapi import FastAPI
from pydantic import BaseModel
from langchain.llms import Ollama
from langchain_community.llms import Ollama
from langchain.prompts import PromptTemplate
from langchain.memory import ConversationBufferMemory
from sentence_transformers import SentenceTransformer, util
import uvicorn
import json
import time
import os

# Load persona examples for similarity detection
persona_examples = {
    "oversharer": "I had such a long day, let me tell you every detail from morning to night...",
    "reserved": "It was fine.",
    "verbose": "Well, it's kind of complicated. First, I was thinking about the topic and then I realized..."
}

# Load embedding model
embedding_model = SentenceTransformer("all-MiniLM-L6-v2")
example_embeddings = {
    key: embedding_model.encode(value, convert_to_tensor=True)
    for key, value in persona_examples.items()
}

# LangChain memory (stores entire chat in plain text)
memory = ConversationBufferMemory(return_messages=True)

# FastAPI app
app = FastAPI()

class Message(BaseModel):
    user_input: str

# Load LLM
llm = Ollama(model="llama3.2:1b")  # Requires `ollama run gemma3:1b` in background

# Auto Persona Detection
def detect_persona(user_input: str) -> str:
    input_embedding = embedding_model.encode(user_input, convert_to_tensor=True)
    similarities = {
        persona: util.pytorch_cos_sim(input_embedding, emb).item()
        for persona, emb in example_embeddings.items()
    }
    return max(similarities, key=similarities.get)

# Prompt templates
prompt_templates = {
    "oversharer": "You are chatting with someone who shares too much personal information. Gently guide them back to the topic.",
    "reserved": "You are chatting with someone very reserved. Encourage them to open up using friendly questions.",
    "verbose": "You are chatting with someone who talks a lot but without reflection. Summarize and clarify their points.",
    "Short an concise":"Provide the answer as well as short.Make sure answer is short concise and complete the meaning"
}

@app.post("/chat")
def chat(msg: Message):
    detected_persona = detect_persona(msg.user_input)
    system_prompt = prompt_templates[detected_persona]

    # Add user's message to memory
    memory.chat_memory.add_user_message(msg.user_input)

    # Format past history
    history_text = "\n".join([
        f"User: {m.content}" if m.type == "human" else f"AI: {m.content}"
        for m in memory.chat_memory.messages
    ])

    # Construct full prompt with memory + current input
    full_prompt = PromptTemplate.from_template(
        f"{system_prompt}\n\nConversation so far:\n{history_text}\n\nUser: {msg.user_input}\nAI:"
    )

    # Get response from model
    response = llm(full_prompt.format())

    # Add model response to memory
    memory.chat_memory.add_ai_message(response)

    # Log response
    log_entry = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "user_input": msg.user_input,
        "persona": detected_persona,
        "response": response
    }
    os.makedirs("logs", exist_ok=True)
    with open("logs/chat_log.jsonl", "a") as f:
        f.write(json.dumps(log_entry) + "\n")

    return {
        "response": response,
        "persona": detected_persona
    }

if __name__ == "__main__":
    uvicorn.run("app:app", host="127.0.0.1", port=8000, reload=True)
