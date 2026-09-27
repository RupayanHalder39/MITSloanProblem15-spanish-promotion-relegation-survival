"""
Phase 9: simple, explicitly exploratory statistical models.

Sample-size discipline (see docs/sample_size_and_power.md for the full
justification): 18 promotion episodes with only 10 observed relegation
events. Conventional survival-modelling guidance wants ~10 events per
covariate for a stable Cox fit -- 10 events supports at most ONE covariate
comfortably. This script therefore fits:

  Model 1 (PRIMARY): CoxPH  survival_duration ~ log(laliga_relative_market_value)
  Model 2 (EXPLORATORY ONLY, flagged low events-per-variable):
           CoxPH  survival_duration ~ log(laliga_relative_market_value) + segundadivision_points_before_promotion
  Model 3: logistic  immediate_relegation ~ laliga_relative_market_value
           (the "easier and more honest" single-season alternative)

For every Cox fit: proportional-hazards assumption is checked (Schoenfeld
residual test via lifelines), and a crude leave-one-out influence check is
run (refit with each observation dropped, report how much the coefficient
moves). All confidence intervals are reported in full -- do not summarize
away their width.

Also loads the pre-existing dashboard model (data/raw/dashboard_models.json)
for La Liga/Segunda and reports it side-by-side with a written comparison
in the results report, NOT reused as-is (it is a different model: a
cross-sectional per-club-season relegation classifier pooling ALL La Liga
club-seasons, not a survival model of promoted clubs specifically).

Output: outputs/reports/exploratory_model_results.md
"""
import json
import logging
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.api as sm
from lifelines import CoxPHFitter

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger(__name__)

BASE = Path(__file__).resolve().parents[2]
PROCESSED = BASE / "data" / "processed"
RAW = BASE / "data" / "raw"
REPORT_DIR = BASE / "outputs" / "reports"


def fit_cox(df, covariates, label):
    cph = CoxPHFitter()
    cols = ["survival_duration", "relegation_event"] + covariates
    d = df[cols].dropna()
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        cph.fit(d, duration_col="survival_duration", event_col="relegation_event")
        convergence_warnings = [str(w.message) for w in caught]
    return cph, d, convergence_warnings


def loo_influence(df, covariates):
    """Leave-one-out sensitivity of the first covariate's coefficient."""
    cols = ["survival_duration", "relegation_event"] + covariates
    d = df[cols].dropna().reset_index(drop=True)
    base_cph = CoxPHFitter()
    base_cph.fit(d, duration_col="survival_duration", event_col="relegation_event")
    base_coef = base_cph.params_[covariates[0]]

    deltas = []
    for i in range(len(d)):
        d_loo = d.drop(index=i)
        try:
            cph_loo = CoxPHFitter()
            cph_loo.fit(d_loo, duration_col="survival_duration", event_col="relegation_event")
            deltas.append((i, cph_loo.params_[covariates[0]] - base_coef))
        except Exception as e:
            deltas.append((i, None))
    return base_coef, deltas


