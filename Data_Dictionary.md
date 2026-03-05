# DATA_DICTIONARY.md  
**Dataset:** `data/raw/synthetic_value_of_forecasts_mvp.csv`  
**Purpose:** Synthetic, research-like dataset that mirrors a **cluster-randomized field experiment** (village-level randomization; household-level outcomes) inspired by “Value of Forecasts”-style designs.

> **Important:** This dataset is **synthetic** (simulated). It is not the original study data.  
> The goal is to support a **reproducible pipeline** that produces:
> 1) a mechanism scorecard (belief updating → investment),  
> 2) downside-risk evaluation, and  
> 3) a budget-constrained targeting policy (forecast vs insurance vs nothing).

---

## 1) Study Design & Units

### Unit of randomization (cluster)
- **Village** (`village_id`)
- Every household in a village shares the same intervention assignment (`arm`).

### Unit of observation
- **Household** (`hh_id`)
- Outcomes and behavior are measured at the household level.

### Why this matters
Cluster randomization changes how we analyze data:
- We keep **arm constant within village**.
- We split train/test **by village** for policy models (to avoid information leakage).
- In research-grade work, uncertainty is **clustered by village**.

---

## 2) Key Concepts the Dataset Represents

This dataset encodes the core causal story behind the study:

**Forecast offer** → may change **beliefs** about monsoon timing → may change **up-front investments** (seed/fertilizer/labor) → may change **welfare outcomes** (profits)  
**Insurance offer** → reduces downside risk and may change **investment behavior** through risk protection

Your project focuses on:
- **Mechanism:** Did beliefs change and did that map into investment?
- **Risk:** Did interventions reduce “bad outcomes” (bottom tail)?
- **Policy translation:** Under a budget, who should get forecast vs insurance vs nothing?

---

## 3) Variables by Category (with explanation + why needed)

### A) Identifiers & experimental assignment
| Variable | Type | Example | Meaning | Why needed |
|---|---|---:|---|---|
| `village_id` | int | 0–249 | Village cluster ID | Needed to respect cluster randomization (same arm within village), cluster splits, and clustering in inference. |
| `hh_id` | int | 0… | Household ID | Needed to uniquely identify each observation and merge (baseline/endline) if needed later. |
| `arm` | string | `control`, `forecast_offer`, `insurance_offer` | Treatment group assigned to the village | This is the core causal variable. All comparisons are across arms. |

---

### B) Offer indicators (intention-to-treat)
| Variable | Type | Example | Meaning | Why needed |
|---|---|---:|---|---|
| `offered_forecast` | 0/1 | 1 | Whether the village was offered the forecast product | Defines ITT (“offer”) effects even when not everyone buys. |
| `offered_insurance` | 0/1 | 0 | Whether the village was offered insurance | Same role as above for insurance. |

**Why we include “offered” variables:**  
Most RCT analysis focuses on **offer effects** (ITT) because take-up is voluntary and can be confounded by who chooses to buy.

---

### C) Take-up & willingness-to-pay (demand side)
| Variable | Type | Example | Meaning | Why needed |
|---|---|---:|---|---|
| `wtp_forecast_inr` | float | 65.2 | Willingness-to-pay for forecast | Helps model demand, heterogeneity, and policy pricing/screening logic. |
| `wtp_insurance_inr` | float | 140.5 | Willingness-to-pay for insurance | Same for insurance. |
| `take_forecast` | 0/1 | 1 | Household bought/used forecast (synthetic) | Enables descriptive take-up and “who buys” analysis; can be used for extensions (TOT). |
| `take_insurance` | 0/1 | 0 | Household bought/used insurance (synthetic) | Same. |

**Why demand variables matter:**  
For scale-up, it’s not enough to know “it works.” You also need to know:
- Will people adopt it?
- Who adopts it?
- Should policy subsidize it or target it?

---

### D) Baseline-style household covariates (pre-treatment features)
These are the inputs to the targeting model and help interpret heterogeneity.

| Variable | Type | Meaning | Why needed |
|---|---|---|---|
| `land_ha` | float | Land size in hectares | Proxy for scale/capacity; often predicts investment levels and risk exposure. Used for targeting and heterogeneity. |
| `irrigation` | 0/1 | Access to irrigation | In monsoon-dependent settings, irrigation changes sensitivity to rainfall timing. Strong modifier of treatment effects. |
| `assets_z` | float | Standardized asset index | Proxy for wealth/credit constraints. Affects ability to invest and adopt products. |
| `risk_aversion_z` | float | Standardized risk aversion | Core to insurance demand and investment under uncertainty; key for targeting insurance. |
| `past_shock` | 0/1 | Prior shock exposure | Captures trauma/experience; can affect trust, updating, and demand for insurance. |

**Why these are necessary for your project:**  
Your targeting policy must use **only pre-season information** (baseline features). These are realistic predictors that a program could observe or elicit before rollout.

---

### E) Beliefs & forecast signal (mechanism variables)
These represent the “information channel.”

| Variable | Type | Meaning | Why needed |
|---|---|---|---|
| `prior_onset_mean_doy` | float | Household’s prior expected monsoon onset (day-of-year) | The starting belief. Needed to measure belief updating and heterogeneity by priors. |
| `prior_onset_sd` | float | Uncertainty about onset (spread) | Higher uncertainty can raise WTP for info and change response to forecasts. |
| `forecast_onset_doy` | float | Forecast signal (day-of-year) | The information being offered. Helps interpret belief movement and supports future extensions. |
| `post_onset_mean_doy` | float | Household’s posterior belief after offer/info | Needed to compute belief updating (`post - prior`). |

