"""
Build a canonical club identity mapping for the Spanish club-season data and
apply it to produce a normalized interim table.

Problem this solves
--------------------
The raw dashboard export (data/raw/spain_dashboard_club_seasons_raw.csv) mixes
two naming conventions by source/division:
  - La Liga rows: proper case with accents, e.g. "Deportivo Alavés"
  - Segunda Division / Primera Federación rows: lowercase, accents stripped,
    e.g. "deportivo alaves"

The same club therefore appears under two different literal strings depending
on which division it was in that season. Left unresolved, this breaks every
season-to-season join (a promoted club "disappears" because its Segunda-season
name string never matches its La Liga-season name string).

Approach
--------
1. Normalize every raw team string: Unicode-strip accents, lowercase, collapse
   whitespace. This normalized string is the join key (`name_key`).
2. Group all raw variants by `name_key`. Verified manually (see
   DataFeasibilityAuditReport.md) that this key produces zero false merges:
   reserve/B teams ("Real Sociedad B", "Villarreal CF B") normalize to their
   own distinct keys, and cross-checking every promoted/relegated club's
   next-season division membership resolves cleanly under this key with no
   ambiguous cases across all 6 season-to-season transitions in the data.
3. Pick a canonical display name per key: prefer a variant that has upper-case
   letters (i.e. came from a properly-cased source, typically the La Liga
   rows) over an all-lowercase variant. If only lowercase variants exist
   (clubs that never appeared in La Liga in this window), title-case it as a
   best-effort display name -- this CANNOT recover missing accents and is
   flagged via `display_name_source = "title_cased_lowercase_only"`.
4. Assign a stable synthetic `club_id` (slug of the normalized key). This is
   NOT a real-world/database club id -- no such id is present in the source
   dashboard data -- and this is documented.

Never overwrites data/raw/. Writes only to data/metadata/ and data/interim/.
"""
import logging
import re
import unicodedata
from pathlib import Path

import pandas as pd

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger(__name__)

BASE = Path(__file__).resolve().parents[2]
RAW_CSV = BASE / "data" / "raw" / "spain_dashboard_club_seasons_raw.csv"
METADATA_DIR = BASE / "data" / "metadata"
INTERIM_DIR = BASE / "data" / "interim"

# Clubs known (from local football-history knowledge, documented here rather
# than left implicit) to have dissolved / refounded during the observed
# window. Kept as metadata, not silently merged with any other entity.
KNOWN_DEFUNCT_NOTES = {
    "extremadura ud (- 2022)": "Extremadura UD was dissolved in 2022 after relegation/administrative "
    "issues; no successor entity is merged into this identity.",
}

# Standalone Spanish club legal-form prefixes. The dashboard source drops
# these inconsistently between tiers (Segunda rows tend to keep "SD"/"CD"/"CF"/
# "UD" style prefixes, Primera Federación rows often drop them), which
# otherwise splits one real club into two name_keys, e.g. "sd huesca" (Segunda)
# vs "huesca" (La Liga). Stripped only as a SECOND pass, after verifying by
# hand (see audit report) that every resulting merge candidate has
# non-overlapping season/division coverage -- i.e. it looks like the same
# club recorded two ways, never two different clubs sharing a stripped name.
LEGAL_FORM_PREFIXES = {"ad", "cd", "cf", "ud", "sd", "rcd", "rc", "ce", "ca", "sc", "cp"}


def strip_legal_prefix(key: str) -> str:
    toks = key.split()
    if len(toks) > 1 and toks[0] in LEGAL_FORM_PREFIXES:
        return " ".join(toks[1:])
    return key


