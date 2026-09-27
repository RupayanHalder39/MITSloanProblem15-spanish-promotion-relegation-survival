"""
Phase 4: full per-club tables testing the core Relative Resource Position (RRP)
mechanism descriptively. Every one of the 18 promotion and 18 relegation
episodes is shown individually -- never hidden behind an aggregate-only view.

Outputs:
    outputs/tables/promotion_full_table.csv / .md
    outputs/tables/relegation_full_table.csv / .md
"""
import logging
from pathlib import Path

import pandas as pd

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger(__name__)

BASE = Path(__file__).resolve().parents[2]
PROCESSED = BASE / "data" / "processed"
TABLE_DIR = BASE / "outputs" / "tables"

PROMOTION_COLS = [
    "club_name", "promotion_season",
    "rrp_last_segunda_season", "rrp_first_laliga_season",
    "promotion_resource_shock", "promotion_resource_ratio",
    "market_value_change_pct",
    "survival_duration", "immediate_relegation", "survived_2_seasons", "survived_3_seasons",
    "relegation_event", "censored", "outcome",
]

RELEGATION_COLS = [
    "club_name", "relegation_season",
    "rrp_last_laliga_season", "rrp_first_segunda_season",
    "relegation_resource_shock", "relegation_resource_ratio",
    "market_value_change_pct",
    "time_to_return", "immediate_return", "returned_within_2", "returned_within_3",
    "return_event", "censored",
]


def main():
    TABLE_DIR.mkdir(parents=True, exist_ok=True)
    promo = pd.read_csv(PROCESSED / "promotion_analysis.csv").sort_values(["club_name", "promotion_season"])
    releg = pd.read_csv(PROCESSED / "relegation_analysis.csv").sort_values(["club_name", "relegation_season"])

    promo_out = promo[PROMOTION_COLS].round(3)
    releg_out = releg[RELEGATION_COLS].round(3)

    promo_out.to_csv(TABLE_DIR / "promotion_full_table.csv", index=False)
    releg_out.to_csv(TABLE_DIR / "relegation_full_table.csv", index=False)

    (TABLE_DIR / "promotion_full_table.md").write_text(
        f"# All 18 promotion episodes (Phase 4)\n\n{promo_out.to_markdown(index=False)}\n"
    )
    (TABLE_DIR / "relegation_full_table.md").write_text(
        f"# All 18 relegation episodes (Phase 4)\n\n{releg_out.to_markdown(index=False)}\n"
    )

    log.info("Wrote promotion_full_table.csv/.md (%d rows) and relegation_full_table.csv/.md (%d rows)", len(promo_out), len(releg_out))


if __name__ == "__main__":
    main()
