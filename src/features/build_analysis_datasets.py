"""
Build the research-analysis datasets that attach club-season characteristics
to each promotion/relegation episode:
    data/processed/promotion_analysis.csv
    data/processed/relegation_analysis.csv

Season-alignment conventions (read this before touching anything downstream)
------------------------------------------------------------------------------
`promotion_episodes.csv`'s `promotion_season` is already defined (in
build_episodes.py) as the club's FIRST season IN La Liga after coming up from
Segunda. Therefore, for a promotion episode:
  - "before promotion" / "the promotion-winning Segunda season" = the row for
    this club at season_idx = promotion_season_idx - 1, division = 2. This is
    the Segunda season the club won/played its way up from.
  - "first La Liga season" = the row at season_idx = promotion_season_idx
    itself (division = 1).

Symmetrically, `relegation_episodes.csv`'s `relegation_season` is already the
club's FIRST season back IN Segunda after coming down from La Liga. So:
  - "before relegation" = the row at season_idx = relegation_season_idx - 1,
    division = 1 (the last La Liga season before going down).
  - "first season after relegation" = the row at season_idx =
    relegation_season_idx itself (division = 2).

Every "before"/"after" lookup below is done by an explicit (club_id,
season_idx) join against spanish_club_seasons.csv -- never by assuming row
order -- so a missing neighbouring season (shouldn't happen inside the
observed window, but checked) raises a visible warning instead of silently
producing a wrong number.

market_value_eur, and everything derived from it, is a squad market-value
PROXY (see build_relative_market_value.py), not real financial data.

Relative Resource Position (RRP) and Resource Shock -- formal definitions
------------------------------------------------------------------------------
    RRP_it = club i's squad market value in season t
             / median squad market value of that club's division in season t

This is exactly the `market_value_to_league_median` column already computed by
build_relative_market_value.py, aliased here under the RRP name used in the
paper. RRP = 1.0 is exactly at the league median; RRP < 1.0 is below it.

    Promotion Resource Shock  = RRP_first_LaLiga_season  - RRP_last_Segunda_season
    Promotion Resource Ratio  = RRP_first_LaLiga_season  / RRP_last_Segunda_season
    Relegation Resource Shock = RRP_first_Segunda_season - RRP_last_LaLiga_season
    Relegation Resource Ratio = RRP_first_Segunda_season / RRP_last_LaLiga_season

A negative Promotion Resource Shock means the club's relative resource
standing WORSENED on promotion (it was more dominant, relatively, in Segunda
than it is in La Liga) even though its absolute squad value rose. A positive
Relegation Resource Shock means the club's relative standing IMPROVED on
relegation (it went from a middling/weak La Liga club to a resource-strong
Segunda club).
"""
import logging
from pathlib import Path

import numpy as np
import pandas as pd

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger(__name__)

BASE = Path(__file__).resolve().parents[2]
PROCESSED = BASE / "data" / "processed"


def load_club_seasons():
    df = pd.read_csv(PROCESSED / "spanish_club_seasons.csv")
    return df.set_index(["club_id", "season_idx"])


def get_row(cs, club_id, season_idx, expected_division, context):
    key = (club_id, season_idx)
    if key not in cs.index:
        log.warning("Missing club-season row for %s at season_idx=%d (%s)", club_id, season_idx, context)
        return None
    row = cs.loc[key]
    if row["division"] != expected_division:
        log.warning(
            "Unexpected division for %s at season_idx=%d: expected %d, got %d (%s)",
            club_id, season_idx, expected_division, row["division"], context,
        )
    return row


def pct_change(before, after):
    if before is None or pd.isna(before) or before == 0:
        return np.nan
    return (after - before) / before * 100.0


