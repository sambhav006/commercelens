# Interview walkthrough

## A five-minute demonstration

1. **Frame the business question (30 seconds).** “I built CommerceLens to explain sales mix, repeat purchasing and fulfillment using auditable metrics. The visible dataset is synthetic; I do not present these findings as a real business result.” Open Executive Overview and point to the source badge and purchase-date range.
2. **Explain ingestion (45 seconds).** Show `pipeline.py` and Data Quality. Headers are inspected before transformations; raw rows are retained. Demonstrate duplicates, missing dates and the difference between removed rows and missing values. Invalid prices exclude the entire order from both sales and AOV. Explain the cost: less coverage, but aligned numerator and denominator.
3. **Show SQL grain (60 seconds).** Open `sql/model.sql`. One order can have many items, payments and reviews. Joining all detail directly creates a Cartesian multiplication. Items/payments are aggregated separately, reviews selected with `ROW_NUMBER`, and facts joined at order grain. Show the fixture test where two items and two payments still yield exactly BRL 150 in sales.
4. **Define KPIs (45 seconds).** Sales means delivered item value excluding freight; AOV uses identical eligible orders. Placed orders include every status; cancellation uses placed orders as denominator. Customer analysis uses `customer_unique_id`. Late rate excludes missing dates and compares calendar days, so 23:00 on the estimated date is on time.
5. **Demonstrate filter semantics (45 seconds).** Select a category and state, apply, then export. Category sales include matching items only; order metrics select containing orders. Thus category order counts overlap and category AOV is not whole-basket AOV. Navigate to Customers: repeat rate follows the filters, while the cohort note explicitly says category/state do not apply. First-ever observed purchase cannot move because of a category selection.
6. **Interpret carefully (45 seconds).** Open Delivery & Reviews. Compare scores with sample sizes; call the pattern an association. Propose comparing within states/categories, not claiming delivery changes caused rating differences. Show the report for exact generated numbers. No commercial uplift is asserted.
7. **Close with validation (30 seconds).** Show the tests and screenshots. Discuss NULL versus zero, future cohort cells, atomic rebuilding, API error recovery, and why current status can bias recent orders.

## Questions to prepare for

- **Why SQLite?** A portable local database makes SQL readable and reproducible without server administration. For larger workloads, keep the dimensional grain and move storage/query execution to an analytical warehouse.
- **Why not use payments as revenue?** Payment values include other charges and are not platform income. Only item prices support this merchandise-sales metric. No costs or commission rates are provided.
- **How is repeat defined?** Two or more delivered orders within the active scope, divided by customers with any delivered purchase in that scope. It is not lifetime retention. Cohorts use month-since-first-purchase separately.
- **Why ignore category/state in cohorts?** A transparent global-cohort definition prevents a category filter from redefining acquisition. A future category-retention feature would need separate cohort-membership and repeat-activity filters, not a naive WHERE clause.
- **Why keep unmatched dimensions?** An order is still placed even if customer geography or product category is missing. Left joins preserve totals; Unknown makes coverage visible. Missing customer identities cannot safely be grouped into a fake customer.
- **Why no comparison at the default range?** The preceding equally long window has no full coverage. Showing a percentage change would imply a known baseline. Select a later date window to obtain a valid comparison.
- **What would you improve?** Validate against a user-supplied real Olist extract, add provenance hashes and chunked ingestion for large data, improve cohort confidence estimates, and investigate review selection bias. A production service would also need authentication, deployment configuration and concurrency planning.

## Three factual resume bullets

- Built a five-page e-commerce analytics dashboard using React, TypeScript, Tailwind CSS, Recharts and FastAPI, with shared filters, CSV exports and documented KPI definitions.
- Implemented a reproducible pandas-to-SQLite pipeline with raw-data preservation, schema validation, deduplication, relationship checks and SQL analysis of sales, customer cohorts and delivery performance.
- Created automated analytical tests for join inflation, customer identity, missing-date denominators, cohort observation windows and export reconciliation, and verified the interface with Playwright browser tests.

Use these as implementation claims only. Do not attach invented percentage improvements, revenue impact or claims of professional work for Olist.
