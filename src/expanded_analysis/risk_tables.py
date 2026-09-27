"""Phase 9: Kaplan-Meier risk-set tables and annotated KM figures with risk tables beneath."""
import numpy as np
import pandas as pd
from lifelines import KaplanMeierFitter

from plot_common import NEUTRAL, RELEGATED, load, savefig, TABLE_DIR, plt


def build_risk_table(durations, events, max_t=5):
    """season-by-season at-risk / events / censored / survival probability."""
    kmf = KaplanMeierFitter()
    kmf.fit(durations, event_observed=events)
    rows = []
    at_risk = len(durations)
    surv_df = kmf.survival_function_
    for t in range(0, max_t + 1):
        n_events = int(((durations == t) & (events == 1)).sum())
        n_censored = int(((durations == t) & (events == 0)).sum())
        if t in surv_df.index:
            surv_prob = surv_df.loc[t].values[0]
        else:
            idx = surv_df.index[surv_df.index <= t]
            surv_prob = surv_df.loc[idx.max()].values[0] if len(idx) else 1.0
        rows.append({"t_seasons": t, "at_risk": at_risk, "events": n_events, "censored": n_censored,
                      "survival_probability": round(surv_prob, 4)})
        at_risk -= (n_events + n_censored)
    return pd.DataFrame(rows), kmf


def km_with_risk_table(durations, events, title, color, ylabel, fname, risk_label_events, risk_label_censored):
    risk_df, kmf = build_risk_table(durations, events)

    fig = plt.figure(figsize=(7.5, 7.2))
    ax_km = fig.add_axes([0.13, 0.38, 0.82, 0.55])
    kmf.plot_survival_function(ax=ax_km, ci_show=True, color=color)
    ax_km.get_legend().remove()
    ax_km.set_xlabel("")
    ax_km.set_ylabel(ylabel)
    ax_km.set_title(title, fontsize=11.5)
    ax_km.set_ylim(0, 1.02)
    ax_km.set_xticks(risk_df.t_seasons)

    ax_tbl = fig.add_axes([0.13, 0.06, 0.82, 0.26])
    ax_tbl.axis("off")
    col_labels = ["Season t", "At risk", risk_label_events, risk_label_censored, "Survival prob."]
    cell_text = [[str(row.t_seasons), str(row.at_risk), str(row.events), str(row.censored), f"{row.survival_probability:.2f}"]
                 for _, row in risk_df.iterrows()]
    tbl = ax_tbl.table(cellText=cell_text, colLabels=col_labels, loc="center", cellLoc="center")
    tbl.auto_set_font_size(False)
    tbl.set_fontsize(8.5)
    tbl.scale(1, 1.4)
    ax_tbl.set_title("Risk table", fontsize=9.5, loc="left")

    fig.savefig(TABLE_DIR.parent / "figures" / fname)
    plt.close(fig)
    print(f"Wrote {TABLE_DIR.parent / 'figures' / fname}")
    return risk_df


def main():
    promo = load("promotion_episodes.csv")
    releg = load("relegation_episodes.csv")

    promo_risk = km_with_risk_table(
        promo.survival_duration, promo.relegation_event,
        "KM01. La Liga survival after promotion, with risk table", NEUTRAL,
        "P(still in La Liga)", "KM01_promotion_survival_with_risk_table.png",
        "Relegations", "Censored",
    )
    promo_risk.to_csv(TABLE_DIR / "promotion_km_risk_table.csv", index=False)
    print(f"Wrote {TABLE_DIR / 'promotion_km_risk_table.csv'}")

    releg_risk = km_with_risk_table(
        releg.time_to_return, releg.return_event,
        "KM02. Time to return after relegation, with risk table", RELEGATED,
        "P(not yet returned)", "KM02_relegation_return_with_risk_table.png",
        "Returns", "Censored",
    )
    releg_risk.to_csv(TABLE_DIR / "relegation_km_risk_table.csv", index=False)
    print(f"Wrote {TABLE_DIR / 'relegation_km_risk_table.csv'}")


if __name__ == "__main__":
    main()
