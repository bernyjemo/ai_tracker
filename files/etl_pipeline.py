"""
AI Model Performance Tracker — ETL Pipeline
============================================
Fetches benchmark data from public sources and loads into PostgreSQL.

Usage:
    pip install psycopg2-binary pandas requests python-dotenv
    python etl_pipeline.py

Set your DB connection in a .env file:
    DB_HOST=localhost
    DB_PORT=5432
    DB_NAME=ai_tracker
    DB_USER=postgres
    DB_PASSWORD=yourpassword
"""

import os
import logging
import csv
import json
from io import StringIO
from datetime import date, datetime
from typing import Optional

import requests
import pandas as pd
import psycopg2
from psycopg2.extras import execute_values
from dotenv import load_dotenv

load_dotenv()
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("etl.log"),
        logging.StreamHandler(),
    ],
)
log = logging.getLogger(__name__)


# ── Database connection ────────────────────────────────────────────────────────

def get_connection():
    """Return a psycopg2 connection using env variables."""
    return psycopg2.connect(
        host=os.getenv("DB_HOST", "localhost"),
        port=os.getenv("DB_PORT", 5432),
        dbname=os.getenv("DB_NAME", "ai_tracker"),
        user=os.getenv("DB_USER", "postgres"),
        password=os.getenv("DB_PASSWORD", ""),
    )


# ── Extraction ─────────────────────────────────────────────────────────────────

def extract_from_csv(filepath: str) -> pd.DataFrame:
    """
    Load benchmark scores from a local CSV file.

    Expected columns:
        model_slug, benchmark_name, score, shot_setting, source_url, recorded_date
    """
    log.info(f"Extracting from CSV: {filepath}")
    df = pd.read_csv(filepath)
    log.info(f"  Loaded {len(df)} rows")
    return df


def extract_from_huggingface_leaderboard() -> pd.DataFrame:
    """
    Fetch open LLM leaderboard data from Hugging Face datasets API.
    Falls back to an empty DataFrame if unreachable.
    """
    url = (
        "https://huggingface.co/datasets/open-llm-leaderboard/"
        "results/resolve/main/data/train-00000-of-00001.parquet"
    )
    log.info("Fetching Hugging Face Open LLM Leaderboard...")
    try:
        df = pd.read_parquet(url)
        log.info(f"  Fetched {len(df)} rows from HF leaderboard")
        return df
    except Exception as e:
        log.warning(f"  Could not fetch HF leaderboard: {e}")
        return pd.DataFrame()


# ── Transformation ─────────────────────────────────────────────────────────────

def clean_scores(df: pd.DataFrame) -> pd.DataFrame:
    """
    Validate and clean a raw scores DataFrame.

    Rules:
    - Drop rows with missing model_slug, benchmark_name, or score
    - Clamp scores to [0, 100]
    - Normalise benchmark names to uppercase
    - Parse recorded_date to date objects
    - Deduplicate on (model_slug, benchmark_name, shot_setting)
    """
    log.info("Cleaning and transforming data...")
    original_len = len(df)

    required_cols = {"model_slug", "benchmark_name", "score"}
    missing = required_cols - set(df.columns)
    if missing:
        raise ValueError(f"DataFrame is missing required columns: {missing}")

    df = df.dropna(subset=list(required_cols)).copy()

    # Normalise text fields
    df["model_slug"]      = df["model_slug"].str.strip().str.lower()
    df["benchmark_name"]  = df["benchmark_name"].str.strip().str.upper()
    df["shot_setting"]    = df.get("shot_setting", pd.Series(["0-shot"] * len(df)))
    df["shot_setting"]    = df["shot_setting"].fillna("0-shot").str.strip()

    # Clamp score to [0, 100]
    df["score"] = pd.to_numeric(df["score"], errors="coerce")
    df = df.dropna(subset=["score"])
    df["score"] = df["score"].clip(0, 100)

    # Parse dates
    if "recorded_date" in df.columns:
        df["recorded_date"] = pd.to_datetime(df["recorded_date"], errors="coerce").dt.date
    else:
        df["recorded_date"] = date.today()
    df["recorded_date"] = df["recorded_date"].fillna(date.today())

    # Deduplicate — keep the latest entry per (model, benchmark, shot)
    df = (
        df.sort_values("recorded_date", ascending=False)
          .drop_duplicates(subset=["model_slug", "benchmark_name", "shot_setting"])
    )

    dropped = original_len - len(df)
    log.info(f"  {len(df)} rows after cleaning ({dropped} dropped)")
    return df


# ── Loading ────────────────────────────────────────────────────────────────────

def get_lookup_maps(conn) -> tuple[dict, dict]:
    """Return {slug: model_id} and {name: benchmark_id} dicts."""
    with conn.cursor() as cur:
        cur.execute("SELECT slug, id FROM models;")
        model_map = {row[0]: row[1] for row in cur.fetchall()}

        cur.execute("SELECT UPPER(name), id FROM benchmarks;")
        bench_map = {row[0]: row[1] for row in cur.fetchall()}

    return model_map, bench_map


