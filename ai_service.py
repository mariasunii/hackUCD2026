
import os
import requests
from dotenv import load_dotenv

# Load API key and model from .env
load_dotenv()

API_KEY = os.getenv("OPENROUTER_API_KEY")
MODEL = os.getenv("OPENROUTER_MODEL")


def ask_ai(prompt):
    if not API_KEY:
        raise ValueError("OpenRouter API key is missing.")

    response = requests.post(
        "https://openrouter.ai/api/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {API_KEY}",
            "Content-Type": "application/json"
        },
        json={
            "model": MODEL,
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        },
        timeout=60
    )

    response.raise_for_status()

    data = response.json()

    return data["choices"][0]["message"]["content"]


# Temporary test
if __name__ == "__main__":
    result = ask_ai(
        "Break down building a library reservation website "
        "into 5 tasks for university students."
    )

    print(result)
