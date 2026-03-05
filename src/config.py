# src/config.py
"""
config.py
---------
Central place for:
1) Project paths (raw data, processed data, outputs)
2) Key column names (IDs, treatment arm, outcomes)
3) Analysis parameters (random seed, downside quantile, budget share, costs)

Why this file exists:
- So you never hard-code paths or column names inside analysis scripts.
- You can change folders/filenames/parameters once here, and everything still runs.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


# -----------------------------
# 1) PATH MANAGEMENT
# -----------------------------
@dataclass(frozen=True)
class Paths:
    """
    Holds all file/folder paths used by the project.

    Using a dataclass makes these paths easy to pass around
    and prevents accidental modification (frozen=True).
    """
    repo_root: Path

    data_dir: Path
    raw_dir: Path
    processed_dir: Path

    outputs_dir: Path
    tables_dir: Path
    figures_dir: Path
    models_dir: Path

    paper_dir: Path


def _repo_root_from_this_file() -> Path:
    """
    Infers repo root from this file's location.

    Assumes this file is at:
      <repo_root>/src/config.py

    So repo_root is one directory up from src/.
    """
    return Path(__file__).resolve().parents[1]


def get_paths() -> Paths:
    """
    Returns all project paths.

    Priority:
    1) If your repo exists at C:\\dev\\forecast-policy-learning, use that.
       (This matches your stated local path)
    2) Otherwise, infer the repo root from this file location.
       (So the code still works if you clone elsewhere)

    This prevents you from needing to edit code if you move the project folder.
    """
    preferred_repo = Path(r"C:\dev\forecast-policy-learning")
    repo_root = preferred_repo if preferred_repo.exists() else _repo_root_from_this_file()

    data_dir = repo_root / "data"
    raw_dir = data_dir / "raw"
    processed_dir = data_dir / "processed"

    outputs_dir = repo_root / "outputs"
    tables_dir = outputs_dir / "tables"
    figures_dir = outputs_dir / "figures"
    models_dir = outputs_dir / "models"

    paper_dir = repo_root / "paper"

    return Paths(
        repo_root=repo_root,
        data_dir=data_dir,
        raw_dir=raw_dir,
        processed_dir=processed_dir,
        outputs_dir=outputs_dir,
        tables_dir=tables_dir,
        figures_dir=figures_dir,
        models_dir=models_dir,
        paper_dir=paper_dir,
    )


def ensure_dirs(paths: Paths) -> None:
    """
    Creates required folders if they don't exist yet.

    This lets your scripts run on a fresh clone without manual folder creation.
    """
    paths.raw_dir.mkdir(parents=True, exist_ok=True)
    paths.processed_dir.mkdir(parents=True, exist_ok=True)
    paths.outputs_dir.mkdir(parents=True, exist_ok=True)
    paths.tables_dir.mkdir(parents=True, exist_ok=True)
    paths.figures_dir.mkdir(parents=True, exist_ok=True)
    paths.models_dir.mkdir(parents=True, exist_ok=True)
    paths.paper_dir.mkdir(parents=True, exist_ok=True)


# -----------------------------
# 2) FILENAMES
# -----------------------------
RAW_DATA_FILENAME = "synthetic_value_of_forecasts_mvp.csv"
PROCESSED_DATA_FILENAME = "analysis_dataset.csv"


def raw_data_path(paths: Paths) -> Path:
    """Full path to the raw CSV inside data/raw/"""
    return paths.raw_dir / RAW_DATA_FILENAME


def processed_data_path(paths: Paths) -> Path:
    """Full path to the cleaned/processed dataset inside data/processed/"""
    return paths.processed_dir / PROCESSED_DATA_FILENAME


# -----------------------------
# 3) COLUMN NAME CONSTANTS
# -----------------------------
# IDs / design
COL_VILLAGE = "village_id"     # cluster (randomization unit)
COL_HH = "hh_id"               # household id (observation unit)
COL_ARM = "arm"                # treatment arm label

# Arm values expected in the dataset
ARM_CONTROL = "control"
ARM_FORECAST = "forecast_offer"
ARM_INSURANCE = "insurance_offer"

# Baseline-style features (pre-season predictors)
BASELINE_FEATURES = [
    "land_ha",
    "irrigation",
    "assets_z",
    "risk_aversion_z",
    "past_shock",
    "prior_onset_mean_doy",
    "prior_onset_sd",
]

# Mechanism columns (belief updating)
COL_PRIOR = "prior_onset_mean_doy"
COL_POST = "post_onset_mean_doy"
COL_FORECAST_SIGNAL = "forecast_onset_doy"  # optional

# Outcome columns
COL_INVEST_TOTAL = "total_upfront_spend_inr"   # main MVP outcome (investment)
COL_PROFIT = "profit_inr"                      # risk/welfare outcome

INVEST_COMPONENTS = [
    "seed_spend_inr",
    "fert_spend_inr",
    "labor_spend_inr",
    "other_spend_inr",
]


# -----------------------------
# 4) ANALYSIS PARAMETERS
# -----------------------------
RANDOM_SEED = 42

# Risk evaluation: define downside as bottom X% of outcome
DOWNSIDE_QUANTILE = 0.20  # bottom 20%

# Policy learning: insurance budget (fraction eligible for insurance subsidy)
INSURANCE_BUDGET_SHARE = 0.15

# Program costs (illustrative; edit later if you want realism)
COST_FORECAST = 10.0
COST_INSURANCE = 120.0