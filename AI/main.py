from NL import query_claude
from lean import query_aristotle, query_transformer, run_transformer_lean
from verify import verify_lean_file, verify_equality
from logger import get_logger

from transformers.utils import logging
logging.set_verbosity_error()

import os
import argparse

if os.path.exists("AI/.env"):
    import dotenv
    dotenv.load_dotenv("AI/.env")

def main(args):
    with open("Solution/solution.lean", "w") as file:
        file.write("")
    
    logger = get_logger()
    LEAN_ATTEMPTS=3

    if "ANTHROPIC_API_KEY" not in os.environ.keys() and args.nl == "anthropic":
        os.environ["ANTHROPIC_API_KEY"] = input("Enter Claude API Key:").strip()    
    if "ARISTOTLE_API_KEY" not in os.environ.keys() and args.lean == "aristotle":
        os.environ["ARISTOTLE_API_KEY"] = input("Enter Aristotle API Key:").strip()

    # Query
    query = input("Enter Maths Claim: ")
    if query == "".strip(" "):
        #query = r"Let G be a group and H, K be two subgroups of G with |H| = 65 and|K| = 56. Prove that H ∩ K = {e}."
        #query = r"Let x be a real number with 0 < x < 1 and let (a_n)n∈N be a sequence of positive real numbers such that, for all n, \frac{a_{n+1}}{a_n}<x. Prove the series \sum^\infty_{n=1}a_n converges."
        #query = r"Let G be a group, prove the following are equivalent\n1. G is abelian\n2. For all g,h \in G $(g * h)^2 = g^2 * h^2$"
        query = r"Let x be a non-negative real number and n be a non-negative integer, prove (1 + x)^n ≥ 1 + nx"
        print(f"No user question given using: {query}")
    
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
        NL_correctness = verify_equality(response, "claude-opus-4-6")
        
    print(response)


    #print(get_proof("Let G be a group and H, K be two subgroups of G with |H| = 65 and|K| = 56. Prove that H ∩ K = {e}."))

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--nl", default="anthropic", help="Model to use for natural language generation")
    parser.add_argument("--lean", default="deepseek", help="Model to use for Lean generation")
    parser.add_argument("--max_attempts", default=float("inf"), help="The maximum number of repeats to do until solution is found defaults to infinite")
    main(parser.parse_args())