import anthropic


def get_proof(claim):
    return f"""Prove the following {claim},
Use the following format

Claim: ...

PROVIDED SOLUTION
...
"""

def query_claude(prompt: str, model: str = "claude-sonnet-4-5-20250929") -> str:
    """Send a prompt to Claude and return the response."""
    client = anthropic.Anthropic()  # Uses ANTHROPIC_API_KEY env variable
    
    print("Waiting for Claude")
    message = client.messages.create(
        model=model,
        max_tokens=2048,
        messages=[
            {"role": "user", "content": prompt}
        ]
    )
    print("Claude Complete")
    return message.content[0].text

