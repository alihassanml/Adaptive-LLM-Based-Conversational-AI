import json
import faiss
import numpy as np
from datetime import datetime
from fastapi import FastAPI
from pydantic import BaseModel
from personas import PERSONAS
from prompt_templates import chat_prompt
from langchain_community.llms import Ollama
from classify_prompt_template import classify_prompt
from sentence_transformers import SentenceTransformer
from fastapi.middleware.cors import CORSMiddleware



app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Or ["http://localhost:3000"] if you want to restrict
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
allow_origins=["http://localhost:3000"]




# Initialize LLM (You must have Ollama running and a model pulled, e.g., mistral)
llm = Ollama(model="gemma3:1b")  # or "llama2", "vicuna", etc.
embedder = SentenceTransformer("all-MiniLM-L6-v2")

# Initialize FAISS index (dimension must match embedding size)
dimension = 384
index = faiss.IndexFlatL2(dimension)

# Metadata list to track messages per vector
metadata = []

class ChatInput(BaseModel):
    message: str


def save_chat_log(persona, user_message, llm_reply):
    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "persona": persona,
        "user_message": user_message,
        "llm_reply": llm_reply
    }
    with open("chat_log.json", "a") as f:
        f.write(json.dumps(log_entry) + "\n")



def detect_persona_rule_based(message: str):
    message = message.lower()
    if len(message.split()) > 25 or "i feel like" in message or "today was" in message:
        return "verbose"
    elif any(word in message for word in ["sorry", "can't stop", "i always", "everyone says"]):
        return "oversharer"
    elif len(message.split()) < 5:
        return "reserved"
    return "verbose"  # default fallback

def add_to_faiss(user_id, message):
    embedding = embedder.encode([message])[0]
    index.add(np.array([embedding]))
    metadata.append({"user_id": user_id, "text": message})

def retrieve_user_history(user_id, query, top_k=4):
    query_embedding = embedder.encode([query])[0]
    distances, indices = index.search(np.array([query_embedding]), top_k)

    # Filter by user_id
    history = []
    for idx in indices[0]:
        if idx < len(metadata) and metadata[idx]["user_id"] == user_id:
            history.append(metadata[idx]["text"])
    return history



PERSONA_RESPONSE_STYLE = {
    "oversharer": "Calm, supportive tone. Avoid dramatic expressions. 2-3 natural sentences only.",
    "verbose": "Respond clearly in 1-2 full sentences.",
    "reserved": "Use short, minimal phrases. Max 10 words."
}

length_guidance = {
    "short": "Keep your reply under 25 words.",
    "medium": "Reply in 2-3 concise sentences.",
    "long": "Provide a thoughtful and supportive 4-5 sentence reply."
}


@app.post("/chat")
async def chat(input: ChatInput):
    # Step 1: Let the LLM classify the persona
    classification_prompt = classify_prompt.format(message=input.message)
    persona = llm.invoke(classification_prompt).strip().lower()
    print(f'persona---{persona}')

    persona_description = PERSONAS[persona]
    # add_to_faiss('user123', input.message)

    # user_history = retrieve_user_history(user_id="user123", query=input.message)
    # history_context = "\n".join(user_history[-3:])  # last 3 interactions

    response_prompt = chat_prompt.format(
        persona_description=persona_description,
        message=input.message,
        response_style=PERSONA_RESPONSE_STYLE[persona],
        length_guidance=length_guidance
        # history=history_context
    )

    response = llm.invoke(response_prompt)

    save_chat_log(persona, input.message, response)

    return {
        "persona_detected": persona,
        "response": response
    }
