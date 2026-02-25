import aristotlelib
from aristotlelib import Project, ProjectInputType
from transformers import AutoModelForCausalLM, AutoTokenizer
import torch
import anthropic

import asyncio
import re
import os

from verify import lean_file_output
#-----------------------------------------------------------------------------------------------------
def get_lean(proof):
    return f"""This is a claim and proof written in natural language can you write it in lean as 1 to 1 as possible even if there is mistakes

{proof}
"""

#-----------------------------------------------------------------------------------------------------
def get_lean_deepseek(proof):
    return f"""
This is a claim and proof written in natural language can you write the equivalent lean code trying to keep it as 1 to 1 as possible

Proof: 
{proof}

Write the guide with the following code included

```lean4
import Mathlib
import Aesop

set_option maxHeartbeats 0

open BigOperators Real Nat Topology Rat
```
Provide a detailed proof plan outlining the main proof steps and strategies. The plan should highlight key ideas, intermediate lemmas, \
and proof structures that will guide the construction of the final formal proof.

""".strip()
#-----------------------------------------------------------------------------------------------------
imports = """
import Mathlib
import Aesop

set_option maxHeartbeats 0

open BigOperators Real Nat Topology Rat\n
""".strip()
#-----------------------------------------------------------------------------------------------------

async def aristotle_request(proof):
    await Project.prove_from_file(
        input_content=proof,
        project_input_type=ProjectInputType.INFORMAL,
        auto_add_imports=False,
        validate_lean_project=False,
        output_file_path=os.path.join(os.environ["SOLUTIONPATH"],"solution.lean")
    )

def query_aristotle(NL, logger=None):
    print("Waiting for Aristotle")
    asyncio.run(aristotle_request(get_lean(NL)))
    print("Aristotle Complete")
    if logger is not None:
        logger.info("Aristotle Complete")


def run_transformer_lean(prompt, model_id):
    tokenizer = AutoTokenizer.from_pretrained(model_id)
    model = AutoModelForCausalLM.from_pretrained(model_id, device_map="auto", dtype=torch.bfloat16, trust_remote_code=True)

    chat = [
    {"role": "user", "content": prompt},
    ]

    inputs = tokenizer.apply_chat_template(chat, tokenize=True, add_generation_prompt=True, return_tensors="pt").to(model.device)

    outputs = model.generate(inputs, max_new_tokens=2048, cache_implementation="quantized")
    return tokenizer.batch_decode(outputs)[0]


def get_lean_code_block(text):
    pattern = re.compile(
        r"```lean4\s*\n(.*?)\n```",  # capture the code only
        flags=re.DOTALL
    )
    blocks = pattern.findall(text)
    code = blocks[-1]
    if "import" not in code:
        code = imports + "\n\n" + code
    return code

def query_claude(prompt: str, model: str = "claude-sonnet-4-5-20250929") -> str:
    """Send a prompt to Claude and return the response."""
    client = anthropic.Anthropic()  # Uses ANTHROPIC_API_KEY env variable
    
    message = client.messages.create(
        model=model,
        max_tokens=4092,
        messages=[
            {"role": "user", "content": prompt}
        ]
    )
    return message.content[0].text


def query_transformer(prompt, model_id="deepseek-ai/DeepSeek-Prover-V2-7B", logger=None, attempts=1, claude_fix_this=True):

    seq = get_lean_deepseek(prompt)

    for i in range(attempts):
        print(f"Waiting for Deepseek (Attempt {i})")
        if i > 0 and claude_fix_this:
            query_claude(seq)
        else:
            out = run_transformer_lean(seq, model_id)
        
        if logger is not None:
            logger.info(out)

        code = get_lean_code_block(out)
        
        with open(os.path.join(os.environ["SOLUTIONPATH"],"solution.lean"), "w") as file:
            file.write(code)
        
        file_passes, output = lean_file_output(os.path.join(os.environ["SOLUTIONPATH"],"solution.lean"))
        
        if file_passes:
            break
        
        seq = f"\n The following lean code \n```lean4\n{code}\n```\n resulted in this error:\n{output}\n Can you fix it, giving the output in as \n```lean4\n...\n```: "
        
    print("Deepseek Complete")
    #print(code)

