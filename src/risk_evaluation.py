# src/risk_evaluation.py
"""
risk_evaluation.py
------------------
Deliverable 3: Risk-focused evaluation (downside risk, not just averages)

What this script does (plain English)
1) Loads the processed dataset created by src/prep_data.py
2) Defines "downside risk" as being in the bottom X% of:
   - total_upfront_spend_inr (investment downside)
   - profit_inr (welfare downside)
   X is set in config.py as DOWNSIDE_QUANTILE (default 0.20 = bottom 20%)
3) Compares downside risk across arms (control vs forecast_offer vs insurance_offer)
4) Produces distribution-focused plots (CDF-style) to visualize shifts in the lower tail
5) Saves tables + figures to outputs/

Outputs:
- outputs/tables/risk_downside_by_arm.csv
- outputs/tables/risk_quantiles_by_arm.csv
- outputs/figures/fig_cdf_investment_by_arm.png
- outputs/figures/fig_cdf_profit_by_arm.png
- outputs/figures/fig_downside_rates_by_arm.png

How to run (from repo root):
  python src/risk_evaluation.py
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from config import (
    get_paths,
    ensure_dirs,
    processed_data_path,
    # columns/constants
    COL_ARM,
    ARM_CONTROL,
    ARM_FORECAST,
    ARM_INSURANCE,
    COL_INVEST_TOTAL,
    COL_PROFIT,
    DOWNSIDE_QUANTILE,
)

# Output filenames
FIG_CDF_INVEST = "fig_cdf_investment_by_arm.png"
FIG_CDF_PROFIT = "fig_cdf_profit_by_arm.png"
FIG_DOWNSIDE_RATES = "fig_downside_rates_by_arm.png"


def _empirical_cdf(x: np.ndarray):
    """Returns sorted x and its empirical CDF values."""
    x = x[np.isfinite(x)]
    x_sorted = np.sort(x)
    if len(x_sorted) == 0:
        return np.array([]), np.array([])
    y = np.arange(1, len(x_sorted) + 1) / len(x_sorted)
    return x_sorted, y


def _plot_cdf(df: pd.DataFrame, value_col: str, title: str, out_path):
    """Plots empirical CDF by arm for a given outcome."""
    arms_order = [ARM_CONTROL, ARM_FORECAST, ARM_INSURANCE]

    plt.figure()
    for arm in arms_order:
        x = df.loc[df[COL_ARM] == arm, value_col].to_numpy()
        xs, ys = _empirical_cdf(x)
        if len(xs) > 0:
            plt.plot(xs, ys, label=arm)

    plt.xlabel(value_col)
    plt.ylabel("Empirical CDF")
    plt.title(title)
    plt.legend()
    plt.tight_layout()
    plt.savefig(out_path, dpi=200)
    plt.close()


def main() -> None:
    paths = get_paths()
    ensure_dirs(paths)

    df = pd.read_csv(processed_data_path(paths))

    # -------------------------
    # 1) Define downside thresholds (global for descriptive comparison)
    # NOTE: For modeling/targeting, you'd define thresholds on TRAIN only to avoid leakage.
    # -------------------------
    invest_thresh = df[COL_INVEST_TOTAL].quantile(DOWNSIDE_QUANTILE)
    profit_thresh = df[COL_PROFIT].quantile(DOWNSIDE_QUANTILE)

    df["downside_invest"] = (df[COL_INVEST_TOTAL] <= invest_thresh).astype(int)
    df["downside_profit"] = (df[COL_PROFIT] <= profit_thresh).astype(int)

    # -------------------------
    # 2) Downside rates by arm
    # -------------------------
    downside_by_arm = (
        df.groupby(COL_ARM)
        .agg(
            n=(COL_INVEST_TOTAL, "size"),
            invest_downside_rate=("downside_invest", "mean"),
            profit_downside_rate=("downside_profit", "mean"),
            mean_invest=(COL_INVEST_TOTAL, "mean"),
            mean_profit=(COL_PROFIT, "mean"),
        )
        .reset_index()
    )

    # -------------------------
    # 3) Quantiles by arm (focus on lower tail)
    # -------------------------
    quantiles = [0.10, 0.20, 0.30, 0.50]
    rows = []
    for arm, g in df.groupby(COL_ARM):
        for q in quantiles:
            rows.append(
                {
                    "arm": arm,
                    "quantile": q,
                    "invest_q": g[COL_INVEST_TOTAL].quantile(q),
                    "profit_q": g[COL_PROFIT].quantile(q),
                }
            )
    quantiles_by_arm = pd.DataFrame(rows)

    # -------------------------
    # Save tables
    # -------------------------
    downside_path = paths.tables_dir / "risk_downside_by_arm.csv"
    quantiles_path = paths.tables_dir / "risk_quantiles_by_arm.csv"

    downside_by_arm.to_csv(downside_path, index=False)
    quantiles_by_arm.to_csv(quantiles_path, index=False)

    # -------------------------
    # 4) Figures
    # -------------------------
    # CDF plots (distribution perspective)
    _plot_cdf(
        df,
        value_col=COL_INVEST_TOTAL,
        title="CDF of Up-front Investment by Treatment Arm",
        out_path=paths.figures_dir / FIG_CDF_INVEST,
    )
    _plot_cdf(
        df,
        value_col=COL_PROFIT,
        title="CDF of Profit by Treatment Arm",
        out_path=paths.figures_dir / FIG_CDF_PROFIT,
    )

    # Downside rate bar chart
    arms_order = [ARM_CONTROL, ARM_FORECAST, ARM_INSURANCE]
    plot_df = downside_by_arm.set_index(COL_ARM).reindex(arms_order).reset_index()

    plt.figure()
    x = np.arange(len(plot_df[COL_ARM]))
    width = 0.35

    plt.bar(x - width / 2, plot_df["invest_downside_rate"], width=width, label="Investment downside")
    plt.bar(x + width / 2, plot_df["profit_downside_rate"], width=width, label="Profit downside")

    plt.xticks(x, plot_df[COL_ARM], rotation=15)
    plt.ylabel(f"Downside rate (bottom {int(DOWNSIDE_QUANTILE*100)}%)")
    plt.title("Downside Risk by Treatment Arm")
    plt.legend()
    plt.tight_layout()
    plt.savefig(paths.figures_dir / FIG_DOWNSIDE_RATES, dpi=200)
    plt.close()

    # Console summary
    print("✅ Risk evaluation complete")
    print(f"Downside thresholds: invest <= {invest_thresh:,.2f}, profit <= {profit_thresh:,.2f}")
    print(f"Saved tables:\n- {downside_path}\n- {quantiles_path}")
    print(f"Saved figures:\n- {paths.figures_dir / FIG_CDF_INVEST}\n- {paths.figures_dir / FIG_CDF_PROFIT}\n- {paths.figures_dir / FIG_DOWNSIDE_RATES}")


if __name__ == "__main__":
    main()