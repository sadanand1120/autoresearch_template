"""
Passive analysis template for autoresearch runs.

Copy this file to `analysis.py` and customize it for your workload.

Design goals:
- do not mutate experimental state
- do not open interactive windows
- print summaries to stdout
- save plots or tables to disk
- make it easy to compare baseline, kept runs, discarded runs, and crashes

This template is meant to consume the stable `results.tsv` schema defined by
the generated `program.md`. If your benchmark harness has both `smoke` and
`measure` profiles, this script should analyze the official measure rows unless
you intentionally choose a different convention.
"""

from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import pandas as pd


RESULTS_PATH = Path("results.tsv")
PLOT_PATH = Path("progress.png")

# Replace these with use-case-specific values.
COMMIT_COLUMN = "commit"
METRIC_COLUMN = "metric"
RESOURCE_COLUMN = "memory"
STATUS_COLUMN = "status"
DESCRIPTION_COLUMN = "description"
PROFILE_COLUMN = None
OFFICIAL_PROFILE = None
KEEP_LABEL = "KEEP"
DISCARD_LABEL = "DISCARD"
CRASH_LABEL = "CRASH"
LOWER_IS_BETTER = True


def load_results(path: Path) -> pd.DataFrame:
    """Load and normalize the experiment log."""
    df = pd.read_csv(path, sep="\t")
    df[METRIC_COLUMN] = pd.to_numeric(df[METRIC_COLUMN], errors="coerce")
    df[RESOURCE_COLUMN] = pd.to_numeric(df[RESOURCE_COLUMN], errors="coerce")
    df[STATUS_COLUMN] = df[STATUS_COLUMN].astype(str).str.strip().str.upper()
    return df


def select_official_runs(df: pd.DataFrame) -> pd.DataFrame:
    """
    Optionally filter to the official benchmark profile.

    Leave `PROFILE_COLUMN` and `OFFICIAL_PROFILE` as `None` if `results.tsv`
    already contains only the rows you want to analyze.
    """
    if PROFILE_COLUMN is None or OFFICIAL_PROFILE is None:
        return df
    return df[df[PROFILE_COLUMN] == OFFICIAL_PROFILE].copy()


def print_header(df: pd.DataFrame) -> None:
    print(f"Total experiments: {len(df)}")
    print(f"Columns: {list(df.columns)}")
    print(df.head(10).to_string())


def print_outcomes(df: pd.DataFrame) -> None:
    counts = df[STATUS_COLUMN].value_counts()
    print("Experiment outcomes:")
    print(counts.to_string())

    n_keep = counts.get(KEEP_LABEL, 0)
    n_discard = counts.get(DISCARD_LABEL, 0)
    n_decided = n_keep + n_discard
    if n_decided > 0:
        print(f"\nKeep rate: {n_keep}/{n_decided} = {n_keep / n_decided:.1%}")


def print_kept_runs(df: pd.DataFrame) -> pd.DataFrame:
    kept = df[df[STATUS_COLUMN] == KEEP_LABEL].copy()
    print(f"\nKEPT experiments ({len(kept)} total):\n")
    for i, row in kept.iterrows():
        print(
            f"  #{i:3d}  {METRIC_COLUMN}={row[METRIC_COLUMN]:.6f}  "
            f"{RESOURCE_COLUMN}={row[RESOURCE_COLUMN]:.1f}  "
            f"{row[DESCRIPTION_COLUMN]}"
        )
    return kept


