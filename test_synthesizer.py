from dotenv import load_dotenv
load_dotenv()
from agents.trend_scout import trend_scout
from agents.content_analyzer import content_analyzer
from agents.brief_synthesizer import brief_synthesizer

state = {'query': 'local LLMs', 'raw_signals': [], 'errors': [], 'status': ''}
state = trend_scout(state)
state = content_analyzer(state)
state = brief_synthesizer(state)

print(state['status'])
if state.get('brief'):
    b = state['brief']
    print(f"Title: {b['title']}")
    print(f"Hook: {b['hook'][:80]}")
    print(f"Angle: {b['angle'][:80]}")
    for e in b['evidence']:
        print(f"  Evidence: {e[:70]}")
else:
    print("Errors:", state['errors'])