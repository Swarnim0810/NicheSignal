# 📡 NicheSignal v5

**NicheSignal** is a multi-agent AI pipeline designed to automate content gap intelligence for YouTube creators. By scraping the web for trending developer data, clustering the results, deep-researching high-value URLs, and synthesizing a structured brief, the pipeline identifies topics the audience is searching for that aren't being well-served by existing content.

## ✨ Features

- **Multi-Source Data Collection:** Concurrently scouts Hacker News, GitHub Trending, Stack Overflow, Dev.to, Lobsters, and Google Trends.
- **Semantic Clustering:** Groups signals using `sentence-transformers` (`all-MiniLM-L6-v2`) to identify the strongest overlapping topics.
- **Deep Web Research:** Automatically fetches and extracts the text payload of the most valuable source URLs.
- **Groq-Powered Brief Synthesis:** Uses `llama-3.3-70b-versatile` to generate highly specific, structured content briefs (Gap Summary, Technical Roadmap, Hooks).
- **LLM-as-a-Judge Evaluation:** Uses `llama-3.1-8b-instant` as a strict evaluator, scoring the generated brief on a 6-dimension rubric (Producibility, Search Demand, Audience Fit, Moat, Actionability, Novelty).
- **Dark Editorial UI:** A premium Streamlit dashboard with a sidebar query history, live intelligence feed, and a detailed Plotly scorecard.

## 🏗️ Architecture

The pipeline is orchestrated entirely with **LangGraph**, routing through the following state nodes:

1. **`trend_scout`**: Gathers realtime signals concurrently.
2. **`content_analyzer`**: Runs semantic clustering to filter out noise.
3. **`deep_researcher`**: Fetches the top URL contexts via BeautifulSoup.
4. **`brief_synthesizer`**: Compiles all context into a targeted JSON brief.
5. **`strict_evaluator`**: Judges the brief against the threshold (72%). Triggers a retry loop (max 3 revisions) with critique feedback if the brief fails.

## 🚀 Getting Started

### Prerequisites
- Python 3.10+
- A [Groq API Key](https://console.groq.com/)

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
   Create a `.env` file in the root directory:
   ```env
   GROQ_API_KEY=your_api_key_here
   ```

### Running Locally

To run the Streamlit UI:
```bash
streamlit run app.py
```

To run a headless terminal test:
```bash
python test_pipeline.py
```

## ☁️ Deployment

This application is configured for 1-click deployment on **Railway**.
1. Create a new Railway project from this repository.
2. The included `Procfile` will automatically configure the server commands (`web: streamlit run app.py --server.port $PORT --server.address 0.0.0.0`).
3. Add your `GROQ_API_KEY` to the Railway Environment Variables.
