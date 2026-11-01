# Data dictionary and cleaning decisions

The real dataset is obtained by the user from [Olist on Kaggle](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce). No real files were available during implementation. Generated demo headers were inspected through the same schema validator used for real ingestion. Extra input columns are preserved in raw and cleaned tables but are not interpreted unless documented below.

| Input / cleaned table | Natural key | Required analytical columns |
|---|---|---|
| orders | order_id | customer_id, order_status, order_purchase_timestamp, order_delivered_customer_date, order_estimated_delivery_date |
| items | order_id + order_item_id | product_id, price, freight_value |
| customers | customer_id | customer_unique_id, customer_state |
| products | product_id | product_category_name |
| translations | product_category_name | product_category_name_english |
| payments | order_id + payment_sequential | payment_value |
| reviews | review_id + order_id | review_score, review_answer_timestamp |

`customer_id` is the order-linked customer record, while `customer_unique_id` is the persistent customer identity used for purchasing and cohorts. Each item row represents one purchased item; `order_item_id` is a sequence, not a quantity field. `price` and `freight_value` are BRL amounts. Payment amount is not merchandise sales: it may include freight and multiple installments/tenders. The model retains payment totals as an audit dimension but never adds them to merchandise sales.

`customer_state` is the customer's state, not seller geography. Product category uses English translation when available, otherwise the original category label, otherwise `Unknown`.

## Storage layers

- `raw_*`: all original columns and rows loaded as strings, before trimming, type conversion or deduplication. Pandas default missing-value tokens are recognized at read time.
- Clean tables: typed analytical fields, normalized strings, natural-key deduplication, excluded orphan child facts. Unique indexes enforce key uniqueness. Relationships are explicitly checked and reported; dangling dimensions use left joins rather than dropping orders.
- `item_facts`: one row per cleaned item with translated category.
- `order_facts`: one row per order, separately aggregated item sales/payment totals, latest valid review, calendar dates, late flag and duration.
- `metadata`: JSON report containing actual source headers, source mode, date bounds, timestamp, seed, raw/clean row counts, missing inputs, invalid values, orphans, duplicate keys, removals and analytical exclusions.

## Rules and consequences

1. Inspect actual CSV headers before transformation. Fail on missing files or required columns. Additional columns are allowed. Files with duplicate or missing natural keys are counted; missing keys are excluded.
2. Trim strings and convert empty strings to missing. For normal natural keys, keep the last row in source order. For repeated `(review_id, order_id)`, sort by answer timestamp and keep the last; stable input order breaks ties. Report duplicate-key rows before removal. Items/payment sequences are converted to positive integers, invalid sequences removed, and key uniqueness checked again after conversion.
3. Parse dates with pandas; invalid timestamps become missing and are counted. Orders without a purchase date are excluded. Actual/estimated days before purchase are invalid and become missing. Naive source dates are treated as source-local dates; no invented timezone is applied.
4. Convert prices, freight and payments to finite, nonnegative numbers. Invalid or missing prices stay NULL; an entire order is ineligible for sales and AOV if any item price is missing or there are no items. This prevents partial item sums silently understating AOV. Other order/customer metrics still include the order. Freight never contributes to sales.
5. Normalize order statuses to lowercase and fill missing status as `unknown`. All statuses count as placed; only exact `delivered` counts toward sales; only exact `canceled` counts in cancellation numerator. Unrecognized statuses remain in the placed denominator. Customer states are uppercase; missing states become `Unknown`.
6. Report orphans from orders to customers, items to products, products to translations, and all child facts to orders. Orphan child facts cannot be attributed and are removed. Missing customer/product/translation dimensions are retained through left joins; missing identities are excluded only from customer-level metrics. Orphan counts include missing dimension links.
7. Reviews accept integer scores 1–5. From distinct review records, choose the latest valid score per order with SQL `ROW_NUMBER`, ordered by answer timestamp descending then review_id descending. Undated valid reviews rank after dated reviews. The latest valid score may be older than a newer invalid score. No averaging of multiple reviews per order.
8. Late delivery compares calendar days. Both actual and estimated dates must be valid. Delivery duration needs only a valid actual date and purchase date. Therefore the duration sample can exceed the late-rate sample.
9. Customer first purchase comes from full delivered-order history. Cohorts ignore category/state and only admit full acquisition months inside both selected and observed ranges. Fully observed months with no activity equal zero; incomplete and future months are NULL. Month zero is the acquisition baseline.
10. Idempotence: build a fresh sibling database, validate unique keys, then replace the prior file after closing it. No append. A validation failure preserves the existing database. Ingestion is intended to run serially with the local API stopped on Windows.

Missing-value counts describe input columns; invalid counts describe conversion failures. Removed-row totals include deduplication and exclusion. Reason counts can overlap and should not be summed as independent populations. No customer identities or review text are exposed by the dashboard.

## Synthetic fixture

Seed 42 creates 4,200 orders across 2023–2024, eight named product categories plus missing categories, eight states, rising volume, repeat identities with different customer IDs, multiple items/payments/reviews, canceled/shipped/unavailable orders, missing delivery dates and exact duplicate rows. State-specific delay probabilities and conditional review distributions are intentionally constructed. Their associations demonstrate the analytical workflow, not market behavior. Seven generated CSVs mirror required Olist fields rather than every optional Olist column.