def build_promotion_analysis(cs: pd.DataFrame) -> pd.DataFrame:
    promo = pd.read_csv(PROCESSED / "promotion_episodes.csv")
    season_idx_map = cs.reset_index().set_index("season")["season_idx"].to_dict()
    # season -> season_idx is 1:1 across the whole panel, safe to build once.
    season_idx_map = dict(cs.reset_index()[["season", "season_idx"]].drop_duplicates().values)

    rows = []
    for _, ep in promo.iterrows():
        cid = ep["club_id"]
        promo_idx = season_idx_map[ep["promotion_season"]]

        before = get_row(cs, cid, promo_idx - 1, 2, f"{cid} before promotion {ep['promotion_season']}")
        first = get_row(cs, cid, promo_idx, 1, f"{cid} first La Liga season {ep['promotion_season']}")

        segunda_mv_before = before["market_value_eur"] if before is not None else np.nan
        laliga_mv_first = first["market_value_eur"] if first is not None else np.nan
        mv_change_abs = laliga_mv_first - segunda_mv_before if pd.notna(segunda_mv_before) and pd.notna(laliga_mv_first) else np.nan
        mv_change_pct = pct_change(segunda_mv_before, laliga_mv_first)

        rrp_last_segunda = before["market_value_to_league_median"] if before is not None else np.nan
        rrp_first_laliga = first["market_value_to_league_median"] if first is not None else np.nan
        promotion_resource_shock = (
            rrp_first_laliga - rrp_last_segunda if pd.notna(rrp_first_laliga) and pd.notna(rrp_last_segunda) else np.nan
        )
        promotion_resource_ratio = (
            rrp_first_laliga / rrp_last_segunda
            if pd.notna(rrp_first_laliga) and pd.notna(rrp_last_segunda) and rrp_last_segunda != 0
            else np.nan
        )

        survival_duration = ep["survival_duration"]
        relegation_event = ep["relegation_event"]
        immediate_relegation = int(survival_duration == 1 and relegation_event == 1)
        survived_2 = int(survival_duration >= 2)
        survived_3 = int(survival_duration >= 3)
        if relegation_event == 1:
            outcome = "relegated_after_1_season" if survival_duration == 1 else "relegated_after_2_plus_seasons"
        else:
            outcome = "still_in_la_liga_censored"

        rows.append({
            "club_id": cid,
            "club_name": ep["club_name"],
            "promotion_season": ep["promotion_season"],
            "promotion_from": ep["promotion_from"],
            "promotion_to": ep["promotion_to"],
            "segundadivision_position_before_promotion": before["final_position"] if before is not None else np.nan,
            "segundadivision_points_before_promotion": before["points"] if before is not None else np.nan,
            "segundadivision_market_value_before_promotion": segunda_mv_before,
            "segundadivision_relative_market_value_before_promotion": before["market_value_to_league_median"] if before is not None else np.nan,
            "laliga_position_first_season": first["final_position"] if first is not None else np.nan,
            "laliga_points_first_season": first["points"] if first is not None else np.nan,
            "laliga_market_value_first_season": laliga_mv_first,
            "laliga_relative_market_value": first["market_value_to_league_median"] if first is not None else np.nan,
            "laliga_market_value_rank": first["market_value_rank"] if first is not None else np.nan,
            "laliga_market_value_percentile": first["market_value_percentile"] if first is not None else np.nan,
            "market_value_change_absolute": mv_change_abs,
            "market_value_change_pct": mv_change_pct,
            "rrp_last_segunda_season": rrp_last_segunda,
            "rrp_first_laliga_season": rrp_first_laliga,
            "promotion_resource_shock": promotion_resource_shock,
            "promotion_resource_ratio": promotion_resource_ratio,
            "survival_duration": survival_duration,
            "relegation_event": relegation_event,
            "censored": ep["censored"],
            "immediate_relegation": immediate_relegation,
            "survived_2_seasons": survived_2,
            "survived_3_seasons": survived_3,
            "outcome": outcome,
        })
    return pd.DataFrame(rows)


