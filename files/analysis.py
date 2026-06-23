"""
AI Model Performance Tracker — Analysis & Visualisation
"""

import os
import logging
import psycopg2
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import seaborn as sns
from dotenv import load_dotenv
from adjustText import adjust_text

load_dotenv()
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")
log = logging.getLogger(__name__)

os.makedirs("charts", exist_ok=True)

STYLE = {
    "font.family":    "sans-serif",
    "axes.spines.top":   False,
    "axes.spines.right": False,
    "axes.grid":         True,
    "grid.alpha":        0.3,
    "figure.dpi":        130,
}
plt.rcParams.update(STYLE)

COLORS = {
    "OpenAI":          "#10a37f",
    "Anthropic":       "#d97659",
    "Google DeepMind": "#4285F4",
    "Meta AI":         "#0866FF",
    "Mistral AI":      "#ff7000",
    "xAI":             "#1DA1F2",
    "Cohere":          "#39C5BB",
}
DEFAULT_COLOR = "#888888"


def get_conn():
    return psycopg2.connect(
        host=os.getenv("DB_HOST", "localhost"),
        port=os.getenv("DB_PORT", 5432),
        dbname=os.getenv("DB_NAME", "ai_tracker"),
        user=os.getenv("DB_USER", "mac"),
        password=os.getenv("DB_PASSWORD", ""),
    )


def query(conn, sql):
    return pd.read_sql_query(sql, conn)


# Chart 1: Overall leaderboard
def chart_overall_leaderboard(conn):
    df = query(conn, """
        SELECT
            model_name, provider,
            ROUND(AVG(score_pct), 1) AS avg_score,
            COUNT(benchmark) AS n_benchmarks
        FROM v_scores
        GROUP BY model_name, provider
        HAVING COUNT(benchmark) >= 3
        ORDER BY avg_score DESC
        LIMIT 12;
    """)
    if df.empty:
        return

    fig, ax = plt.subplots(figsize=(11, 6))
    bar_colors = [COLORS.get(p, DEFAULT_COLOR) for p in df["provider"]]
    bars = ax.barh(df["model_name"], df["avg_score"], color=bar_colors, height=0.6)

    for bar, n in zip(bars, df["n_benchmarks"]):
        ax.text(
            bar.get_width() + 0.3,
            bar.get_y() + bar.get_height() / 2,
            f"{bar.get_width():.1f}%  ({n} benchmarks)",
            va="center", fontsize=9, color="#555"
        )

    ax.set_xlabel("Average score (%)")
    ax.set_xlim(0, 115)
    ax.invert_yaxis()
    ax.set_title("Overall AI model leaderboard", fontsize=13, fontweight="bold", pad=12)

    seen = {}
    for p, c in zip(df["provider"], bar_colors):
        if p not in seen:
            seen[p] = c
    handles = [mpatches.Patch(color=c, label=p) for p, c in seen.items()]
    ax.legend(handles=handles, fontsize=8, loc="lower right",
              bbox_to_anchor=(1.0, 0.0), framealpha=0.9)

    plt.tight_layout()
    plt.savefig("charts/01_overall_leaderboard.png", bbox_inches="tight")
    plt.close()
    log.info("Saved charts/01_overall_leaderboard.png")


