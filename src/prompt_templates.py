chat_prompt = """
You are a chatbot adapted to the following personality traits:
{persona_description},{length_guidance}


User says: "{message}"

{response_style}

Respond in a natural tone, consistent with the personality.
Only reply with the assistant's final message below. Do not include any explanation, greeting, or system instruction. Just respond as the assistant would.

"""


# Recent history:
# {history}
