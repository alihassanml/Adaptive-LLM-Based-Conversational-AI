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
from fastapi.responses import JSONResponse



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

# llm = Ollama(model="mistral:latest")  # or "llama2", "vicuna", etc.
# llm = Ollama(model="llama3.2:latest")  # or "llama2", "vicuna", etc.
llm = Ollama(model="gemma3:1b")  # or "llama2", "vicuna", etc.
# llm = Ollama(model="gemma3:4b")  # or "llama2", "vicuna", etc.

# Initialize FAISS index (dimension must match embedding size)


# Metadata list to track messages per vector

class ChatInput(BaseModel):
    message: str


def save_chat_log(persona, user_message, llm_reply, user_id="user123"):
    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "persona": persona,
        "user_id": user_id,
        "user_message": user_message,
        "llm_reply": llm_reply
    }
    with open("chat_log.json", "a") as f:
        f.write(json.dumps(log_entry) + "\n")


def load_recent_history(user_id: str, limit: int = 8):
    history = []
    try:
        with open("chat_log.json", "r") as f:
            lines = f.readlines()
            for line in reversed(lines):
                entry = json.loads(line)
                if entry.get("user_id", "user123") == user_id:
                    user_msg = entry["user_message"]
                    llm_reply = entry["llm_reply"]
                    history.append(f"User: {user_msg}\nBot: {llm_reply}")
                    if len(history) == limit:
                        break
    except FileNotFoundError:
        pass
    return list(reversed(history))  # newest last


def detect_persona_rule_based(message: str):
    message = message.lower()
    if len(message.split()) > 25 or "i feel like" in message or "today was" in message:
        return "verbose"
    elif any(word in message for word in ["sorry", "can't stop", "i always", "everyone says"]):
        return "oversharer"
    elif len(message.split()) < 5:
        return "reserved"
    return "verbose"  # default fallback




PERSONA_RESPONSE_STYLE = {
    "oversharer": "Calm, supportive tone. Avoid dramatic expressions. 2-3 natural sentences only.",
    "verbose": "Respond clearly in 1-2 full sentences. Use emojis if they fit naturally.",
    "reserved": "Use short, minimal phrases.Add only 1 emoji. Max 10 words."
}

length_guidance = {
    "short": "Keep your reply under 25 words.",
    "medium": "Reply in 2-3 concise sentences.",
    "long": "Provide a thoughtful and supportive 4-5 sentence reply."
}
VALID_PERSONAS = {"verbose", "reserved", "oversharer"}


@app.post("/chat")
async def chat(input: ChatInput):
    # Step 1: Let the LLM classify the persona
    classification_prompt = classify_prompt.format(message=input.message)
    persona = llm.invoke(classification_prompt).strip().lower()
    print(f'persona---{persona}')
    if persona not in VALID_PERSONAS:
        persona = "oversharer"

    persona_description = PERSONAS[persona]

    user_history = load_recent_history("user123", limit=4)
    history_context = "\n".join(user_history)
    print('Previous Histories::---',history_context)

    response_prompt = chat_prompt.format(
        persona_description=persona_description,
        message=input.message,
        response_style=PERSONA_RESPONSE_STYLE[persona],
        length_guidance=length_guidance,
        history=history_context
    )

    response = llm.invoke(response_prompt)

    save_chat_log(persona, input.message, response)

    return {
        "persona_detected": persona,
        "response": response
    }



@app.get("/chat/history")
def get_chat_history(user_id: str = "user123", limit: int = 10):
    history = []
    try:
        with open("chat_log.json", "r") as f:
            lines = f.readlines()
            for line in reversed(lines):
                entry = json.loads(line)
                if entry.get("user_id", "user123") == user_id:
                    history.append({
                        "timestamp": entry["timestamp"],
                        "message": entry["user_message"],
                        "response": entry["llm_reply"]
                    })
                    if len(history) >= limit:
                        break
    except FileNotFoundError:
        return JSONResponse(content={"history": []})

    return {"history": list(reversed(history))}  # most recent last


from collections import Counter
import json

@app.get("/persona-counts")
def get_persona_counts():
    counts = Counter()
    try:
        with open("chat_log.json", "r") as f:
            for line in f:
                entry = json.loads(line)
                persona = entry.get("persona")
                if persona:
                    counts[persona] += 1
    except FileNotFoundError:
        pass
    return counts