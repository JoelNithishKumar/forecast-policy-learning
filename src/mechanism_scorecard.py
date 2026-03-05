# src/mechanism_scorecard.py
"""
mechanism_scorecard.py
----------------------
Deliverable 2: Mechanism Scorecard (belief updating -> up-front investment)

What this script does (plain English)
1) Loads the processed dataset created by src/prep_data.py
2) Quantifies belief updating:
   - belief_change = post_onset_mean_doy - prior_onset_mean_doy
3) Produces a small "scorecard" of mechanism evidence:
   A) Do forecast villages show larger belief updating than control/insurance?
   B) Is belief_change associated with up-front investment (total_upfront_spend_inr)?
   C) Does this relationship differ by prior tercile (early/mid/late)?
4) Writes tables + figures to outputs/:
   - outputs/tables/mechanism_scorecard_summary.csv
   - outputs/tables/mechanism_by_arm.csv
   - outputs/tables/mechanism_by_prior_tercile.csv
   - outputs/figures/fig_belief_change_by_arm.png
   - outputs/figures/fig_investment_by_arm.png
   - outputs/figures/fig_investment_vs_belief_change.png
   - outputs/figures/fig_belief_change_by_tercile_and_arm.png

How to run (from repo root):
  python src/mechanism_scorecard.py
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import statsmodels.api as sm

from config import (
    get_paths,
    ensure_dirs,
    processed_data_path,
    # columns/constants
    COL_VILLAGE,
    COL_ARM,
    ARM_CONTROL,
    ARM_FORECAST,
    ARM_INSURANCE,
    COL_INVEST_TOTAL,
    COL_PRIOR,
    COL_POST,
)

# Output filenames
FIG_BELIEF_BY_ARM = "fig_belief_change_by_arm.png"
FIG_INVEST_BY_ARM = "fig_investment_by_arm.png"
FIG_INVEST_VS_BELIEF = "fig_investment_vs_belief_change.png"
FIG_BELIEF_BY_TERCILE_ARM = "fig_belief_change_by_tercile_and_arm.png"


def _cluster_ols(df: pd.DataFrame, y_col: str, x_cols: list[str], cluster_col: str):
    """
    Runs a simple OLS with cluster-robust SEs (clustered at village level).
    Returns a fitted statsmodels result.
    """
    X = sm.add_constant(df[x_cols], has_constant="add")
    y = df[y_col]
    model = sm.OLS(y, X, missing="drop")
    res = model.fit(cov_type="cluster", cov_kwds={"groups": df[cluster_col]})
    return res


def main() -> None:
    paths = get_paths()
    ensure_dirs(paths)

    df = pd.read_csv(processed_data_path(paths))

    # Ensure the derived columns exist (created in prep_data.py)
    if "belief_change" not in df.columns:
        df["belief_change"] = df[COL_POST] - df[COL_PRIOR]
    if "prior_tercile" not in df.columns:
        raise ValueError("prior_tercile not found. Run src/prep_data.py first.")

    # -------------------------
    # 1) Mechanism summary tables
    # -------------------------
    by_arm = (
        df.groupby(COL_ARM)
        .agg(
            n=("belief_change", "size"),
            mean_belief_change=("belief_change", "mean"),
            sd_belief_change=("belief_change", "std"),
            mean_invest=(COL_INVEST_TOTAL, "mean"),
            sd_invest=(COL_INVEST_TOTAL, "std"),
        )
        .reset_index()
    )

    # Belief updating by arm and prior tercile (heterogeneity)
    by_tercile_arm = (
        df.groupby(["prior_tercile", COL_ARM])
        .agg(
            n=("belief_change", "size"),
            mean_belief_change=("belief_change", "mean"),
            mean_invest=(COL_INVEST_TOTAL, "mean"),
        )
        .reset_index()
        .sort_values(["prior_tercile", COL_ARM])
    )

    # -------------------------
    # 2) Regression-style "scorecard" tests
    # -------------------------
    # A) Does forecast offer shift beliefs? (belief_change ~ arm indicators)
    df_reg = df.copy()
    df_reg["is_forecast"] = (df_reg[COL_ARM] == ARM_FORECAST).astype(int)
    df_reg["is_insurance"] = (df_reg[COL_ARM] == ARM_INSURANCE).astype(int)

    res_belief = _cluster_ols(
        df_reg,
        y_col="belief_change",
        x_cols=["is_forecast", "is_insurance"],
        cluster_col=COL_VILLAGE,
    )

    # B) Is belief_change associated with investment? (investment ~ belief_change + arm)
    res_invest = _cluster_ols(
        df_reg,
        y_col=COL_INVEST_TOTAL,
        x_cols=["belief_change", "is_forecast", "is_insurance"],
        cluster_col=COL_VILLAGE,
    )

    # C) Does the belief->investment link differ by arm? (interaction terms)
    df_reg["belief_x_forecast"] = df_reg["belief_change"] * df_reg["is_forecast"]
    df_reg["belief_x_insurance"] = df_reg["belief_change"] * df_reg["is_insurance"]

    res_interact = _cluster_ols(
        df_reg,
        y_col=COL_INVEST_TOTAL,
        x_cols=[
            "belief_change",
            "is_forecast",
            "is_insurance",
            "belief_x_forecast",
            "belief_x_insurance",
        ],
        cluster_col=COL_VILLAGE,
    )

    # Build a human-readable scorecard table (coefficients only)
    def coef_table(res, label):
        out = pd.DataFrame(
            {
                "term": res.params.index,
                "coef": res.params.values,
                "se_cluster": res.bse.values,
                "p_value": res.pvalues.values,
            }
        )
        out["model"] = label
        return out

    scorecard = pd.concat(
        [
            coef_table(res_belief, "A_belief_change_on_arm"),
            coef_table(res_invest, "B_investment_on_belief_and_arm"),
            coef_table(res_interact, "C_investment_interactions"),
        ],
        ignore_index=True,
    )

    # -------------------------
    # Save tables
    # -------------------------
    by_arm_path = paths.tables_dir / "mechanism_by_arm.csv"
    by_tercile_arm_path = paths.tables_dir / "mechanism_by_prior_tercile.csv"
    scorecard_path = paths.tables_dir / "mechanism_scorecard_summary.csv"

    by_arm.to_csv(by_arm_path, index=False)
    by_tercile_arm.to_csv(by_tercile_arm_path, index=False)
    scorecard.to_csv(scorecard_path, index=False)

    # -------------------------
    # 3) Figures (simple, clean)
    # -------------------------

    # Figure 1: Belief change by arm (bar)
    arms_order = [ARM_CONTROL, ARM_FORECAST, ARM_INSURANCE]
    plot_df = by_arm.set_index(COL_ARM).reindex(arms_order).reset_index()

    plt.figure()
    plt.bar(plot_df[COL_ARM], plot_df["mean_belief_change"])
    plt.xlabel("Treatment arm")
    plt.ylabel("Mean belief change (post - prior)")
    plt.title("Belief Updating by Treatment Arm")
    plt.xticks(rotation=15)
    plt.tight_layout()
    plt.savefig(paths.figures_dir / FIG_BELIEF_BY_ARM, dpi=200)
    plt.close()

    # Figure 2: Investment by arm (bar)
    plt.figure()
    plt.bar(plot_df[COL_ARM], plot_df["mean_invest"])
    plt.xlabel("Treatment arm")
    plt.ylabel("Mean total up-front spend (INR)")
    plt.title("Up-front Investment by Treatment Arm")
    plt.xticks(rotation=15)
    plt.tight_layout()
    plt.savefig(paths.figures_dir / FIG_INVEST_BY_ARM, dpi=200)
    plt.close()

    # Figure 3: Investment vs belief change (scatter with simple line)
    # (Keep it simple and readable; no fancy styling)
    plt.figure()
    plt.scatter(df["belief_change"], df[COL_INVEST_TOTAL], alpha=0.35)
    plt.xlabel("Belief change (post - prior)")
    plt.ylabel("Total up-front spend (INR)")
    plt.title("Investment vs Belief Updating")

    # Add a simple fitted line (least squares) for visual intuition
    x = df["belief_change"].to_numpy()
    y = df[COL_INVEST_TOTAL].to_numpy()
    mask = np.isfinite(x) & np.isfinite(y)
    if mask.sum() > 2:
        b1, b0 = np.polyfit(x[mask], y[mask], 1)
        xs = np.linspace(x[mask].min(), x[mask].max(), 50)
        ys = b1 * xs + b0
        plt.plot(xs, ys)
    plt.tight_layout()
    plt.savefig(paths.figures_dir / FIG_INVEST_VS_BELIEF, dpi=200)
    plt.close()

    # Figure 4: Belief change by tercile and arm (grouped bar)
    pivot = (
        by_tercile_arm.pivot(index="prior_tercile", columns=COL_ARM, values="mean_belief_change")
        .reindex(index=["early", "mid", "late"], columns=arms_order)
    )

    plt.figure()
    x_pos = np.arange(len(pivot.index))
    width = 0.25

    for i, arm in enumerate(arms_order):
        plt.bar(x_pos + (i - 1) * width, pivot[arm].values, width=width, label=arm)

    plt.xticks(x_pos, pivot.index)
    plt.xlabel("Prior tercile")
    plt.ylabel("Mean belief change (post - prior)")
    plt.title("Belief Updating by Priors and Treatment Arm")
    plt.legend()
    plt.tight_layout()
    plt.savefig(paths.figures_dir / FIG_BELIEF_BY_TERCILE_ARM, dpi=200)
    plt.close()

    # Console summary (helpful when running)
    print("✅ Mechanism scorecard complete")
    print(f"Saved tables:\n- {by_arm_path}\n- {by_tercile_arm_path}\n- {scorecard_path}")
    print(f"Saved figures:\n- {paths.figures_dir / FIG_BELIEF_BY_ARM}\n- {paths.figures_dir / FIG_INVEST_BY_ARM}\n"
          f"- {paths.figures_dir / FIG_INVEST_VS_BELIEF}\n- {paths.figures_dir / FIG_BELIEF_BY_TERCILE_ARM}")


if __name__ == "__main__":
    main()