-- ============================================================
-- AI Model Performance Tracker — Seed Data
-- ============================================================

-- ── Providers
INSERT INTO providers (name, country, founded, is_open_source) VALUES
('OpenAI',          'USA', 2015, FALSE),
('Anthropic',       'USA', 2021, FALSE),
('Google DeepMind', 'USA', 2023, FALSE),
('Meta AI',         'USA', 2013, TRUE),
('Mistral AI',      'France', 2023, TRUE),
('Cohere',          'Canada', 2019, FALSE),
('xAI',             'USA', 2023, FALSE);

-- ── Benchmarks
INSERT INTO benchmarks (name, description, category, max_score, higher_is_better) VALUES
('MMLU',       'Massive Multitask Language Understanding — 57 academic subjects', 'general',   100.0, TRUE),
('HumanEval',  'Code generation — pass@1 on 164 Python problems',                'coding',    100.0, TRUE),
('GSM8K',      'Grade school math — 8,500 word problems',                        'math',      100.0, TRUE),
('HellaSwag',  'Commonsense NLI and sentence completion',                        'reasoning', 100.0, TRUE),
('MATH',       'Competition mathematics — 12,500 problems',                      'math',      100.0, TRUE),
('MBPP',       'Mostly Basic Python Programming — 374 problems',                 'coding',    100.0, TRUE),
('ARC-C',      'AI2 Reasoning Challenge — Challenge set',                       'reasoning', 100.0, TRUE),
('TruthfulQA', 'Measures truthfulness and avoidance of falsehoods',              'safety',    100.0, TRUE);

-- ── Models
INSERT INTO models (name, slug, provider_id, release_date, parameters_billions, context_window_k, is_open_weights, input_cost_per_1m, output_cost_per_1m, modality) VALUES
-- OpenAI
('GPT-4o',              'gpt-4o',              1, '2024-05-13', NULL,  128, FALSE, 5.00,  15.00, 'multimodal'),
('GPT-4 Turbo',         'gpt-4-turbo',         1, '2024-04-09', NULL,  128, FALSE, 10.00, 30.00, 'multimodal'),
('GPT-3.5 Turbo',       'gpt-35-turbo',        1, '2022-11-30', NULL,   16, FALSE, 0.50,   1.50, 'text'),
('o1',                  'o1',                  1, '2024-12-05', NULL,  200, FALSE, 15.00, 60.00, 'text'),
-- Anthropic
('Claude 3.5 Sonnet',   'claude-35-sonnet',    2, '2024-06-20', NULL,  200, FALSE, 3.00,  15.00, 'multimodal'),
('Claude 3 Opus',       'claude-3-opus',       2, '2024-03-04', NULL,  200, FALSE, 15.00, 75.00, 'multimodal'),
('Claude 3 Haiku',      'claude-3-haiku',      2, '2024-03-07', NULL,  200, FALSE, 0.25,   1.25, 'multimodal'),
-- Google
('Gemini 1.5 Pro',      'gemini-15-pro',       3, '2024-02-15', NULL, 1000, FALSE, 3.50,  10.50, 'multimodal'),
('Gemini 1.5 Flash',    'gemini-15-flash',     3, '2024-05-14', NULL, 1000, FALSE, 0.35,   1.05, 'multimodal'),
-- Meta
('Llama 3.1 405B',      'llama-31-405b',       4, '2024-07-23', 405.0, 128, TRUE,  NULL,   NULL, 'text'),
('Llama 3.1 70B',       'llama-31-70b',        4, '2024-07-23',  70.0, 128, TRUE,  NULL,   NULL, 'text'),
('Llama 3.1 8B',        'llama-31-8b',         4, '2024-07-23',   8.0, 128, TRUE,  NULL,   NULL, 'text'),
-- Mistral
('Mistral Large 2',     'mistral-large-2',     5, '2024-07-24', 123.0, 128, FALSE, 3.00,   9.00, 'text'),
('Mixtral 8x22B',       'mixtral-8x22b',       5, '2024-04-10', 141.0,  64, TRUE,  2.00,   6.00, 'text'),
-- xAI
('Grok-2',              'grok-2',              7, '2024-08-13', NULL,  128, FALSE, 2.00,  10.00, 'text');

