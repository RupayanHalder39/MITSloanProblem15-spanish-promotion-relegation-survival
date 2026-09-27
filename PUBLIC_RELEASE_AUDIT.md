# Public Release Audit

**Status:** Ready for local Git preparation; blocked for public push pending data-licence, authorship, and review-stage decisions
**Audit date:** 27 September 2026

## Required release status

- **DATA LICENCE: NEEDS AUTHORIZATION** - row-level SoccerSolver/dashboard data are excluded.
- **REPRODUCIBILITY: CONDITIONAL** - code and aggregates are inspectable; end-to-end recomputation requires independently authorized source access.
- **AUTHORSHIP: PARTIAL / NOT FINALIZED** - Rupayan Halder is confirmed; the complete author list remains unresolved.
- **SECRET SCAN: PASS** - no secret or credential material was detected in the prospective repository.
- **PORTABILITY: PASS** - executable workflows use repository-relative or user-supplied paths.
- **FIGURE HASH CHECK: PASS** - the two locked figures match the authoritative hashes and are the only files under `results/figures/`.
- **PUBLICATION STATUS: READY FOR GIT PREPARATION / BLOCKED FOR PUBLICATION** - local initialization and staging are appropriate; commit and push require the remaining decisions below.

## Safe to release

- Portable preparation, analysis, robustness, and validation source code.
- Revised manuscript DOCX and PDF, subject to conference identity/review rules.
- Aggregate headline result tables.
- The two locked historical paper figures. Figure 2 contains club labels already present in the approved paper; no additional row-level data are supplied.
- Methodology, limitations, reviewer-response audit, and reproduction instructions.

## Deliberately excluded

- SoccerSolver/dashboard row-level data and embedded HTML exports.
- Raw and processed JSON/CSV episode datasets.
- SQL dumps, database files, Parquet files, caches, virtual environments, logs, temporary files, and historical internal drafts.
- The new `PromotionRelegation.html`, which is overlapping proprietary source material rather than independent validation.
- Private master-project handoff history containing local paths and internal workflow details.

## Data licensing

Redistribution authorization for the row-level SoccerSolver data has not been established. The repository links reproduction to an independently obtained authorized local export and does not include the source data. This is a publication blocker if the intended release requires bundled data or a claim of unconditional full reproduction.

`PromotionRelegation.html` was inspected only for overlap and provenance. Its 454 overlapping Spain observations are the same underlying study data, its fitted models are in-sample rather than independent validation, and the file is excluded.

## Locked figures

Only these two approved historical figures are included:

- `results/figures/final_figure1_original.jpg` - SHA-256 `e998390838411c3c2e0441a4d3b94c4bc3918a7779c2d84959796162965a7541`
- `results/figures/final_figure2_original.jpg` - SHA-256 `46f8e320fc4145c21fc6dd519ecd2ea79e0fd2b053cb5e6a1ff76c65f9d83ddc`

Both were extracted directly from the preserved historical paper. They were not redesigned, regenerated, cropped, recolored, relabelled, or supplemented.

## Sensitive-information and secret scan

The completed local scan found no credentials, tokens, API keys, passwords, SSH material, `.env` files, private database locations, private correspondence, or confidential club records. Incidental `.DS_Store` files created during local inspection were removed and are covered by `.gitignore`. The scan should still be rerun immediately before publication.

## Portability

Executable code and README instructions use repository-relative paths or caller-supplied input paths. A complete text scan found no `/Users/rupayan/`, `file://`, macOS absolute-path dependency, Windows absolute-path dependency, or private database URI. The repository has no symlinks. The portable ingestion script was tested against an authorized local dashboard passed as a command-line argument and extracted 2,357 data rows, seven model groups, and 348 preview rows into a temporary directory outside the repository.

## Authorship

Rupayan Halder is confirmed as a researcher/author. The complete author list is not finalized, so `CITATION.cff` is explicitly provisional and must be reviewed before publication. The SoccerSolver collaboration statement does not make SoccerSolver or its personnel authors.

## Reproducibility

The included Python source compiled successfully. The pipeline and aggregate results are inspectable. End-to-end reproduction is conditional on authorized access to the excluded row-level source. The paper’s headline values have been validated against the authoritative private project outputs. Both the editable DOCX and final PDF render as two clean A4 pages; every page was visually inspected.

The included `scripts/verify_release.py` passed its locked-figure, required-file, headline-aggregate, and symlink checks. The only CSV is the safe aggregate `results/tables/main_results_table.csv`; no raw or processed row-level dataset is present.

## Public identity assets

The researcher photograph and SoccerSolver logo are physical files under `assets/` and are referenced through relative paths. Pillow inspection found no EXIF entries in either public copy. The photograph contains no GPS or device metadata. The confirmed GitHub link resolved with HTTP 200; LinkedIn returned its automated-access response code 999, while the user-confirmed URL and email `mailto:` syntax were preserved exactly.

## Git preparation

The repository is initialized locally on branch `main`, and all prospective release files are staged for inspection. No commit exists, no remote is configured, and nothing has been pushed or published.

## Remaining publication decisions

1. Obtain or document row-level data redistribution authorization, or retain the current code-only/aggregate-output release model.
2. Finalize the complete author list and citation metadata.
3. Confirm whether author identity and repository linkage are allowed at the relevant MIT Sloan review stage.
4. Replace the manuscript’s anonymized repository placeholder only when permitted.
