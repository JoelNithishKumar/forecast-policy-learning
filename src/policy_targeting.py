# src/policy_targeting.py
"""
policy_targeting.py
-------------------
Deliverable 1: Targeting policy under budget (Forecast vs Insurance vs Nothing)

What this script does (plain English)
1) Loads the processed dataset created by src/prep_data.py
2) Uses ONLY baseline (pre-season) features to learn who benefits from:
   - forecast_offer
   - insurance_offer
   relative to control
3) Builds two targeting policies:
   Policy A (Unconstrained):
     - For each household, choose the option with the highest predicted NET benefit
       (benefit minus program cost): Forecast vs Insurance vs Nothing
   Policy B (Budget-constrained Insurance):
     - Allocate insurance to only the top X% of households by predicted insurance net benefit
       (X = INSURANCE_BUDGET_SHARE in config.py)
     - For everyone else, allocate forecast if forecast net benefit is positive; otherwise nothing
4) Saves:
   - A policy assignment file
   - Summary tables and a "budget frontier" plot (optional but useful)

Important notes
- Train/test split is done BY VILLAGE to respect cluster randomization.
- This is an MVP scaffold. For publishable work, you'd add doubly robust off-policy evaluation.
  Here we provide:
  (a) model-based predicted policy value and
  (b) a simple "matched-arm" observed-value check as a sanity check.

How to run (from repo root):
  python src/policy_targeting.py
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.model_selection import train_test_split
from sklearn.ensemble import GradientBoostingRegressor

from config import (
    get_paths,
    ensure_dirs,
    processed_data_path,
    # columns/constants
    COL_VILLAGE,
    COL_HH,
    COL_ARM,
    ARM_CONTROL,
    ARM_FORECAST,
    ARM_INSURANCE,
    BASELINE_FEATURES,
    COL_INVEST_TOTAL,
    RANDOM_SEED,
    # policy params
    INSURANCE_BUDGET_SHARE,
    COST_FORECAST,
    COST_INSURANCE,
)

# Output filenames
TABLE_POLICY_SUMMARY = "policy_summary.csv"
TABLE_POLICY_ASSIGNMENTS = "policy_assignments_test.csv"
FIG_BUDGET_FRONTIER = "fig_budget_frontier.png"


def _fit_arm_model(df_arm: pd.DataFrame, features: list[str], outcome: str) -> GradientBoostingRegressor:
    """Train a regression model on a single arm."""
    model = GradientBoostingRegressor(random_state=RANDOM_SEED)
    X = df_arm[features].values
    y = df_arm[outcome].values
    model.fit(X, y)
    return model


def _predict(model: GradientBoostingRegressor, df: pd.DataFrame, features: list[str]) -> np.ndarray:
    """Predict outcomes for a dataframe using baseline features."""
    return model.predict(df[features].values)


def _assign_unconstrained(test: pd.DataFrame) -> pd.Series:
    """
    Policy A: choose the option with highest predicted net benefit (benefit - cost).
    Returns a policy label per row: control / forecast / insurance.
    """
    net_forecast = (test["yhat_forecast"] - test["yhat_control"]) - COST_FORECAST
    net_insurance = (test["yhat_insurance"] - test["yhat_control"]) - COST_INSURANCE

    policy = pd.Series("control", index=test.index)
    # forecast if best and positive
    choose_forecast = (net_forecast > 0) & (net_forecast >= net_insurance)
    # insurance if best and positive
    choose_insurance = (net_insurance > 0) & (net_insurance > net_forecast)

    policy.loc[choose_forecast] = "forecast"
    policy.loc[choose_insurance] = "insurance"
    return policy


def _assign_budget(test: pd.DataFrame, insurance_budget_share: float) -> pd.Series:
    """
    Policy B: insurance budget constraint.
    - Give insurance to top X% by predicted insurance net benefit (if positive).
    - For the rest, give forecast if forecast net benefit is positive.
    - Otherwise control.
    """
    net_forecast = (test["yhat_forecast"] - test["yhat_control"]) - COST_FORECAST
    net_insurance = (test["yhat_insurance"] - test["yhat_control"]) - COST_INSURANCE

    policy = pd.Series("control", index=test.index)

    # pick top X% by net insurance benefit
    k = int(np.floor(len(test) * insurance_budget_share))
    ranked = test.assign(net_insurance=net_insurance).sort_values("net_insurance", ascending=False)
    top_idx = ranked.head(k).index

    # insurance to top group if net positive
    policy.loc[top_idx] = np.where(net_insurance.loc[top_idx] > 0, "insurance", "control")

    # rest: forecast if net forecast positive
    remaining = policy.index.difference(top_idx)
    policy.loc[remaining] = np.where(net_forecast.loc[remaining] > 0, "forecast", "control")

    return policy


def _predicted_policy_value(test: pd.DataFrame, policy: pd.Series) -> float:
    """
    Model-based value: average predicted outcome under the chosen policy.
    """
    yhat = np.where(
        policy == "insurance",
        test["yhat_insurance"],
        np.where(policy == "forecast", test["yhat_forecast"], test["yhat_control"]),
    )
    return float(np.mean(yhat))


def _matched_arm_value(test: pd.DataFrame, policy: pd.Series, outcome_col: str) -> tuple[float, float]:
    """
    Simple sanity check value:
    average observed outcome among units whose chosen policy matches their experimental arm.

    Returns:
    - mean observed outcome among matched units
    - match rate (fraction matched)

    Note: This is NOT a full off-policy evaluation; it is a quick check.
    """
    arm_map = {"control": ARM_CONTROL, "forecast": ARM_FORECAST, "insurance": ARM_INSURANCE}
    chosen_arm = policy.map(arm_map)
    match = test[COL_ARM] == chosen_arm
    if match.mean() == 0:
        return float("nan"), 0.0
    return float(test.loc[match, outcome_col].mean()), float(match.mean())


def _plot_budget_frontier(test: pd.DataFrame, out_path) -> None:
    """
    Optional: show how predicted policy value changes as insurance budget share changes.
    """
    shares = np.linspace(0.0, 0.30, 16)  # 0% to 30%
    values = []
    for s in shares:
        pol = _assign_budget(test, insurance_budget_share=float(s))
        values.append(_predicted_policy_value(test, pol))

    plt.figure()
    plt.plot(shares, values, marker="o")
    plt.xlabel("Insurance budget share")
    plt.ylabel("Predicted mean outcome under policy")
    plt.title("Budget Frontier: Insurance Coverage vs Predicted Outcome")
    plt.tight_layout()
    plt.savefig(out_path, dpi=200)
    plt.close()


def main() -> None:
    paths = get_paths()
    ensure_dirs(paths)

    df = pd.read_csv(processed_data_path(paths))

    # -------------------------
    # Train/test split BY VILLAGE
    # -------------------------
    villages = df[COL_VILLAGE].unique()
    v_train, v_test = train_test_split(villages, test_size=0.30, random_state=RANDOM_SEED)
    train = df[df[COL_VILLAGE].isin(v_train)].copy()
    test = df[df[COL_VILLAGE].isin(v_test)].copy()

    outcome = COL_INVEST_TOTAL
    features = BASELINE_FEATURES  # baseline-only

    # -------------------------
    # Fit separate models by arm (ITT)
    # -------------------------
    m_control = _fit_arm_model(train[train[COL_ARM] == ARM_CONTROL], features, outcome)
    m_forecast = _fit_arm_model(train[train[COL_ARM] == ARM_FORECAST], features, outcome)
    m_insurance = _fit_arm_model(train[train[COL_ARM] == ARM_INSURANCE], features, outcome)

    # Predict counterfactual outcomes on TEST villages
    test["yhat_control"] = _predict(m_control, test, features)
    test["yhat_forecast"] = _predict(m_forecast, test, features)
    test["yhat_insurance"] = _predict(m_insurance, test, features)

    # -------------------------
    # Build policies
    # -------------------------
    test["policy_unconstrained"] = _assign_unconstrained(test)
    test["policy_budget"] = _assign_budget(test, insurance_budget_share=INSURANCE_BUDGET_SHARE)

    # -------------------------
    # Evaluate policies (two ways)
    # -------------------------
    # Baselines (model-based)
    base_all_control = float(test["yhat_control"].mean())
    base_all_forecast = float(test["yhat_forecast"].mean())
    base_all_insurance = float(test["yhat_insurance"].mean())

    val_uncon = _predicted_policy_value(test, test["policy_unconstrained"])
    val_budget = _predicted_policy_value(test, test["policy_budget"])

    # Simple matched-arm observed check
    obs_uncon, match_uncon = _matched_arm_value(test, test["policy_unconstrained"], outcome)
    obs_budget, match_budget = _matched_arm_value(test, test["policy_budget"], outcome)

    summary = pd.DataFrame(
        [
            {"policy": "all_control", "pred_value": base_all_control, "obs_value_if_matched": np.nan, "match_rate": np.nan},
            {"policy": "all_forecast", "pred_value": base_all_forecast, "obs_value_if_matched": np.nan, "match_rate": np.nan},
            {"policy": "all_insurance", "pred_value": base_all_insurance, "obs_value_if_matched": np.nan, "match_rate": np.nan},
            {"policy": "unconstrained", "pred_value": val_uncon, "obs_value_if_matched": obs_uncon, "match_rate": match_uncon},
            {"policy": f"budget_insurance_{INSURANCE_BUDGET_SHARE:.2f}", "pred_value": val_budget, "obs_value_if_matched": obs_budget, "match_rate": match_budget},
        ]
    )

    # Policy assignment counts
    counts_uncon = test["policy_unconstrained"].value_counts(dropna=False).rename("count").reset_index().rename(columns={"index": "assignment"})
    counts_uncon["policy"] = "unconstrained"
    counts_budget = test["policy_budget"].value_counts(dropna=False).rename("count").reset_index().rename(columns={"index": "assignment"})
    counts_budget["policy"] = f"budget_insurance_{INSURANCE_BUDGET_SHARE:.2f}"

    counts = pd.concat([counts_uncon, counts_budget], ignore_index=True)

    # -------------------------
    # Save outputs
    # -------------------------
    summary_path = paths.tables_dir / TABLE_POLICY_SUMMARY
    assignments_path = paths.tables_dir / TABLE_POLICY_ASSIGNMENTS

    summary.to_csv(summary_path, index=False)

    out_assign = test[
        [
            COL_VILLAGE,
            COL_HH,
            COL_ARM,
            outcome,
            "yhat_control",
            "yhat_forecast",
            "yhat_insurance",
            "policy_unconstrained",
            "policy_budget",
        ]
    ].copy()
    out_assign.to_csv(assignments_path, index=False)

    counts_path = paths.tables_dir / "policy_assignment_counts.csv"
    counts.to_csv(counts_path, index=False)

    # Optional: budget frontier plot
    frontier_path = paths.figures_dir / FIG_BUDGET_FRONTIER
    _plot_budget_frontier(test, frontier_path)

    # Console output
    print("✅ Policy targeting complete")
    print(f"Saved summary:     {summary_path}")
    print(f"Saved assignments: {assignments_path}")
    print(f"Saved counts:      {counts_path}")
    print(f"Saved frontier:    {frontier_path}")
    print("\nPolicy summary (predicted value):")
    print(summary[["policy", "pred_value"]].to_string(index=False))


if __name__ == "__main__":
    main()