**Derived mechanism metric used in this repo:**
- `belief_change = post_onset_mean_doy - prior_onset_mean_doy`

**Why these are necessary:**  
They allow your mechanism deliverable to answer:
- Did the forecast change beliefs?
- Do belief changes relate to investment behavior?

---

### F) Realized climate states / shocks (environment)
| Variable | Type | Meaning | Why needed |
|---|---|---|---|
| `true_onset_doy` | float | The realized monsoon onset (synthetic ground truth) | Useful for extensions (forecast accuracy, state-dependent impacts). Not required for MVP but helps realism. |
| `flood_village` | 0/1 | Village-level flood shock | Helps explore why profits might not move even if investments move (unforecasted shocks). Useful for robustness. |

**Why these are helpful:**  
Real agriculture outcomes depend on realized weather, not just beliefs. Shocks can break the investment→profit link, which is important for interpretation and risk evaluation.

---

### G) Up-front investment outcomes (primary behavioral endpoints)
These are the main outcomes for “Up-front investment MVP.”

| Variable | Type | Meaning | Why needed |
|---|---|---|---|
| `seed_spend_inr` | float | Spending on seeds | Component of investment; helps diagnose which input changes. |
| `fert_spend_inr` | float | Spending on fertilizer | Same. |
| `labor_spend_inr` | float | Spending on labor | Same. |
| `other_spend_inr` | float | Other input spending | Captures remaining up-front costs. |
| `total_upfront_spend_inr` | float | Total investment (sum of components) | **Primary MVP outcome** for mechanism, risk evaluation, and policy targeting. |

**Why these are necessary:**  
Forecasts are an **ex ante** tool. If they work, the first place you should see change is in up-front decisions (input spending, planting plans), not necessarily profits immediately.

---

### H) Welfare outcome (noisier, but policy-relevant)
| Variable | Type | Meaning | Why needed |
|---|---|---|---|
| `profit_inr` | float | Profit outcome (synthetic) | Used for risk evaluation as a welfare endpoint; profits tend to be noisy and shock-driven. |

**Why profit is included:**  
Policy makers care about welfare, but profits can be noisy. Including profit lets you:
- compare “behavioral effects” vs “welfare effects”
- run downside-risk analysis on a welfare endpoint
- motivate why insurance may matter for downside protection even when profits are hard to move in one season

---

## 4) Why these data points are necessary for your 3 deliverables

### Deliverable 1: Budget targeting policy (Forecast vs Insurance vs Nothing)
Needs:
- `arm` (to learn patterns from experimental arms)
- baseline covariates: `land_ha`, `irrigation`, `assets_z`, `risk_aversion_z`, `past_shock`, priors
- outcome: `total_upfront_spend_inr`
- policy settings: costs/budget share (in `config.py`)

Why:
- At rollout time, you only have **baseline info**, so the model must be trained to make decisions from baseline features.

---

### Deliverable 2: Mechanism scorecard (belief updating → investment)
Needs:
- `prior_onset_mean_doy`, `post_onset_mean_doy` → compute belief change
- `arm` → compare belief updating across arms
- `total_upfront_spend_inr` → connect belief updating to investment
- `prior_tercile` derived from `prior_onset_mean_doy` (to show heterogeneity)

Why:
- Mechanism is about explaining **how** forecasts work: information changes beliefs, which changes behavior.

---

### Deliverable 3: Risk-focused evaluation (downside risk)
Needs:
- `total_upfront_spend_inr` and/or `profit_inr`
- `arm` to compare groups
- downside thresholds (bottom 20%) computed during processing

Why:
- Climate policy is often justified by **risk reduction**, not just higher averages.  
  Measuring bottom-tail outcomes gives a clearer “protect against disaster” picture.

---

## 5) Value ranges / interpretation notes
- **INR variables** (`*_spend_inr`, `profit_inr`) are simulated currency units.
- **DOY (day-of-year)** variables represent timing on a yearly calendar.
- **Standardized (z-score)** variables (`assets_z`, `risk_aversion_z`) have mean ~0 and spread ~1, to represent relative differences.

---

## 6) Known simplifications (synthetic-data disclaimer)
This dataset is a scaffold. It does not capture all real-world issues like:
- missingness, heaping/rounding, measurement error, enumerator effects
- spillovers between households within village
- complex pricing mechanisms and compliance patterns

The goal is to build a workflow that can be applied to real research data by mapping columns and rerunning the same scripts.

---

## 7) Recommended “baseline-only” feature set (used in targeting)
The baseline predictors used in this repo are:
- `land_ha`
- `irrigation`
- `assets_z`
- `risk_aversion_z`
- `past_shock`
- `prior_onset_mean_doy`
- `prior_onset_sd`

Why these are good:
- They are pre-treatment
- They are economically meaningful
- They plausibly predict who benefits more from information (forecast) vs protection (insurance)

---

## 8) Contact / repo notes
If you adapt this scaffold to real data, keep the same column naming convention (or add a mapping layer) so all scripts run without edits.