import json
from textblob import TextBlob

# Load logs
with open("chat_logs.json") as f:
    logs = json.load(f)

# Results per persona
summary = {}

for entry in logs:
    persona = entry["persona"]
    text = entry["llm_reply"]
    word_count = len(text.split())
    sentiment = TextBlob(text).sentiment.polarity
    contains_empathy = any(kw in text.lower() for kw in ["sorry", "understand", "that sounds", "here for you"])

    if persona not in summary:
        summary[persona] = {"word_counts": [], "sentiments": [], "empathy_count": 0}

    summary[persona]["word_counts"].append(word_count)
    summary[persona]["sentiments"].append(sentiment)
    if contains_empathy:
        summary[persona]["empathy_count"] += 1

# Print summary
for persona, stats in summary.items():
    print(f"\n🧠 Persona: {persona}")
    print(f"Average Reply Length: {sum(stats['word_counts']) / len(stats['word_counts']):.2f} words")
    print(f"Average Sentiment: {sum(stats['sentiments']) / len(stats['sentiments']):.2f}")
    print(f"Empathy Phrases Used: {stats['empathy_count']} times")
