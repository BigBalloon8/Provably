from NL import query_claude
from lean import query_aristotle, query_transformer, run_transformer_lean
from verify import verify_lean_file, verify_equality
from logger import get_logger

from transformers.utils import logging
logging.set_verbosity_error()

import os
import argparse
import json


if os.path.exists("AI/.env"):
    import dotenv
    dotenv.load_dotenv("AI/.env")

def get_solution(question, args):
    with open("Solution/solution.lean", "w") as f:
        f.write("")
    
    query = question["question_text"]

    logger = get_logger()
    LEAN_ATTEMPTS=3
    
    logger.info(query)

    NL_correctness = False

    # Is valid
    attempts = 1
    while not (verify_lean_file("Solution/solution.lean") and NL_correctness):
        if attempts > args.max_attempts:
            raise RecursionError("Solution not found")
        attempts += 1
        # NL
        if args.nl == "anthropic":
            response = query_claude(query)
        else:
            response = run_transformer_lean(query, args.nl)
        
        logger.info(response)

        # LEAN
        if args.lean == "aristotle":
            query_aristotle(response, logger=logger)
        elif args.lean == "deepseek":
            query_transformer(response, logger=logger, attempts=LEAN_ATTEMPTS)
        else:
            query_transformer(response, model_id= args.lean, logger=logger, attempts=LEAN_ATTEMPTS)

        # check lean and NL are the same
        NL_correctness = verify_equality(response)
    

    if os.path.exists("benchmark_solutions.json"):
        with open("benchmark_solutions.json", "r") as f:
            solutions = json.load(f)
    else:
        solutions = {}

    with open("Solution/solution.lean", "r") as f:
        lean4 = f.read()
        
    solutions[question["id"]] = {"NL": response, "lean": lean4}

    with open("benchmark_solutions.json", "w") as f:
        json.dump(solutions, f)

def main(args):
    file = os.path.join(os.path.dirname(__file__),"benchmark_questions.json")
    with open(file, "r") as f:
        questions = json.load(f)
    if os.path.exists("benchmark_solutions.json"):
        with open("benchmark_solutions.json", "r") as f:
            solutions = json.load(f)
    else:
        solutions = {}
    for q in questions:
        if q["id"] not in solutions.keys():
            get_solution(q, args)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--nl", default="anthropic", help="Model to use for natural language generation")
    parser.add_argument("--lean", default="deepseek", help="Model to use for Lean generation")
    parser.add_argument("--max_attempts", default=float("inf"), help="The maximum number of repeats to do until solution is found defaults to infinite")
    main(parser.parse_args())