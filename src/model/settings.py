"""
CONTROLS THE MODELS SETTINGS/ HOW WE CALL THE 
"""
from openai import OpenAI
import os

class Settings:
    def __init__(self):
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    def get_response(self, user_input):
        response = self.client.responses.create(
            model="gpt-5.4-mini",
            input=user_input,
            reasoning={"effort": "low"},
        )
        return response.output[0].content[0].text           #return response to whoever called the request