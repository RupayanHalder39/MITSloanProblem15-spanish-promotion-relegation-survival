# Data access and preparation

## Source

The research uses an authorized SoccerSolver league-dashboard export containing club-season records for Spanish competitions. Required fields are:

| Field | Description |
|---|---|
| `nation` | Country |
| `league` | Competition |
| `div` | Division level |
| `season` | Season label |
| `team` | Club name |
| `pts` | Final points |
| `pos` | Final position |
| `mv` / `mv_m` | Squad market value |
| `promoted` | Promotion indicator where supplied |
| `relegated` | Relegation indicator where supplied |

## Redistribution decision

The source is SoccerSolver-provided row-level data. Explicit redistribution authorization has not been established. It is therefore **not included** in this repository. No raw JSON, HTML dashboard, database dump, club-season CSV, or episode-level row data is distributed here.

Researchers with authorized access may run the portable ingestion command documented in the main README. The pipeline writes extracted data under `data/raw/` and processed data under `data/processed/`; both locations are ignored by Git.

## Study coverage

The validated source panel used by the paper contains 454 Spanish club-seasons across 2019-20 to 2025-26. The primary analysis constructs 18 La Liga promotion episodes and 18 relegation episodes.

## Reproducibility limitation

Code, aggregate tables, figures, and the final paper are public-release candidates. End-to-end numeric reproduction remains conditional on obtaining the authorized source export. Do not substitute fabricated data.