def strip_accents(s: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFKD", s) if not unicodedata.combining(c))


def normalize_key(raw_name: str) -> str:
    s = strip_accents(raw_name)
    s = re.sub(r"\s*\(.*?\)\s*", " ", s)  # drop parenthetical annotations, e.g. "(- 2022)"
    s = s.lower().strip()
    s = re.sub(r"\s+", " ", s)
    return s


def slugify(key: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", key).strip("_")


def pick_display_name(variants: list[str]) -> tuple[str, str]:
    cased = [v for v in variants if v != v.lower()]
    if cased:
        # Prefer the shortest properly-cased variant occurring most often is overkill;
        # take the first alphabetically for determinism.
        return sorted(cased)[0], "source_proper_case"
    # Only lowercase/no-accent variants available: best-effort title case.
    base = sorted(variants)[0]
    base_clean = re.sub(r"\s*\(.*?\)\s*", "", base).strip()
    return base_clean.title(), "title_cased_lowercase_only"


def main():
    df = pd.read_csv(RAW_CSV)
    df["name_key"] = df["team"].apply(normalize_key)

    groups = df.groupby("name_key")["team"].apply(lambda s: sorted(set(s))).to_dict()

    # Pass 1: one identity per literal normalized name.
    key_to_display = {}
    key_to_source = {}
    for key, variants in groups.items():
        display, source = pick_display_name(variants)
        key_to_display[key] = display
        key_to_source[key] = source

    # Pass 2: merge legal-form-prefix variants of the same club, but only when
    # their season/division coverage does not overlap (safety check against
    # accidentally merging two different clubs that happen to share a
    # stripped name).
    df["stripped_key"] = df["name_key"].apply(strip_legal_prefix)
    key_seasons = df.groupby("name_key").apply(
        lambda g: set(zip(g["season"], g["league"])), include_groups=False
    ).to_dict()

    merge_target = {}  # name_key -> canonical name_key
    for stripped, keys in df.groupby("stripped_key")["name_key"].apply(lambda s: sorted(set(s))).items():
        if len(keys) < 2:
            continue
        coverage_sets = [key_seasons[k] for k in keys]
        overlap = any(a & b for i, a in enumerate(coverage_sets) for b in coverage_sets[i + 1:])
        if overlap:
            log.warning("NOT merging %s: season/division overlap detected, likely genuinely distinct clubs", keys)
            continue
        # Safe to merge: canonical key is the one with the richer (properly-cased) display, else the longest.
        canonical = max(keys, key=lambda k: (key_to_source[k] == "source_proper_case", len(k)))
        for k in keys:
            merge_target[k] = canonical
        log.info("Merging prefix variants %s -> '%s' (%s)", keys, canonical, key_to_display[canonical])

    df["name_key"] = df["name_key"].map(lambda k: merge_target.get(k, k))

    mapping_rows = []
    for key in sorted(df["name_key"].unique()):
        variants = sorted(set(df.loc[df["name_key"] == key, "team"]))
        display, source = pick_display_name(variants)
        club_id = f"esp_{slugify(key)}"
        note = KNOWN_DEFUNCT_NOTES.get(key, "")
        merged_from = sorted({k for k, v in merge_target.items() if v == key and k != key})
        if merged_from:
            note = (note + " " if note else "") + f"Merged prefix-variant name_keys: {merged_from}."
        mapping_rows.append(
            {
                "club_id": club_id,
                "name_key": key,
                "canonical_display_name": display,
                "display_name_source": source,
                "raw_name_variants": " | ".join(variants),
                "n_raw_variants": len(variants),
                "notes": note,
            }
        )

    mapping = pd.DataFrame(mapping_rows).sort_values("canonical_display_name")
    METADATA_DIR.mkdir(parents=True, exist_ok=True)
    mapping_path = METADATA_DIR / "club_name_mapping.csv"
    mapping.to_csv(mapping_path, index=False)
    log.info("Wrote %d canonical club identities -> %s", len(mapping), mapping_path)

    ambiguous = mapping[mapping["display_name_source"] == "title_cased_lowercase_only"]
    log.info(
        "%d/%d club identities never appeared with proper casing/accents (title-cased best-effort; "
        "accents not guaranteed correct). See notes column in %s.",
        len(ambiguous),
        len(mapping),
        mapping_path,
    )

    key_to_id = mapping.set_index("name_key")["club_id"].to_dict()
    key_to_display = mapping.set_index("name_key")["canonical_display_name"].to_dict()
    df["club_id"] = df["name_key"].map(key_to_id)
    df["club_name"] = df["name_key"].map(key_to_display)

    INTERIM_DIR.mkdir(parents=True, exist_ok=True)
    out_path = INTERIM_DIR / "spain_club_seasons_normalized.csv"
    df.to_csv(out_path, index=False)
    log.info("Wrote normalized club-season table (%d rows) -> %s", len(df), out_path)


if __name__ == "__main__":
    main()
