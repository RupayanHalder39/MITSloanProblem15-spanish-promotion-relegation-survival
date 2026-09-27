"""
Build data/processed/league_transitions.csv -- a season-to-season state
table for every club, suitable for a multi-state transition-count model
(La Liga <-> Segunda <-> Primera Federación <-> unobserved).

state_t / state_t_plus_1 use the division_name strings from
spanish_club_seasons.csv plus two sentinel states:
  "Censored (end of data)"  -- season_idx t is the last observed season
                                 (2025-2026); no t+1 exists by construction.
  "Exited observed pyramid" -- the club has a row at season t but none at
                                 season t+1, and t is NOT the last season --
                                 i.e. it dropped out of La Liga/Segunda/
                                 Primera Federación (relegated below tier 3,
                                 dissolved, etc.) before the window ended.
"""
import logging
from pathlib import Path

import pandas as pd

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger(__name__)

BASE = Path(__file__).resolve().parents[2]
CLUB_SEASONS = BASE / "data" / "processed" / "spanish_club_seasons.csv"
PROCESSED_DIR = BASE / "data" / "processed"

LAST_SEASON_IDX = 6


def main():
    df = pd.read_csv(CLUB_SEASONS)
    by_club = {cid: g.set_index("season_idx") for cid, g in df.groupby("club_id")}

    rows = []
    for cid, g in by_club.items():
        for idx, row in g.iterrows():
            state_t = row["division_name"]
            if idx == LAST_SEASON_IDX:
                state_next = "Censored (end of data)"
            elif (idx + 1) in g.index:
                state_next = g.loc[idx + 1, "division_name"]
            else:
                state_next = "Exited observed pyramid"
            rows.append(
                {
                    "club_id": cid,
                    "club_name": row["club_name"],
                    "season": row["season"],
                    "state_t": state_t,
                    "state_t_plus_1": state_next,
                    "transition": f"{state_t} -> {state_next}",
                }
            )

    out = pd.DataFrame(rows).sort_values(["club_id", "season"])
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    out_path = PROCESSED_DIR / "league_transitions.csv"
    out.to_csv(out_path, index=False)
    log.info("Wrote %d transition rows -> %s", len(out), out_path)

    counts = out["transition"].value_counts()
    log.info("Transition counts:\n%s", counts.to_string())


if __name__ == "__main__":
    main()
