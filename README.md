# Forecasts vs Insurance: Mechanism + Risk + Budget Targeting (Synthetic RCT Scaffold)

This repository contains a **reproducible analysis scaffold** inspired by the cluster-randomized design in *“The Value of Forecasts”* (villages randomized; household outcomes). Using a single combined synthetic dataset (`synthetic_value_of_forecasts_mvp.csv`), the project produces three deliverables:

1) **Targeting policy under a budget** (Forecast vs Insurance vs Nothing)  
2) **Mechanism scorecard** (belief updating → up-front investment)  
3) **Risk-focused evaluation** (downside risk, not just averages)

> **Disclaimer:** The dataset is **synthetic** and is not the original study data.  
> The purpose is to build a clean, reusable workflow that can be mapped to real research data later.

---

## Big Question

**How should a policymaker allocate a low-cost forecast product and a higher-cost insurance subsidy—using only pre-season information—to maximize up-front investment and reduce downside risk, and through what belief-updating mechanism does the forecast work?**

---

## Research Questions (mapped to deliverables)

### Deliverable 1 — Budget Targeting Policy  
**Q1:** Given only baseline (pre-season) farmer characteristics, who should receive forecasts, who should receive insurance, and who should receive neither under a limited budget?

### Deliverable 2 — Mechanism Scorecard  
**Q2:** Does forecast access change beliefs about monsoon timing, and do those belief changes explain changes in up-front investment?

### Deliverable 3 — Risk-Focused Evaluation  
**Q3:** Do forecasts and/or insurance reduce the probability of “bad outcomes” (downside risk), and does targeting change when the policy objective is risk reduction instead of average gains?

---

## Dataset

**Input file:** `data/raw/synthetic_value_of_forecasts_mvp.csv`

### Design
- **Unit of randomization:** `village_id` (treatment assigned at village level)
- **Unit of observation:** `hh_id` (household-level outcomes)
- **Treatment arms:** `arm ∈ {control, forecast_offer, insurance_offer}` (constant within village)

### Key columns (examples)
**Baseline-style (pre-season features)**
- `land_ha`, `irrigation`, `assets_z`, `risk_aversion_z`, `past_shock`
- Priors: `prior_onset_mean_doy`, `prior_onset_sd`

**Mechanism**
- `post_onset_mean_doy` (posterior belief)
- `forecast_onset_doy` (forecast signal)

**Up-front investment**
- `seed_spend_inr`, `fert_spend_inr`, `labor_spend_inr`, `other_spend_inr`
- `total_upfront_spend_inr` (primary MVP outcome)

**Risk / welfare**
- `profit_inr` (used for downside-risk evaluation)

---

## Method Overview (plain English)

### A) Mechanism scorecard
- Measure belief updating: `belief_change = post_onset_mean_doy - prior_onset_mean_doy`
- Compare belief change by treatment arm
- Link belief changes to up-front investment outcomes
- Report heterogeneity by prior terciles (early / mid / late priors)

### B) Risk-focused evaluation
- Define downside risk (e.g., bottom 20% of investment or profit)
- Compare treatment arms on probability of bad outcomes
- Summarize which intervention reduces downside risk most

### C) Budget targeting policy
- Use **only baseline features** to predict expected outcomes under each arm
- Assign households to **Forecast / Insurance / Nothing** based on predicted benefit and program cost
- Compare against baselines: forecast-for-all, insurance-for-all (or same-budget random), do-nothing
- **Important:** train/test split is done **by village** to respect cluster randomization

---

## Folder Structure
```text
forecast-policy-learning/
├─ README.md
├─ LICENSE
├─ requirements.txt
├─ .gitignore
│
├─ data/
│  ├─ raw/
│  │  └─ synthetic_value_of_forecasts_mvp.csv
│  └─ processed/
│     └─ analysis_dataset.csv
│
├─ src/
│  ├─ 00_config.py
│  ├─ 01_prep_data.py
│  ├─ 02_mechanism_scorecard.py
│  ├─ 03_risk_evaluation.py
│  ├─ 04_policy_targeting.py
│  └─ utils/
│     ├─ io.py
│     ├─ features.py
│     ├─ plots.py
│     └─ metrics.py
│
├─ outputs/
│  ├─ figures/
│  ├─ tables/
│  └─ models/
│
├─ paper/
│  ├─ memo.md
│  ├─ appendix.md
│  └─ figures/              # (optional) copies of key figures for the write-up
│
└─ notebooks/

   └─ exploration.ipynb      # (optional; keep most work in /src for reproducibility)

