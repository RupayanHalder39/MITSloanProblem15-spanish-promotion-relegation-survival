"""
Phase 6: event-centered trajectory panels.

Convention (pick ONE, documented everywhere): **event_time = 0 is the first
season in the NEW division** -- i.e. for a promotion episode, t=0 is the
club's first La Liga season (= `promotion_season` in promotion_episodes.csv);
for a relegation episode, t=0 is the club's first Segunda season (=
`relegation_season` in relegation_episodes.csv). This matches the convention
already used everywhere else in this project (`promotion_season` /
`relegation_season` are defined the same way in build_episodes.py), so t=0
here is NOT "the season ending in promotion/relegation" -- it is one season
later than that. event_time = -1 is therefore the last season in the OLD
division (the "before" season used throughout build_analysis_datasets.py).

event_time range used: -2, -1, 0, +1, +2, +3, restricted to whatever falls
inside the observed window (2019-2020 .. 2025-2026) for each club -- no
padding/interpolation of seasons that don't exist in the data.

Outputs:
    data/processed/promotion_event_panel.csv
    data/processed/relegation_event_panel.csv
"""
import logging
from pathlib import Path

import pandas as pd

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger(__name__)

BASE = Path(__file__).resolve().parents[2]
PROCESSED = BASE / "data" / "processed"

EVENT_TIMES = [-2, -1, 0, 1, 2, 3]
COLS = ["final_position", "points", "market_value_eur", "market_value_to_league_median", "market_value_rank", "division_name"]


def build_panel(episodes_path, season_col, episode_id_col, cs, cs_by_season):
    episodes = pd.read_csv(episodes_path)
    rows = []
    for _, ep in episodes.iterrows():
        cid = ep["club_id"]
        t0_idx = cs_by_season[ep[season_col]]
        for et in EVENT_TIMES:
            idx = t0_idx + et
            key = (cid, idx)
            if key not in cs.index:
                continue  # outside observed window for this club -- not padded
            row = cs.loc[key]
            rows.append({
                "club_id": cid,
                "club_name": ep["club_name"],
                "event_id": ep[episode_id_col],
                "event_time": et,
                "season": row["season"],
                "division": row["division"],
                "division_name": row["division_name"],
                "final_position": row["final_position"],
                "points": row["points"],
                "market_value_eur": row["market_value_eur"],
                "relative_market_value": row["market_value_to_league_median"],
                "market_value_rank": row["market_value_rank"],
            })
    return pd.DataFrame(rows)


def main():
    cs_full = pd.read_csv(PROCESSED / "spanish_club_seasons.csv")
    cs = cs_full.set_index(["club_id", "season_idx"])
    cs_by_season = dict(cs_full[["season", "season_idx"]].drop_duplicates().values)

    promo_panel = build_panel(PROCESSED / "promotion_episodes.csv", "promotion_season", "promotion_id", cs, cs_by_season)
    releg_panel = build_panel(PROCESSED / "relegation_episodes.csv", "relegation_season", "relegation_id", cs, cs_by_season)

    promo_out = PROCESSED / "promotion_event_panel.csv"
    releg_out = PROCESSED / "relegation_event_panel.csv"
    promo_panel.to_csv(promo_out, index=False)
    releg_panel.to_csv(releg_out, index=False)

    log.info("Promotion event panel: %d rows across %d episodes -> %s", len(promo_panel), promo_panel["event_id"].nunique(), promo_out)
    log.info("Relegation event panel: %d rows across %d episodes -> %s", len(releg_panel), releg_panel["event_id"].nunique(), releg_out)
    log.info("Promotion panel coverage by event_time:\n%s", promo_panel.groupby("event_time").size().to_string())
    log.info("Relegation panel coverage by event_time:\n%s", releg_panel.groupby("event_time").size().to_string())


if __name__ == "__main__":
    main()
