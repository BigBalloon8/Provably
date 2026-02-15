from transformers import AutoModelForCausalLM, AutoTokenizer
import torch
import outlines

import subprocess

def get_verify_prompt(proof, lean_file):
    with open(lean_file, "r") as f:
        lean = f.read()
    return f"""True or False: The following lean code is doing the same as the natural language proof.
-------------------LEAN----------------
```lean4
{lean}
```
------------------PROOF----------------
{proof}
"""

def verify_equality(proof, model_name="deepseek-ai/DeepSeek-Prover-V2-7B"):
    model = outlines.from_transformers(
    AutoModelForCausalLM.from_pretrained(model_name, device_map="auto", dtype=torch.bfloat16, trust_remote_code=True),
    AutoTokenizer.from_pretrained(model_name)
    )
    return model(get_verify_prompt(proof, "Solution/solution.lean"), bool)

def verify_lean_file(filepath: str) -> bool:
    """Returns True if the Lean file compiles successfully."""
    result = subprocess.run(
        ["lake", "env", "lean", filepath],
        capture_output=True,
        text=True
    )
    if result.returncode == 0:
        return True
    else:
        return False
    