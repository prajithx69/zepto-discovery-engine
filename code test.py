from dotenv import load_dotenv
load_dotenv()

import anthropic

client = anthropic.Anthropic()

response = client.messages.create(
    model="claude-haiku-4-5",
    max_tokens=100,
    messages=[
        {"role": "user", "content": "Reply with exactly: API working, ready to build."}
    ],
)

print(response.content[0].text)