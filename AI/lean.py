import aristotlelib
from aristotlelib import Project, ProjectInputType
from transformers import AutoModelForCausalLM, AutoTokenizer
import torch

import asyncio
import re

def get_lean(proof):
    return f"""This is a claim and proof written in natural language can you write it in lean as 1 to 1 as possible even if there is mistakes

{proof}
"""

def get_lean_deepseek(proof):
    return f"""
This is a claim and proof written in natural language can you write it in lean as 1 to 1 as possible even if there is mistakes

{proof}

Complete the following Lean 4 code:

```lean4
import Mathlib
import Aesop

set_option maxHeartbeats 0

open BigOperators Real Nat Topology Rat
```
even if there are errors in the given proof the lean should follow the given proof exactly, please only leave sorry's if 
""".strip()

imports = """
import Mathlib
import Aesop

set_option maxHeartbeats 0

open BigOperators Real Nat Topology Rat\n
""".strip()

async def aristotle_request(proof):
    await Project.prove_from_file(
        input_content=proof,
        project_input_type=ProjectInputType.INFORMAL,
        auto_add_imports=False,
        validate_lean_project=False,
        output_file_path="Solution/solution.lean"
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
    {"role": "user", "content": get_lean(prompt)},
    ]

    inputs = tokenizer.apply_chat_template(chat, tokenize=True, add_generation_prompt=True, return_tensors="pt").to(model.device)

    outputs = model.generate(inputs, max_new_tokens=2048, cache_implementation="quantized")
    return tokenizer.batch_decode(outputs)

def query_deepseek(prompt, model_id="deepseek-ai/DeepSeek-Prover-V2-7B", logger=None):
    print("Waiting for Deepseek")
    out = run_transformer_lean(get_lean_deepseek(prompt), model_id)[0]
    
    if logger is not None:
        logger.info(out)

    pattern = re.compile(
        r"```lean4\s*\n(.*?)\n```",  # capture the code only
        flags=re.DOTALL
    )
    blocks = pattern.findall(out)
    code = blocks[-1]
    if "import" not in code:
        code = imports + "\n\n" + code
    with open("Solution/solution.lean", "w") as file:
        file.write(code)
    print("Deepseek Complete")
    #print(code)

