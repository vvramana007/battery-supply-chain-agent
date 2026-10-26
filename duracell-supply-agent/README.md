# 🔋 Battery Supply Chain AI Agent

An end-to-end AI agent that answers plain-English questions about battery
inventory, orders, shipments, and company policies — grounded in a SQL database
and internal SOP documents, with role-based security and a web UI.

Built as a hands-on learning project to practice the full **Forward Deployed
Engineer** workflow: turning a real business problem into a working, deployed
AI solution.

<!-- Add your live demo link here once deployed on Streamlit Cloud -->
**🔗 Live demo:** _coming soon_
**📸 Screenshot:** _add a screenshot of the app here_

---

## What it does

Ask it questions like:
- *"Which products are at risk of running out?"*
- *"Is order ORD-1027 delayed?"*
- *"How fast must we restock Procell items?"* (answered from the SOP, with citations)
- *"What's our cost on Coppertop AA?"* → refused for Analysts (role-based access)

The agent reads the question, picks the right tool(s), queries live data, and
answers — showing which tools it used so the answer is transparent and trusted.

---

## Architecture

```
          ┌─────────────────────────────────────────────┐
          │              Streamlit web UI                │  role selector + audit log
          └───────────────────────┬─────────────────────┘
                                   │
                        ┌──────────▼───────────┐
                        │   LangGraph agent     │  think → act → look → repeat
                        │   (Claude as the LLM) │
                        └──────────┬───────────┘
                                   │ chooses tools
             ┌─────────────────────┼─────────────────────┐
             ▼                     ▼                     ▼
      ┌────────────┐       ┌──────────────┐      ┌──────────────┐
      │ SQL tools  │       │  RAG search  │      │ role + audit │
      │ (SQLite)   │       │  (ChromaDB)  │      │  (security)  │
      └────────────┘       └──────────────┘      └──────────────┘
```

---

## Key features

| Feature | How it's done |
|--------|----------------|
| Answers from live data | SQL tools over a modeled supply-chain database |
| Grounded, cited answers | RAG over SOP documents (ChromaDB + embeddings) |
| Role-based access control | Analysts can't see cost/margin data; Managers can |
| Audit logging | Every question recorded (who, when, what) |
| Multi-step reasoning | LangGraph agent chains tools automatically |
| Usable by non-engineers | Streamlit web UI showing the tools it used |
| Production-ready path | Dockerfile + GitHub Actions CI pipeline |

## Tech stack

Python · SQLite · Claude (Anthropic API) · LangGraph · ChromaDB · Streamlit ·
Docker · GitHub Actions

---

## Run it locally

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Build the database
python setup_database.py

# 3. Add your Claude API key
cp .env.example .env        # then paste your key into .env

# 4. Launch the web app
streamlit run app.py
```

You can also run each piece on its own:
```bash
python tools.py             # test the database tools (no API key needed)
python phase3_rag.py        # test the RAG document search
python phase4_security.py   # see role-based access + audit logging
python agent.py "Which items are low and is order ORD-1027 delayed?"
```

---

## Project structure

```
setup_database.py     Synthetic data + SQLite database
phase3_rag.py         RAG over the SOP document
phase4_security.py    Role-based access control + audit log
tools.py              The agent's tools (functions over the data)
agent.py              The LangGraph agent brain
app.py                Streamlit web UI
Dockerfile            Container recipe
.github/workflows/    CI pipeline
docs/                 SOP document + business case
data/                 Generated CSV data
```

> All data in this project is synthetic and for demonstration only.

## Deployment

See [`DEPLOY.md`](DEPLOY.md) for two paths: a quick live version on Streamlit
Community Cloud, and the Docker-to-cloud-server approach used in production.
