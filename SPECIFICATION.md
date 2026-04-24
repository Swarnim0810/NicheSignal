# Technical Specification: NicheSignal AI Pipeline

## 1. Task Decomposition

The system is decomposed into five specialized agents (nodes) operating within a shared state graph. This modular approach ensures high reliability and allows for targeted optimization of each stage.

### Node 1: Trend Scout (`trend_scout`)
- **Responsibility:** Aggregating raw signals from high-signal community sources.
- **Tools:** Concurrent scrapers for Hacker News, GitHub Trending, Stack Overflow, Dev.to, and Google Trends.
- **Rationale:** Using specialized scrapers instead of generic search ensures we capture "developer intent" rather than just generic SEO content.

### Node 2: Content Analyzer (`content_analyzer`)
- **Responsibility:** Reducing noise and identifying themes.
- **Methodology:** Semantic Embeddings using `sentence-transformers`. It clusters raw signals and filters for "high-density" topics that appear across multiple platforms.

### Node 3: Deep Researcher (`deep_researcher`)
- **Responsibility:** Context extraction.
- **Tools:** BeautifulSoup + Requests (Custom Extraction Engine).
- **Rationale:** We use custom extraction to bypass generic search noise and directly ingest the technical documentation or discussion threads of the identified URLs. This provides a "ground truth" for the synthesizer.

### Node 4: Brief Synthesizer (`brief_synthesizer`)
- **Responsibility:** Creative compilation.
- **LLM:** Groq LLaMA 3.3-70B.
- **Output:** A structured JSON object containing the Gap Summary, Technical Roadmap, and Hook ideation.

### Node 5: Strict Evaluator (`strict_evaluator`)
- **Responsibility:** Quality control (LLM-as-a-Judge).
- **LLM:** Groq LLaMA 3.1-8B.
- **Mechanism:** Evaluates the brief on 6 dimensions (Actionability, Novelty, Moat, etc.). 
- **Cycle:** If the score is below 72%, it generates a critique and sends the state back to the Synthesizer for revision.

---

## 2. State Management (LangGraph)

The graph uses a persistent `AgentState` schema to track:
- `raw_signals`: The initial pool of data.
- `content_gaps`: The identified opportunities.
- `research_context`: The extracted text from source URLs.
- `brief`: The current draft of the creator brief.
- `evaluation`: The scoring and critique from the judge.

---

## 3. Infrastructure & Security

- **Authentication:** Firebase Auth (Google OAuth) manages user identity on the frontend.
- **Persistence:** Each user has a dedicated sub-collection in **Cloud Firestore** (`users/{uid}/history`), ensuring data isolation and secure retrieval.
- **Backend Secrets:** API keys and Service Account JSONs are managed via Streamlit Secrets and `.env` files (excluded from Git).
