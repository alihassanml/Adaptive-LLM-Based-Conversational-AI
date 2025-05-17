import json
from datetime import datetime
from fastapi import FastAPI
from pydantic import BaseModel
from personas import PERSONAS
from prompt_templates import chat_prompt
from langchain.llms import Ollama
from classify_prompt_template import classify_prompt


app = FastAPI()

# Initialize LLM (You must have Ollama running and a model pulled, e.g., mistral)
llm = Ollama(model="gemma3:1b")  # or "llama2", "vicuna", etc.

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


PERSONA_RESPONSE_STYLE = {
    "oversharer": "Use gentle, validating language in 2-3 sentences.",
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


    response_prompt = chat_prompt.format(
        persona_description=persona_description,
        message=input.message,
        response_style=PERSONA_RESPONSE_STYLE[persona],
        length_guidance=length_guidance
    )

    response = llm.invoke(response_prompt)

    save_chat_log(persona, input.message, response)

    return {
        "persona_detected": persona,
        "response": response
    }
