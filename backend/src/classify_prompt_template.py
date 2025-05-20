classify_prompt = """
Classify the message below as one of the following personas:

- oversharer: Emotional, reveals too much personal info impulsively
- verbose: Long, descriptive, but emotionally neutral or on-topic
- reserved: Short, avoids sharing, emotionally distant

Only reply with one: oversharer, verbose, reserved.

Examples:

Message: "I cried again at work today and I feel like such a mess. I just want to tell someone."
Persona: oversharer

Message: "My afternoon started with a project sync, then I wrote code for a few hours."
Persona: verbose

Message: "It's okay."
Persona: reserved

Now classify this:

Message: "{message}"
Persona:
"""
