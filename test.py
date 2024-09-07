from dotenv import load_dotenv
import os
from openai import OpenAI

load_dotenv()

# print("starting test.py with key:", os.getenv("OPENAI_API_KEY"))

from openai import OpenAI
client = OpenAI()
response = client.chat.completions.create(
  model="gpt-4o",
  messages=[
    {"role": "system", "content": "You are a helpful assistant."},
    {"role": "user", "content": "What is a LLM?"}
  ]
)

print(response.choices[0].message)