-- ── Benchmark Scores (sourced from public leaderboards)
INSERT INTO benchmark_scores (model_id, benchmark_id, score, shot_setting, recorded_date) VALUES
-- MMLU (benchmark_id = 1)
( 1, 1, 88.7, '5-shot', '2024-05-13'),  -- GPT-4o
( 2, 1, 86.5, '5-shot', '2024-04-09'),  -- GPT-4 Turbo
( 3, 1, 70.0, '5-shot', '2023-03-01'),  -- GPT-3.5 Turbo
( 4, 1, 92.3, '5-shot', '2024-12-05'),  -- o1
( 5, 1, 88.7, '5-shot', '2024-06-20'),  -- Claude 3.5 Sonnet
( 6, 1, 86.8, '5-shot', '2024-03-04'),  -- Claude 3 Opus
( 7, 1, 75.2, '5-shot', '2024-03-07'),  -- Claude 3 Haiku
( 8, 1, 85.9, '5-shot', '2024-02-15'),  -- Gemini 1.5 Pro
( 9, 1, 78.9, '5-shot', '2024-05-14'),  -- Gemini 1.5 Flash
(10, 1, 88.6, '5-shot', '2024-07-23'),  -- Llama 3.1 405B
(11, 1, 83.6, '5-shot', '2024-07-23'),  -- Llama 3.1 70B
(12, 1, 73.0, '5-shot', '2024-07-23'),  -- Llama 3.1 8B
(13, 1, 84.0, '5-shot', '2024-07-24'),  -- Mistral Large 2
(15, 1, 87.1, '5-shot', '2024-08-13'),  -- Grok-2

-- HumanEval (benchmark_id = 2)
( 1, 2, 90.2, '0-shot', '2024-05-13'),
( 2, 2, 87.1, '0-shot', '2024-04-09'),
( 3, 2, 48.1, '0-shot', '2023-03-01'),
( 4, 2, 92.4, '0-shot', '2024-12-05'),
( 5, 2, 92.0, '0-shot', '2024-06-20'),
( 6, 2, 84.9, '0-shot', '2024-03-04'),
( 7, 2, 75.9, '0-shot', '2024-03-07'),
( 8, 2, 84.1, '0-shot', '2024-02-15'),
( 9, 2, 74.3, '0-shot', '2024-05-14'),
(10, 2, 89.0, '0-shot', '2024-07-23'),
(11, 2, 80.5, '0-shot', '2024-07-23'),
(12, 2, 72.6, '0-shot', '2024-07-23'),
(13, 2, 92.0, '0-shot', '2024-07-24'),
(15, 2, 88.5, '0-shot', '2024-08-13'),

-- GSM8K (benchmark_id = 3)
( 1, 3, 94.1, '5-shot', '2024-05-13'),
( 2, 3, 93.7, '5-shot', '2024-04-09'),
( 3, 3, 57.1, '5-shot', '2023-03-01'),
( 4, 3, 96.4, '5-shot', '2024-12-05'),
( 5, 3, 96.4, '5-shot', '2024-06-20'),
( 6, 3, 95.0, '5-shot', '2024-03-04'),
( 7, 3, 88.9, '5-shot', '2024-03-07'),
( 8, 3, 91.7, '5-shot', '2024-02-15'),
( 9, 3, 86.2, '5-shot', '2024-05-14'),
(10, 3, 96.8, '5-shot', '2024-07-23'),
(11, 3, 95.1, '5-shot', '2024-07-23'),
(12, 3, 84.5, '5-shot', '2024-07-23'),
(13, 3, 93.7, '5-shot', '2024-07-24'),
(15, 3, 94.1, '5-shot', '2024-08-13'),

-- MATH (benchmark_id = 5)
( 1, 5, 76.6, '4-shot', '2024-05-13'),
( 2, 5, 73.4, '4-shot', '2024-04-09'),
( 4, 5, 94.8, '4-shot', '2024-12-05'),
( 5, 5, 71.1, '4-shot', '2024-06-20'),
( 6, 5, 60.1, '4-shot', '2024-03-04'),
( 8, 5, 67.7, '4-shot', '2024-02-15'),
(10, 5, 73.8, '4-shot', '2024-07-23'),
(13, 5, 69.9, '4-shot', '2024-07-24'),

-- TruthfulQA (benchmark_id = 8)
( 1, 8, 77.8, '0-shot', '2024-05-13'),
( 2, 8, 72.4, '0-shot', '2024-04-09'),
( 5, 8, 82.3, '0-shot', '2024-06-20'),
( 6, 8, 80.1, '0-shot', '2024-03-04'),
( 8, 8, 75.2, '0-shot', '2024-02-15'),
(10, 8, 73.1, '0-shot', '2024-07-23'),
(13, 8, 71.8, '0-shot', '2024-07-24');
