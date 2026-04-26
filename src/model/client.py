import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

_api_key = os.getenv("OPENAI_API_KEY") or os.getenv("OPEN_AI_API_KEY")
client = OpenAI(api_key=_api_key)

def get_response(prompt):
    """Yield response chunks as they stream in from the model."""
    stream = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        stream=True,
    )
    try:
        for chunk in stream:
            delta = chunk.choices[0].delta.content
            if delta:
                yield delta
    finally:
        stream.close()