# Chart 2: Benchmark heatmap
def chart_benchmark_heatmap(conn):
    df = query(conn, """
        SELECT model_name, benchmark, ROUND(score, 1) AS score
        FROM v_scores
        ORDER BY model_name, benchmark;
    """)
    if df.empty:
        return

    pivot = df.pivot(index="model_name", columns="benchmark", values="score")

    # Sort columns — old benchmarks first, then new ones
    old_benchmarks = ["MMLU", "HumanEval", "GSM8K", "MATH", "TruthfulQA",
                      "HellaSwag", "MBPP", "ARC-C"]
    new_benchmarks = ["GPQA Diamond", "AIME 2025", "SWE-bench"]
    ordered_cols = [c for c in old_benchmarks if c in pivot.columns] + \
                   [c for c in new_benchmarks if c in pivot.columns]
    pivot = pivot[[c for c in ordered_cols if c in pivot.columns]]

    # Sort rows by average score descending
    pivot = pivot.loc[pivot.mean(axis=1).sort_values(ascending=False).index]

    fig, ax = plt.subplots(figsize=(16, max(6, len(pivot) * 0.55)))
    sns.heatmap(
        pivot,
        annot=True, fmt=".1f",
        cmap="YlGn",
        linewidths=0.4, linecolor="#e0e0e0",
        ax=ax,
        cbar_kws={"label": "Score (%)"},
        annot_kws={"size": 8},
    )
    ax.set_title("All Models × All Benchmarks — Old and New",
                 fontsize=13, fontweight="bold", pad=12)
    ax.set_xlabel("")
    ax.set_ylabel("")

    # Add a vertical line separating old vs new benchmarks
    n_old = len([c for c in old_benchmarks if c in pivot.columns])
    ax.axvline(x=n_old, color="#2E86AB", linewidth=2, linestyle="--", alpha=0.7)
    ax.text(n_old - 0.5, -0.8, "← Old benchmarks",
            ha="right", fontsize=8, color="#2E86AB", transform=ax.get_xaxis_transform())
    ax.text(n_old + 0.1, -0.8, "New benchmarks →",
            ha="left", fontsize=8, color="#2E86AB", transform=ax.get_xaxis_transform())

    plt.xticks(rotation=30, ha="right", fontsize=9)
    plt.yticks(rotation=0, fontsize=9)
    plt.tight_layout()
    plt.savefig("charts/02_benchmark_heatmap.png", bbox_inches="tight")
    plt.close()
    log.info("Saved charts/02_benchmark_heatmap.png")


# Chart 4: Open vs closed
def chart_open_vs_closed(conn):
    df = query(conn, """
        SELECT
            CASE WHEN is_open_weights THEN 'Open weights' ELSE 'Proprietary' END AS model_type,
            benchmark,
            ROUND(AVG(score), 1) AS avg_score
        FROM v_scores
        GROUP BY is_open_weights, benchmark
        ORDER BY benchmark;
    """)
    if df.empty:
        return

    pivot = df.pivot(index="benchmark", columns="model_type", values="avg_score")
    pivot.plot(
        kind="bar", figsize=(10, 6),
        color=["#4e9af1", "#f4845f"],
        edgecolor="white", width=0.55
    )
    plt.title("Open vs proprietary model scores by benchmark",
              fontsize=13, fontweight="bold", pad=12)
    plt.xlabel("")
    plt.ylabel("Average score (%)")
    plt.xticks(rotation=30, ha="right")
    plt.legend(title="Model type", fontsize=9, bbox_to_anchor=(1.0, 1.0))
    plt.tight_layout()
    plt.savefig("charts/04_open_vs_closed.png", bbox_inches="tight")
    plt.close()
    log.info("Saved charts/04_open_vs_closed.png")

# ── New models only versions ───────────────────────────────────────────────

def chart_new_leaderboard(conn):
    df = query(conn, """
        SELECT
            model_name, provider,
            ROUND(AVG(score_pct), 1) AS avg_score,
            COUNT(benchmark) AS n_benchmarks
        FROM v_scores
        WHERE release_date >= '2025-01-01'
        GROUP BY model_name, provider
        HAVING COUNT(benchmark) >= 2
        ORDER BY avg_score DESC
        LIMIT 12;
    """)
    if df.empty:
        return

    fig, ax = plt.subplots(figsize=(11, 6))
    bar_colors = [COLORS.get(p, DEFAULT_COLOR) for p in df["provider"]]
    bars = ax.barh(df["model_name"], df["avg_score"], color=bar_colors, height=0.6)

    for bar, n in zip(bars, df["n_benchmarks"]):
        ax.text(
            bar.get_width() + 0.3,
            bar.get_y() + bar.get_height() / 2,
            f"{bar.get_width():.1f}%  ({n} benchmarks)",
            va="center", fontsize=9, color="#555"
        )

    ax.set_xlabel("Average score (%)")
    ax.set_xlim(0, 115)
    ax.invert_yaxis()
    ax.set_title("2025+ Model Leaderboard (New Models Only)",
                 fontsize=13, fontweight="bold", pad=12)

    seen = {}
    for p, c in zip(df["provider"], bar_colors):
        if p not in seen:
            seen[p] = c
    handles = [mpatches.Patch(color=c, label=p) for p, c in seen.items()]
    ax.legend(handles=handles, fontsize=8, loc="lower right",
              bbox_to_anchor=(1.0, 0.0), framealpha=0.9)

    plt.tight_layout()
    plt.savefig("charts/06_new_leaderboard.png", bbox_inches="tight")
    plt.close()
    log.info("Saved charts/06_new_leaderboard.png")


