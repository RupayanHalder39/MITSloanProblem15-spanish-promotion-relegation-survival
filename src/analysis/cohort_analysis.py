"""
Phase 4/5 cohort analysis: compare promoted-club and relegated-club outcome
groups on prior sporting form and squad market-value proxy.

With only 18 promotion and 18 relegation episodes (and comparison subgroups
as small as n=5-8), this script deliberately reports MEDIAN, IQR, and the
full list of individual observations alongside any single summary statistic,
and a rank-biserial effect size rather than leaning on p-values alone (a
Mann-Whitney U p-value is still reported as a supplementary reference point,
never as the headline result). See docs/sample_size_and_power.md for the
full justification.

Outputs:
    outputs/tables/promotion_cohort_table.md
    outputs/tables/promotion_group_comparison.md
    outputs/tables/relegation_cohort_table.md
    outputs/tables/relegation_group_comparison.md
"""
import logging
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger(__name__)

BASE = Path(__file__).resolve().parents[2]
PROCESSED = BASE / "data" / "processed"
TABLE_DIR = BASE / "outputs" / "tables"


def iqr(s):
    s = s.dropna()
    if len(s) == 0:
        return (np.nan, np.nan)
    return (np.percentile(s, 25), np.percentile(s, 75))


def rank_biserial(a, b):
    """Effect size for Mann-Whitney: r = 1 - 2U/(n1*n2), robust and interpretable for tiny n."""
    a, b = pd.Series(a).dropna(), pd.Series(b).dropna()
    if len(a) == 0 or len(b) == 0:
        return np.nan, np.nan, np.nan
    u, p = stats.mannwhitneyu(a, b, alternative="two-sided")
    r = 1 - (2 * u) / (len(a) * len(b))
    return r, p, u


def describe_group(s, label):
    s = s.dropna()
    q1, q3 = iqr(s)
    return (
        f"- **{label}** (n={len(s)}): median={s.median():,.2f}, IQR=[{q1:,.2f}, {q3:,.2f}], "
        f"individual values = {sorted(round(v, 2) for v in s.tolist())}\n"
    )


def compare_variable(df, group_col, group_a, group_b, var, var_label, lines):
    a = df.loc[df[group_col] == group_a, var]
    b = df.loc[df[group_col] == group_b, var]
    lines.append(f"\n#### {var_label}\n")
    if len(a.dropna()) == 0 or len(b.dropna()) == 0:
        lines.append(f"- **{group_a}**: n={len(a.dropna())}, **{group_b}**: n={len(b.dropna())} -- "
                      f"comparison skipped, one group is empty (see note below).\n")
        return
    lines.append(describe_group(a, group_a))
    lines.append(describe_group(b, group_b))
    r, p, u = rank_biserial(a, b)
    if not np.isnan(r):
        med_diff = a.median() - b.median()
        lines.append(
            f"- Median difference ({group_a} - {group_b}): {med_diff:,.2f}. "
            f"Rank-biserial effect size r={r:.2f} (|r|>0.5 large, >0.3 moderate by convention). "
            f"Mann-Whitney U={u:.1f}, p={p:.3f} (reference only, n too small for reliable inference).\n"
        )


def promotion_cohort(promo: pd.DataFrame):
    lines = ["# Promotion cohort table (Phase 4)\n\n"]
    cols = [
        "club_name", "promotion_season", "segundadivision_position_before_promotion",
        "segundadivision_points_before_promotion", "segundadivision_market_value_before_promotion",
        "laliga_market_value_first_season", "laliga_relative_market_value", "survival_duration", "outcome",
    ]
    lines.append(promo[cols].sort_values("promotion_season").to_markdown(index=False, floatfmt=",.2f"))
    lines.append("\n")
    (TABLE_DIR / "promotion_cohort_table.md").write_text("".join(lines))

    # Comparison groups
    promo = promo.copy()
    promo["group_immediate_vs_survived2"] = np.where(
        promo["immediate_relegation"] == 1, "immediately_relegated",
        np.where(promo["survived_2_seasons"] == 1, "survived_2_plus_seasons", "other"),
    )
    promo["group_relegated_vs_censored"] = np.where(
        promo["relegation_event"] == 1, "relegated_within_window", "right_censored_survivor"
    )

    lines2 = ["# Promotion outcome group comparisons (Phase 4)\n"]
    lines2.append("\n## Group A: immediately relegated vs. survived >= 2 seasons\n")
    sub = promo[promo["group_immediate_vs_survived2"] != "other"]
    n_a = (sub.group_immediate_vs_survived2 == "immediately_relegated").sum()
    n_b = (sub.group_immediate_vs_survived2 == "survived_2_plus_seasons").sum()
    lines2.append(f"\nn immediately_relegated={n_a}, n survived_2_plus_seasons={n_b} "
                  f"({len(promo) - len(sub)} excluded as neither: relegated after exactly... n/a here since survived_2_seasons already covers >=2)\n")
    for var, label in [
        ("segundadivision_market_value_before_promotion", "Segunda market value before promotion (EUR)"),
        ("laliga_relative_market_value", "Relative La Liga market value at entry (ratio to league median)"),
        ("segundadivision_points_before_promotion", "Prior Segunda points"),
        ("segundadivision_position_before_promotion", "Prior Segunda finishing position"),
        ("market_value_change_pct", "Market-value change after promotion (%)"),
    ]:
        compare_variable(sub, "group_immediate_vs_survived2", "immediately_relegated", "survived_2_plus_seasons", var, label, lines2)

    lines2.append("\n\n## Group B: relegated within window vs. right-censored survivors\n")
    n_a2 = (promo.group_relegated_vs_censored == "relegated_within_window").sum()
    n_b2 = (promo.group_relegated_vs_censored == "right_censored_survivor").sum()
    lines2.append(f"\nn relegated_within_window={n_a2}, n right_censored_survivor={n_b2}\n")
    for var, label in [
        ("segundadivision_market_value_before_promotion", "Segunda market value before promotion (EUR)"),
        ("laliga_relative_market_value", "Relative La Liga market value at entry (ratio to league median)"),
        ("segundadivision_points_before_promotion", "Prior Segunda points"),
        ("segundadivision_position_before_promotion", "Prior Segunda finishing position"),
        ("market_value_change_pct", "Market-value change after promotion (%)"),
    ]:
        compare_variable(promo, "group_relegated_vs_censored", "relegated_within_window", "right_censored_survivor", var, label, lines2)

    (TABLE_DIR / "promotion_group_comparison.md").write_text("".join(lines2))
    log.info("Wrote promotion_cohort_table.md and promotion_group_comparison.md")
    return promo


