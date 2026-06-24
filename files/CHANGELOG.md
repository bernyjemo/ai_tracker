# 📋 Changelog

All notable updates to the AI Model Performance Tracker are documented here.

---

## [2.0.0] — June 2026

### 🆕 New Models Added (8)

| Model | Provider | Release Date | Cost (Input/1M) |
|-------|----------|-------------|-----------------|
| GPT-5 | OpenAI | Aug 2025 | $1.25 |
| o3 | OpenAI | Apr 2025 | $2.00 |
| Claude Opus 4.5 | Anthropic | Nov 2025 | $5.00 |
| Claude Sonnet 4.5 | Anthropic | Oct 2025 | $3.00 |
| Gemini 2.5 Pro | Google DeepMind | Mar 2025 | $2.00 |
| Llama 4 Maverick | Meta AI | Apr 2025 | Free (open weights) |
| DeepSeek R1 | DeepSeek | Jan 2025 | $0.14 |
| Grok 3 | xAI | Feb 2025 | $3.00 |

**Total models: 15 → 23**

---

### 🆕 New Benchmarks Added (3)

| Benchmark | Category | What it measures |
|-----------|----------|-----------------|
| GPQA Diamond | Reasoning | PhD-level science questions in biology, chemistry and physics — Google-proof |
| AIME 2025 | Math | American Invitational Mathematics Examination — competition-level math |
| SWE-bench Verified | Coding | Real GitHub issues models must fix end-to-end |

**Total benchmarks: 8 → 11**

#### Why new benchmarks?
The original benchmarks (MMLU, GSM8K, HumanEval) are now **saturated** — every frontier model scores 90%+ so they no longer differentiate between models. The field has moved to harder tests. This shift is visible in the heatmap: old models have empty cells on the right side because they were never tested on the harder benchmarks.

---

### 🆕 New Charts Added (5)

| Chart | File | Description |
|-------|------|-------------|
| Old vs New per Provider | `05_old_vs_new_per_provider.png` | Side-by-side comparison of each provider's old and new models |
| 2025 Leaderboard | `06_new_leaderboard.png` | Ranks only 2025 frontier models |
| 2025 Heatmap | `07_new_heatmap.png` | New models across GPQA Diamond, AIME 2025, SWE-bench |
| 2025 Cost vs Performance | `08_new_cost_vs_performance.png` | Value analysis for new generation models |
| 2025 Open vs Proprietary | `09_new_open_vs_closed.png` | Open-weight vs proprietary on harder benchmarks |

**Total charts: 4 → 9**

The headline new chart is the **All Models × All Benchmarks Heatmap** (`02_benchmark_heatmap.png`) — updated to show all 23 models across all 11 benchmarks with a dashed line separating old and new benchmarks.

---

### 🔍 Key Findings from the Update

- **Claude Opus 4.5 leads real-world coding** — 80.9% on SWE-bench Verified, the highest of any model tested
- **GPT-5 leads competition math** — 94.6% on AIME 2025 without tools
- **DeepSeek R1 is the biggest surprise** — 79.8% on AIME 2025 at only $0.14/1M tokens, matching models that cost 35× more
- **Benchmark saturation is real** — MMLU and GSM8K scores are now clustered at 88–92% for all frontier models, making them poor discriminators
- **Open source gap widens on coding** — Llama 4 Maverick scores only 32.4% on SWE-bench vs Claude Opus 4.5's 80.9%, showing proprietary models still lead on complex agentic tasks

---

### 🛠️ Technical Changes

- Added `DeepSeek` as a new provider (China, 2023, open source)
- Updated `analysis.py` to generate 9 charts instead of 4
- Updated benchmark heatmap to show old vs new benchmarks separated by a dashed line
- Fixed git configuration to use VS Code as default editor
- Removed `charts/` from `.gitignore` so charts are now visible on GitHub

---

## [1.0.0] — June 2026

### Initial release

- 15 AI models from OpenAI, Anthropic, Google, Meta, Mistral, and xAI
- 8 benchmarks: MMLU, HumanEval, GSM8K, MATH, TruthfulQA, HellaSwag, MBPP, ARC-C
- 4 charts: overall leaderboard, benchmark heatmap, cost vs performance, open vs proprietary
- Full ETL pipeline with psycopg2 and pandas
- PostgreSQL schema with normalised tables and v_scores view
- 10 SQL analysis queries using window functions (RANK, LAG)
