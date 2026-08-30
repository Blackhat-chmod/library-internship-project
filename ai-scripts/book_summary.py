import os
from groq import Groq

client = Groq(
    api_key=os.getenv("GROQ_API_KEY")
)

title = input("Enter book title: ")
description = input("Enter book description: ")

prompt = f"""
Book title: {title}

Book description:
{description}

Write one short paragraph summarizing this book.
Then suggest the most suitable genre.
"""

response = client.chat.completions.create(
    model="openai/gpt-oss-20b",
    messages=[
        {
            "role": "user",
            "content": prompt
        }
    ]
)

print("\nAI Result:\n")
print(response.choices[0].message.content)