def chart_new_heatmap(conn):
    df = query(conn, """
        SELECT model_name, benchmark, ROUND(score, 1) AS score
        FROM v_scores
        WHERE release_date >= '2025-01-01'
        ORDER BY model_name, benchmark;
    """)
    if df.empty:
        return

    pivot = df.pivot(index="model_name", columns="benchmark", values="score")

    fig, ax = plt.subplots(figsize=(13, max(5, len(pivot) * 0.6)))
    sns.heatmap(
        pivot,
        annot=True, fmt=".1f",
        cmap="YlGn",
        linewidths=0.4, linecolor="#e0e0e0",
        ax=ax,
        cbar_kws={"label": "Score (%)"},
        annot_kws={"size": 9},
    )
    ax.set_title("2025+ Models — Scores Across All Benchmarks",
                 fontsize=13, fontweight="bold", pad=12)
    ax.set_xlabel("")
    ax.set_ylabel("")
    plt.xticks(rotation=30, ha="right", fontsize=9)
    plt.yticks(rotation=0, fontsize=9)
    plt.tight_layout()
    plt.savefig("charts/07_new_heatmap.png", bbox_inches="tight")
    plt.close()
    log.info("Saved charts/07_new_heatmap.png")


def chart_new_cost_vs_performance(conn):
    df = query(conn, """
        SELECT
            model_name, provider,
            ROUND(AVG(score), 1) AS avg_score,
            input_cost_per_1m,
            is_open_weights
        FROM v_scores
        WHERE input_cost_per_1m IS NOT NULL
          AND release_date >= '2025-01-01'
        GROUP BY model_name, provider, input_cost_per_1m, is_open_weights;
    """)
    if df.empty:
        return

    fig, ax = plt.subplots(figsize=(11, 7))
    texts = []

    for _, row in df.iterrows():
        c = COLORS.get(row["provider"], DEFAULT_COLOR)
        ax.scatter(row["input_cost_per_1m"], row["avg_score"],
                   color=c, s=100, zorder=3, edgecolors="white", linewidths=0.8)
        texts.append(ax.text(
            row["input_cost_per_1m"], row["avg_score"],
            row["model_name"], fontsize=8, color="#333"
        ))

    for text in texts:
        x, y = text.get_position()
        text.set_position((x + 0.15, y + 0.3))

    ax.set_xlabel("Input cost (USD per 1M tokens)", fontsize=10)
    ax.set_ylabel("Average benchmark score (%)", fontsize=10)
    ax.set_title("2025+ Models — Cost vs Performance",
                 fontsize=13, fontweight="bold", pad=12)
    ax.set_xlim(-0.5, 10)
    ax.set_ylim(50, 100)
    plt.tight_layout()
    plt.savefig("charts/08_new_cost_vs_performance.png", bbox_inches="tight")
    plt.close()
    log.info("Saved charts/08_new_cost_vs_performance.png")


