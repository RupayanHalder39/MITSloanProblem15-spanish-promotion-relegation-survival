"""Phase 10: master tables T1-T8 for the expanded analysis."""
import numpy as np
import pandas as pd
from scipy import stats

from plot_common import load, TABLE_DIR


def rank_biserial(a, b):
    a, b = pd.Series(a).dropna(), pd.Series(b).dropna()
    u, p_val = stats.mannwhitneyu(a, b, alternative="two-sided")
    r = 1 - (2 * u) / (len(a) * len(b))
    return r, p_val, len(a), len(b)


def t01_promotion_master(p):
    cols = {
        "club_name": "club", "promotion_season": "promotion_season",
        "segundadivision_position_before_promotion": "last_segunda_position",
        "segundadivision_points_before_promotion": "last_segunda_points",
        "segundadivision_market_value_before_promotion": "last_segunda_market_value_eur",
        "rrp_last_segunda_season": "last_segunda_rrp",
        "laliga_market_value_first_season": "first_laliga_market_value_eur",
        "rrp_first_laliga_season": "first_laliga_rrp",
        "promotion_resource_shock": "promotion_shock",
        "promotion_resource_ratio": "promotion_ratio",
        "market_value_change_pct": "uplift_pct",
        "survival_duration": "survival_duration",
        "relegation_event": "event",
        "censored": "censored",
        "outcome": "outcome_category",
    }
    out = p[list(cols.keys())].rename(columns=cols).round(3)
    out.to_csv(TABLE_DIR / "T01_promotion_episode_master_table.csv", index=False)
    print(f"Wrote {TABLE_DIR / 'T01_promotion_episode_master_table.csv'}")
    return out


def t02_relegation_master(r):
    cols = {
        "club_name": "club", "relegation_season": "relegation_season",
        "laliga_position_before_relegation": "last_laliga_position",
        "laliga_points_before_relegation": "last_laliga_points",
        "laliga_market_value_before_relegation": "last_laliga_market_value_eur",
        "rrp_last_laliga_season": "last_laliga_rrp",
        "segundadivision_market_value_after_relegation": "first_segunda_market_value_eur",
        "rrp_first_segunda_season": "first_segunda_rrp",
        "relegation_resource_shock": "relegation_shock",
        "relegation_resource_ratio": "relegation_ratio",
        "market_value_change_pct": "value_change_pct",
        "time_to_return": "time_to_return",
        "return_event": "event",
        "censored": "censored",
    }
    out = r[list(cols.keys())].rename(columns=cols).round(3)
    out["outcome"] = np.where(out.event == 1, "returned", "not_yet_returned_censored")
    out.to_csv(TABLE_DIR / "T02_relegation_episode_master_table.csv", index=False)
    print(f"Wrote {TABLE_DIR / 'T02_relegation_episode_master_table.csv'}")
    return out


def t03_season_promotion_summary(p):
    g = p.groupby("promotion_season").agg(
        promoted_clubs=("club_name", "count"),
        median_entry_rrp=("rrp_first_laliga_season", "median"),
        median_uplift_pct=("market_value_change_pct", "median"),
        immediate_relegations=("immediate_relegation", "sum"),
        survived_2plus=("survived_2_seasons", "sum"),
        censored=("censored", "sum"),
    ).round(2).reset_index()
    g.to_csv(TABLE_DIR / "T03_season_promotion_summary.csv", index=False)
    print(f"Wrote {TABLE_DIR / 'T03_season_promotion_summary.csv'}")
    return g


def t04_season_relegation_summary(r):
    g = r.groupby("relegation_season").agg(
        relegated_clubs=("club_name", "count"),
        median_first_segunda_rrp=("rrp_first_segunda_season", "median"),
        median_resource_shock=("relegation_resource_shock", "median"),
        returned_within_2=("returned_within_2", "sum"),
        returned_later=("return_event", lambda s: int((s == 1).sum())),
        censored=("censored", "sum"),
    ).round(2).reset_index()
    g["returned_later"] = g["returned_later"] - r.groupby("relegation_season").returned_within_2.sum().values
    g.to_csv(TABLE_DIR / "T04_season_relegation_summary.csv", index=False)
    print(f"Wrote {TABLE_DIR / 'T04_season_relegation_summary.csv'}")
    return g


def t05_promotion_outcome_comparison(p):
    imm = p[p.immediate_relegation == 1]
    surv2 = p[p.survived_2_seasons == 1]
    rows = []
    for var, label in [
        ("rrp_first_laliga_season", "First La Liga RRP"),
        ("rrp_last_segunda_season", "Last Segunda RRP"),
        ("promotion_resource_shock", "Promotion shock"),
        ("promotion_resource_ratio", "Promotion ratio"),
        ("market_value_change_pct", "Uplift %"),
        ("segundadivision_points_before_promotion", "Prior points"),
    ]:
        r_est, p_val, n1, n2 = rank_biserial(imm[var], surv2[var])
        rows.append({
            "variable": label, "median_immediately_relegated": round(imm[var].median(), 3),
            "median_survived_2plus": round(surv2[var].median(), 3),
            "difference": round(imm[var].median() - surv2[var].median(), 3),
            "rank_biserial_r": round(r_est, 3), "exploratory_p": round(p_val, 3), "n1": n1, "n2": n2,
        })
    out = pd.DataFrame(rows)
    out.to_csv(TABLE_DIR / "T05_promotion_outcome_comparison.csv", index=False)
    print(f"Wrote {TABLE_DIR / 'T05_promotion_outcome_comparison.csv'}")
    return out


