import anthropic
from transformers import AutoModelForCausalLM, AutoTokenizer
import torch


def get_proof(claim):
    return f"""Prove the following {claim},
Use the following format write the solution in markdown

Claim: ...

PROVIDED SOLUTION
...
"""

def provablyify(text:str):
    return text.replace("∎", "◻")

def run_transformer(prompt, model_id):
    tokenizer = AutoTokenizer.from_pretrained(model_id)
    model = AutoModelForCausalLM.from_pretrained(model_id, device_map="auto", dtype=torch.bfloat16, trust_remote_code=True)

    chat = [
    {"role": "user", "content": get_proof(prompt)},
    ]

    inputs = tokenizer.apply_chat_template(chat, tokenize=True, add_generation_prompt=True, return_tensors="pt").to(model.device)

    print(f"{model_id} Started")
    outputs = model.generate(inputs, max_new_tokens=4096)
    print(f"{model_id} Completed")
    return provablyify(tokenizer.batch_decode(outputs)[0])


def query_claude(prompt: str, model: str = "claude-sonnet-4-5-20250929") -> str:
    """Send a prompt to Claude and return the response."""
    client = anthropic.Anthropic()  # Uses ANTHROPIC_API_KEY env variable
    
    print("Waiting for Claude")
    message = client.messages.create(
        model=model,
        max_tokens=4096,
        messages=[
            {"role": "user", "content": get_proof(prompt)}
        ]
    )
    print("Claude Complete")
    return provablyify(message.content[0].text)

