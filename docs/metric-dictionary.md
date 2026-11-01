# Metric dictionary

Generated from `docs/metrics.json`, also served by `/api/methodology`. NULL values display as Unavailable. Counts can validly be zero.

## Delivered merchandise sales

- **Formula:** SUM(item price) on delivered orders with at least one item and no missing/invalid prices. Category selection sums only matching items.

- **Statuses:** delivered

- **Date:** Order purchase calendar date, inclusive date range

- **Grain:** Item contribution, aggregated once per order

- **Exclusions:** Freight; non-delivered orders; entire orders with incomplete item prices. Not platform revenue or profit. Unavailable when no eligible orders.

## Delivered-order average order value

- **Formula:** Delivered merchandise sales / count of the same eligible delivered orders. With a category filter this is matching-category spend per containing order.

- **Statuses:** delivered

- **Date:** Order purchase calendar date

- **Grain:** One order

- **Exclusions:** Same exclusions as sales. NULL for zero eligible orders. Category order counts overlap.

## Placed orders

- **Formula:** COUNT of distinct order_id, including all statuses

- **Statuses:** All, including canceled, unavailable and unknown

- **Date:** Order purchase calendar date

- **Grain:** One order

- **Exclusions:** Missing order keys or invalid purchase dates; duplicate keys resolved before counting. Category selects orders containing matching items.

## Cancellation rate

- **Formula:** Canceled orders / all placed orders

- **Statuses:** Numerator canceled; denominator all statuses

- **Date:** Order purchase calendar date

- **Grain:** One order

- **Exclusions:** Unavailable is not canceled. NULL for zero placed orders.

## Unique purchasing customers

- **Formula:** COUNT(DISTINCT customer_unique_id) among delivered orders

- **Statuses:** delivered

- **Date:** Order purchase calendar date within selected period

- **Grain:** Customer identity, not customer_id

- **Exclusions:** Missing customer identities. Missing-price orders still count as purchases. Category and state select matching orders.

## Repeat customer rate

- **Formula:** Customers with at least two delivered orders / customers with at least one delivered order WITHIN the active date/category/state scope

- **Statuses:** delivered

- **Date:** Order purchase calendar date within selected period

- **Grain:** customer_unique_id

- **Exclusions:** Missing identities. Not lifetime repeat rate. NULL when no purchasing customers.

## Late delivery rate

- **Formula:** Delivered orders with actual delivery DAY > estimated delivery DAY / delivered orders with both valid dates

- **Statuses:** delivered

- **Date:** Filter by purchase date; compare actual and estimated dates at calendar-day granularity

- **Grain:** One order

- **Exclusions:** Missing dates and dates before purchase; no timezone conversion of source local timestamps. NULL when denominator is zero.

## Average delivery duration

- **Formula:** AVG(actual delivery calendar date minus purchase calendar date)

- **Statuses:** delivered

- **Date:** Purchase date filter

- **Grain:** One order

- **Exclusions:** Missing actual date or actual date before purchase. Estimated date is not required. Show duration sample separately from late sample.

## Review score by delivery outcome

- **Formula:** AVG(latest valid review_score per order), grouped as Late, On time or Unknown dates

- **Statuses:** delivered

- **Date:** Purchase date filter; latest review ordered by answer timestamp DESC then review_id DESC

- **Grain:** One reviewed order

- **Exclusions:** Scores outside integer 1â€“5; missing scores. Valid scores without answer dates rank after dated scores. Missing delivery dates form a separate group. Association, not causation.

## Monthly cohort retention

- **Formula:** Distinct cohort customers purchasing in month M / cohort size; M0 is acquisition baseline, M1+ is repeat activity

- **Statuses:** delivered

- **Date:** First observed delivered purchase month from all history. Date filters select fully contained acquisition months and observation cutoff.

- **Grain:** customer_unique_id Ã— cohort month Ã— month offset

- **Exclusions:** Category and state filters explicitly do not apply. Missing identities excluded. Incomplete acquisition months excluded. Cells after last complete observed month are NULL, never zero. Observed months without purchases are zero.

## Prior-period percentage change

- **Formula:** Current / previous - 1; previous period ends one day before current start and has the same inclusive day count

- **Statuses:** Inherited from each metric

- **Date:** Immediately preceding equal-length calendar-day window

- **Grain:** Metric and period

- **Exclusions:** NULL for zero/missing baseline or incomplete dataset coverage. Rate changes are relative percentages, not percentage-point differences. Equal day counts do not guarantee seasonally comparable windows.

## Category and regional contribution

- **Formula:** Category: matching item sales / selected sales; region: order sales grouped by customer state

- **Statuses:** delivered with complete prices for sales; all statuses for regional placed orders

- **Date:** Order purchase calendar date

- **Grain:** Category: item, region: order

- **Exclusions:** Category delivered-order counts overlap across categories. Regions use customer location, not seller location. Sample sizes accompany delivery rates.
