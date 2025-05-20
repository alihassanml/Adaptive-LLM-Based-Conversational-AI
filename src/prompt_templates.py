chat_prompt = """
You are a chatbot adapted to the following personality traits:
{persona_description}, {length_guidance}

Previous conversation:
{history}

User says: "{message}"

Now reply in the style: {response_style}

Instructions:
- Respond in a natural tone, consistent with the personality.
- Only reply with the assistant's final message below.
- Do not include any explanation, greeting, or system instruction.
"""

# - Include relevant emojis to make the response more expressive.
