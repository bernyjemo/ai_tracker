-- ============================================================
-- AI Model Performance Tracker — Key Analysis Queries
-- ============================================================
-- Run these against the v_scores view or raw tables.
-- Each query answers a real analytical question.
-- ============================================================


-- ── 1. LEADERBOARD ────────────────────────────────────────────────────────────
-- Who is #1 on each benchmark right now?
-- Uses RANK() window function partitioned by benchmark.

SELECT
    benchmark,
    benchmark_category,
    model_name,
    provider,
    score,
    RANK() OVER (PARTITION BY benchmark ORDER BY score DESC) AS rank
FROM v_scores
WHERE rank <= 5                        -- top 5 per benchmark
ORDER BY benchmark, rank;


-- ── 2. OVERALL LEADERBOARD ────────────────────────────────────────────────────
-- Average normalised score across all benchmarks.
-- Penalises models with fewer benchmark entries.

SELECT
    model_name,
    provider,
    COUNT(benchmark)                    AS benchmarks_tested,
    ROUND(AVG(score_pct), 1)           AS avg_score_pct,
    ROUND(MIN(score_pct), 1)           AS weakest_benchmark,
    ROUND(MAX(score_pct), 1)           AS strongest_benchmark,
    RANK() OVER (ORDER BY AVG(score_pct) DESC) AS overall_rank
FROM v_scores
GROUP BY model_name, provider
HAVING COUNT(benchmark) >= 3           -- only rank models with 3+ benchmarks
ORDER BY overall_rank;


-- ── 3. COST vs PERFORMANCE ────────────────────────────────────────────────────
-- Which model gives the best score per dollar?
-- Value = avg_score / cost_per_1M_tokens (higher = better value).

SELECT
    model_name,
    provider,
    ROUND(AVG(score), 1)               AS avg_score,
    input_cost_per_1m,
    CASE
        WHEN input_cost_per_1m IS NULL OR input_cost_per_1m = 0 THEN NULL
        ELSE ROUND(AVG(score) / input_cost_per_1m, 2)
    END                                AS score_per_dollar,
    is_open_weights
FROM v_scores
GROUP BY model_name, provider, input_cost_per_1m, is_open_weights
ORDER BY score_per_dollar DESC NULLS LAST;


-- ── 4. PROVIDER COMPARISON ───────────────────────────────────────────────────
-- How does each AI lab perform across benchmark categories?

SELECT
    provider,
    benchmark_category,
    COUNT(DISTINCT model_name)         AS models_tested,
    ROUND(AVG(score), 1)               AS avg_score,
    ROUND(MAX(score), 1)               AS best_score
FROM v_scores
GROUP BY provider, benchmark_category
ORDER BY provider, benchmark_category;


-- ── 5. OPEN VS CLOSED WEIGHTS ────────────────────────────────────────────────
-- Do open-weight models keep up with closed proprietary ones?

SELECT
    CASE WHEN is_open_weights THEN 'Open weights' ELSE 'Proprietary' END AS model_type,
    benchmark,
    ROUND(AVG(score), 1)               AS avg_score,
    ROUND(MAX(score), 1)               AS best_score,
    COUNT(DISTINCT model_name)         AS model_count
FROM v_scores
GROUP BY is_open_weights, benchmark
ORDER BY benchmark, model_type;


-- ── 6. SCORE IMPROVEMENT OVER RELEASES ───────────────────────────────────────
-- How much has each benchmark's SOTA improved over time?
-- Uses LAG() to compute year-on-year gains.

WITH ranked AS (
    SELECT
        benchmark,
        model_name,
        score,
        release_date,
        ROW_NUMBER() OVER (
            PARTITION BY benchmark
            ORDER BY release_date
        ) AS rn
    FROM v_scores
),
with_lag AS (
    SELECT
        benchmark,
        model_name,
        score,
        release_date,
        LAG(score)        OVER (PARTITION BY benchmark ORDER BY release_date) AS prev_score,
        LAG(release_date) OVER (PARTITION BY benchmark ORDER BY release_date) AS prev_date
    FROM ranked
)
SELECT
    benchmark,
    model_name,
    release_date,
    ROUND(score, 1)                         AS score,
    ROUND(prev_score, 1)                    AS prev_score,
    ROUND(score - prev_score, 1)            AS absolute_gain,
    ROUND((score - prev_score) / prev_score * 100, 1) AS pct_gain
FROM with_lag
WHERE prev_score IS NOT NULL
ORDER BY benchmark, release_date;


-- ── 7. BENCHMARK CATEGORY STRENGTHS ─────────────────────────────────────────
-- For each model, find its strongest and weakest category.

WITH cat_scores AS (
    SELECT
        model_name,
        benchmark_category,
        ROUND(AVG(score), 1) AS cat_avg
    FROM v_scores
    GROUP BY model_name, benchmark_category
),
ranked_cats AS (
    SELECT *,
        RANK() OVER (PARTITION BY model_name ORDER BY cat_avg DESC) AS best_rank,
        RANK() OVER (PARTITION BY model_name ORDER BY cat_avg ASC)  AS worst_rank
    FROM cat_scores
)
SELECT
    model_name,
    MAX(CASE WHEN best_rank  = 1 THEN benchmark_category END) AS strongest_category,
    MAX(CASE WHEN best_rank  = 1 THEN cat_avg END)            AS strongest_score,
    MAX(CASE WHEN worst_rank = 1 THEN benchmark_category END) AS weakest_category,
    MAX(CASE WHEN worst_rank = 1 THEN cat_avg END)            AS weakest_score
FROM ranked_cats
GROUP BY model_name
ORDER BY model_name;


-- ── 8. FIND MODELS MISSING BENCHMARKS ────────────────────────────────────────
-- Useful for spotting gaps in your data collection.

SELECT
    m.name          AS model_name,
    b.name          AS missing_benchmark
FROM models m
CROSS JOIN benchmarks b
LEFT JOIN benchmark_scores bs
    ON bs.model_id = m.id AND bs.benchmark_id = b.id
WHERE bs.id IS NULL
ORDER BY m.name, b.name;


-- ── 9. PARAMETER EFFICIENCY ──────────────────────────────────────────────────
-- Among open-weight models: do more parameters always mean better scores?

SELECT
    model_name,
    parameters_billions,
    ROUND(AVG(score), 1)     AS avg_score,
    COUNT(benchmark)         AS benchmarks_covered
FROM v_scores
WHERE is_open_weights = TRUE
  AND parameters_billions IS NOT NULL
GROUP BY model_name, parameters_billions
ORDER BY parameters_billions;


-- ── 10. TOP MODEL PER BENCHMARK + COST CONTEXT ───────────────────────────────
-- The winning model on each benchmark and what it costs to use.
-- Great for a portfolio "insights" section.

WITH top_per_bench AS (
    SELECT DISTINCT ON (benchmark)
        benchmark,
        model_name,
        provider,
        score,
        input_cost_per_1m,
        is_open_weights
    FROM v_scores
    ORDER BY benchmark, score DESC
)
SELECT
    benchmark,
    model_name,
    provider,
    ROUND(score, 1)                             AS top_score,
    CASE
        WHEN is_open_weights THEN 'Free (self-host)'
        WHEN input_cost_per_1m IS NULL THEN 'Unknown'
        ELSE '$' || input_cost_per_1m || ' / 1M tokens'
    END                                         AS cost_to_use
FROM top_per_bench
ORDER BY benchmark;
