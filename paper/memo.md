# Forecasts vs Insurance: Mechanism + Risk + Budget Targeting (Project Memo)

## 1) Big Question
How should a policymaker allocate a low-cost forecast product and a higher-cost insurance subsidy—using only pre-season information—to maximize up-front investment and reduce downside risk, and through what belief-updating mechanism does the forecast work?

## 2) What this repo does
This repo is a reproducible scaffold inspired by a cluster-randomized field experiment design:
- **Unit of randomization:** village (`village_id`)
- **Unit of observation:** household (`hh_id`)
- **Treatment arms:** `control`, `forecast_offer`, `insurance_offer` (constant within village)

This project produces three deliverables:
1) **Budget targeting policy:** Forecast vs Insurance vs Nothing  
2) **Mechanism scorecard:** belief updating → investment  
3) **Risk-focused evaluation:** downside risk, not just mean effects

> Note: The dataset used here is **synthetic** and is not the original study data.  
> The contribution is the **workflow + policy-learning framework** and how the outputs map to the research question.

## 3) Data + key variables
**Input:** `data/raw/synthetic_value_of_forecasts_mvp.csv`  
**Processed:** `data/processed/analysis_dataset.csv`

Key variables:
- Beliefs: `prior_onset_mean_doy`, `post_onset_mean_doy`
- Mechanism: `belief_change = post - prior`
- Up-front investment (primary MVP outcome): `total_upfront_spend_inr`
- Welfare/risk endpoint: `profit_inr`
- Baseline covariates (for targeting): land, irrigation, assets, risk aversion, past shock, priors

## 4) Methods (high level)
### Mechanism scorecard
We test whether the forecast arm changes beliefs (belief updating “first stage”) and whether belief changes explain investment outcomes. We also examine heterogeneity using terciles of baseline priors (early/mid/late).

### Risk evaluation
We define downside risk as being in the **bottom 20%** of the outcome distribution and compare downside rates across arms for:
- investment downside (`total_upfront_spend_inr`)
- profit downside (`profit_inr`)

### Budget targeting policy
Using **only baseline covariates**, we train separate prediction models by arm (control/forecast/insurance) to predict expected investment. We then construct two rollout policies:
- **Unconstrained:** choose the option with the highest predicted net benefit (benefit minus program cost).
- **Budget-constrained:** insurance limited to 15% coverage; forecast allocated to others if predicted net benefit is positive; otherwise “nothing.”

Train/test splits are done **by village** to respect cluster randomization.

## 5) Results

### Deliverable 2 — Mechanism scorecard (belief updating → investment)
**Key finding:** In this synthetic run, the forecast arm does not shift beliefs on average, and belief change is not strongly associated with investment.

From `outputs/tables/mechanism_scorecard_summary.csv`:
- Forecast arm effect on belief change: **−0.08** (p = 0.80)
- Belief change → investment: **−18.7 INR** per 1-day shift (p = 0.28)
- Insurance arm effect on investment: **+882.4 INR** (p ≈ 2.38e−12)

Figures:
- `fig_belief_change_by_arm`: average belief change is near zero; control/insurance are ~0.
- `fig_belief_change_by_tercile_and_arm`: belief updating varies by prior tercile within forecast arm (early vs late priors move in opposite directions), but the average effect is small.
- `fig_investment_by_arm`: insurance increases investment substantially; forecast does not.

**Interpretation:** In this scaffold run, forecast effects do not appear to operate through a strong average belief-updating channel, while insurance has a large direct investment impact.

---

### Deliverable 3 — Risk-focused evaluation (downside risk)
**Key finding:** Insurance substantially reduces downside risk for investment, but not for profit in this synthetic draw.

From `outputs/tables/risk_downside_by_arm.csv` (bottom 20% downside):
- **Investment downside rate**
  - Control: **22.49%**
  - Forecast: **23.90%** (+1.41 pp vs control)
  - Insurance: **13.69%** (−8.80 pp vs control)

- **Profit downside rate**
  - Control: **18.17%**
  - Forecast: **21.39%** (+3.21 pp vs control)
  - Insurance: **20.44%** (+2.26 pp vs control)

Figures:
- `fig_cdf_investment_by_arm`: insurance shifts the investment distribution away from the lower tail.
- `fig_downside_rates_by_arm`: downside investment risk is much lower under insurance.
- `fig_cdf_profit_by_arm`: profit distributions overlap heavily (profit is noisy here).

**Interpretation:** Under this scaffold, insurance is the key instrument for preventing very low investment outcomes. Profit is noisier and does not show downside improvements in this run.

---

### Deliverable 1 — Targeting policy under budget (Forecast vs Insurance vs Nothing)
**Key finding:** Targeting outperforms universal policies and produces a clear budget frontier.

From `outputs/tables/policy_summary.csv` (model-predicted mean investment):
- All Control: **11,639.6**
- All Forecast: **11,624.4**
- All Insurance: **12,578.7**
- **Unconstrained targeting:** **12,845.2** (best)
- **Budget targeting (15% insurance):** **12,322.2**

From `outputs/tables/policy_assignment_counts.csv` (test sample = 900 households):
- **Unconstrained policy:** 65.3% insurance / 16.2% forecast / 18.4% nothing
- **Budget policy (15% cap):** 15.0% insurance / 36.9% forecast / 48.1% nothing

Figure:
- `fig_budget_frontier`: predicted mean outcome increases as insurance budget share rises (with diminishing returns).

**Interpretation:** When insurance is expensive/scarce, the policy-learning framework concentrates insurance on the highest predicted-benefit group, uses forecasts for a middle group, and assigns “nothing” where predicted net gains are low.

## 6) How the three deliverables answer the big question
- **Mechanism (why forecasts work):** The scorecard diagnoses whether forecast effects run through belief updating and whether beliefs map to investments.
- **Risk lens (what matters for climate policy):** The downside evaluation focuses on avoiding bad outcomes, not only improving averages.
- **Policy translation (what to do at scale):** The targeting rule converts experimental heterogeneity into an implementable rollout strategy under a budget.

## 7) Limitations (important for credibility)
- The dataset is synthetic; results are illustrative. The value is the reproducible workflow and policy-learning logic.
- Current policy evaluation is primarily model-based. Research-grade evaluation would add doubly robust off-policy estimators and clustered uncertainty.
- Interaction mechanism models can be numerically unstable; see Appendix.

## 8) Reproducibility
Run from repo root:
```bash
python src/prep_data.py
python src/mechanism_scorecard.py
python src/risk_evaluation.py
python src/policy_targeting.py


Key output tables used in this memo:
outputs/tables/mechanism_scorecard_summary.csv

outputs/tables/risk_downside_by_arm.csv

outputs/tables/policy_summary.csv

outputs/tables/policy_assignment_counts.csv