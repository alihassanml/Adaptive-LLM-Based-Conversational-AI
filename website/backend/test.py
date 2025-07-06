import json
from collections import defaultdict
from textblob import TextBlob
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd

# Load chat log
CHAT_LOG = './src/chat_log.json'
persona_sentiments = defaultdict(lambda: {'positive': 0, 'neutral': 0, 'negative': 0})

def get_sentiment_label(text):
    polarity = TextBlob(text).sentiment.polarity
    if polarity > 0.1:
        return 'positive'
    elif polarity < -0.1:
        return 'negative'
    else:
        return 'neutral'

with open(CHAT_LOG, 'r') as f:
    for line in f:
        entry = json.loads(line)
        persona = entry.get('persona')
        response = entry.get('llm_reply', '')
        if persona and response:
            label = get_sentiment_label(response)
            persona_sentiments[persona][label] += 1

# --- Format Data for Plotting ---
personas = list(persona_sentiments.keys())
data = {
    'persona': [],
    'sentiment': [],
    'count': []
}
for persona, sentiments in persona_sentiments.items():
    for sentiment, count in sentiments.items():
        data['persona'].append(persona)
        data['sentiment'].append(sentiment)
        data['count'].append(count)

df = pd.DataFrame(data)

# --- 1. Stacked Bar Chart ---
pivot_df = df.pivot(index='persona', columns='sentiment', values='count').fillna(0)
pivot_df[['positive', 'neutral', 'negative']].plot(
    kind='bar',
    stacked=True,
    color=['#66bb6a', '#ffee58', '#ef5350'],
    figsize=(8, 5)
)
plt.title('Sentiment Distribution per Persona (Stacked Bar)')
plt.ylabel('Message Count')
plt.xlabel('Persona')
plt.tight_layout()
plt.savefig('sentiment_stacked_bar.png')
plt.show()

# --- 2. Heatmap ---
plt.figure(figsize=(6, 4))
sns.heatmap(pivot_df, annot=True, fmt="g", cmap="YlGnBu")
plt.title('Sentiment Heatmap per Persona')
plt.ylabel('Persona')
plt.xlabel('Sentiment')
plt.tight_layout()
plt.savefig('sentiment_heatmap.png')
plt.show()
