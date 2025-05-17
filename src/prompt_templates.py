chat_prompt = """
You are a chatbot adapted to the following personality traits:
{persona_description},{length_guidance}
Recent history:
{history}

User says: "{message}"

{response_style}

Respond in a natural tone, consistent with the personality.
"""
