from dotenv import load_dotenv
load_dotenv()
from state import NicheSignalState
from agents.trend_scout import trend_scout

state = {'query': 'local LLMs', 'raw_signals': [], 'errors': [], 'status': ''}
result = trend_scout(state)
print(result['status'])
for s in result['raw_signals']:
    print(f"{s['source']:<25} score={s['score']:.2f}  {s['title'][:55]}")
