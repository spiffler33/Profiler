import os
import openai
from config import Config

api_key = Config.OPENAI_API_KEY

print(f"API key present: {bool(api_key)}")
print(f"API key length: {len(api_key or '')}")

try:
    client = openai.OpenAI(api_key=api_key)
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": "Say hello"}],
        max_tokens=10
    )
    print(f"Test API call successful: {response.choices[0].message.content}")
except Exception as e:
    print(f"API Error: {str(e)}")