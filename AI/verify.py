from transformers import AutoModelForCausalLM, AutoTokenizer
import torch
import outlines

import subprocess
import os

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
    return model(get_verify_prompt(proof, os.path.join(os.environ["SOLUTIONPATH"],"solution.lean")), bool)

def verify_lean_file(filepath: str) -> bool:
    """Returns True if the Lean file compiles successfully."""
    print("Verifying Lean")
    
    with open(filepath, "r") as f:
        sorries = "sorry" in f.read()

    result = subprocess.run(
        ["lake", "env", "lean", filepath],
        capture_output=True,
        text=True
    )
    if result.returncode == 0:
        print("Lean Succeed")
        return True and not sorries
    else:
        print("Lean Failed")
        return False

def lean_file_output(filepath: str) -> bool:
    """Returns True if the Lean file compiles successfully."""
    print("Verifying Lean")

    result = subprocess.run(
        ["lake", "env", "lean", filepath],
        capture_output=True,
        text=True
    )
    if result.returncode == 0:
        print("Lean Succeed")
        return True, result.stdout
    else:
        print("Lean Failed")
        return False, result.stdout
    