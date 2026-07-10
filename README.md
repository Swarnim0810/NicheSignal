# NicheSignal v5
**Created by Swarnim & Mahi**

**NicheSignal** is a multi-agent AI pipeline designed to automate content gap intelligence for YouTube creators. By scraping the web for trending developer data, clustering the results, deep-researching high-value URLs, and synthesizing a structured brief, the pipeline identifies topics the audience is searching for that aren't being well-served by existing content.

### 🚀 Live Demo
[View Live on Streamlit Cloud](https://nichesignal-f2uh9zfltdcsnbo28tp4p5.streamlit.app/)

### 📺 Video Walkthrough
[Watch the Demo on Loom](https://www.loom.com/share/1888d82059ee40a78d2d6a8ed47e0805)

## ✨ Features

- **Google Authentication:** Secure sign-in using Firebase Auth (Google Provider).
- **Per-User History:** Queries and briefs are saved to individual user collections in Cloud Firestore.
- **Multi-Source Data Collection:** Concurrently scouts Hacker News, GitHub Trending, Stack Overflow, Dev.to, Lobsters, and Google Trends.
- **Semantic Clustering:** Groups signals using `sentence-transformers` (`all-MiniLM-L6-v2`) to identify the strongest overlapping topics.
- **Deep Web Research:** Automatically fetches and extracts the text payload of the most valuable source URLs.
- **RAG-Powered Deduplication:** Retrieves semantically similar past briefs from query history using vector embeddings, ensuring each new brief proposes a differentiated content angle rather than repeating past suggestions.
- **Groq-Powered Brief Synthesis:** Uses `llama-3.1-8b-instant` to generate highly specific, structured content briefs (Gap Summary, Technical Roadmap, Hooks) — now augmented with historical intelligence from RAG.
- **LLM-as-a-Judge Evaluation:** Uses `llama-3.1-8b-instant` as a strict evaluator, scoring the generated brief on a 6-dimension rubric.
- **Dark Editorial UI:** A premium Streamlit dashboard with a sidebar query history, live intelligence feed, and a detailed Plotly scorecard.

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         NicheSignal Pipeline                            │
│                        (LangGraph Orchestration)                        │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│   ┌──────────────┐    ┌──────────────────┐    ┌──────────────────┐     │
│   │  Trend Scout  │───▶│ Content Analyzer  │───▶│ Deep Researcher  │     │
│   │              │    │                  │    │                  │     │
│   │ • Hacker News│    │ • all-MiniLM-L6  │    │ • URL fetching   │     │
│   │ • GitHub     │    │ • Cosine cluster  │    │ • Text extraction│     │
│   │ • Stack OF   │    │ • Momentum score  │    │ • Sentence trunc │     │
│   │ • Dev.to     │    │                  │    │                  │     │
│   │ • Lobsters   │    └──────────────────┘    └────────┬─────────┘     │
│   │ • G. Trends  │                                     │               │
│   └──────────────┘                                     ▼               │
│                                                ┌──────────────────┐     │
│                                                │  RAG Retriever   │     │
│                                                │                  │     │
│                                                │ • Vector search  │     │
│                                                │ • Past briefs    │     │
│                                                │ • Deduplication  │     │
│                                                │ • 0 LLM tokens   │     │
│                                                └────────┬─────────┘     │
│                                                         ▼               │
│   ┌──────────────────┐    ┌──────────────────────────────────────┐     │
│   │ Strict Evaluator │◀───│        Brief Synthesizer             │     │
│   │                  │    │                                      │     │
│   │ • 6-dim rubric   │    │ • Groq llama-3.1-8b-instant         │     │
│   │ • Pass threshold │    │ • 9-field JSON brief                 │     │
│   │   ≥ 0.72        │    │ • RAG context: angles to avoid       │     │
│   │ • Weighted score │    │ • Retry-aware (feeds back critique)  │     │
│   └────────┬─────────┘    └──────────────────────────────────────┘     │
│            │                                         ▲                  │
│            ▼                                         │                  │
│   ┌─────────────────┐                               │                  │
│   │  Pass? ──▶ END  │    ┌────────────────────┐     │                  │
│   │  Fail? ──▶──────│───▶│ Increment Revision │─────┘                  │
│   │  (max 2 retries)│    └────────────────────┘                        │
│   └─────────────────┘                                                   │
│                                                                         │
├─────────────────────────────────────────────────────────────────────────┤
│  RAG Store (rag_store.py)                                               │
│  • Indexes query_history.json at startup (passed=True entries only)     │
│  • all-MiniLM-L6-v2 embeddings, numpy cosine similarity                │
│  • Self-improving: grows with each successful pipeline run              │
└─────────────────────────────────────────────────────────────────────────┘
```

See [PROBLEM_STATEMENT.md](./PROBLEM_STATEMENT.md) for the project background and [SPECIFICATION.md](./SPECIFICATION.md) for the full technical breakdown.

## 📁 Project Structure

```
nichesignalv3/
├── app.py                     # Streamlit UI (dark editorial magazine theme)
├── pipeline.py                # LangGraph orchestration (6 nodes + revision loop)
├── state.py                   # TypedDict pipeline state schema
├── event_bus.py               # Real-time event logging for live feed
├── rag_store.py               # RAG vector store (indexes past briefs)
├── agents/
│   ├── trend_scout.py         # Multi-source web scraper (6 sources)
│   ├── content_analyzer.py    # Semantic clustering (all-MiniLM-L6-v2)
│   ├── deep_researcher.py     # URL content extraction
│   ├── rag_retriever.py       # RAG retrieval node (0 LLM tokens)
│   ├── brief_synthesizer.py   # Groq brief generation + RAG context
│   └── strict_evaluator.py    # LLM-as-a-Judge (6 dimensions)
├── auth_frontend/             # Firebase Auth component
├── assets/                    # Architecture diagram
├── test_rag.py                # RAG integration test suite (35 tests)
├── test_pipeline.py           # Pipeline integration tests
├── requirements.txt           # Python dependencies
└── .env                       # API keys (not committed)
```

## 🧠 RAG System

NicheSignal uses **Retrieval-Augmented Generation** to prevent the pipeline from suggesting content angles that have already been covered in past runs.

**How it works:**
1. At startup, `rag_store.py` builds a vector index over all past successful briefs from `query_history.json`
2. When a new query runs, `rag_retriever` finds the top-3 most semantically similar past briefs
3. These are injected into the `brief_synthesizer` prompt as "angles to avoid"
4. The LLM is instructed to aggressively differentiate from past suggestions

**Token cost:** ~120–180 tokens added to `brief_synthesizer` (well within the 8192-token window). The `rag_retriever` itself makes zero LLM calls — it's pure embedding similarity.

**Self-improving:** The index automatically grows as `query_history.json` accumulates new successful runs.

## 🚀 Getting Started

### Prerequisites
- Python 3.10+
- A [Groq API Key](https://console.groq.com/)
- A [Firebase Project](https://console.firebase.google.com/) (for Auth and Firestore)

### Installation

1. **Clone the repo**
   ```bash
   git clone https://github.com/Swarnim0810/NicheSignal.git
   cd NicheSignal
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set your environment variables**
   Create a `.env` file for local testing or use Streamlit Secrets for cloud deployment:
   ```toml
   GROQ_API_KEY="your_api_key"
   
   [firebase]
   type = "service_account"
   project_id = "..."
   private_key = "..."
   ...
   ```

### Running Locally

To run the Streamlit UI:
```bash
streamlit run app.py
```

### Running RAG Tests
```bash
python test_rag.py
```

## ☁️ Deployment

This application is deployed on **Streamlit Community Cloud**.
1. Connected via the `main` branch.
2. **Secrets:** Configured with `GROQ_API_KEY` and the `[firebase]` service account credentials.
3. **Requirements:** Automatically installs modules from `requirements.txt`.
