from dotenv import load_dotenv
load_dotenv()
from agents.trend_scout import trend_scout
from agents.content_analyzer import content_analyzer

state = {'query': 'local LLMs', 'raw_signals': [], 'errors': [], 'status': ''}
state = trend_scout(state)
state = content_analyzer(state)
print(state['status'])
print(f"Clusters: {len(state['clustered_signals'])}")
print(f"Top signals: {len(state['top_signals'])}")
for s in state['top_signals']:
    print(f"  {s['source']:<20} {s['title'][:60]}")
