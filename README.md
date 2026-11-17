# GTM Intelligence Lab

A portfolio project that combines marketing analytics, marketing data science, and product marketing to estimate customer value, segment buying behavior, and propose go-to-market recommendations.

## Problem

Most e-commerce teams have customer transaction data, but they still struggle to connect that data to channel allocation, customer value, and positioning decisions. In real environments, the business question is not only "who bought?" but also:

- Which customer groups are most valuable?
- Which segments are most likely to respond to different channels?
- How should we allocate budget across acquisition and retention strategies?
- What message should we use for each segment?

This project turns raw transaction data into a functional marketing decision workflow using a simple, explainable analytical stack.

## Approach

The application follows a four-layer flow:

1. Data foundation
   - Load real Olist-like data if available
   - Otherwise generate a deterministic synthetic sample for local testing
   - Build a clean customer-level table with lifetime metrics

2. Business analytics
   - Calculate revenue, average order value, repeat purchase rate, CAC, ROAS, and payback
   - Treat marketing spend as simulated planning assumptions, not observed data

3. Data science
   - Create RFM features on customer behavior
   - Cluster customers using K-means
   - Select K with elbow and silhouette diagnostics
   - Estimate segment-level LTV with a transparent, explainable formula

4. Product marketing
   - Generate a GTM brief using Anthropic when an API key is available
   - Provide a fallback local brief when the key is not configured
   - Simulate channel reallocation and estimate revenue/LTV impact under explicit assumptions

## Repository structure

```text
.
├── app/
│   ├── __init__.py
│   └── Home.py
├── src/
│   ├── data/
│   ├── features/
│   ├── llm/
│   ├── models/
│   └── simulation/
├── data/
│   ├── raw/
│   └── processed/
├── docs/
│   └── decisions.md
├── tests/
├── .env.example
├── .streamlit/
│   └── config.toml
├── app.py
├── requirements.txt
├── README.md
└── .gitignore
```

## Technical decisions

The project intentionally prioritizes simplicity and explainability:

- RFM + K-means: easy to explain in marketing interviews and familiar to stakeholders
- Transparent LTV estimator: better for a portfolio project than a more opaque advanced model
- Simulated media spend: realistic for an e-commerce portfolio without hidden proprietary channel data
- Anthropic integration: optional and safe; the app has a local fallback for demos and offline use

A detailed explanation of the main analytical decisions is available in [docs/decisions.md](docs/decisions.md).

## Limitations

This project is designed for portfolio and learning purposes, not for production-grade marketing attribution.

- The marketing spend file is simulated, not observed from actual ad platforms
- CAC, ROAS, and payback are scenario-based planning metrics
- The LTV model is simple and explainable, not a full probabilistic customer lifetime engine
- The GTM brief is a strategic draft and should be reviewed by a marketer or PM before execution
- Segment assignments are statistical, not a substitute for business judgment

## Local setup

```bash
cd "C:\Users\castr\OneDrive\Documentos\GTM Intelligence LAB"
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py
```

If you want to enable the Anthropic-generated GTM brief, create a `.env` file from the example and add your key:

```bash
copy .env.example .env
```

Example:

```env
ANTHROPIC_API_KEY=your_api_key_here
ANTHROPIC_MODEL=claude-sonnet-4-6
```

## Testing

```bash
python -m pytest tests -q
```

## Save and publish

The local project and GitHub publishing steps are described in [docs/upload-to-github.md](docs/upload-to-github.md). Raw CSVs, processed tables, `.env`, and Streamlit secrets are excluded from Git by [.gitignore](.gitignore); the app generates its synthetic demo data when needed.

An interview-ready two-minute pitch in Portuguese and English is available in [docs/interview-pitch.md](docs/interview-pitch.md).

## Streamlit Community Cloud deployment

This project is prepared for Streamlit Community Cloud with:

- a root-level `app.py` entrypoint
- `requirements.txt` at the repository root
- `.streamlit/config.toml` for container settings

Deployment steps:

1. Push this repository to GitHub
2. Open Streamlit Community Cloud
3. Create a new app from the repo
4. Select the branch and main app file: `app.py`
5. Confirm the app starts successfully
6. If needed, add `ANTHROPIC_API_KEY` under the app's Secrets settings; do not commit it to GitHub

## Screenshots

Add screenshots of the app here as the project matures, for example:

- Segment dashboard
- RFM clustering view
- GTM brief output
- Budget simulator panel

## Deployment link

Add the public Streamlit link here once deployed.

Example:

https://your-project-name.streamlit.app

## Contact

This project is part of a portfolio for roles in marketing analytics, marketing data science, product management, and product marketing.