def t06_relegation_outcome_comparison(r):
    fast = r[r.returned_within_2 == 1]
    slow = r[r.return_event == 0]
    rows = []
    for var, label in [
        ("rrp_first_segunda_season", "First Segunda RRP"),
        ("rrp_last_laliga_season", "Last La Liga RRP"),
        ("relegation_resource_shock", "Relegation shock"),
        ("relegation_resource_ratio", "Relegation ratio"),
        ("market_value_change_pct", "Value change %"),
    ]:
        r_est, p_val, n1, n2 = rank_biserial(fast[var], slow[var])
        rows.append({
            "variable": label, "median_fast_return": round(fast[var].median(), 3),
            "median_not_returned": round(slow[var].median(), 3),
            "difference": round(fast[var].median() - slow[var].median(), 3),
            "rank_biserial_r": round(r_est, 3), "exploratory_p": round(p_val, 3), "n1": n1, "n2": n2,
        })
    out = pd.DataFrame(rows)
    out.to_csv(TABLE_DIR / "T06_relegation_outcome_comparison.csv", index=False)
    print(f"Wrote {TABLE_DIR / 'T06_relegation_outcome_comparison.csv'}")
    return out


def t08_claim_evidence_matrix():
    rows = [
        dict(claim="18/18 promoted clubs entered La Liga below league median RRP",
             graph="P1, P3, X1, X3", table="T1", n="18", effect_size="n/a (direct count)",
             statistical_status="Observed fact", evidence_grade="A", caution="None -- exceptionless count"),
        dict(claim="18/18 promoted clubs had a negative Promotion Resource Shock",
             graph="P2, X1", table="T1, T7", n="18", effect_size="n/a (direct count)",
             statistical_status="Observed fact", evidence_grade="A", caution="Robust under mean/rank alternative definitions (T7)"),
        dict(claim="18/18 relegated clubs landed in Segunda above league median RRP",
             graph="R1, R3, X1, X3", table="T2", n="18", effect_size="n/a (direct count)",
             statistical_status="Observed fact", evidence_grade="A", caution="None -- exceptionless count"),
        dict(claim="18/18 relegated clubs had a positive Relegation Resource Shock",
             graph="R2, X1", table="T2, T7", n="18", effect_size="n/a (direct count)",
             statistical_status="Observed fact", evidence_grade="A", caution="Robust under mean/rank alternative definitions (T7)"),
        dict(claim="Post-promotion uplift % separates immediate relegation from 2+ season survival",
             graph="P5, P6, C3", table="T5", n="5 vs 10", effect_size="r=0.76",
             statistical_status="Exploratory (Mann-Whitney reference p=0.019)", evidence_grade="B",
             caution="Leave-one-out stable (r range 0.70-0.85, B4); small n"),
        dict(claim="First-Segunda RRP separates fast returners from prolonged absence",
             graph="R4, R6, R8, C3", table="T6", n="7 vs 8", effect_size="r=-0.82",
             statistical_status="Exploratory (Mann-Whitney reference p=0.006)", evidence_grade="B",
             caution="Leave-one-out stable (r range -0.96 to -0.79, B4); strongest finding in the project"),
        dict(claim="Entry RRP alone (without uplift) separates promotion outcomes",
             graph="P5, C3", table="T5", n="5 vs 10", effect_size="r=0.40",
             statistical_status="Exploratory (p=0.254)", evidence_grade="C",
             caution="Weaker and noisier than the uplift-based finding; visible counter-examples (Cadiz)"),
        dict(claim="Additive Promotion Resource Shock separates promotion outcomes",
             graph="P2, C3", table="T5", n="5 vs 10", effect_size="r=0.24",
             statistical_status="Exploratory (p=0.513)", evidence_grade="D",
             caution="Notably weaker than the % uplift version of the same question -- reported honestly, not hidden"),
        dict(claim="Cox model: relative market value at entry predicts relegation hazard",
             graph="(not separately plotted; see exploratory_model_results.md)", table="n/a",
             n="18 (10 events)", effect_size="HR=0.50, 95% CI [0.11, 2.24]",
             statistical_status="Exploratory, NOT significant", evidence_grade="D",
             caution="CI crosses null; coefficient sensitive to a single observation (Girona) on the original LOO check"),
        dict(claim="Promotion-side typology quadrants are validated managerial archetypes",
             graph="P7", table="club_typology.md", n="cells as small as 3",
             effect_size="n/a", statistical_status="Illustrative only", evidence_grade="D",
             caution="Explicitly NOT a validated 4-way typology -- smallest cells are anecdotal"),
        dict(claim="Resource-advantage erosion is faster for clubs that fail to return (R7)",
             graph="R7", table="n/a", n="7 vs 11 (event-time cells)",
             effect_size="visual pattern only", statistical_status="Confounded -- see caution",
             evidence_grade="E", caution="For fast-return clubs, t>=1 points are measured AFTER they are already back in "
                                          "La Liga (division-relative RRP switches denominator) -- this figure does NOT "
                                          "cleanly isolate within-Segunda erosion; flagged as a methodological limitation, "
                                          "not removed, per instructions to report weaknesses honestly"),
    ]
    out = pd.DataFrame(rows)
    out.to_csv(TABLE_DIR / "T08_claim_evidence_matrix.csv", index=False)
    print(f"Wrote {TABLE_DIR / 'T08_claim_evidence_matrix.csv'}")
    return out


def main():
    p = load("promotion_analysis.csv")
    r = load("relegation_analysis.csv")
    t01_promotion_master(p)
    t02_relegation_master(r)
    t03_season_promotion_summary(p)
    t04_season_relegation_summary(r)
    t05_promotion_outcome_comparison(p)
    t06_relegation_outcome_comparison(r)
    t08_claim_evidence_matrix()


if __name__ == "__main__":
    main()
