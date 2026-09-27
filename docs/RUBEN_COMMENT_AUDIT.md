# Ruben Comment Audit

**Project:** Spanish promotion and relegation survival study<br>
**Audit date:** 27 September 2026<br>
**Decision:** Minimal scientific revision; no methodological redesign

## Scope and evidence reviewed

The audit covered the complete project handoff, feasibility and claim audits, methodology and story documents, processed analysis datasets, episode tables, main and expanded result tables, robustness reports, figure-generation scripts, manuscript validation reports, the historical two-page paper, and the added `PromotionRelegation.html` dashboard. Numerical claims were checked against the authoritative processed episode datasets and generated result tables rather than inferred from the PDF.

## Comment 1: the 18 of 18 promotion result

### 1. Original manuscript claim

The historical paper stated that the league boundary produced a “striking mirror image” and foregrounded the observation that every promoted club in the sample (18/18) entered La Liga below the league median.

### 2. Ruben's exact concern

> “Near-mechanical by construction. A newly promoted club is almost always resource-poor relative to an established top-flight. The 18/18 framing overstates the finding.”

### 3. Evidence inspected

- `data/processed/promotion_analysis.csv`
- `data/processed/promotion_episodes.csv`
- `outputs/tables/main_results_table.md`
- `outputs/tables/promotion_group_comparison.md`
- `outputs/reports/ExpandedExperimentalResultsReport.md`
- `outputs/reports/Sloan_Abstract_Number_Validation.md`
- `paper/manuscript.md`
- Figure-generation assertions in `src/reports/build_abstract_visual_figures.py`

The verified promotion values are:

- 18 promotion episodes;
- median final-Segunda RRP: **1.81**;
- median first-La Liga RRP: **0.57**;
- median promotion resource shock: **-1.27**;
- 18/18 first-La Liga RRP values below 1.0;
- 18/18 clubs increased absolute squad market value after promotion;
- median absolute squad-value uplift: **78.38%**, reported as **78.4%**.

### 4. Whether the concern is valid

**Yes, substantially.** The result is not a mathematical identity: a promoted club could, in principle, enter La Liga above its median. It is nevertheless strongly structurally expected because RRP is re-normalized against the much richer La Liga comparison set after promotion. Treating 18/18 as surprising overstates its evidentiary contribution.

### 5. Scientific interpretation

The stronger empirical contribution is the size and consistency of the **relative resource shock**. Promoted clubs became substantially richer in absolute squad value while becoming much weaker relative to the clubs they newly faced. The verified median shift from RRP 1.81 to 0.57, alongside an absolute-value uplift of 78.4%, expresses this “richer yet relatively poorer” result directly.

### 6. Whether additional analysis was necessary

No. The existing paired pre/post RRP construction and absolute-value uplift already answer the interpretive issue. A new model, new causal design, expanded country sample, or altered episode construction was not scientifically necessary.

### 7. Exact manuscript changes made

- Removed “striking” framing from the 18/18 observation.
- Explicitly described the below-median pattern as strongly structurally expected when moving into the richer top-flight environment.
- Retained 18/18 only as a supporting descriptive fact.
- Made the 1.81 to 0.57 RRP shift and the 78.4% absolute uplift the main promotion result.
- Added the intuitive interpretation that every promoted club became richer in absolute terms while becoming weaker relative to its new competitors.
- Replaced the Figure 1 caption’s unsupported causal verb “produces” with “is accompanied by.”

### 8. Whether any numbers changed

No scientific value changed. The paper reports the validated median uplift rounded from 78.38% to 78.4%, consistent with the existing reporting convention.

### 9. Remaining limitation

RRP depends on division-season medians and the source dashboard’s squad-market-value snapshots. The exact valuation methodology and snapshot timing are not independently documented. The Spain sample also contains only 18 promotion episodes.

## Comment 2: RRP as a proxy rather than a driver

### 1. Original manuscript claim

The historical paper reported that relegated clubs returning within two seasons entered Segunda at median RRP 2.62 versus 1.36 for clubs not yet returned, with rank-biserial r=-0.82 and p=0.006.

### 2. Ruben's exact concern

> “Strongest finding. But RRP at entry correlates with everything else a well-run club brings down, structure, academy, staff. RRP may be a proxy, not the driver.”

### 3. Evidence inspected

- `data/processed/relegation_analysis.csv`
- `data/processed/relegation_episodes.csv`
- `outputs/tables/relegation_group_comparison.md`
- `outputs/tables/main_results_table.md`
- `outputs/reports/ExpandedExperimentalResultsReport.md`
- `outputs/reports/exploratory_model_results.md`
- `outputs/reports/manuscript_number_validation.md`
- `DataFeasibilityAuditReport.md`

The verified comparison is:

- return within two seasons: n=7, median first-Segunda RRP **2.62**;
- no observed return by the window end: n=8, median first-Segunda RRP **1.36**;
- rank-biserial effect size **r=-0.82**;
- Mann-Whitney exploratory **p=0.006**;
- the direction remains stable in the existing leave-one-out checks.

The available data do not contain defensible controls for academy quality, coaching or sporting-director continuity, ownership stability, wages, revenue, recruitment quality, parachute payments, player retention, or broader organizational quality.

### 4. Whether the concern is valid

**Yes.** The observed separation is strong within this small sample, but it does not identify a causal effect of RRP. Squad market value and RRP may summarize or proxy for several unobserved sporting and organizational advantages.

### 5. Scientific interpretation

Higher entry RRP is strongly **associated with** faster return. It is useful descriptively and potentially predictively, but the present design cannot establish that raising RRP would itself cause a faster return.

### 6. Whether additional analysis was necessary

No additional low-risk analysis in the authorized dataset could resolve the omitted-variable problem. A causal claim would require new variables and a substantially different design, which was outside the approved scope.

### 7. Exact manuscript changes made

- Retained the verified 2.62 versus 1.36 result, effect size, exploratory p-value, group sizes, and leave-one-out statement.
- Labeled the relationship explicitly as an association.
- Added a direct warning that it should not be interpreted causally.
- Added the substantive proxy/confounding limitation and enumerated the main unobserved organizational factors.
- Clarified that the figures and p-values are descriptive and exploratory rather than causal estimates.

### 8. Whether any numbers changed

No.

### 9. Remaining limitation

The comparison is based on 7 fast-return and 8 not-yet-returned episodes; the latter are right-censored rather than known permanent non-returners. The small observational sample and omitted organizational variables prevent causal interpretation.

## Added dashboard audit: PromotionRelegation.html

The added dashboard contains 2,357 club-season rows across Argentina, England, France, Germany, Italy, Portugal, and Spain. Its Spain section contains 494 rows. All **454** Spain club-seasons used by the study match the existing source on season, league, team, points, position, division, and squad market value. The additional **40** Spain rows are primarily extra Primera Federación/current-season coverage. The dashboard also contains fitted league models, including Spain regressions and promotion/relegation classifiers.

The dashboard was **not incorporated into the study**. Its overlapping Spain rows are the same underlying observations, and its fitted models are in-sample. They therefore do not constitute independent validation. Adding the 40 extra rows would alter lower-division coverage without improving the construction of the 18 La Liga-Segunda promotion and 18 relegation episodes or resolving either reviewer concern. It was used only as a read-only provenance and overlap cross-check.

## Final audit decision

Both reviewer comments are resolved through precise framing, explicit association-versus-causation language, and a strengthened limitations statement. The supplied research graphs remain unchanged; only their document placement and caption spacing were controlled in the revised paper. The central question, RRP definition, core sample, episode construction, statistical comparisons, and scientific values remain unchanged.
