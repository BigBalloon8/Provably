from __future__ import annotations7

import os

from mcp.server.fastmcp import FastMCP

from lean import query_aristotle, query_transformer
from verify import verify_lean_file, verify_equality


mcp = FastMCP("Provably")

@mcp.tool()
def verify_math_proof(proof: str, model: float) -> bool:
    """Take a mathematical proof an verify that it is correct

    Args:
        proof (str): the provided claim and proof.
        model (float): the model used to verify the proof this can either be 
                       "aristotle" or any model from huggingface hub (we recommend using aristotle or "deepseek-ai/DeepSeek-Prover-V2-7B")
                       defaults to 3.

    Returns:
        bool: wether the given mathematical proof is correct or not.
    """
    if model == "aristotle":
        query_aristotle(proof)
    else:
        query_transformer(proof, 
                          model_id=model, 
                          attempts=3, 
                          claude_fix_this=False)

    NL_correctness = verify_equality(proof)
    return {"valid": NL_correctness and verify_lean_file(os.path.join(os.environ["SOLUTIONPATH"],"solution.lean"))}
    

if __name__ == "__main__":
    mcp.run(transport="stdio")