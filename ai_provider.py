import os

from groq import Groq


MODEL = "openai/gpt-oss-20b"

def generate_chat_reply(messages):
    api_key = os.getenv("GROQ_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError("GROQ_API_KEY is not set in the environment.")

    response = Groq(api_key=api_key).chat.completions.create(
        model=MODEL,
        messages=messages,
        max_tokens=600,
    )
    reply = response.choices[0].message.content
    if not isinstance(reply, str) or not reply.strip():
        raise ValueError("The AI provider returned an empty or invalid reply.")
    return reply.strip()
