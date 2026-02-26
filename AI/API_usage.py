import requests

def main(address:str):
    query = r"Let G be a group, prove the following are equivalent\n1. G is abelian\n2. For all g,h \in G $(g * h)^2 = g^2 * h^2$"
    NL_model = "claude-sonnet-4-5-20250929"

    lean_model = "deepseek-ai/DeepSeek-Prover-V2-7B"
    lean_attempts = 3
    claude_fix_this = False


    nl_data = {
        "query": query,
        "model": NL_model
    }
    response = requests.post(address + "/nl/", json=nl_data)

    lean_data = {
        "proof": response["proof"],
        "model": lean_model,
        "lean_attempts": lean_attempts,
        "claude_fix_this": claude_fix_this 
    }
    
    lean_correct = requests.post(address + "/lean-verify/", json=lean_data)
    while not lean_correct["valid"]:
        response = requests.post(address + "/nl/", json=nl_data).json()
        lean_data = {
            "proof": response["proof"],
            "model": lean_model,
            "lean_attempts": lean_attempts,
            "claude_fix_this": claude_fix_this 
        }
        lean_correct = requests.post(address + "/lean-verify/", json=lean_data)
    
    print(response["proof"])

if __name__ == "__main__":
    host = "http://127.0.0.1:8000"
    main(host)