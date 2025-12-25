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
from fastapi import FastAPI, File, UploadFile
from src.rag_handler import rag_handler
import time
from collections import defaultdict
import shutil
import os

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
allow_origins=["*"]

llm = Ollama(model="mistral:latest")  # or "llama2", "vicuna", etc.
# llm = Ollama(model="llama3.2:latest")  # or "llama2", "vicuna", etc.
# llm = Ollama(model="gemma3:1b")  # or "llama2", "vicuna", etc.
# llm = Ollama(model="gemma3:4b")  # or "llama2", "vicuna", etc.
# llm = Ollama(model="gemma3:270m")  # or "llama2", "vicuna", etc.


class ChatInput(BaseModel):
    message: str

CHAT_LOG = './src/chat_log.json'

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


def load_recent_history(user_id: str, limit: int = 15):
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
    # RAG retrieval
    # RAG retrieval with error handling
    rag_context = ""
    relevant_docs = []
    try:
        if rag_handler.index and rag_handler.index.ntotal > 0:
            relevant_docs = rag_handler.search(input.message, top_k=2)
            if relevant_docs:
                rag_context = "\n\n-- RELEVANT DOCUMENT CONTEXT:\n" + "\n".join(relevant_docs)
    except Exception as e:
        print(f"⚠️ RAG search error: {e}")
        # Continue without RAG context

    history_context = "\n".join(user_history)
    print('Previous Histories::---',history_context)

    response_prompt = chat_prompt.format(
        persona_description=persona_description,
        message=input.message,
        response_style=PERSONA_RESPONSE_STYLE[persona],
        length_guidance=length_guidance,
        history=history_context + rag_context
    )

    response = llm.invoke(response_prompt)

    save_chat_log(persona, input.message, response)

    return {
        "persona_detected": persona,
        "response": response,
        "timestamp": datetime.now().isoformat(),
        "rag_used": bool(rag_context.strip()),
        "rag_sources": len(relevant_docs) if rag_context else 0
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


UPLOAD_DIR = "./src/uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@app.post("/upload-document")
async def upload_document(file: UploadFile = File(...)):
    try:
        # Validate file type
        allowed_extensions = ['pdf', 'txt', 'doc', 'docx']
        file_ext = file.filename.split('.')[-1].lower()
        
        if file_ext not in allowed_extensions:
            return {
                "status": "error", 
                "message": f"File type .{file_ext} not supported. Use: {', '.join(allowed_extensions)}"
            }
        
        # Save file
        file_path = os.path.join(UPLOAD_DIR, file.filename)
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        print(f"📁 File saved: {file_path}")
        
        # Process with RAG
        rag_handler.add_document(file_path, file_ext)
        
        return {
            "status": "success",
            "message": f"File '{file.filename}' uploaded and indexed successfully",
            "chunks": rag_handler.index.ntotal
        }
    except Exception as e:
        print(f"❌ Upload error: {e}")
        return {
            "status": "error", 
            "message": f"Upload failed: {str(e)}"
        }
    


@app.get("/uploaded-files")
def get_uploaded_files():
    """Return list of uploaded files"""
    try:
        files = []
        if os.path.exists(UPLOAD_DIR):
            for filename in os.listdir(UPLOAD_DIR):
                file_path = os.path.join(UPLOAD_DIR, filename)
                if os.path.isfile(file_path):
                    # Get file upload time
                    upload_time = os.path.getmtime(file_path)
                    files.append({
                        "name": filename,
                        "uploadedAt": datetime.fromtimestamp(upload_time).strftime("%I:%M %p, %b %d")
                    })
        
        return {
            "files": files,
            "total_chunks": rag_handler.index.ntotal
        }
    except Exception as e:
        return {"files": [], "total_chunks": 0}
    


@app.delete("/delete-file/{filename}")
async def delete_file(filename: str):
    """Delete an uploaded file and rebuild index"""
    try:
        file_path = os.path.join(UPLOAD_DIR, filename)
        if os.path.exists(file_path):
            os.remove(file_path)
            
            # Rebuild RAG index from remaining files
            rag_handler.index = faiss.IndexFlatL2(rag_handler.dimension)
            rag_handler.metadata = []
            
            # Re-index remaining files
            if os.path.exists(UPLOAD_DIR):
                for remaining_file in os.listdir(UPLOAD_DIR):
                    remaining_path = os.path.join(UPLOAD_DIR, remaining_file)
                    if os.path.isfile(remaining_path):
                        file_ext = remaining_file.split('.')[-1].lower()
                        rag_handler.add_document(remaining_path, file_ext)
            
            return {"status": "success", "message": f"File '{filename}' deleted"}
        else:
            return {"status": "error", "message": "File not found"}
    except Exception as e:
        return {"status": "error", "message": str(e)}
    

from evaluation.model_comparison import ModelBenchmark
@app.get("/benchmarks")
def get_benchmarks():
    benchmark = ModelBenchmark()
    
    test_queries = [
        "Hello, how are you?",
        "I'm feeling really stressed about work today...",
        "What's the weather?",
    ]
    
    test_personas = [
        {"message": "I can't stop crying, everything is falling apart...", "expected": "oversharer"},
        {"message": "Okay.", "expected": "reserved"},
        {"message": "Today I went to the store, bought groceries, came home...", "expected": "verbose"},
    ]
    
    return {
        "response_times": benchmark.benchmark_response_time(test_queries),
        "persona_accuracy": benchmark.benchmark_persona_accuracy(test_personas)
    }




metrics = {
    "response_times": [],
    "endpoint_hits": defaultdict(int)  # ✅ Use defaultdict(int) for counters
}

@app.middleware("http")
async def track_performance(request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    
    metrics["response_times"].append(process_time)
    metrics["endpoint_hits"][request.url.path] += 1  # ✅ Now works correctly
    
    return response
    

@app.get("/metrics")
def get_metrics():
    if not metrics["response_times"]:
        return {
            "avg_response_time": 0,
            "total_requests": 0,
            "endpoint_hits": {},
            "model": "mistral:latest"
        }
    
    return {
        "avg_response_time": sum(metrics["response_times"]) / len(metrics["response_times"]),
        "total_requests": len(metrics["response_times"]),
        "endpoint_hits": dict(metrics["endpoint_hits"]),  # Convert defaultdict to dict
        "model": "mistral:latest"
    }