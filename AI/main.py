from NL import query_claude, get_proof, run_transformer
from lean import query_aristotle, verify_lean_file, query_deepseek, run_transformer_lean

import os
import asyncio
import argparse
import logging


def main(args): 

    logging.Logger()

    with open("Solution/solution.lean", "w") as file:
        file.write("")

    if "ANTHROPIC_API_KEY" not in os.environ.keys():
        os.environ["ANTHROPIC_API_KEY"] = input("Enter Claude API Key:").strip()    
    if "ARISTOTLE_API_KEY" not in os.environ.keys():
        os.environ["ARISTOTLE_API_KEY"] = input("Enter Aristotle API Key:").strip()

    # Query
    query = input("Enter Maths Claim: ")
    if query == "".strip(" "):
        query = r"Let G be a group and H, K be two subgroups of G with |H| = 65 and|K| = 56. Prove that H ∩ K = {e}."
    
    # NL
    if args.nl == "anthropic":
        response = query_claude(get_proof(query))
    else: # default to a trans
        response = run_transformer(query, args.nl)
    # print(response)

    # LEAN
    if args.lean == "deepseek":
        query_deepseek(response)
    elif args.lean == "aristotle":
        query_aristotle(response)
    else:
        raise ValueError("Models Supported for LEAN are: (query_claude)")


    # Is valid
    attempts = 1
    while not verify_lean_file("Solution/solution.lean"):
        if attempts >= args.max_attempts:
            raise RecursionError("Solution not found")
        attempts += 1
        # NL
        if args.nl == "anthropic":
            response = query_claude(query)
        else:
            run_transformer_lean(query, args.nl)

        # LEAN
        if args.lean == "deepseek":
            query_deepseek(response)
        elif args.lean == "aristotle":
            query_aristotle(response)
    
    print(response)


    #print(get_proof("Let G be a group and H, K be two subgroups of G with |H| = 65 and|K| = 56. Prove that H ∩ K = {e}."))

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--nl", default="anthropic", help="Model to use for natural language generation")
    parser.add_argument("--lean", default="deepseek", help="Model to use for Lean generation")
    parser.add_argument("--max_attempts", default=float("inf"), help="The maximum number of repeats to do until solution is found defaults to infinite")
    main(parser.parse_args())