import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

_api_key = os.getenv("OPENAI_API_KEY") or os.getenv("OPEN_AI_API_KEY")
client = OpenAI(api_key=_api_key)

def get_response(prompt):
    response = client.chat.completions.create(
        model="gpt-5.4-mini",
        messages=messages,
        stream=True,
        reasoning_effort="low",
    )
    return response.choices[0].message.content