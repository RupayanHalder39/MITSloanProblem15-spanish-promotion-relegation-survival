"""
Phase 6: the central result table for the paper.

Outputs:
    outputs/tables/main_results_table.md
    outputs/tables/main_results_table.csv
"""
import logging
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats
from lifelines import KaplanMeierFitter

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger(__name__)

BASE = Path(__file__).resolve().parents[2]
PROCESSED = BASE / "data" / "processed"
TABLE_DIR = BASE / "outputs" / "tables"


def med_iqr(s):
    s = pd.Series(s).dropna()
    if len(s) == 0:
        return "n/a"
    q1, q3 = np.percentile(s, 25), np.percentile(s, 75)
    return f"{s.median():.2f} [{q1:.2f}, {q3:.2f}]"


def rank_biserial(a, b):
    a, b = pd.Series(a).dropna(), pd.Series(b).dropna()
    if len(a) == 0 or len(b) == 0:
        return np.nan, np.nan
    u, p = stats.mannwhitneyu(a, b, alternative="two-sided")
    r = 1 - (2 * u) / (len(a) * len(b))
    return r, p


def main():
    TABLE_DIR.mkdir(parents=True, exist_ok=True)
    promo = pd.read_csv(PROCESSED / "promotion_analysis.csv")
    releg = pd.read_csv(PROCESSED / "relegation_analysis.csv")

    rows = []

    # --- Promotion side ---
    rows.append(("PROMOTION SIDE", "", ""))
    rows.append(("Number of episodes", len(promo), ""))
    rows.append(("Immediate relegation rate", f"{int(promo.immediate_relegation.sum())}/{len(promo)} "
                                                f"({100*promo.immediate_relegation.mean():.0f}%)", ""))
    rows.append(("Survived >= 2 seasons", f"{int(promo.survived_2_seasons.sum())}/{len(promo)} "
                                           f"({100*promo.survived_2_seasons.mean():.0f}%)", ""))
    rows.append(("Right-censored (still in La Liga)", f"{int(promo.censored.sum())}/{len(promo)}", ""))
    kmf_p = KaplanMeierFitter().fit(promo.survival_duration, event_observed=promo.relegation_event)
    rows.append(("Kaplan-Meier median survival (censoring-adjusted, seasons)", f"{kmf_p.median_survival_time_:.1f}", ""))
    rows.append(("Naive median survival duration (seasons), median [IQR] -- NOT censoring-adjusted, kept only for the group comparisons below", med_iqr(promo.survival_duration), ""))
    rows.append(("Median RRP, last Segunda season, median [IQR]", med_iqr(promo.rrp_last_segunda_season), ""))
    rows.append(("Median RRP, first La Liga season, median [IQR]", med_iqr(promo.rrp_first_laliga_season), ""))
    rows.append(("Median Promotion Resource Shock, median [IQR]", med_iqr(promo.promotion_resource_shock), ""))
    rows.append(("Median Promotion Resource Ratio, median [IQR]", med_iqr(promo.promotion_resource_ratio), ""))
    rows.append(("Median squad market-value uplift (%), median [IQR]", med_iqr(promo.market_value_change_pct), ""))
    rows.append(("Clubs entering La Liga above league median (RRP > 1.0)", f"{int((promo.rrp_first_laliga_season > 1.0).sum())}/{len(promo)}", ""))

    rows.append(("", "", ""))
    rows.append(("Survivor (2+ seasons) vs. immediately-relegated comparison", "Immediately relegated (n=5)", "Survived 2+ seasons (n=10)"))
    for var, label in [
        ("rrp_first_laliga_season", "  RRP, first La Liga season"),
        ("promotion_resource_shock", "  Promotion Resource Shock"),
        ("market_value_change_pct", "  Squad value uplift (%)"),
        ("segundadivision_points_before_promotion", "  Prior Segunda points"),
    ]:
        a = promo.loc[promo.immediate_relegation == 1, var]
        b = promo.loc[promo.survived_2_seasons == 1, var]
        r, p = rank_biserial(a, b)
        rows.append((label, med_iqr(a), med_iqr(b)))
        rows.append((f"    -> rank-biserial r={r:.2f}, Mann-Whitney p={p:.3f} (exploratory reference only)", "", ""))

    # --- Relegation side ---
    rows.append(("", "", ""))
    rows.append(("RELEGATION SIDE", "", ""))
    rows.append(("Number of episodes", len(releg), ""))
    kmf_r = KaplanMeierFitter().fit(releg.time_to_return, event_observed=releg.return_event)
    rows.append(("Kaplan-Meier median time to return (censoring-adjusted, seasons)", f"{kmf_r.median_survival_time_:.1f}", ""))
    rows.append(("Naive median time to return (seasons), median [IQR] -- NOT censoring-adjusted, kept only for the group comparisons below", med_iqr(releg.time_to_return), ""))
    rows.append(("Returned within 2 seasons", f"{int(releg.returned_within_2.sum())}/{len(releg)} "
                                                f"({100*releg.returned_within_2.mean():.0f}%)", ""))
    rows.append(("Returned within window (any duration)", f"{int(releg.return_event.sum())}/{len(releg)}", ""))
    rows.append(("Right-censored (not yet returned)", f"{int(releg.censored.sum())}/{len(releg)}", ""))
    rows.append(("Immediate return (next season)", f"{int(releg.immediate_return.sum())}/{len(releg)} (0%)", ""))
    rows.append(("Median RRP, last La Liga season, median [IQR]", med_iqr(releg.rrp_last_laliga_season), ""))
    rows.append(("Median RRP, first Segunda season, median [IQR]", med_iqr(releg.rrp_first_segunda_season), ""))
    rows.append(("Median Relegation Resource Shock, median [IQR]", med_iqr(releg.relegation_resource_shock), ""))
    rows.append(("Median Relegation Resource Ratio, median [IQR]", med_iqr(releg.relegation_resource_ratio), ""))
    rows.append(("Clubs landing in Segunda above league median (RRP > 1.0)", f"{int((releg.rrp_first_segunda_season > 1.0).sum())}/{len(releg)}", ""))

    rows.append(("", "", ""))
    rows.append(("Fast return (<=2 seasons) vs. not-returned comparison", "Returned <=2 seasons (n=7)", "Not returned, censored (n=8)"))
    fast = releg[releg.returned_within_2 == 1]
    slow = releg[releg.return_event == 0]
    for var, label in [
        ("rrp_first_segunda_season", "  RRP, first Segunda season"),
        ("relegation_resource_shock", "  Relegation Resource Shock"),
        ("rrp_last_laliga_season", "  RRP, last La Liga season"),
    ]:
        r, p = rank_biserial(fast[var], slow[var])
        rows.append((label, med_iqr(fast[var]), med_iqr(slow[var])))
        rows.append((f"    -> rank-biserial r={r:.2f}, Mann-Whitney p={p:.3f} (exploratory reference only)", "", ""))

    out = pd.DataFrame(rows, columns=["Metric", "Value / Group A", "Group B"])
    out.to_csv(TABLE_DIR / "main_results_table.csv", index=False)
    (TABLE_DIR / "main_results_table.md").write_text(
        "# Main results table\n\nAll medians reported as `median [IQR-low, IQR-high]`. "
        "p-values are Mann-Whitney reference statistics only -- see docs/sample_size_and_power.md "
        "before treating any of them as confirmatory.\n\n" + out.to_markdown(index=False) + "\n"
    )
    log.info("Wrote main_results_table.md/.csv (%d rows)", len(out))


if __name__ == "__main__":
    main()
