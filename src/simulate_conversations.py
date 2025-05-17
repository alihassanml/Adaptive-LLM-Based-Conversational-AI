import requests
import json
from datetime import datetime

# Endpoint of your backend
API_URL = "http://127.0.0.1:8000/chat"

# Simulated test turns for each persona
test_data = {
    "oversharer": [
        "I had a bad day.",
        "My friend ignored me again, and I can't stop thinking about it.",
        "I don’t know why I always mess things up.",
    ],
    "verbose": [
        "Today was quite unusual, it started off cloudy and then suddenly turned sunny.",
        "I had three meetings back to back, which made me feel drained mentally.",
        "Later in the evening, I started wondering if I’m doing the right thing in my life.",
    ],
    "reserved": [
        "Not great.",
        "I’m fine.",
        "Just tired.",
    ]
}

# Store all results here
all_conversations = []

for persona, messages in test_data.items():
    for i, message in enumerate(messages):
        response = requests.post(API_URL, json={"message": message, "persona": persona})
        reply = response.json().get("response", "ERROR")
        
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "persona": persona,
            "user_message": message,
            "llm_reply": reply,
            "turn": i + 1
        }
        print(f"[{persona.upper()}] User: {message}")
        print(f"→ Bot: {reply}\n")

        all_conversations.append(log_entry)

# Save to JSON file
with open("chat_logs.json", "w") as f:
    json.dump(all_conversations, f, indent=4)
