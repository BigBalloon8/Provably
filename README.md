# Provably

## Setup

1. Install lean4
2. Run: `pip install torch transformers aristotlelib`
3. If using Claude or aristotle add keys to environment variables
```bash
export ANTHROPIC_API_KEY=sk-ant-api03-...
export ARISTOTLE_API_KEY=arstl_...
```

## Running Provably

```
git clone https://github.com/BigBalloon8/Provably.git
cd Provably
export SOLUTIONPATH=$PWD/Solution
lake build
python AI/main.py
```
The above code will ask for a user math problem, then generate a valid proof as the response, the equivalent lean script will be written to TestProj/solution.lean


```
python AI/main.py --help
usage: main.py [-h] [--nl NL] [--lean LEAN] [--max_attempts MAX_ATTEMPTS]

options:
  -h, --help            show this help message and exit
  --nl NL               Model to use for natural language generation
  --lean LEAN           Model to use for Lean generation
  --max_attempts MAX_ATTEMPTS
                        The maximum number of repeats to do until solution is found defaults to infinite
```

Any model on the huggingface hub can be passed for the natural language generation of the proof, by default claude is used. For lean generation we currently support aristotle and deepseek.