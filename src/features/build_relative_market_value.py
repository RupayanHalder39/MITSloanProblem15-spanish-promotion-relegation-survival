"""
Enrich data/processed/spanish_club_seasons.csv with within-league-season relative
squad market-value measures.

Rationale
---------
A club's absolute squad market value is not directly comparable across divisions
(La Liga values are an order of magnitude above Segunda) or even across seasons
within the same division (market-wide inflation). What matters for the survival
question -- "was this promoted club resource-competitive in the league it just
entered?" -- is its value RELATIVE to the other clubs in the same season x
division. This script computes that.

IMPORTANT TERMINOLOGY: `market_value_eur` is a squad market-value PROXY (likely
Transfermarkt-style aggregation per the source dashboard), not accounting
revenue, wages, or any other financial-statement figure. All derived columns
below inherit that caveat -- never describe them as "financial strength" in the
paper without qualifying "resource proxy" / "squad valuation proxy".

New columns added, computed separately within each (season, division) group:
    league_median_market_value   -- median market_value_eur in that season x division
    league_mean_market_value     -- mean market_value_eur in that season x division
    market_value_to_league_median -- ratio to the group median (1.0 = exactly at median)
    market_value_to_league_mean   -- ratio to the group mean
    market_value_percentile       -- percentile rank within the group, 0-100, 100 = most valuable
    market_value_rank             -- integer rank within the group, 1 = most valuable

This script OVERWRITES data/processed/spanish_club_seasons.csv in place (adding
columns), run immediately after build_club_seasons.py in the pipeline. No source
data is touched -- this only modifies this project's own processed/ output.
"""
import logging
from pathlib import Path

import pandas as pd

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger(__name__)

BASE = Path(__file__).resolve().parents[2]
CLUB_SEASONS = BASE / "data" / "processed" / "spanish_club_seasons.csv"


def main():
    df = pd.read_csv(CLUB_SEASONS)

    group = df.groupby(["season", "division"])["market_value_eur"]
    df["league_median_market_value"] = group.transform("median")
    df["league_mean_market_value"] = group.transform("mean")
    df["market_value_to_league_median"] = df["market_value_eur"] / df["league_median_market_value"]
    df["market_value_to_league_mean"] = df["market_value_eur"] / df["league_mean_market_value"]
    df["market_value_percentile"] = group.transform(lambda s: s.rank(pct=True) * 100)
    df["market_value_rank"] = group.transform(lambda s: s.rank(ascending=False, method="min")).astype(int)

    df.to_csv(CLUB_SEASONS, index=False)
    log.info("Enriched %s with relative market-value columns (%d rows)", CLUB_SEASONS, len(df))

    sample = df[df["season"] == "2023-2024"].sort_values(["division", "market_value_rank"])
    log.info(
        "Sanity check, La Liga 2023-2024 top 3 by market value:\n%s",
        sample[sample.division == 1][["club_name", "market_value_eur", "market_value_rank", "market_value_percentile"]].head(3).to_string(index=False),
    )


if __name__ == "__main__":
    main()