def load_scores(conn, df: pd.DataFrame) -> dict:
    """
    Upsert cleaned scores into benchmark_scores.
    Uses ON CONFLICT to skip duplicates gracefully.
    Returns a summary dict with inserted/skipped counts.
    """
    model_map, bench_map = get_lookup_maps(conn)

    rows_to_insert = []
    skipped = []

    for _, row in df.iterrows():
        model_id = model_map.get(row["model_slug"])
        bench_id = bench_map.get(row["benchmark_name"])

        if model_id is None:
            skipped.append(f"Unknown model slug: {row['model_slug']}")
            continue
        if bench_id is None:
            skipped.append(f"Unknown benchmark: {row['benchmark_name']}")
            continue

        rows_to_insert.append((
            model_id,
            bench_id,
            float(row["score"]),
            str(row["shot_setting"]),
            row.get("source_url", None),
            row["recorded_date"],
        ))

    if not rows_to_insert:
        log.warning("No valid rows to insert.")
        return {"inserted": 0, "skipped": len(skipped), "errors": skipped}

    sql = """
        INSERT INTO benchmark_scores
            (model_id, benchmark_id, score, shot_setting, source_url, recorded_date)
        VALUES %s
        ON CONFLICT (model_id, benchmark_id, shot_setting) DO NOTHING;
    """

    with conn.cursor() as cur:
        execute_values(cur, sql, rows_to_insert, page_size=500)
    conn.commit()

    log.info(f"  Inserted {len(rows_to_insert)} rows | Skipped {len(skipped)} rows")
    if skipped:
        for msg in skipped[:5]:      # log first 5 issues only
            log.warning(f"    {msg}")

    return {"inserted": len(rows_to_insert), "skipped": len(skipped)}


def upsert_model(conn, model: dict) -> int:
    """
    Insert a new model if it doesn't exist yet.
    Returns the model's id.
    """
    sql = """
        INSERT INTO models
            (name, slug, provider_id, release_date, parameters_billions,
             context_window_k, is_open_weights, input_cost_per_1m, output_cost_per_1m, modality)
        VALUES
            (%(name)s, %(slug)s, %(provider_id)s, %(release_date)s, %(parameters_billions)s,
             %(context_window_k)s, %(is_open_weights)s, %(input_cost_per_1m)s,
             %(output_cost_per_1m)s, %(modality)s)
        ON CONFLICT (slug) DO NOTHING
        RETURNING id;
    """
    with conn.cursor() as cur:
        cur.execute(sql, model)
        result = cur.fetchone()
    conn.commit()
    return result[0] if result else None


# ── Orchestration ──────────────────────────────────────────────────────────────

def run_etl(csv_path: Optional[str] = None):
    """
    Full ETL run:
      1. Extract from CSV file (or Hugging Face if not provided)
      2. Clean and validate
      3. Load into PostgreSQL
    """
    log.info("=== ETL pipeline starting ===")
    start = datetime.now()

    conn = get_connection()
    log.info("Connected to PostgreSQL")

    try:
        if csv_path and os.path.exists(csv_path):
            raw_df = extract_from_csv(csv_path)
        else:
            log.info("No CSV provided — attempting Hugging Face fetch")
            raw_df = extract_from_huggingface_leaderboard()

        if raw_df.empty:
            log.warning("No data extracted. Exiting.")
            return

        clean_df = clean_scores(raw_df)
        summary  = load_scores(conn, clean_df)

        elapsed = (datetime.now() - start).seconds
        log.info(f"=== ETL complete in {elapsed}s — {summary} ===")
        return summary

    except Exception as e:
        conn.rollback()
        log.error(f"ETL failed: {e}", exc_info=True)
        raise

    finally:
        conn.close()


# ── Sample CSV generator (for testing without a real DB) ──────────────────────

def generate_sample_csv(output_path: str = "data/sample_scores.csv"):
    """Write a sample CSV you can use to test the pipeline."""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    rows = [
        {"model_slug": "gpt-4o",          "benchmark_name": "MMLU",      "score": 88.7, "shot_setting": "5-shot", "recorded_date": "2024-05-13"},
        {"model_slug": "claude-35-sonnet", "benchmark_name": "MMLU",      "score": 88.7, "shot_setting": "5-shot", "recorded_date": "2024-06-20"},
        {"model_slug": "llama-31-405b",    "benchmark_name": "HUMANEVAL", "score": 89.0, "shot_setting": "0-shot", "recorded_date": "2024-07-23"},
        {"model_slug": "gemini-15-pro",    "benchmark_name": "GSM8K",     "score": 91.7, "shot_setting": "5-shot", "recorded_date": "2024-02-15"},
        {"model_slug": "mistral-large-2",  "benchmark_name": "MATH",      "score": 69.9, "shot_setting": "4-shot", "recorded_date": "2024-07-24"},
    ]
    df = pd.DataFrame(rows)
    df.to_csv(output_path, index=False)
    log.info(f"Sample CSV written to {output_path}")
    return output_path


if __name__ == "__main__":
    import sys
    csv_file = sys.argv[1] if len(sys.argv) > 1 else None
    run_etl(csv_path=csv_file)