def plot_progress(df: pd.DataFrame) -> None:
    """
    Save one passive progress plot.

    Adapt this to your own metric semantics. The default version assumes:
    - crashes should be omitted from the chart
    - kept runs define the frontier
    - discarded runs are useful background signal
    """
    valid = df[df[STATUS_COLUMN] != CRASH_LABEL].copy().reset_index(drop=True)
    if valid.empty:
        print("No non-crash runs available; skipping plot.")
        return

    baseline = valid.loc[0, METRIC_COLUMN]
    kept_mask = valid[STATUS_COLUMN] == KEEP_LABEL
    kept_idx = valid.index[kept_mask]
    kept_metric = valid.loc[kept_mask, METRIC_COLUMN]
    if kept_metric.empty:
        print("No kept runs available; skipping plot.")
        return

    frontier = kept_metric.cummin() if LOWER_IS_BETTER else kept_metric.cummax()
    focus = valid[valid[METRIC_COLUMN].notna()]

    fig, ax = plt.subplots(figsize=(16, 8))

    discarded = focus[focus[STATUS_COLUMN] == DISCARD_LABEL]
    ax.scatter(
        discarded.index,
        discarded[METRIC_COLUMN],
        c="#cccccc",
        s=12,
        alpha=0.5,
        zorder=2,
        label="Discarded",
    )

    kept = focus[focus[STATUS_COLUMN] == KEEP_LABEL]
    ax.scatter(
        kept.index,
        kept[METRIC_COLUMN],
        c="#2ecc71",
        s=50,
        zorder=4,
        label="Kept",
        edgecolors="black",
        linewidths=0.5,
    )

    ax.step(
        kept_idx,
        frontier,
        where="post",
        color="#27ae60",
        linewidth=2,
        alpha=0.7,
        zorder=3,
        label="Running best",
    )

    for idx, metric in zip(kept_idx, kept_metric):
        desc = str(valid.loc[idx, DESCRIPTION_COLUMN]).strip()
        if len(desc) > 45:
            desc = desc[:42] + "..."
        ax.annotate(
            desc,
            (idx, metric),
            textcoords="offset points",
            xytext=(6, 6),
            fontsize=8.0,
            color="#1a7a3a",
            alpha=0.9,
            rotation=30,
            ha="left",
            va="bottom",
        )

    ax.set_xlabel("Experiment #", fontsize=12)
    ax.set_ylabel(METRIC_COLUMN, fontsize=12)
    ax.set_title("Autoresearch Progress", fontsize=14)
    ax.legend(loc="best", fontsize=9)
    ax.grid(True, alpha=0.2)

    best = frontier.iloc[-1]
    spread = abs(baseline - best) * 0.15 or 0.0005
    if LOWER_IS_BETTER:
        ax.set_ylim(best - spread, baseline + spread)
    else:
        ax.set_ylim(baseline - spread, best + spread)

    fig.tight_layout()
    fig.savefig(PLOT_PATH, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"Saved to {PLOT_PATH}")


def print_summary(df: pd.DataFrame) -> None:
    kept = df[df[STATUS_COLUMN] == KEEP_LABEL].copy()
    if kept.empty:
        print("No kept runs available for summary.")
        return

    baseline = df.iloc[0][METRIC_COLUMN]
    best_row = (
        kept.loc[kept[METRIC_COLUMN].idxmin()]
        if LOWER_IS_BETTER
        else kept.loc[kept[METRIC_COLUMN].idxmax()]
    )
    best = best_row[METRIC_COLUMN]
    delta = baseline - best if LOWER_IS_BETTER else best - baseline
    pct = 0.0 if baseline == 0 else delta / abs(baseline) * 100

    print(f"Baseline {METRIC_COLUMN}:  {baseline:.6f}")
    print(f"Best {METRIC_COLUMN}:      {best:.6f}")
    print(f"Total improvement: {delta:.6f} ({pct:.2f}%)")
    print(f"Best experiment:   {best_row[DESCRIPTION_COLUMN]}")
    print()

    print("Cumulative effort per improvement:")
    kept_sorted = kept.reset_index()
    for _, row in kept_sorted.iterrows():
        print(
            f"  Experiment #{row['index']:3d}: "
            f"{METRIC_COLUMN}={row[METRIC_COLUMN]:.6f}  "
            f"{row[DESCRIPTION_COLUMN]}"
        )

    kept["prev_metric"] = kept[METRIC_COLUMN].shift(1)
    if LOWER_IS_BETTER:
        kept["delta"] = kept["prev_metric"] - kept[METRIC_COLUMN]
    else:
        kept["delta"] = kept[METRIC_COLUMN] - kept["prev_metric"]
    hits = kept.iloc[1:].copy().sort_values("delta", ascending=False)

    print(f"{'Rank':>4}  {'Delta':>8}  {'Metric':>10}  Description")
    print("-" * 80)
    for rank, (_, row) in enumerate(hits.iterrows(), 1):
        print(
            f"{rank:4d}  {row['delta']:+.6f}  "
            f"{row[METRIC_COLUMN]:.6f}  {row[DESCRIPTION_COLUMN]}"
        )

    print(f"\n{'':>4}  {hits['delta'].sum():+.6f}  {'':>10}  TOTAL improvement over baseline")


def main() -> None:
    df = select_official_runs(load_results(RESULTS_PATH))
    print_header(df)
    print_outcomes(df)
    print_kept_runs(df)
    plot_progress(df)
    print_summary(df)


if __name__ == "__main__":
    main()
