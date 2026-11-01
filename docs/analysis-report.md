# CommerceLens analysis report

**Source: Olist local CSV files.**

Descriptive findings from locally supplied Olist files; no causal or profit claims.

Purchase window: **2016-09-04 to 2018-10-17**. Ingested: 2026-11-01T10:16:58.618649+00:00. All categories and customer states.


| KPI | Result |
|---|---:|
| Delivered merchandise sales (BRL, excluding freight) | 13,221,498.11 |
| Eligible delivered orders | 96,478 |
| Total placed orders | 99,441 |
| Delivered-order AOV (BRL) | 137.04 |
| Repeat customers / purchasing customers | 2,801 / 93,358 (3.0%) |
| Canceled / placed orders | 625 / 99,441 (0.6%) |
| Late / valid-date delivered orders | 6,534 / 96,470 (6.8%) |


## Findings


### 1. Observation

Health Beauty contributes 9.3% of selected delivered merchandise sales.

**Possible interpretation:** This is the largest category contribution in the selected scope.

**Proposed investigation:** Compare category mix and stock availability over time.

**Limitation:** Item-level sales exclude freight; category order counts overlap. No profitability data is available.


### 2. Observation

Late orders average 2.27/5 (6,381 reviews); on-time orders average 4.29/5 (89,443 reviews).

**Possible interpretation:** Delivery experience may be associated with review scores.

**Proposed investigation:** Compare this pattern within states and categories before prioritizing investigation.

**Limitation:** This is an association, not causation; non-response and product mix may influence scores.


### 3. Observation

2,801 of 93,358 purchasing customers placed at least two delivered orders (3.0%).

**Possible interpretation:** Repeat purchasing contributes to the selected customer mix.

**Proposed investigation:** Inspect complete monthly cohorts for differences in repeat activity.

**Limitation:** Repeat rate is measured within the active filters and is sensitive to the length of the date window.


## Regional context


| Customer state | Sales (BRL) | Late rate | Valid-date orders |
|---|---:|---:|---:|
| SP | 5,067,633.16 | 4.5% | 40,494 |
| RJ | 1,759,651.13 | 12.1% | 12,350 |
| MG | 1,552,481.83 | 4.6% | 11,354 |
| RS | 728,897.47 | 6.1% | 5,344 |
| PR | 666,063.51 | 4.0% | 4,923 |
| SC | 507,012.13 | 8.2% | 3,546 |
| BA | 493,584.14 | 12.2% | 3,256 |
| DF | 296,498.41 | 5.7% | 2,080 |
| GO | 282,836.70 | 6.5% | 1,957 |
| ES | 268,643.45 | 10.7% | 1,995 |
| PE | 251,889.49 | 9.6% | 1,593 |
| CE | 219,757.38 | 13.8% | 1,279 |
| PA | 174,470.59 | 11.2% | 946 |
| MT | 152,191.62 | 6.0% | 886 |
| MA | 117,009.38 | 17.4% | 717 |
| MS | 115,429.97 | 9.7% | 701 |
| PB | 112,586.82 | 10.4% | 517 |
| PI | 84,721.00 | 13.9% | 476 |
| RN | 82,105.66 | 9.3% | 474 |
| AL | 78,855.72 | 21.4% | 397 |
| SE | 56,574.19 | 15.2% | 335 |
| TO | 48,402.51 | 9.9% | 274 |
| RO | 45,682.76 | 2.9% | 243 |
| AM | 22,155.84 | 2.8% | 145 |
| AC | 15,930.97 | 3.8% | 80 |
| AP | 13,374.81 | 3.0% | 67 |
| RR | 7,057.47 | 12.2% | 41 |


## Scope and limitations


All patterns in demo mode are consequences of the generator. The generator intentionally varies delay probabilities and review scores; it cannot support real operational recommendations.

First purchase means first observed delivered purchase. Cohort month zero is the acquisition baseline; future or incomplete months are unavailable. Repeat rate measures repeat orders within the selected period.

Review non-response, product mix and geography can confound associations. Delivery missingness changes the denominator. Current order statuses may bias recent purchase periods.

Sales exclude freight and entire orders with incomplete prices. No costs, profit, margins, returns, discounts or channels are inferred.

Rebuild this report after changing the source: `python -m scripts.report`. Dashboard and exports always use the current database; this document is a dated snapshot.