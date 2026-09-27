"""
Build data/processed/spanish_club_seasons.csv -- the club-season backbone
for all downstream survival / multi-state analysis.

Lineage
-------
Data/index.html (read-only master)
    -> src/ingestion/extract_dashboard_data.py -> data/raw/spain_dashboard_club_seasons_raw.csv
    -> src/cleaning/normalize_club_names.py    -> data/interim/spain_club_seasons_normalized.csv
    -> THIS SCRIPT                              -> data/processed/spanish_club_seasons.csv

Division encoding
------------------
    1 = La Liga (top flight)
    2 = Segunda División
    3 = Primera Federación (third tier; named this way only from 2021-2022
        onward -- see DataFeasibilityAuditReport.md for the pre-2021
        Segunda B discontinuity)

promoted / relegated semantics (as found in source, verified against real
results for every season 2019-2020..2024-2025): the flag marks a club moving
OUT of its current-season division after that season -- "promoted" = moved up
a division, "relegated" = moved down a division. A top-flight club can only
be relegated (nothing above it); flags for the final observed season
(2025-2026) are null in the source because the dashboard could not look
ahead to a non-existent 2026-2027 season to confirm the movement -- see
`flag_source` column below.

next_division / previous_division are computed empirically from the club's
own observed division in the surrounding seasons, NOT solely trusted from
the promoted/relegated flags, so that they also work for the last season
(where movement is unknown/right-censored) and for clubs exiting the
three-division window entirely (relegated out of Primera Federación, or a
club only ever observed in one division with no prior/next season on record).
"""
import logging
from pathlib import Path

import pandas as pd

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger(__name__)

BASE = Path(__file__).resolve().parents[2]
INTERIM_CSV = BASE / "data" / "interim" / "spain_club_seasons_normalized.csv"
PROCESSED_DIR = BASE / "data" / "processed"

SEASON_ORDER = ["2019-2020", "2020-2021", "2021-2022", "2022-2023", "2023-2024", "2024-2025", "2025-2026"]
SEASON_IDX = {s: i for i, s in enumerate(SEASON_ORDER)}
LAST_SEASON = SEASON_ORDER[-1]

LEAGUE_TO_DIVISION = {"la liga": 1, "segunda division": 2, "Primera Federación": 3}
DIVISION_NAME = {v: k for k, v in LEAGUE_TO_DIVISION.items()}
DIVISION_NAME[1] = "La Liga"
DIVISION_NAME[2] = "Segunda División"
DIVISION_NAME[3] = "Primera Federación"


def main():
    df = pd.read_csv(INTERIM_CSV)
    df["division"] = df["league"].map(LEAGUE_TO_DIVISION)
    if df["division"].isna().any():
        bad = df[df["division"].isna()]["league"].unique()
        raise ValueError(f"Unmapped league values: {bad}")
    df["division"] = df["division"].astype(int)
    df["season_idx"] = df["season"].map(SEASON_IDX)

    # One row per (club_id, season) expected; Primera Federación has two
    # regional groups but a club only ever sits in one group per season, so
    # this should already hold. Confirm it rather than assume it.
    dupes = df[df.duplicated(subset=["club_id", "season"], keep=False)]
    if len(dupes):
        log.warning(
            "%d duplicate (club_id, season) rows found -- keeping first occurrence, see validation report",
            len(dupes),
        )
        dupes.sort_values(["club_id", "season"]).to_csv(PROCESSED_DIR.parent / "metadata" / "duplicate_club_season_rows.csv", index=False)
    df = df.drop_duplicates(subset=["club_id", "season"], keep="first").copy()

    # club_id -> {season_idx: division}, used to look up neighbouring seasons.
    club_div_by_season = {}
    for cid, g in df.groupby("club_id"):
        club_div_by_season[cid] = dict(zip(g["season_idx"], g["division"]))

    def lookup_division(cid, idx):
        return club_div_by_season.get(cid, {}).get(idx)

    prev_divs, next_divs = [], []
    for _, row in df.iterrows():
        prev_divs.append(lookup_division(row["club_id"], row["season_idx"] - 1))
        next_divs.append(lookup_division(row["club_id"], row["season_idx"] + 1))
    df["previous_division"] = prev_divs
    df["next_division"] = next_divs

    # Empirical promoted/relegated: derived from the actual next_division, so
    # it is defined even where the source flag is null, EXCEPT for the final
    # season where next_division is unknowable (true right censoring).
    def derive_event(row):
        if pd.isna(row["next_division"]):
            return pd.NA  # unknown / censored (last observed season for this club)
        if row["next_division"] < row["division"]:
            return "promoted"
        if row["next_division"] > row["division"]:
            return "relegated"
        return "stayed"

    df["observed_transition"] = df.apply(derive_event, axis=1)

    # Cross-check against the source's own promoted/relegated flags where both exist.
    def flag_agrees(row):
        if pd.isna(row["next_division"]):
            return pd.NA
        src_promoted = row.get("promoted") == 1
        src_relegated = row.get("relegated") == 1
        if row["observed_transition"] == "promoted":
            return bool(src_promoted) or pd.isna(row.get("promoted"))
        if row["observed_transition"] == "relegated":
            return bool(src_relegated) or pd.isna(row.get("relegated"))
        return not src_promoted and not src_relegated

    df["source_flag_agrees"] = df.apply(flag_agrees, axis=1)
    disagreements = df[df["source_flag_agrees"] == False]  # noqa: E712
    if len(disagreements):
        log.warning("%d rows where derived transition disagrees with source promoted/relegated flag", len(disagreements))
        disagreements.to_csv(PROCESSED_DIR.parent / "metadata" / "transition_flag_disagreements.csv", index=False)
    else:
        log.info("All derivable promoted/relegated flags agree with empirical next-season division movement.")

    df["is_last_observed_season"] = df["season"] == LAST_SEASON
    df["division_name"] = df["division"].map(DIVISION_NAME)

    out_cols = [
        "club_id", "club_name", "season", "season_idx", "division", "division_name", "group",
        "final_position", "points", "market_value_eur",
        "previous_division", "next_division", "observed_transition",
        "is_last_observed_season", "source_flag_agrees",
    ]
    out = df.rename(columns={"pos": "final_position", "pts": "points", "mv": "market_value_eur"})[out_cols]
    out = out.sort_values(["club_id", "season_idx"]).reset_index(drop=True)

    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    out_path = PROCESSED_DIR / "spanish_club_seasons.csv"
    out.to_csv(out_path, index=False)
    log.info("Wrote %d club-season rows (%d clubs, %d seasons) -> %s", len(out), out["club_id"].nunique(), out["season"].nunique(), out_path)

    # Quick validation summary
    counts = out.groupby(["division_name", "season"]).size().unstack(fill_value=0)
    log.info("Teams per division/season:\n%s", counts.to_string())


if __name__ == "__main__":
    main()
