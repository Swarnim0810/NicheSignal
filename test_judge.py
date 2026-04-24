from dotenv import load_dotenv
load_dotenv()
from agents.trend_scout import trend_scout
from agents.content_analyzer import content_analyzer
from agents.brief_synthesizer import brief_synthesizer
from agents.quality_auditor import quality_auditor
from agents.llm_judge import llm_judge

state = {'query': 'local LLMs', 'raw_signals': [], 'errors': [], 'status': '', 'revision_count': 0}
state = trend_scout(state)
state = content_analyzer(state)
state = brief_synthesizer(state)
state = quality_auditor(state)
state = llm_judge(state)

print(state['status'])
js = state.get('judge_score')
if js:
    print(f"Overall:      {js['overall']:.2f}")
    print(f"Specificity:  {js['specificity']:.2f}")
    print(f"Actionability:{js['actionability']:.2f}")
    print(f"Evidence:     {js['evidence_strength']:.2f}")
    print(f"Clickability: {js['clickability']:.2f}")
    print(f"Search align: {js['search_alignment']:.2f}")
    print(f"Novelty:      {js['novelty']:.2f}")
    print(f"Weakest:      {js['weakest_dimension']}")
    print(f"Rationale:    {js['rationale']}")
    print(f"Recommend:    {js['recommendation']}")
else:
    print("Errors:", state['errors'])