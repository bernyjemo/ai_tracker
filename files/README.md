# AI Model Performance Tracker

Track, compare, and analyse AI model benchmark scores over time using Python and PostgreSQL.

## What it does

- Stores structured data on AI models (provider, cost, release date, parameters)
- Records scores across benchmarks: MMLU, HumanEval, GSM8K, MATH, TruthfulQA, and more
- ETL pipeline to load data from CSV files or the Hugging Face leaderboard
- SQL analysis queries for leaderboards, cost/performance tradeoffs, provider comparisons
- Matplotlib/Seaborn charts ready to embed in a portfolio or report

---

## Project structure

```
ai_tracker/
├── sql/
│   ├── 01_schema.sql          # All tables, indexes, and the v_scores view
│   ├── 02_seed_data.sql       # Real model data to get started immediately
│   └── 03_analysis_queries.sql # 10 analytical SQL queries with comments
├── etl/
│   └── etl_pipeline.py        # Extract → Clean → Load pipeline
├── analysis/
│   └── analysis.py            # Runs queries and saves charts to charts/
├── data/
│   └── sample_scores.csv      # Sample CSV for testing the ETL
└── README.md
```

---

## Setup

### 1. Prerequisites

- Python 3.10+
- PostgreSQL 14+

### 2. Create the database

```bash
psql -U postgres -c "CREATE DATABASE ai_tracker;"
psql -U postgres -d ai_tracker -f sql/01_schema.sql
psql -U postgres -d ai_tracker -f sql/02_seed_data.sql
```

### 3. Install Python dependencies

```bash
pip install psycopg2-binary pandas requests matplotlib seaborn python-dotenv
```

### 4. Configure your connection

Create a `.env` file in the project root:

```env
DB_HOST=localhost
DB_PORT=5432
DB_NAME=ai_tracker
DB_USER=postgres
DB_PASSWORD=yourpassword
```

### 5. Run the ETL pipeline

```bash
# Load from CSV
python etl/etl_pipeline.py data/sample_scores.csv

# Or attempt Hugging Face leaderboard fetch
python etl/etl_pipeline.py
```

### 6. Run analysis and generate charts

```bash
python analysis/analysis.py
# Charts saved to analysis/charts/
```

### 7. Run SQL queries interactively

```bash
psql -U postgres -d ai_tracker -f sql/03_analysis_queries.sql
```

---

## Key SQL concepts demonstrated

| Query | Concept |
|-------|---------|
| Overall leaderboard | `AVG`, `HAVING`, `GROUP BY` |
| Rank per benchmark | `RANK() OVER (PARTITION BY ...)` |
| Score improvement over time | `LAG() OVER (ORDER BY release_date)` |
| Cost vs performance | `CASE WHEN`, computed columns |
| Missing benchmark gaps | `CROSS JOIN` + `LEFT JOIN` pattern |
| Category strengths | CTEs + conditional aggregation |

---

## Data sources

| Source | URL |
|--------|-----|
| Hugging Face Open LLM Leaderboard | https://huggingface.co/spaces/open-llm-leaderboard/open_llm_leaderboard |
| Papers With Code | https://paperswithcode.com/sota |
| Artificial Analysis | https://artificialanalysis.ai |
| LMSYS Chatbot Arena | https://chat.lmsys.org |

---

## Portfolio talking points

- Designed a **normalised PostgreSQL schema** with foreign keys, indexes, and a view
- Built an **ETL pipeline** with data validation, deduplication, and error logging
- Used **window functions** (`RANK`, `LAG`) for time-series and comparative analysis
- Produced **data visualisations** showing cost/performance tradeoffs across 15 models
- Identified that open-weight models (Llama 3.1 405B) match proprietary models on MMLU/GSM8K
