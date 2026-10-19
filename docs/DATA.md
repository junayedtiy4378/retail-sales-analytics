# Dataset and cleaning contract

## Source

`scripts/generate_demo_data.py` creates three CSVs with a fixed random seed. No records were scraped, purchased, or copied from the bootcamp. All customer IDs are artificial. Dates fall in January–June 2026. The sample contains 480 valid orders plus 12 duplicate rows and 8 deliberately invalid rows.

## Files

### customers.csv

| Column | Meaning |
| --- | --- |
| customer_id | Unique case-insensitive customer key |
| city | Synthetic city assignment |
| region | Dhaka, Chattogram, Sylhet, or Khulna |
| segment | Consumer or Small Business |

### products.csv

| Column | Meaning |
| --- | --- |
| product_id | Unique case-insensitive product key |
| product_name | Descriptive label |
| category | Product category |
| list_price_bdt | Demo generator's list price; the analysis uses each order's actual price |
| unit_cost_bdt | Fixed per-unit product cost, before overheads |

### sales_raw.csv

| Column | Meaning |
| --- | --- |
| order_id | Unique order identifier after cleaning |
| order_date | ISO date, YYYY-MM-DD |
| customer_id | Customer table key |
| product_id | Product table key |
| quantity | Positive whole number |
| unit_price_bdt | Actual per-unit price before discount |
| discount_pct | Whole percentage from 0 to 100 |
| status | completed, returned, or cancelled |

## Cleaning

1. Check required columns before analysis.
2. Trim outer whitespace, uppercase IDs, lowercase order statuses.
3. Accept BDT amounts with commas, the `BDT` prefix, or the taka symbol; reject negative amounts and fractions smaller than one paisa. Prices must be positive; product costs may be zero.
4. Validate dates, quantities, discount bounds, statuses, and reference IDs.
5. Keep the first valid occurrence of an order ID and reject later occurrences. A malformed earlier row does not suppress a later valid one.
6. Record every rejected source row, its original values, and all identified reasons. Source row numbers are CSV data-record numbers including the header as row 1, not physical lines in files with embedded multiline values.
7. Join using validated many-to-one reference relationships.

Duplicate reference keys stop the analysis instead of multiplying rows. Blank/malformed reference fields also stop analysis. Missing or unsupported order values are rejected; they are not silently imputed. If no valid orders remain, analysis stops with a clear error.

## Accounting assumptions

Amounts are computed in integer paisa. Net sales are rounded half-up **per order**, not after monthly summation. One unit priced BDT 10.01, quantity 3, with a 15% discount produces BDT 25.53 net sales.

Returned and cancelled orders have zero booked revenue and product cost. This is a simplified status-based dataset, not a refund ledger. Gross profit excludes taxes, shipping, payment fees, inventory changes, and operating costs. Full discounts can produce negative gross profit.

## SQL files

`schema.sql` creates normalized tables with primary-key, foreign-key, and value constraints, plus a joined analysis view. `analysis.sql` contains eight named SELECT queries. Every query is actually executed and exported. Monetary SQL output columns ending in `_paisa` need division by 100 for BDT.

The pipeline reconciles SQL and Pandas overall KPIs and every month, region, and category group before exporting reports. SQLite does not support SQL Server-style stored procedures; those bootcamp topics are outside this small project.
