# Submission Repository Handoff

## Current stage

This is a clean local submission/public-release candidate built from the validated master project. Nothing has been initialized, committed, pushed, or uploaded.

## Fixed final-paper graphs

The final paper must contain only the two graphs embedded in the preserved historical master PDF `Resource_Shock_Story_Style1_Spaced_A4.docx.pdf`. They were extracted directly from that PDF and were not redesigned, regenerated, cropped, substituted, or scientifically altered.

- `results/figures/final_figure1_original.jpg` - SHA-256 `e998390838411c3c2e0441a4d3b94c4bc3918a7779c2d84959796162965a7541`
- `results/figures/final_figure2_original.jpg` - SHA-256 `46f8e320fc4145c21fc6dd519ecd2ea79e0fd2b053cb5e6a1ff76c65f9d83ddc`

The submission DOCX contains exactly two embedded media images, and both hashes match these files. No other graph is included in `results/figures/` or in the paper. Future editing must preserve these two images unchanged; only surrounding prose, captions, or document placement may be adjusted.

## Scientific revision

Ruben’s two comments were resolved without changing the study design. The paper now treats the 18/18 below-median promotion observation as structurally expected context and emphasizes the verified 1.81 to 0.57 relative resource shock alongside the 78.4% median absolute uplift. The 2.62 versus 1.36 return comparison remains, but it is explicitly described as an association that may proxy for unobserved organizational strength.

## Included

- Revised editable paper and final PDF.
- Two final paper figures.
- Aggregate headline tables.
- Portable preparation, analysis, robustness, and audit code. The two approved paper graphs are preserved assets and are not regenerated.
- Data access/schema documentation.
- Reviewer-response audit and public-release audit.

## Excluded

Restricted SoccerSolver/dashboard row-level data, HTML exports, database dumps, processed row-level datasets, private project history, caches, environments, logs, temporary outputs, and unrelated work.

## Added-dashboard decision

The added multi-country dashboard was inspected but not incorporated. Its 454 overlapping Spain rows match the existing study and its fitted models are in-sample, not independent validation. Its roughly 40 additional Spain rows do not improve the defined La Liga-Segunda episode analysis.

## Reproduction

Install `requirements.txt`, obtain an authorized dashboard export, run the portable ingestion command, then execute the feature, analysis, and paper commands in `README.md`. The two approved graphs are preserved assets rather than regenerated outputs. Without authorized source access, users can inspect the complete code, aggregate results, figures, and paper but cannot rerun the row-level pipeline.

## Validation

- Headline values checked against authoritative master outputs.
- Causal wording reviewed contextually.
- Revised DOCX and PDF rendered as two A4 pages and visually inspected.
- The only included graphs are the two exact images extracted from the preserved historical PDF: `results/figures/final_figure1_original.jpg` (SHA-256 `e998390838411c3c2e0441a4d3b94c4bc3918a7779c2d84959796162965a7541`) and `results/figures/final_figure2_original.jpg` (SHA-256 `46f8e320fc4145c21fc6dd519ecd2ea79e0fd2b053cb5e6a1ff76c65f9d83ddc`). No replacement or additional graph is included.
- All included Python source compiled successfully.
- Portable ingestion was exercised with a caller-supplied authorized HTML export and wrote only to a temporary directory.
- Secret-pattern, absolute-path, symlink, and restricted-data-extension scans passed after removing an incidental `.DS_Store`.
- No remote or Git operation performed.

## Blockers before publication

- Row-level data redistribution authorization is unresolved.
- Complete authorship and `CITATION.cff` metadata are not finalized.
- MIT Sloan blind-review identity/repository-link rules must be confirmed.
- The anonymized repository placeholder in the paper must be handled according to the applicable review stage.

## Master provenance

The authoritative revised master remains in the private research project. The public copy contains only publication-appropriate material and does not depend on local absolute paths.

## Final Git-preparation update - 27 September 2026

### Reviewer resolution and methodology

- Ruben Comment 1: resolved. The 18/18 below-median observation is supporting, structurally expected context; the 1.81 to 0.57 RRP shock and 78.4% absolute uplift are emphasized.
- Ruben Comment 2: resolved. The 2.62 versus 1.36 comparison, rank-biserial r=-0.82, and exploratory p=0.006 are explicitly associative rather than causal.
- No central question, sample, RRP definition, episode construction, or statistical method was redesigned.
- `PromotionRelegation.html` was not incorporated and is not present in the repository.

### Final paper

- `paper/Resource_Shock_Story_MIT_Sloan_Revised.docx`
- `paper/Resource_Shock_Story_MIT_Sloan_Revised.pdf`

These are the only public paper files and are the unmistakable current versions.

### README and public assets

The README now follows the Problem 6 presentation pattern while retaining independent Problem 15 science. It is research-first and includes the research question, dataset, RRP definition, approved findings, only the two locked figures, interpretation, three reproducibility tiers, limitations, researcher profile, SoccerSolver collaboration, provisional citation, and licence sections.

Physical repository assets:

- `assets/RupayanHalder.jpeg` - no EXIF metadata; SHA-256 `64e529e780c9e33f5b6408c0ee700fccfbe586c8348ae526643683aecd5fe168`
- `assets/SoccerSolverLogo.png` - no EXIF metadata; SHA-256 `726f16865cf5f1bd11c937c8034fb72232a485f4c1882d4dc323f0912ea051f5`

All README images use repository-relative paths. The confirmed GitHub URL returned HTTP 200. LinkedIn returned its automated-access code 999, but the exact user-confirmed URL is correctly encoded. The email `mailto:` link is correct.

### Release status

- Data licence: **needs authorization**; no row-level data are included.
- Reproducibility: **conditional**; code and aggregate checks are public, end-to-end recomputation requires authorized source access.
- Authorship: **partial**; Rupayan Halder is confirmed, complete author list not finalized.
- Secret scan: **pass**; only safe audit-text mentions of scan terms were found.
- Portability: **pass**; no executable absolute paths, external symlinks, or private database URLs.
- Locked figures: **pass**; exactly two files with authoritative hashes.
- Large-file check: **pass**; no non-Git file exceeds 20 MB.

### Git status

- Local Git repository initialized.
- Branch renamed to `main`.
- All prospective release files staged.
- No commit created.
- No remote configured.
- Nothing pushed or published.

### Next action

Manually review the staged list, resolve final authorship and review-stage identity decisions, and decide whether the code-and-aggregate release can proceed while row-level data remain excluded. Only after explicit approval should a commit or GitHub remote be created.
