from NL import query_claude, get_proof
from lean import query_aristotle, verify_lean_file, query_deepseek

import os
import asyncio

def main(): 
    if "ANTHROPIC_API_KEY" not in os.environ.keys():
        os.environ["ANTHROPIC_API_KEY"] = input("Enter Claude API Key:").strip()    
    if "ARISTOTLE_API_KEY" not in os.environ.keys():
        os.environ["ARISTOTLE_API_KEY"] = input("Enter Aristotle API Key:").strip()

    # Query
    query = input("Enter Maths Claim: ")
    if query == "".strip(" "):
        query = r"Let G be a group and H, K be two subgroups of G with |H| = 65 and|K| = 56. Prove that H ∩ K = {e}."
    
    # NL
    response = query_claude(get_proof(query))
    # print(response)

    # LEAN
    #query_aristotle(response)
    query_deepseek(response)
    #exit()

    # Is valid
    while not verify_lean_file("/home/crae/projects/lean_ai/TestProj/TestProj/solution.lean"):
        # repeat if not
        response = query_claude(get_proof(query))
        # print(response)
        asyncio.run(query_aristotle(response))
    
    print(response)


    #print(get_proof("Let G be a group and H, K be two subgroups of G with |H| = 65 and|K| = 56. Prove that H ∩ K = {e}."))

if __name__ == "__main__":
    main()