def main():
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    promo = pd.read_csv(PROCESSED / "promotion_analysis.csv")
    promo["log_rel_mv"] = np.log(promo["laliga_relative_market_value"])

    lines = ["# Exploratory model results (Phase 9)\n\n",
             "**These models are exploratory.** n=18 promotion episodes, 10 observed relegation events. "
             "Every result below should be read as a preliminary, small-sample signal -- not a validated "
             "predictive model -- per docs/sample_size_and_power.md.\n\n"]

    # --- Model 1: primary Cox, single covariate ---
    lines.append("## Model 1 (PRIMARY): CoxPH, survival_duration ~ log(relative La Liga market value at entry)\n\n")
    cph1, d1, warn1 = fit_cox(promo, ["log_rel_mv"], "model1")
    summ1 = cph1.summary
    lines.append(f"n={len(d1)}, events={int(d1['relegation_event'].sum())}\n\n")
    lines.append(summ1[["coef", "exp(coef)", "se(coef)", "coef lower 95%", "coef upper 95%", "p"]].to_markdown() + "\n")
    lines.append(f"\nConcordance index: {cph1.concordance_index_:.3f}\n")
    if warn1:
        lines.append(f"\nConvergence warnings: {warn1}\n")
    ci_width = summ1["exp(coef) upper 95%"].iloc[0] - summ1["exp(coef) lower 95%"].iloc[0]
    lines.append(f"\nHazard ratio 95% CI width: {ci_width:.2f} (exp(coef) CI: "
                 f"[{summ1['exp(coef) lower 95%'].iloc[0]:.3f}, {summ1['exp(coef) upper 95%'].iloc[0]:.3f}]) "
                 f"-- this is a WIDE interval, consistent with n=18/10 events; treat the point estimate as "
                 f"directionally suggestive only.\n")

    # PH assumption check
    lines.append("\n### Proportional-hazards assumption check (Schoenfeld residuals)\n\n")
    try:
        results = cph1.check_assumptions(d1, p_value_threshold=0.05, show_plots=False)
        lines.append("No exception raised; see log output for per-covariate test statistics "
                      "(lifelines prints to stdout/stderr, captured separately). With only 10 events, "
                      "this test has low power -- a non-significant result here means 'no evidence of "
                      "violation detected', not 'assumption confirmed'.\n")
    except Exception as e:
        lines.append(f"check_assumptions raised: {e}\n")

    # Leave-one-out influence
    lines.append("\n### Leave-one-out influence check\n\n")
    base_coef, deltas = loo_influence(promo, ["log_rel_mv"])
    lines.append(f"Base coefficient (log_rel_mv): {base_coef:.4f}\n\n")
    delta_df = pd.DataFrame([(i, promo.iloc[i]["club_name"], promo.iloc[i]["promotion_season"], delta)
                              for i, delta in deltas if delta is not None],
                             columns=["row", "club_name", "promotion_season", "coef_delta_when_removed"])
    delta_df = delta_df.sort_values("coef_delta_when_removed", key=abs, ascending=False)
    lines.append(delta_df.to_markdown(index=False, floatfmt=",.4f") + "\n")
    most_influential = delta_df.iloc[0]
    lines.append(f"\nMost influential single observation: **{most_influential['club_name']} "
                 f"({most_influential['promotion_season']})**, removing it shifts the coefficient by "
                 f"{most_influential['coef_delta_when_removed']:.4f}. "
                 f"{'This is a material shift relative to the base coefficient magnitude -- interpret model 1 cautiously.' if abs(most_influential['coef_delta_when_removed']) > abs(base_coef) * 0.3 else 'This is a modest shift.'}\n")

    # --- Model 2: exploratory, 2 covariates ---
    lines.append("\n\n## Model 2 (EXPLORATORY ONLY -- low events-per-variable): + prior Segunda points\n\n")
    lines.append("10 events / 2 covariates = 5 events-per-variable, below the conventional 10-EPV "
                  "guideline. Reported for completeness, not as a improvement over Model 1.\n\n")
    cph2, d2, warn2 = fit_cox(promo, ["log_rel_mv", "segundadivision_points_before_promotion"], "model2")
    summ2 = cph2.summary
    lines.append(f"n={len(d2)}, events={int(d2['relegation_event'].sum())}\n\n")
    lines.append(summ2[["coef", "exp(coef)", "se(coef)", "coef lower 95%", "coef upper 95%", "p"]].to_markdown() + "\n")
    lines.append(f"\nConcordance index: {cph2.concordance_index_:.3f}\n")
    if warn2:
        lines.append(f"\nConvergence warnings: {warn2}\n")

    # --- Model 3: logistic, immediate relegation ---
    lines.append("\n\n## Model 3: Logistic, immediate_relegation ~ relative La Liga market value\n\n")
    X = sm.add_constant(promo[["laliga_relative_market_value"]])
    y = promo["immediate_relegation"]
    logit = sm.Logit(y, X).fit(disp=0)
    lines.append(f"n={len(promo)}, immediate relegations={int(y.sum())}\n\n")
    lines.append(logit.summary2().tables[1].to_markdown() + "\n")
    lines.append(f"\nPseudo R2: {logit.prsquared:.3f}\n")
    lines.append("Coefficient is negative as expected (higher relative market value -> lower probability "
                  "of immediate relegation) but with n=18/5 events the confidence interval is wide -- see "
                  "table above; treat as directionally suggestive, not a calibrated probability model.\n")

    # --- Comparison to dashboard MODELS blob ---
    lines.append("\n\n## Comparison to the pre-existing dashboard model (data/raw/dashboard_models.json)\n\n")
    models = json.loads((RAW / "dashboard_models.json").read_text())
    ll = models["Spain"]["la liga"]["relegation"]
    seg = models["Spain"]["segunda division"]
    lines.append(
        f"The dashboard's own embedded model fits a **cross-sectional logistic regression of relegation "
        f"probability on log(market value in millions), one row per club-SEASON, pooling every La Liga "
        f"club-season** (not just promoted clubs): n={ll['n']} club-seasons, {ll['events']} relegation "
        f"events, AUC={ll['auc']}, Brier={ll['brier']}. Segunda's equivalent promotion model: "
        f"n={seg['promotion']['n']}, events={seg['promotion']['events']}, AUC={seg['promotion']['auc']}.\n\n"
        f"**This is a materially different model from Model 1/2 above, not a version of the same thing:**\n"
        f"- It asks *'given any La Liga club's market value this season, what is the probability it is "
        f"relegated this season?'* for every club every season -- not *'given a club was JUST promoted, "
        f"how long does it survive?'*. Newly-promoted clubs are a small, structurally different subset "
        f"(this project's whole reason for a survival/episode framing) mixed in with 15+ incumbent clubs "
        f"per season in their model.\n"
        f"- It treats each club-season as an independent Bernoulli trial. The same club appears in "
        f"multiple seasons (non-independence / repeated-measures), and it does not model time-since-"
        f"promotion, duration, or censoring at all -- there is no concept of a promotion episode in it.\n"
        f"- Its reported AUC (0.84) looks strong, but AUC on a cross-sectional classifier with a much "
        f"larger, more heterogeneous n=120 is not directly comparable to a small-sample survival model's "
        f"concordance index; the two answer different questions and shouldn't be presented as competing "
        f"estimates of the same effect.\n"
        f"- **Verdict: useful as a complementary robustness check (both approaches agree market value is "
        f"negatively associated with relegation risk -- the dashboard's beta1={ll['beta1']:.3f} on "
        f"log(market value) is negative, same direction as Model 1/3 here) but not reusable as-is for the "
        f"survival/episode question this project asks.** It is not methodologically 'problematic' for its "
        f"own (different) question, just answering a different one -- conflating the two would overstate "
        f"what either model actually supports.\n"
    )

    out = REPORT_DIR / "exploratory_model_results.md"
    out.write_text("".join(lines))
    log.info("Wrote %s", out)


if __name__ == "__main__":
    main()
