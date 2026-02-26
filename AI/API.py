from fastapi import FastAPI
from pydantic import BaseModel

from NL import query_claude, run_transformer
from lean import query_aristotle, query_transformer
from verify import verify_lean_file, verify_equality
from logger import get_logger

from transformers.utils import logging
logging.set_verbosity_error()

import os

provablyAPI = FastAPI()

# Define request body schema
class NLQuery(BaseModel):
    query: str
    model: str

class VerifyQuery(BaseModel):
    proof: str
    model: str
    lean_attempts: int
    claude_fix_this: bool


@provablyAPI.post("/nl/")
async def nl_solution(nlquery: NLQuery):
    logger = get_logger() 
    
    logger.info(nlquery.query)
    
    if "claude" in nlquery.model:
        response = query_claude(nlquery.query, nlquery.model)
    else:
        response = run_transformer(nlquery.query, nlquery.model)
    
    logger.info(response)
    
    return {"proof": response}


@provablyAPI.post("/lean-verify/")
async def create_item(verifyquery: VerifyQuery):
    with open(os.path.join(os.environ["SOLUTIONPATH"],"solution.lean"), "w") as file:
        file.write("")
    
    logger = get_logger() 
    if verifyquery.model == "aristotle":
        query_aristotle(verifyquery.proof, logger=logger)
    else:
        query_transformer(verifyquery.proof, 
                          model_id=verifyquery.model, 
                          logger=logger, 
                          attempts=verifyquery.lean_attempts, 
                          claude_fix_this=verifyquery.claude_fix_this)

    NL_correctness = verify_equality(verifyquery.proof)
    return {"valid": NL_correctness and verify_lean_file(os.path.join(os.environ["SOLUTIONPATH"],"solution.lean"))}
