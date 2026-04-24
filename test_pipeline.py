# test_pipeline.py
import sys
import os
import json
import time
from dotenv import load_dotenv

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
load_dotenv(dotenv_path=os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env"), override=True)

from pipeline import run_pipeline
from event_bus import get_events

def main():
    query = "local llm optimization"
    print(f"Starting pipeline test for query: '{query}'")
    start_time = time.time()
    
    state = run_pipeline(query)
    
    elapsed = time.time() - start_time
    print("\n" + "="*50)
    print("PIPELINE EXECUTION COMPLETE")
    print(f"Total time: {elapsed:.2f} seconds")
    print("="*50 + "\n")
    
    # Print Brief
    brief = state.get("brief")
    if brief:
        print("FINAL BRIEF (JSON):")
        print(json.dumps(brief, indent=2))
    else:
        print("NO BRIEF GENERATED.")
        
    # Print Evaluation
    evaluation = state.get("evaluation")
    if evaluation:
        print("\nEVALUATION SCORES:")
        print(json.dumps(evaluation, indent=2))
    else:
        print("\nNO EVALUATION AVAILABLE.")

    print("\nEVENT LOG:")
    for evt in state.get("log_events", []):
        print(f"- {evt}")

if __name__ == "__main__":
    main()
