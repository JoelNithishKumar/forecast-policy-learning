
---

## `paper/appendix.md`

```markdown
# Appendix: Implementation Notes, Robustness, and Next Extensions

## A1) File map (what to look at)
### Tables
- `outputs/tables/prep_summary.csv`
- `outputs/tables/mechanism_by_arm.csv`
- `outputs/tables/mechanism_by_prior_tercile.csv`
- `outputs/tables/mechanism_scorecard_summary.csv`
- `outputs/tables/risk_downside_by_arm.csv`
- `outputs/tables/risk_quantiles_by_arm.csv`
- `outputs/tables/policy_summary.csv`
- `outputs/tables/policy_assignments_test.csv`
- `outputs/tables/policy_assignment_counts.csv`

### Figures
- Mechanism:
  - `fig_belief_change_by_arm`
  - `fig_belief_change_by_tercile_and_arm`
  - `fig_investment_by_arm`
  - `fig_investment_vs_belief_change`
- Risk:
  - `fig_cdf_investment_by_arm`
  - `fig_cdf_profit_by_arm`
  - `fig_downside_rates_by_arm`
- Policy:
  - `fig_budget_frontier`

## A2) Why some figures look “empty” or stacked
- Many plots show control/insurance belief change near zero, so those bars may be visually small.
- Scatter plots show a vertical pile at `belief_change = 0` because many households have near-zero belief updating in those arms.
- This is expected given the synthetic structure used in this run.

## A3) Mechanism interaction instability (Model C)
In `mechanism_scorecard_summary.csv`, the interaction model can produce extremely large coefficients (numerical instability). This typically reflects one of:
- collinearity among interaction terms
- limited within-arm variation in `belief_change`
- heavy mass at `belief_change = 0`

**Recommended fixes (choose one):**
1) Center belief change before interactions:
   - `belief_change_centered = belief_change - mean(belief_change)`
2) Estimate within-arm slope:
   - regress investment on belief_change within forecast arm only
3) Use a binned or winsorized belief_change for interaction plots

## A4) Robustness checks (easy upgrades)
### A) Outcome transformations
- Winsorize `total_upfront_spend_inr` and `profit_inr` at 1%/99%
- Use `log(1 + outcome)` and confirm qualitative ranking of arms/policies

### B) Alternative downside definitions
- Bottom 10% and bottom 30% (not just bottom 20%)
- CVaR-style metric (average outcome among bottom tail)

### C) Sensitivity to program costs
The targeting policies depend on placeholder costs:
- `COST_FORECAST = 10`
- `COST_INSURANCE = 120`

Run sensitivity:
- (forecast cost near zero)
- (insurance cost 2×)
- identify when forecast becomes optimal for more households

## A5) Research-grade policy evaluation (next step)
The current MVP reports model-based predicted policy value and a simple matched-arm sanity check.

To strengthen research credibility, add:
- **Doubly robust off-policy evaluation** for multi-arm settings
- **Clustered uncertainty** via village bootstrapping
- A clear “policy value with CI bands” figure

## A6) Fairness / equity extensions (optional, policy-relevant)
When targeting insurance, impose constraints like:
- minimum coverage for the smallest landholders
- equal opportunity across irrigation status
- avoid concentrating all subsidies in one subgroup

Then compare:
- constrained vs unconstrained policy value
- budget frontier with fairness constraints

## A7) How to map this scaffold to real RCT data later
1) Create a baseline covariate table and an endline outcomes table (or a combined file).
2) Ensure keys exist: `village_id`, `hh_id`
3) Ensure arms are labeled consistently:
   - `control`, `forecast_offer`, `insurance_offer`
4) Map your real columns to the baseline feature set and outcome(s)
5) Re-run the same scripts to regenerate tables/figures/policy outputs

## A8) Disclaimer
This repo uses synthetic data designed to match a cluster RCT workflow. It is not intended to reproduce the original study’s estimates. The goal is reproducible development of a policy-learning and evaluation pipeline that can be applied to real experimental data.