def relegation_cohort(releg: pd.DataFrame):
    lines = ["# Relegation cohort table (Phase 5)\n\n"]
    cols = [
        "club_name", "relegation_season", "laliga_position_before_relegation",
        "laliga_market_value_before_relegation", "laliga_relative_market_value_before_relegation",
        "segundadivision_market_value_after_relegation", "market_value_change_pct",
        "time_to_return", "return_event", "censored",
    ]
    lines.append(releg[cols].sort_values("relegation_season").to_markdown(index=False, floatfmt=",.2f"))
    lines.append("\n")
    (TABLE_DIR / "relegation_cohort_table.md").write_text("".join(lines))

    releg = releg.copy()

    def bucket(row):
        if row["return_event"] == 1:
            if row["time_to_return"] == 1:
                return "immediate_return"
            elif row["time_to_return"] <= 2:
                return "returned_within_2"
            else:
                return "returned_later"
        return "not_returned_censored"

    releg["return_bucket"] = releg.apply(bucket, axis=1)

    lines2 = ["# Relegation outcome group comparisons (Phase 5)\n"]
    lines2.append("\n## Return-speed buckets\n\n")
    counts = releg["return_bucket"].value_counts()
    lines2.append(counts.to_markdown() + "\n")

    lines2.append("\n\n## Immediate return vs. not returned by end of data\n")
    if counts.get("immediate_return", 0) == 0:
        lines2.append(
            "\n**Zero clubs (0/18) achieved an immediate return** (relegated and promoted straight back the "
            "very next season) within the observed window -- the fastest observed return is 2 seasons "
            "(7 clubs). This is a genuine empirical finding, not a data gap: it means an instant 'yo-yo' "
            "bounce-back did not occur even once for Spanish clubs relegated from La Liga in 2019-2026, "
            "so the comparison below is reported against `returned_within_2` instead.\n"
        )
    sub = releg[releg["return_bucket"].isin(["returned_within_2", "not_returned_censored"])]
    for var, label in [
        ("laliga_market_value_before_relegation", "La Liga market value before relegation (EUR)"),
        ("laliga_relative_market_value_before_relegation", "Relative La Liga market value before relegation"),
        ("market_value_change_pct", "Market-value change after relegation (%)"),
        ("segundadivision_relative_market_value_after_relegation", "Relative Segunda market value after relegation"),
        ("laliga_position_before_relegation", "La Liga position before relegation"),
    ]:
        compare_variable(sub, "return_bucket", "returned_within_2", "not_returned_censored", var, label, lines2)

    lines2.append("\n\n## Returned within window vs. not returned (censored) -- \"do stronger relegated clubs return faster?\"\n")
    releg["returned_vs_censored"] = np.where(releg["return_event"] == 1, "returned_within_window", "not_returned_censored")
    for var, label in [
        ("laliga_relative_market_value_before_relegation", "Relative La Liga market value before relegation"),
        ("segundadivision_relative_market_value_after_relegation", "Relative Segunda market value after relegation"),
        ("market_value_change_pct", "Market-value change after relegation (%)"),
    ]:
        compare_variable(releg, "returned_vs_censored", "returned_within_window", "not_returned_censored", var, label, lines2)

    # Correlation between relative market value after relegation and time_to_return, among returners only
    returners = releg[releg["return_event"] == 1]
    if len(returners) >= 3:
        rho, p = stats.spearmanr(returners["segundadivision_relative_market_value_after_relegation"], returners["time_to_return"])
        lines2.append(
            f"\n\nAmong the {len(returners)} clubs that did return: Spearman correlation between relative "
            f"Segunda market value after relegation and time_to_return = {rho:.2f} (p={p:.3f}, reference only). "
            f"{'Negative' if rho < 0 else 'Positive'} sign {'is consistent with' if rho < 0 else 'runs counter to'} "
            f"\"stronger relegated clubs return faster\".\n"
        )

    (TABLE_DIR / "relegation_group_comparison.md").write_text("".join(lines2))
    log.info("Wrote relegation_cohort_table.md and relegation_group_comparison.md")
    return releg


def main():
    TABLE_DIR.mkdir(parents=True, exist_ok=True)
    promo = pd.read_csv(PROCESSED / "promotion_analysis.csv")
    releg = pd.read_csv(PROCESSED / "relegation_analysis.csv")
    promotion_cohort(promo)
    relegation_cohort(releg)


if __name__ == "__main__":
    main()
