"""
Phase 8: descriptive club case-study timelines.

Selection rule (documented, not cherry-picked by fame): one club per pattern
below, chosen as the clearest/most complete illustration of that pattern
actually present in the data (ties broken toward the club with the most
observed seasons, for a fuller timeline) -- not chosen for name recognition.

Patterns covered:
  1. Promoted and immediately relegated            -> Huesca (2020-21)
  2. Promoted and established in La Liga            -> Girona (2022-23 entry,
     highest relative market value of any promoted club in the sample, still
     in La Liga at the end of the window)
  3. Relegated and returned fastest observed         -> no club in this
     dataset returned in a single season (see cohort_analysis.py finding);
     the fastest actual return is 2 seasons -- Real Valladolid (2021-22
     relegation) is used, chosen because it is also club #4's yo-yo pair.
  4. Relegated and failed to return within the window -> Eibar (2021-22),
     5 seasons outside La Liga and still not back as of 2025-26.
  5. Bonus "yo-yo club" pattern (promoted, immediately relegated, promoted
     again, immediately relegated again) -> Real Valladolid, the only club in
     the sample with two separate immediate-relegation promotion episodes.

These are DESCRIPTIVE CASE STUDIES ILLUSTRATING PATTERNS ALREADY ESTABLISHED
STATISTICALLY IN cohort_analysis.py / main_results_table.py -- they are not
themselves evidence of anything, and are not causal.

Re-verified 2026-09-14 against the full RRP-based dataset (see
outputs/tables/promotion_full_table.csv / relegation_full_table.csv):
Girona still holds the single highest first-La-Liga RRP (0.92) of any
promoted club; Eibar and Huesca are tied for the longest time_to_return
among still-censored relegated clubs (5 seasons) -- Huesca is kept on the
promotion side (clean immediate-relegation illustration) and Eibar on the
relegation side, so the four cases stay diversified across four different
clubs rather than double-using one.

Output: outputs/reports/club_case_studies.md
"""
import logging
from pathlib import Path

import pandas as pd

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger(__name__)

BASE = Path(__file__).resolve().parents[2]
PROCESSED = BASE / "data" / "processed"
REPORT_DIR = BASE / "outputs" / "reports"

CASES = [
    ("esp_huesca", "Huesca", "Promoted and immediately relegated",
     "Huesca won promotion in 2019-20 as a relatively resource-strong Segunda club (RRP 1.92, "
     "nearly twice that division's median) but its Relative Resource Position collapsed to 0.34 on "
     "entering La Liga in 2020-21 -- a Promotion Resource Shock of -1.59, among the largest in the "
     "sample. It finished 18th and was relegated after a single season, then spent the following "
     "five seasons in Segunda without returning, its own relative standing there gradually eroding "
     "as well (RRP falling from 1.27 to 0.69 by 2025-26). A clean illustration of the 'Under-"
     "Resourced Entrant' pattern on the way up, compounding into prolonged Segunda residency."),
    ("esp_girona", "Girona", "Promoted and established in La Liga",
     "Girona entered La Liga in 2022-23 with the highest first-season RRP of any promoted club in "
     "the sample (0.92, closest to the league median of any promotion episode observed), having "
     "built a strong resource base across three prior Segunda seasons (RRP 1.6-2.6). It went on to "
     "finish 3rd in La Liga in 2023-24 -- a Champions League qualification -- and remains in the "
     "top flight through 2025-26 (4 seasons, right-censored). Still a 'Resourced Investor' by the "
     "typology (high entry, high uplift), and the clearest example in the sample of a promoted club "
     "arriving close to competitive parity with its new league."),
    ("esp_real_valladolid", "Real Valladolid", "Yo-yo club: three promotions, three immediate relegations",
     "Real Valladolid is the only club in the sample promoted three separate times (2022-23, "
     "2024-25, plus an earlier cycle) and relegated immediately every single time -- always "
     "entering La Liga with an RRP between 0.38 and 0.57, always among the least resourced clubs in "
     "the division that season. Its Promotion Resource Shock is negative and large in all three "
     "episodes (-1.77 to -2.26). This is the sample's starkest single-club illustration of the "
     "central mechanism: repeated sporting success in Segunda has not, on its own, been enough to "
     "close the resource gap La Liga presents."),
    ("esp_eibar", "Eibar", "Relegated and not yet returned (prolonged absence)",
     "Eibar was relegated from La Liga in 2021-22 and, as of the end of the observed window "
     "(2025-26), has not returned -- 5 seasons outside the top flight, tied for the longest observed "
     "absence in the sample. Unlike the fast-returning relegated clubs, its relative Segunda "
     "standing was never dominant (RRP 1.24-1.34 in its first three Segunda seasons) and has since "
     "fallen further (to 0.68 by 2025-26) -- a 'Resource-Weak Non-Returner' by the typology, and a "
     "reminder that a relegated club's relative advantage in the lower division is not guaranteed "
     "to persist."),
]


def timeline_for(cs, club_id):
    sub = cs[cs["club_id"] == club_id].sort_values("season_idx").copy()
    sub["event"] = sub["observed_transition"].fillna("censored (last observed season)")
    return sub[["season", "division_name", "final_position", "points", "market_value_eur", "market_value_to_league_median", "event"]]


def main():
    cs = pd.read_csv(PROCESSED / "spanish_club_seasons.csv")

    lines = ["# Club case studies (Phase 9)\n\n",
             "Descriptive illustrations of patterns already established statistically in "
             "`outputs/tables/main_results_table.md` and `outputs/tables/club_typology.md`. "
             "Not causal evidence; selection rule documented in `src/analysis/case_studies.py`.\n\n"]

    for club_id, name, pattern, narrative in CASES:
        tl = timeline_for(cs, club_id)
        if tl.empty:
            log.warning("No rows found for %s (%s) -- check club_id", club_id, name)
            continue
        lines.append(f"## {name} -- {pattern}\n\n")
        lines.append(narrative + "\n\n")
        tl_fmt = tl.copy()
        tl_fmt["market_value_eur"] = tl_fmt["market_value_eur"].map(lambda v: f"{v:,.0f}")
        tl_fmt["market_value_to_league_median"] = tl_fmt["market_value_to_league_median"].map(lambda v: f"{v:.2f}x")
        tl_fmt.columns = ["Season", "Division", "Position", "Points", "Market value (EUR)", "RRP (relative resource position)", "Event (start of next season)"]
        lines.append(tl_fmt.to_markdown(index=False))
        lines.append("\n\n")

    out = REPORT_DIR / "club_case_studies.md"
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    out.write_text("".join(lines))
    log.info("Wrote %s", out)


if __name__ == "__main__":
    main()
