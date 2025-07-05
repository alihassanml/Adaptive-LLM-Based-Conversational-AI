import json
import faiss
import numpy as np
from datetime import datetime
from fastapi import FastAPI
from pydantic import BaseModel
from src.personas import PERSONAS
from src.prompt_templates import chat_prompt
from langchain_community.llms import Ollama
from src.classify_prompt_template import classify_prompt
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from fastapi import FastAPI,Depends,HTTPException,Form
import bcrypt
from src.database.database import SessionLocal
import src.database.model as model
from src.database.database import engine
from src.database.model import Base  




app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
allow_origins=["*"]
Base.metadata.create_all(bind=engine)




# llm = Ollama(model="mistral:latest")  # or "llama2", "vicuna", etc.
# llm = Ollama(model="llama3.2:latest")  # or "llama2", "vicuna", etc.
llm = Ollama(model="gemma3:1b")  # or "llama2", "vicuna", etc.
# llm = Ollama(model="gemma3:4b")  # or "llama2", "vicuna", etc.


class ChatInput(BaseModel):
    message: str


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

class Signup(BaseModel):
    name:str
    username: str
    email: str
    password: str

CHAT_LOG = './src/chat_log.json'


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))

@app.post('/Create')
async def create_user(signup: Signup, db: Session = Depends(get_db)):
    
    user_name = db.query(model.Signup).filter(model.Signup.username == signup.username).first()
    user_email = db.query(model.Signup).filter(model.Signup.email == signup.email).first()
    if user_name:
        raise HTTPException(status_code=400, detail="Username Must Be Unique!")
    if user_email:
        raise HTTPException(status_code=400, detail="email Must Be Unique!")
    hashed_password = hash_password(signup.password)
    new_user = model.Signup(
        name=signup.name,
        username=signup.username,
        email=signup.email,
        password=hashed_password,
    )
    db.add(new_user)
    db.commit()
    return {'message': 'User created successfully', 'user': new_user}


@app.post('/login/')
async def login(
            username: str = Form(..., title='Enter Your User Name'),
            password: str = Form(..., title='Enter Password'),
            db: Session = Depends(get_db)):
    
    user = db.query(model.Signup).filter(model.Signup.username == username).first()
    if not user:
        raise HTTPException(status_code=400, detail="Incorrect username or password")
    
    if not verify_password(password, user.password):
        raise HTTPException(status_code=400, detail="Incorrect username or password")
        
    return {"message": "Login successful"}



def save_chat_log(persona, user_message, llm_reply, user_id="user123"):
    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "persona": persona,
        "user_id": user_id,
        "user_message": user_message,
        "llm_reply": llm_reply
    }
    with open(CHAT_LOG, "a") as f:
        f.write(json.dumps(log_entry) + "\n")


def load_recent_history(user_id: str, limit: int = 8):
    history = []
    try:
        with open(CHAT_LOG, "r") as f:
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
        with open(CHAT_LOG, "r") as f:
            lines = f.readlines()
            for line in reversed(lines):
                entry = json.loads(line)
                if entry.get("user_id", "user123") == user_id:
                    history.append({
                        "timestamp": entry["timestamp"],
                        "message": entry["user_message"],
                        "response": entry["llm_reply"]
                    })
                   
    except FileNotFoundError:
        return JSONResponse(content={"history": []})

    return {"history": list(reversed(history))}  # most recent last


from collections import Counter
import json

@app.get("/persona-counts")
def get_persona_counts():
    counts = Counter()
    try:
        with open(CHAT_LOG, "r") as f:
            for line in f:
                entry = json.loads(line)
                persona = entry.get("persona")
                if persona:
                    counts[persona] += 1
    except FileNotFoundError:
        pass
    return counts