def chart_new_open_vs_closed(conn):
    df = query(conn, """
        SELECT
            CASE WHEN is_open_weights THEN 'Open weights' ELSE 'Proprietary' END AS model_type,
            benchmark,
            ROUND(AVG(score), 1) AS avg_score
        FROM v_scores
        WHERE release_date >= '2025-01-01'
        GROUP BY is_open_weights, benchmark
        ORDER BY benchmark;
    """)
    if df.empty:
        return

    pivot = df.pivot(index="benchmark", columns="model_type", values="avg_score")
    pivot.plot(
        kind="bar", figsize=(10, 6),
        color=["#4e9af1", "#f4845f"],
        edgecolor="white", width=0.55
    )
    plt.title("2025+ Models — Open vs Proprietary by Benchmark",
              fontsize=13, fontweight="bold", pad=12)
    plt.xlabel("")
    plt.ylabel("Average score (%)")
    plt.xticks(rotation=30, ha="right")
    plt.legend(title="Model type", fontsize=9, bbox_to_anchor=(1.0, 1.0))
    plt.tight_layout()
    plt.savefig("charts/09_new_open_vs_closed.png", bbox_inches="tight")
    plt.close()
    log.info("Saved charts/09_new_open_vs_closed.png")

# Chart 5: Old vs New models per provider
def chart_old_vs_new_per_provider(conn):
    df = query(conn, """
        SELECT
            m.name AS model_name,
            p.name AS provider,
            ROUND(AVG(bs.score), 1) AS avg_score,
            m.release_date,
            CASE
                WHEN m.release_date >= '2025-01-01' THEN 'New (2025+)'
                ELSE 'Old (pre-2025)'
            END AS model_era
        FROM benchmark_scores bs
        JOIN models m ON m.id = bs.model_id
        JOIN providers p ON p.id = m.provider_id
        GROUP BY m.name, p.name, m.release_date
        HAVING COUNT(bs.score) >= 2
        ORDER BY p.name, m.release_date;
    """)
    if df.empty:
        return

    providers = ['OpenAI', 'Anthropic', 'Google DeepMind', 'Meta AI']
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    fig.suptitle('Old vs New Models — Score Improvement by Provider',
                 fontsize=14, fontweight='bold', y=1.02)

    for ax, provider in zip(axes.flatten(), providers):
        pdata = df[df['provider'] == provider].sort_values('release_date')
        if pdata.empty:
            ax.set_visible(False)
            continue

        colors = ['#AACCDD' if e == 'Old (pre-2025)' else COLORS.get(provider, '#333')
                  for e in pdata['model_era']]
        bars = ax.barh(pdata['model_name'], pdata['avg_score'],
                       color=colors, height=0.5)

        for bar in bars:
            ax.text(bar.get_width() + 0.3,
                    bar.get_y() + bar.get_height() / 2,
                    f"{bar.get_width():.1f}%",
                    va='center', fontsize=8, color='#555')

        ax.set_title(provider, fontsize=11, fontweight='bold',
                     color=COLORS.get(provider, '#333'))
        ax.set_xlim(0, 105)
        ax.invert_yaxis()
        ax.set_xlabel("Avg score (%)", fontsize=8)

        from matplotlib.patches import Patch
        legend = [
            Patch(color='#AACCDD', label='Old (pre-2025)'),
            Patch(color=COLORS.get(provider, '#333'), label='New (2025+)')
        ]
        ax.legend(handles=legend, fontsize=7, loc='lower right')

    plt.tight_layout()
    plt.savefig("charts/05_old_vs_new_per_provider.png", bbox_inches="tight")
    plt.close()
    log.info("Saved charts/05_old_vs_new_per_provider.png")

def run():
    conn = get_conn()
    log.info("Connected — running analysis...")
    try:
        chart_overall_leaderboard(conn)
        chart_benchmark_heatmap(conn)
        chart_new_cost_vs_performance(conn)
        chart_open_vs_closed(conn)
        chart_new_leaderboard(conn)
        chart_new_heatmap(conn)
        chart_new_cost_vs_performance(conn)
        chart_new_open_vs_closed(conn)
        chart_old_vs_new_per_provider(conn)
        log.info("All charts saved to charts/")
    finally:
        conn.close()


if __name__ == "__main__":
    run()