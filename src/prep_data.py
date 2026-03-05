# src/prep_data.py
"""
prep_data.py
------------
Purpose:
- Load the single combined raw CSV (synthetic_value_of_forecasts_mvp.csv)
- Run basic data validation checks for a cluster-randomized design
- Create derived variables needed for the three deliverables:
  (1) Mechanism scorecard: belief updating -> investment
  (2) Risk evaluation: downside risk indicators
  (3) Policy targeting: baseline-only feature set (used later)

Inputs:
- data/raw/synthetic_value_of_forecasts_mvp.csv

Outputs:
- data/processed/analysis_dataset.csv
- outputs/tables/prep_summary.csv

How to run (from repo root):
  python src/prep_data.py
"""

from __future__ import annotations

import pandas as pd
import numpy as np

from config import (
    get_paths,
    ensure_dirs,
    raw_data_path,
    processed_data_path,
    # columns / constants
    COL_VILLAGE,
    COL_HH,
    COL_ARM,
    ARM_CONTROL,
    ARM_FORECAST,
    ARM_INSURANCE,
    BASELINE_FEATURES,
    COL_PRIOR,
    COL_POST,
    COL_INVEST_TOTAL,
    COL_PROFIT,
    INVEST_COMPONENTS,
    DOWNSIDE_QUANTILE,
)

EXPECTED_ARMS = {ARM_CONTROL, ARM_FORECAST, ARM_INSURANCE}


def _assert_required_columns(df: pd.DataFrame, required: list[str]) -> None:
    """Stops early if the dataset is missing any required columns."""
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns: {missing}")


def _assert_arm_constant_within_village(df: pd.DataFrame) -> None:
    """
    Cluster randomized design check:
    Every household in the same village should have the same treatment arm.
    """
    nunique = df.groupby(COL_VILLAGE)[COL_ARM].nunique()
    bad = nunique[nunique > 1]
    if len(bad) > 0:
        raise ValueError(
            "Found villages with multiple arms (should be 1 arm per village). "
            f"Example villages: {bad.index[:10].tolist()}"
        )


def _make_prior_tercile(df: pd.DataFrame) -> pd.Series:
    """
    Creates terciles of prior monsoon-onset beliefs.
    - early = lowest third of prior_onset_mean_doy
    - mid   = middle third
    - late  = highest third
    """
    terc = pd.qcut(df[COL_PRIOR], q=3, labels=["early", "mid", "late"])
    return terc.astype(str)


def main() -> None:
    # 1) Resolve paths + ensure folders exist
    paths = get_paths()
    ensure_dirs(paths)

    # 2) Load raw data
    raw_path = raw_data_path(paths)
    df = pd.read_csv(raw_path)

    # 3) Basic validation checks
    required_cols = (
        [COL_VILLAGE, COL_HH, COL_ARM, COL_PRIOR, COL_POST, COL_INVEST_TOTAL, COL_PROFIT]
        + BASELINE_FEATURES
        + INVEST_COMPONENTS
    )
    _assert_required_columns(df, required_cols)

    # Arm labels check
    arms = set(df[COL_ARM].dropna().unique().tolist())
    if not arms.issubset(EXPECTED_ARMS):
        raise ValueError(f"Unexpected arm labels found: {arms}. Expected subset of {EXPECTED_ARMS}")

    # Cluster randomization integrity check
    _assert_arm_constant_within_village(df)

    # Unique keys check (one row per household)
    if df.duplicated(subset=[COL_VILLAGE, COL_HH]).any():
        raise ValueError("Duplicate (village_id, hh_id) rows found. Expected unique household rows.")

    # 4) Create derived variables

    # Mechanism: belief updating
    df["belief_change"] = df[COL_POST] - df[COL_PRIOR]

    # Heterogeneity: terciles of priors
    df["prior_tercile"] = _make_prior_tercile(df)

    # Spending shares (useful QA + robustness)
    total = df[COL_INVEST_TOTAL].replace(0, np.nan)
    for col in INVEST_COMPONENTS:
        df[f"{col}_share"] = df[col] / total

    # Risk flags: define downside as bottom X% (MVP)
    # NOTE: For modeling scripts later, compute thresholds on TRAIN only to avoid leakage.
    invest_thresh = df[COL_INVEST_TOTAL].quantile(DOWNSIDE_QUANTILE)
    profit_thresh = df[COL_PROFIT].quantile(DOWNSIDE_QUANTILE)

    df["downside_invest"] = (df[COL_INVEST_TOTAL] <= invest_thresh).astype(int)
    df["downside_profit"] = (df[COL_PROFIT] <= profit_thresh).astype(int)

    # 5) Save processed dataset
    out_processed = processed_data_path(paths)
    df.to_csv(out_processed, index=False)

    # 6) Save a small QA/summary table (helps confirm pipeline ran correctly)
    prep_summary = pd.DataFrame(
        {
            "n_rows": [len(df)],
            "n_villages": [df[COL_VILLAGE].nunique()],
            "n_households": [df[COL_HH].nunique()],
            "arms": [", ".join(sorted(list(arms)))],
            "invest_downside_threshold": [float(invest_thresh)],
            "profit_downside_threshold": [float(profit_thresh)],
            "mean_invest_total": [df[COL_INVEST_TOTAL].mean()],
            "mean_profit": [df[COL_PROFIT].mean()],
        }
    )
    summary_path = paths.tables_dir / "prep_summary.csv"
    prep_summary.to_csv(summary_path, index=False)

    print("✅ Prep complete")
    print(f"Raw:       {raw_path}")
    print(f"Processed: {out_processed}")
    print(f"Summary:   {summary_path}")


if __name__ == "__main__":
    main()