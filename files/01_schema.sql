-- ============================================================
-- AI Model Performance Tracker — PostgreSQL Schema
-- ============================================================

-- Drop existing tables if rebuilding
DROP TABLE IF EXISTS benchmark_scores CASCADE;
DROP TABLE IF EXISTS models CASCADE;
DROP TABLE IF EXISTS providers CASCADE;
DROP TABLE IF EXISTS benchmarks CASCADE;

-- ── 1. Providers (OpenAI, Anthropic, Meta, Google, etc.)
CREATE TABLE providers (
    id          SERIAL PRIMARY KEY,
    name        VARCHAR(100) NOT NULL UNIQUE,   -- 'Anthropic'
    country     VARCHAR(50),                    -- 'USA'
    founded     INT,                            -- 2021
    is_open_source BOOLEAN DEFAULT FALSE
);

-- ── 2. Benchmarks (MMLU, HumanEval, GSM8K, etc.)
CREATE TABLE benchmarks (
    id          SERIAL PRIMARY KEY,
    name        VARCHAR(100) NOT NULL UNIQUE,   -- 'MMLU'
    description TEXT,
    category    VARCHAR(50),                    -- 'reasoning', 'coding', 'math', 'general'
    max_score   NUMERIC(6,2) DEFAULT 100.0,     -- most are 0–100
    higher_is_better BOOLEAN DEFAULT TRUE
);

-- ── 3. Models
CREATE TABLE models (
    id                    SERIAL PRIMARY KEY,
    name                  VARCHAR(150) NOT NULL,     -- 'Claude 3.5 Sonnet'
    slug                  VARCHAR(100) UNIQUE,       -- 'claude-3-5-sonnet'
    provider_id           INT REFERENCES providers(id) ON DELETE SET NULL,
    release_date          DATE,
    parameters_billions   NUMERIC(8,1),              -- 70.0, 405.0, NULL if unknown
    context_window_k      INT,                       -- context length in thousands of tokens
    is_open_weights       BOOLEAN DEFAULT FALSE,
    input_cost_per_1m     NUMERIC(8,4),              -- USD per 1M input tokens
    output_cost_per_1m    NUMERIC(8,4),              -- USD per 1M output tokens
    modality              VARCHAR(50) DEFAULT 'text',-- 'text', 'multimodal'
    notes                 TEXT
);

-- ── 4. Benchmark Scores (the core fact table)
CREATE TABLE benchmark_scores (
    id            SERIAL PRIMARY KEY,
    model_id      INT NOT NULL REFERENCES models(id) ON DELETE CASCADE,
    benchmark_id  INT NOT NULL REFERENCES benchmarks(id) ON DELETE CASCADE,
    score         NUMERIC(6,2) NOT NULL,
    shot_setting  VARCHAR(20),                       -- '0-shot', '5-shot'
    source_url    VARCHAR(500),                      -- link to paper or leaderboard
    recorded_date DATE NOT NULL DEFAULT CURRENT_DATE,
    UNIQUE (model_id, benchmark_id, shot_setting)    -- no duplicate entries
);

-- ── Indexes for fast querying
CREATE INDEX idx_scores_model    ON benchmark_scores(model_id);
CREATE INDEX idx_scores_benchmark ON benchmark_scores(benchmark_id);
CREATE INDEX idx_scores_date     ON benchmark_scores(recorded_date);
CREATE INDEX idx_models_provider ON models(provider_id);
CREATE INDEX idx_models_release  ON models(release_date);

-- ── Helpful view: flattened scores with names
CREATE VIEW v_scores AS
SELECT
    bs.id,
    m.name         AS model_name,
    m.slug,
    p.name         AS provider,
    bk.name        AS benchmark,
    bk.category    AS benchmark_category,
    bs.score,
    bk.max_score,
    ROUND(bs.score / bk.max_score * 100, 1) AS score_pct,
    bs.shot_setting,
    m.release_date,
    m.parameters_billions,
    m.input_cost_per_1m,
    m.output_cost_per_1m,
    m.is_open_weights,
    bs.recorded_date
FROM benchmark_scores bs
JOIN models    m  ON m.id  = bs.model_id
JOIN providers p  ON p.id  = m.provider_id
JOIN benchmarks bk ON bk.id = bs.benchmark_id;
