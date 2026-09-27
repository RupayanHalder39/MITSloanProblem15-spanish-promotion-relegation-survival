"""
Initial descriptive / exploratory survival analysis.

Produces:
    outputs/figures/promotion_survival_km.png
    outputs/figures/relegation_return_km.png
    outputs/figures/league_transition_matrix.png
    outputs/tables/descriptive_summary.md

This is intentionally a first pass: sample sizes are small (18 promotion
episodes, 18 relegation episodes over 6 usable seasons of transitions), so
these Kaplan-Meier curves are descriptive/illustrative, not a publishable
inferential result. See DataFeasibilityAuditReport.md section 7-8 for the
power/sample-size caveat.
"""
import logging
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
from lifelines import KaplanMeierFitter

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger(__name__)

BASE = Path(__file__).resolve().parents[2]
PROCESSED = BASE / "data" / "processed"
FIG_DIR = BASE / "outputs" / "figures"
TABLE_DIR = BASE / "outputs" / "tables"

plt.rcParams.update({"figure.dpi": 150, "font.size": 10, "axes.spines.top": False, "axes.spines.right": False})


def plot_promotion_survival():
    df = pd.read_csv(PROCESSED / "promotion_episodes.csv")
    kmf = KaplanMeierFitter()
    kmf.fit(df["survival_duration"], event_observed=df["relegation_event"], label="Promoted clubs")

    fig, ax = plt.subplots(figsize=(6, 4))
    kmf.plot_survival_function(ax=ax, ci_show=True)
    ax.set_xlabel("Seasons in La Liga since promotion")
    ax.set_ylabel("P(still in La Liga)")
    ax.set_title(f"La Liga survival after promotion (n={len(df)} episodes, 2020-2026)")
    ax.set_ylim(0, 1.02)
    fig.tight_layout()
    out = FIG_DIR / "promotion_survival_km.png"
    fig.savefig(out)
    plt.close(fig)
    log.info("Wrote %s", out)
    return kmf


def plot_relegation_return():
    df = pd.read_csv(PROCESSED / "relegation_episodes.csv")
    kmf = KaplanMeierFitter()
    kmf.fit(df["time_to_return"], event_observed=df["return_event"], label="Relegated clubs")

    fig, ax = plt.subplots(figsize=(6, 4))
    kmf.plot_survival_function(ax=ax, ci_show=True)
    ax.set_xlabel("Seasons since relegation")
    ax.set_ylabel("P(not yet returned to La Liga)")
    ax.set_title(f"Time to return to La Liga after relegation (n={len(df)} episodes, 2020-2026)")
    ax.set_ylim(0, 1.02)
    fig.tight_layout()
    out = FIG_DIR / "relegation_return_km.png"
    fig.savefig(out)
    plt.close(fig)
    log.info("Wrote %s", out)
    return kmf


def plot_transition_matrix():
    df = pd.read_csv(PROCESSED / "league_transitions.csv")
    states = ["La Liga", "Segunda División", "Primera Federación"]
    counts = pd.DataFrame(0, index=states, columns=states + ["Exited observed pyramid"])
    for _, row in df.iterrows():
        s0, s1 = row["state_t"], row["state_t_plus_1"]
        if s0 in states and s1 in counts.columns:
            counts.loc[s0, s1] += 1

    fig, ax = plt.subplots(figsize=(6.5, 4.5))
    im = ax.imshow(counts.values, cmap="Greens")
    ax.set_xticks(range(len(counts.columns)))
    ax.set_xticklabels(counts.columns, rotation=30, ha="right")
    ax.set_yticks(range(len(states)))
    ax.set_yticklabels(states)
    for i in range(len(states)):
        for j in range(len(counts.columns)):
            ax.text(j, i, counts.values[i, j], ha="center", va="center", fontsize=9)
    ax.set_title("Season-to-season division transitions, 2019-20..2025-26")
    fig.colorbar(im, ax=ax, shrink=0.8, label="club-seasons")
    fig.tight_layout()
    out = FIG_DIR / "league_transition_matrix.png"
    fig.savefig(out)
    plt.close(fig)
    log.info("Wrote %s", out)
    return counts


def write_summary(promo_kmf, releg_kmf, transition_counts):
    promo = pd.read_csv(PROCESSED / "promotion_episodes.csv")
    releg = pd.read_csv(PROCESSED / "relegation_episodes.csv")
    club_seasons = pd.read_csv(PROCESSED / "spanish_club_seasons.csv")

    lines = []
    lines.append("# Descriptive summary\n")
    lines.append(f"- Club-seasons: {len(club_seasons)} ({club_seasons['club_id'].nunique()} distinct clubs, "
                  f"{club_seasons['season'].nunique()} seasons, 2019-2020..2025-2026)\n")
    lines.append(f"- Promotion episodes (Segunda -> La Liga): {len(promo)}, of which "
                  f"{int(promo['relegation_event'].sum())} were relegated back down within the window and "
                  f"{int(promo['censored'].sum())} are right-censored (still in La Liga at end of data)\n")
    lines.append(f"- Immediate relegation rate of promoted clubs (survival_duration==1 and relegation_event==1): "
                  f"{int(((promo['survival_duration']==1) & (promo['relegation_event']==1)).sum())} / {len(promo)}\n")
    lines.append(f"- Relegation episodes (La Liga -> Segunda): {len(releg)}, of which "
                  f"{int(releg['return_event'].sum())} returned to La Liga within the window and "
                  f"{int(releg['censored'].sum())} have not yet returned (right-censored)\n")
    lines.append("\n## Kaplan-Meier median survival (La Liga tenure after promotion)\n")
    try:
        lines.append(f"- Median seasons survived: {promo_kmf.median_survival_time_}\n")
    except Exception:
        lines.append("- Median not reached within observed window (fewer than 50% of episodes have failed).\n")
    lines.append("\n## Kaplan-Meier median time to return (after relegation)\n")
    try:
        lines.append(f"- Median seasons to return: {releg_kmf.median_survival_time_}\n")
    except Exception:
        lines.append("- Median not reached within observed window (fewer than 50% of episodes have returned).\n")
    lines.append("\n## Division transition counts\n")
    lines.append(transition_counts.to_markdown())
    lines.append("\n")

    TABLE_DIR.mkdir(parents=True, exist_ok=True)
    out = TABLE_DIR / "descriptive_summary.md"
    out.write_text("".join(lines))
    log.info("Wrote %s", out)


def main():
    FIG_DIR.mkdir(parents=True, exist_ok=True)
    TABLE_DIR.mkdir(parents=True, exist_ok=True)
    promo_kmf = plot_promotion_survival()
    releg_kmf = plot_relegation_return()
    counts = plot_transition_matrix()
    write_summary(promo_kmf, releg_kmf, counts)


if __name__ == "__main__":
    main()
