from transformers import AutoModelForCausalLM, AutoTokenizer
import torch
import outlines
import anthropic

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

def verify_with_claude(proof, model_name):
    client = anthropic.Anthropic()
    model = outlines.from_anthropic(client, model_name)

def verify_equality(proof, model_name="deepseek-ai/DeepSeek-Prover-V2-7B"):
    if "claude" in model_name:
        client = anthropic.Anthropic()
        prompt = get_verify_prompt(proof, os.path.join(os.environ["SOLUTIONPATH"],"solution.lean"))
        response = client.messages.create(
            model=model_name,
            max_tokens=1024,
            tools=[{
                "name": "lean4_equivalency_check",
                "description": "Classify whether The give lean4 code is doing the same as the given natural language proof",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "result": {
                            "type": "boolean",
                            "description": "True if the lean4 code is doing the same as the given natural language proof, False otherwise"
                        }
                    },
                    "required": ["result"]
                }
            }],
            tool_choice={"type": "tool", "name": "lean4_equivalency_check"},
            messages=[{"role": "user", "content": prompt}]
        )
        return response.content[0].input["result"]
    else:
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

    with open(filepath, "r") as f:
        sorries = "sorry" in f.read()

    result = subprocess.run(
        ["lake", "env", "lean", filepath],
        capture_output=True,
        text=True
    )
    if result.returncode == 0:
        print("Lean Succeed")
        return True and not sorries, result.stdout
    else:
        print("Lean Failed")
        return False, result.stdout
    