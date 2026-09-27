"""
Phase 8: interpretable club typology (managerial tool, not a statistical model).

Promotion typology: 2x2 split at the sample median of (a) RRP in the first
La Liga season [entry resource position] and (b) post-promotion squad-value
uplift %. Relegation typology: split at the sample median of RRP in the
first Segunda season vs. whether the club returned to La Liga within 2
seasons.

IMPORTANT: quadrant boundaries are SAMPLE-MEDIAN splits of n=18 -- quadrants
have as few as 3 observations. This is presented as a managerial
interpretation lens, not a validated statistical clustering. Labels are
chosen/adjusted based on what the data actually shows (see below), not
assumed in advance.

Output: outputs/tables/club_typology.md
"""
import logging
from pathlib import Path

import pandas as pd

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger(__name__)

BASE = Path(__file__).resolve().parents[2]
PROCESSED = BASE / "data" / "processed"
TABLE_DIR = BASE / "outputs" / "tables"

PROMO_LABELS = {
    "high_entry_high_uplift": "Resourced Investors",
    "low_entry_high_uplift": "Aggressive Closers",
    "high_entry_low_uplift": "Complacent Entrants",
    "low_entry_low_uplift": "Under-Resourced Entrants",
}


def promotion_typology(p: pd.DataFrame):
    entry_med = p["rrp_first_laliga_season"].median()
    uplift_med = p["market_value_change_pct"].median()

    def quad(row):
        he = row["rrp_first_laliga_season"] >= entry_med
        hu = row["market_value_change_pct"] >= uplift_med
        if he and hu:
            return "high_entry_high_uplift"
        if he and not hu:
            return "high_entry_low_uplift"
        if not he and hu:
            return "low_entry_high_uplift"
        return "low_entry_low_uplift"

    p = p.copy()
    p["quadrant"] = p.apply(quad, axis=1)
    p["quadrant_label"] = p["quadrant"].map(PROMO_LABELS)

    summary = p.groupby("quadrant_label").agg(
        n=("club_name", "count"),
        median_survival=("survival_duration", "median"),
        immediate_relegations=("immediate_relegation", "sum"),
        survived_2plus=("survived_2_seasons", "sum"),
    ).reindex(list(PROMO_LABELS.values()))

    return p, summary, entry_med, uplift_med


def relegation_typology(r: pd.DataFrame):
    rrp_med = r["rrp_first_segunda_season"].median()

    def quad(row):
        hr = row["rrp_first_segunda_season"] >= rrp_med
        fast = row["returned_within_2"] == 1
        if hr and fast:
            return "high_rrp_fast_return"
        if hr and not fast:
            return "high_rrp_slow_or_no_return"
        if not hr and fast:
            return "low_rrp_fast_return"
        return "low_rrp_slow_or_no_return"

    r = r.copy()
    r["quadrant"] = r.apply(quad, axis=1)
    labels = {
        "high_rrp_fast_return": "Resource-Dominant Returners",
        "high_rrp_slow_or_no_return": "Resource-Dominant Laggards",
        "low_rrp_fast_return": "Resource-Weak Returners",
        "low_rrp_slow_or_no_return": "Resource-Weak Non-Returners",
    }
    r["quadrant_label"] = r["quadrant"].map(labels)
    summary = r.groupby("quadrant_label").agg(
        n=("club_name", "count"),
        median_time_to_return=("time_to_return", "median"),
        returned=("return_event", "sum"),
        censored=("censored", "sum"),
    ).reindex(list(labels.values()))

    return r, summary, rrp_med


def main():
    TABLE_DIR.mkdir(parents=True, exist_ok=True)
    promo = pd.read_csv(PROCESSED / "promotion_analysis.csv")
    releg = pd.read_csv(PROCESSED / "relegation_analysis.csv")

    p, p_summary, entry_med, uplift_med = promotion_typology(promo)
    r, r_summary, rrp_med = relegation_typology(releg)

    lines = ["# Club typology (Phase 8) -- managerial interpretation tool, not a statistical model\n\n"]

    lines.append("## Promotion typology: entry resource position x post-promotion uplift\n\n")
    lines.append(f"Split at sample medians: entry RRP median={entry_med:.2f}, uplift median={uplift_med:.1f}%.\n\n")
    lines.append(p_summary.to_markdown() + "\n\n")
    lines.append(
        "**Note on labels:** the data does NOT cleanly support a naive expectation that "
        "'high entry + high uplift' would be the best-performing quadrant. The best median survival "
        "(4.0 seasons) is actually in the *Aggressive Closers* quadrant (low entry RRP, high uplift, "
        "n=3: Elche 2020-21, Cádiz 2020-21, Rayo Vallecano 2021-22) -- higher than *Resourced "
        "Investors* (high entry, high uplift, n=6, median 2.0 seasons). This is consistent with the "
        "main-effect finding that uplift SIZE matters more than starting position (r=0.76 on uplift "
        "vs r=0.40 on entry RRP alone), but n=3 in that quadrant means this specific quadrant "
        "comparison should be read as illustrative, not a validated finding.\n\n"
    )
    lines.append("### Full assignment\n\n")
    cols = ["club_name", "promotion_season", "rrp_first_laliga_season", "market_value_change_pct", "quadrant_label", "survival_duration", "outcome"]
    lines.append(p[cols].sort_values("quadrant_label").round(2).to_markdown(index=False) + "\n\n")

    lines.append("## Relegation typology: first-Segunda RRP x return speed\n\n")
    lines.append(f"Split at sample median RRP={rrp_med:.2f}; 'fast' = returned within 2 seasons.\n\n")
    lines.append(r_summary.to_markdown() + "\n\n")
    lines.append(
        "**Note on labels:** unlike the promotion side, this is NOT really a 2x2 interaction -- it is "
        "close to a single dominant axis. 6/6 *Resource-Dominant Returners* returned, all in exactly 2 "
        "seasons; 7/8 *Resource-Weak Non-Returners* are still censored. The off-diagonal cells are thin "
        "(1 and 3 observations) and do not support a genuine typology beyond 'relative Segunda "
        "dominance, roughly, predicts return' -- reported here for completeness and because the "
        "project brief asked for it, but the honest read is a single-axis relationship, not four "
        "distinct managerial archetypes.\n\n"
    )
    lines.append("### Full assignment\n\n")
    cols2 = ["club_name", "relegation_season", "rrp_first_segunda_season", "time_to_return", "return_event", "censored", "quadrant_label"]
    lines.append(r[cols2].sort_values("quadrant_label").round(2).to_markdown(index=False) + "\n")

    out = TABLE_DIR / "club_typology.md"
    out.write_text("".join(lines))
    log.info("Wrote %s", out)


if __name__ == "__main__":
    main()
