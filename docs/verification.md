# Verification results

Verified on Windows with Python 3.11, the project-local `.venv`, SQLite, Vite and headless Chromium. Source mode: **Synthetic demo data**. Dataset purchase range: **2023-01-01 to 2024-12-31**.

## Executed checks

| Check | Result |
|---|---|
| `python -m pytest backend\tests -q` | 8 passed |
| `npm.cmd run build` | Passed TypeScript checks and Vite production build |
| `npx.cmd playwright test` | 2 passed |
| FastAPI and Vite startup | Both running successfully on loopback |
| Browser page/console errors in normal workflow | None captured |
| Responsive overflow | No document overflow at 820 px tablet or 390 px mobile widths |
| Visual inspection | Executive Overview, Customers heatmap and tablet screenshots inspected |
| Reproducible demo and idempotent ingestion | Byte-identical generated CSVs; repeated ingestion yields identical KPI and category results |
| Initial npm dependency audit | 0 reported vulnerabilities at installation time |

The production build splits chart dependencies from the application bundle and completes without bundle-size warnings. Backend tests emit one upstream Starlette/AnyIO deprecation warning; Playwright emits a terminal-color environment warning. Neither affects the test results. No app runtime console errors were observed in the tested workflow.

## Analytical failure cases

Small hand-calculated CSV fixtures verify:

- A two-item order with two payment rows and multiple reviews contributes exactly BRL 150, not a multiplied amount; the newest valid review is retained.
- Different customer IDs sharing one `customer_unique_id` count as one customer with repeat purchases.
- A canceled order with BRL 999 of items contributes nothing to delivered merchandise sales.
- Missing delivery dates are excluded from late-rate denominators; different hours on the same estimated calendar day do not create a false late delivery.
- Category-filtered sales reconcile across category, monthly and regional CSVs; AOV uses the same containing-order eligibility. SQL injection-like category input is rejected.
- First-purchase cohort membership is unchanged by category/state. Unobserved months return NULL while an observed month with no purchases returns zero.
- A zero baseline produces no percentage change. The preceding period is adjacent and equal in inclusive day count.
- Invalid prices exclude the entire order from sales and AOV; orphan facts and duplicate keys are counted. Failed schema validation preserves the previous database.
- Partial real input fails rather than silently switching source mode.

## Browser workflow

Chromium visited all five pages, applied category/state filters, downloaded a filtered CSV, clicked a sortable column, checked the cohort filter exception, reset filters, opened a metric definition, selected a future empty window, recovered from a simulated API failure, and checked tablet/mobile layout width. Screenshots were captured from the live app:

- [Executive Overview](screenshots/overview.png)
- [Customers and retention](screenshots/customers.png)
- [Delivery and reviews](screenshots/delivery.png)
- [Data quality and methodology](screenshots/methodology.png)
- [Tablet overview](screenshots/tablet.png)

## Remaining verification limits

Real Olist CSVs were not supplied and were not downloaded. The adapter validates real headers at ingestion, but end-to-end execution against the real dataset has not been performed. Browser automation used Chromium, not Firefox or WebKit. No formal screen-reader or WCAG conformance audit was performed. The app is a single-user local portfolio, not a production-hosting configuration.

Rerun the documented commands after changes. Browser tests expect the deterministic demo and both local servers to be running; they deliberately select a generated category. The analysis report is a snapshot and must be regenerated after a new ingestion.