def build_relegation_analysis(cs: pd.DataFrame) -> pd.DataFrame:
    releg = pd.read_csv(PROCESSED / "relegation_episodes.csv")
    season_idx_map = dict(cs.reset_index()[["season", "season_idx"]].drop_duplicates().values)

    rows = []
    for _, ep in releg.iterrows():
        cid = ep["club_id"]
        releg_idx = season_idx_map[ep["relegation_season"]]

        before = get_row(cs, cid, releg_idx - 1, 1, f"{cid} before relegation {ep['relegation_season']}")
        first = get_row(cs, cid, releg_idx, 2, f"{cid} first Segunda season {ep['relegation_season']}")

        laliga_mv_before = before["market_value_eur"] if before is not None else np.nan
        segunda_mv_after = first["market_value_eur"] if first is not None else np.nan
        mv_change_abs = segunda_mv_after - laliga_mv_before if pd.notna(laliga_mv_before) and pd.notna(segunda_mv_after) else np.nan
        mv_change_pct = pct_change(laliga_mv_before, segunda_mv_after)

        rrp_last_laliga = before["market_value_to_league_median"] if before is not None else np.nan
        rrp_first_segunda = first["market_value_to_league_median"] if first is not None else np.nan
        relegation_resource_shock = (
            rrp_first_segunda - rrp_last_laliga if pd.notna(rrp_first_segunda) and pd.notna(rrp_last_laliga) else np.nan
        )
        relegation_resource_ratio = (
            rrp_first_segunda / rrp_last_laliga
            if pd.notna(rrp_first_segunda) and pd.notna(rrp_last_laliga) and rrp_last_laliga != 0
            else np.nan
        )

        time_to_return = ep["time_to_return"]
        return_event = ep["return_event"]
        immediate_return = int(time_to_return == 1 and return_event == 1)
        returned_within_2 = int(return_event == 1 and time_to_return <= 2)
        returned_within_3 = int(return_event == 1 and time_to_return <= 3)

        rows.append({
            "club_id": cid,
            "club_name": ep["club_name"],
            "relegation_season": ep["relegation_season"],
            "laliga_position_before_relegation": before["final_position"] if before is not None else np.nan,
            "laliga_points_before_relegation": before["points"] if before is not None else np.nan,
            "laliga_market_value_before_relegation": laliga_mv_before,
            "laliga_relative_market_value_before_relegation": before["market_value_to_league_median"] if before is not None else np.nan,
            "segundadivision_market_value_after_relegation": segunda_mv_after,
            "segundadivision_relative_market_value_after_relegation": first["market_value_to_league_median"] if first is not None else np.nan,
            "segundadivision_market_value_rank_after_relegation": first["market_value_rank"] if first is not None else np.nan,
            "market_value_change_absolute": mv_change_abs,
            "market_value_change_pct": mv_change_pct,
            "rrp_last_laliga_season": rrp_last_laliga,
            "rrp_first_segunda_season": rrp_first_segunda,
            "relegation_resource_shock": relegation_resource_shock,
            "relegation_resource_ratio": relegation_resource_ratio,
            "time_to_return": time_to_return,
            "return_event": return_event,
            "censored": ep["censored"],
            "immediate_return": immediate_return,
            "returned_within_2": returned_within_2,
            "returned_within_3": returned_within_3,
            "fell_outside_top_two": ep["fell_to_third_tier"],
        })
    return pd.DataFrame(rows)


def main():
    cs = load_club_seasons()
    promo_analysis = build_promotion_analysis(cs)
    releg_analysis = build_relegation_analysis(cs)

    promo_path = PROCESSED / "promotion_analysis.csv"
    releg_path = PROCESSED / "relegation_analysis.csv"
    promo_analysis.to_csv(promo_path, index=False)
    releg_analysis.to_csv(releg_path, index=False)

    log.info("Wrote %d rows -> %s", len(promo_analysis), promo_path)
    log.info("Wrote %d rows -> %s", len(releg_analysis), releg_path)

    n_missing_promo = promo_analysis[["segundadivision_market_value_before_promotion", "laliga_market_value_first_season"]].isna().any(axis=1).sum()
    n_missing_releg = releg_analysis[["laliga_market_value_before_relegation", "segundadivision_market_value_after_relegation"]].isna().any(axis=1).sum()
    log.info("Promotion episodes with any missing before/after market value: %d/%d", n_missing_promo, len(promo_analysis))
    log.info("Relegation episodes with any missing before/after market value: %d/%d", n_missing_releg, len(releg_analysis))


if __name__ == "__main__":
    main()
