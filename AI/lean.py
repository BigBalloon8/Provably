import aristotlelib
from aristotlelib import Project, ProjectInputType
from transformers import AutoModelForCausalLM, AutoTokenizer
import torch

import asyncio
import re

from verify import lean_file_output

def get_lean(proof):
    return f"""This is a claim and proof written in natural language can you write it in lean as 1 to 1 as possible even if there is mistakes

{proof}
"""

def get_lean_deepseek_one_step(proof):
    return f"""
This is a claim and proof written in natural language can you write it in lean as 1 to 1 as possible even if there is mistakes.

Proof: 
{proof}

Complete the following Lean 4 code:

```lean4
import Mathlib
import Aesop

set_option maxHeartbeats 0

open BigOperators Real Nat Topology Rat
```

""".strip()

def get_lean_deepseek_stage_1(proof):
    return f"""
This is a claim and proof written in natural language can you write a guide for how to solve it in lean leaving sorry's for me to fill in the tactics

Proof: 
{proof}

Write the guide with the following code included

```lean4
import Mathlib
import Aesop

set_option maxHeartbeats 0

open BigOperators Real Nat Topology Rat
```

""".strip()


imports = """
import Mathlib
import Aesop

set_option maxHeartbeats 0

open BigOperators Real Nat Topology Rat\n
""".strip()

def get_lean_deepseek_stage_2(lean_code):
    return f"""
Please fill in the sorry's in the following lean4 code

```lean4
{lean_code}
```
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


def query_deepseek(prompt, model_id="deepseek-ai/DeepSeek-Prover-V2-7B", logger=None, stage_2=True, attempts=1):

    seq = get_lean_deepseek_stage_1(prompt) if stage_2 else get_lean_deepseek_one_step(prompt)

    for i in range(attempts):
        print(f"Waiting for Deepseek Stage 1 ({i})")
        out = run_transformer_lean(seq, model_id)[0]
        
        if logger is not None:
            logger.info(out)

        code = get_lean_code_block(out)
        
        with open("Solution/solution.lean", "w") as file:
            file.write(code)
        
        file_passes, output = lean_file_output("Solution/solution.lean")
        
        if file_passes:
            break
        
        seq = f"\n The following lean code \n```lean4\n{code}\n```\n resulted in this error:\n{output}\n Can you fix it"
        
        print(f"Deepseek Stage 1 Complete ({i})")


    if stage_2:
        seq = get_lean_deepseek_stage_2(code)
        for i in range(attempts):
            print(f"Waiting for Deepseek Stage 2 ({i})")
            out = run_transformer_lean(seq, model_id)[0]

            complete_code = get_lean_code_block(out)

            with open("Solution/solution.lean", "w") as file:
                file.write(complete_code)
            
            if logger is not None:
                logger.info(out)
            
            file_passes, output = lean_file_output("Solution/solution.lean")
        
            if file_passes:
                break

            seq = f"\n The following lean code \n```lean4\n{complete_code}\n```\n resulted in this error:\n{output}\n Can you rewrite it with the fixes"

    print("Deepseek Complete")
    #print(code)

