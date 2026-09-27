"""
Build the survival-analysis episode tables from data/processed/spanish_club_seasons.csv:
    data/processed/promotion_episodes.csv   (Segunda -> La Liga survival)
    data/processed/relegation_episodes.csv  (La Liga -> Segunda recovery time)

Duration / censoring definitions (documented once, here, and in Handoff.md)
----------------------------------------------------------------------------
Promotion episode: starts at the first season a club plays in La Liga (div 1)
immediately after a season in Segunda (div 2) -- i.e. previous_division == 2.
`survival_duration` = number of CONSECUTIVE seasons in La Liga starting at
(and including) the promotion season, up to and including the last season
before relegation. If the club is relegated within the observed window,
`relegation_event = 1` and `censored = 0`. If the club is still in La Liga at
the end of the observed window (season 2025-2026) with no observed
relegation, `relegation_event = 0` and `censored = 1` (right-censored --
we do NOT know if/when it will eventually be relegated).

Relegation episode: starts at the first season a club plays in Segunda (div 2)
immediately after a season in La Liga (div 1) -- i.e. previous_division == 1.
`time_to_return` = number of seasons from (and including) the relegation
season until the club is back in La Liga. If it returns within the window,
`return_event = 1`, `censored = 0`. If it has not returned by the end of the
window, `return_event = 0`, `censored = 1`. If, before returning, the club
falls further to Primera Federación (div 3), `fell_to_third_tier = 1`. If the
club's trail disappears from the observed three-division window entirely
(e.g. relegated below Primera Federación, which is out of scope) before
either returning or reaching the end of the window, this is recorded
explicitly (`exited_observed_pyramid = 1`) rather than silently treated as
"still in Segunda".

Both tables exclude episodes whose START is left-censored, i.e. any club
already in La Liga (for promotions) or Segunda (for relegations) in the
very first observed season (2019-2020) with no prior-season data to confirm
it was actually a fresh promotion/relegation that year.
"""
import logging
from pathlib import Path

import pandas as pd

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger(__name__)

BASE = Path(__file__).resolve().parents[2]
CLUB_SEASONS = BASE / "data" / "processed" / "spanish_club_seasons.csv"
PROCESSED_DIR = BASE / "data" / "processed"

LAST_SEASON_IDX = 6  # 2025-2026, 0-indexed from 2019-2020


def build_promotion_episodes(df: pd.DataFrame) -> pd.DataFrame:
    starts = df[(df["division"] == 1) & (df["previous_division"] == 2)].copy()
    episodes = []
    for i, (_, start_row) in enumerate(starts.iterrows(), start=1):
        cid = start_row["club_id"]
        start_idx = start_row["season_idx"]
        club_rows = df[df["club_id"] == cid].set_index("season_idx").sort_index()

        duration = 0
        idx = start_idx
        relegation_event = 0
        while idx in club_rows.index and club_rows.loc[idx, "division"] == 1:
            duration += 1
            idx += 1
        # idx is now either: past a relegation season, past end of window+1, or a gap.
        if (idx - 1) == LAST_SEASON_IDX:
            censored = 1  # ran out of data while still top-flight
        elif idx in club_rows.index and club_rows.loc[idx, "division"] == 2:
            relegation_event = 1
            censored = 0
        elif idx not in club_rows.index and (idx - 1) < LAST_SEASON_IDX:
            # club vanished from dataset before the window ended and before a relegation was recorded
            censored = 1
            log.warning("Club %s vanished from data after season_idx %d (promotion episode %d)", cid, idx - 1, i)
        else:
            censored = 1

        episodes.append(
            {
                "promotion_id": f"PROM_{i:03d}",
                "club_id": cid,
                "club_name": start_row["club_name"],
                "promotion_season": start_row["season"],
                "promotion_from": 2,
                "promotion_to": 1,
                "survival_duration": duration,
                "relegation_event": relegation_event,
                "censored": censored,
            }
        )
    return pd.DataFrame(episodes)


def build_relegation_episodes(df: pd.DataFrame) -> pd.DataFrame:
    starts = df[(df["division"] == 2) & (df["previous_division"] == 1)].copy()
    episodes = []
    for i, (_, start_row) in enumerate(starts.iterrows(), start=1):
        cid = start_row["club_id"]
        start_idx = start_row["season_idx"]
        club_rows = df[df["club_id"] == cid].set_index("season_idx").sort_index()

        idx = start_idx
        fell_to_third_tier = 0
        exited_pyramid = 0
        return_event = 0
        time_to_return = 0
        while True:
            if idx not in club_rows.index:
                exited_pyramid = 1
                break
            div = club_rows.loc[idx, "division"]
            time_to_return += 1
            if div == 1:
                return_event = 1
                break
            if div == 3:
                fell_to_third_tier = 1
            if idx == LAST_SEASON_IDX:
                break
            idx += 1

        censored = 0 if return_event == 1 else 1
        episodes.append(
            {
                "relegation_id": f"RELEG_{i:03d}",
                "club_id": cid,
                "club_name": start_row["club_name"],
                "relegation_season": start_row["season"],
                "relegated_from": 1,
                "relegated_to": 2,
                "time_to_return": time_to_return,
                "return_event": return_event,
                "fell_to_third_tier": fell_to_third_tier,
                "exited_observed_pyramid": exited_pyramid,
                "censored": censored,
            }
        )
    return pd.DataFrame(episodes)


def main():
    df = pd.read_csv(CLUB_SEASONS)

    promo = build_promotion_episodes(df)
    releg = build_relegation_episodes(df)

    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    promo_path = PROCESSED_DIR / "promotion_episodes.csv"
    releg_path = PROCESSED_DIR / "relegation_episodes.csv"
    promo.to_csv(promo_path, index=False)
    releg.to_csv(releg_path, index=False)

    log.info(
        "Promotion episodes: %d (relegated back down: %d, still surviving/censored: %d) -> %s",
        len(promo), promo["relegation_event"].sum(), promo["censored"].sum(), promo_path,
    )
    log.info(
        "Relegation episodes: %d (returned: %d, not yet returned/censored: %d) -> %s",
        len(releg), releg["return_event"].sum(), releg["censored"].sum(), releg_path,
    )


if __name__ == "__main__":
    main()
