# Excel, Power BI, and Tableau exercises

First run `python analyze.py` with the project dependencies installed, or download the report artifact from a successful GitHub Actions run. All values are synthetic; use the definitions in DATA.md.

## Excel

Open `reports/sales_analysis.xlsx`.

1. Review Read_Me and KPIs.
2. In Clean_Sales, select a cell inside the SalesData table.
3. Insert → PivotTable → New Worksheet.
4. Put `region` in Rows, `category` in Columns, and `net_sales_bdt` in Values, summarized by Sum.
5. Add `status` as a filter and select completed. Net sales already zeroes excluded statuses, but this makes the order scope clear.
6. Add a PivotChart, then apply conditional formatting to the pivot values.
7. Build a second pivot with `month` and `gross_profit_bdt`.

The supplied workbook contains ordinary summary tables and a chart, not a prebuilt native PivotTable. Formula_Practice demonstrates SUM, COUNTIF, SUMIFS, and IFERROR. Excel recalculates formulas when opened; Python writes formulas without evaluating them.

For XLOOKUP practice in a current Excel version, place a product ID in a spare cell A10 and use:

```excel
=XLOOKUP(A10,TableProducts[product_id],TableProducts[product_name],"Not found")
```

## Power BI Desktop

Power BI Desktop is a separate Windows application; this repository does not contain a `.pbix` file.

### Beginner option: one flat table

Import `reports/clean_sales.csv`, name the table `Sales`, and set:

- `order_date`: Date.
- `quantity`: Whole number.
- Columns ending in `_bdt`: Fixed decimal number.
- `month`, IDs, status, region, category, product_name: Text.

Use Power Query to confirm types and inspect empty values. The Python pipeline has already cleaned this file; keep the raw CSVs for cleaning practice in a separate query.

Create these measures:

```dax
Net Sales = SUM(Sales[net_sales_bdt])

Gross Profit = SUM(Sales[gross_profit_bdt])

Completed Orders =
    CALCULATE(COUNTROWS(Sales), Sales[status] = "completed")

Average Order Value = DIVIDE([Net Sales], [Completed Orders], 0)

Gross Margin = DIVIDE([Gross Profit], [Net Sales])

Returned Orders =
    CALCULATE(COUNTROWS(Sales), Sales[status] = "returned")

Return Rate =
    DIVIDE([Returned Orders], [Completed Orders] + [Returned Orders], 0)
```

Add each measure separately. Format Gross Margin and Return Rate as percentages; do not multiply them by 100 as well. Format financial measures in BDT with two decimals.

Build cards for sales, profit, completed orders, and margin. Add monthly sales, region sales, category profit, and slicers for region/category/month. Use `kpis.json` as the unfiltered reconciliation reference.

### Relationship practice: star model

Instead of the flat file, import the three files in `reports/bi/`:

- fact_sales: one row per valid order.
- dim_customers: unique customer_id.
- dim_products: unique product_id.

Create one-to-many relationships from each dimension to fact_sales, with single-direction filtering from dimension to fact. Use dimension labels in visuals. Adapt the measures above to table `fact_sales`. Do not append the flat sales file to the fact table, which would duplicate transactions.

## Tableau

Tableau is a separate application; this repository does not contain a native Tableau workbook.

1. Connect to `reports/clean_sales.csv` as a text file.
2. Set order_date to Date and monetary columns to decimal numbers.
3. Use `SUM(net_sales_bdt)` for net sales and `SUM(gross_profit_bdt)` for gross profit.
4. Build monthly sales, sales by region, and category-profit worksheets.
5. Add region, category, and month filters to a dashboard.
6. For average order value, use:

```text
SUM([net_sales_bdt]) / SUM(IIF([status] = "completed", 1, 0))
```

Guard against a zero denominator for filtered selections with no completed orders. Validate the unfiltered dashboard against `kpis.json`. Revenue and cost measures already exclude returned/cancelled orders; all-order counts still include them.

## Portfolio evidence

After building your own dashboard, add screenshots and explain the business question, metric definitions, cleaning decisions, and at least two limitations. Credit this project's synthetic sample and the bootcamp as learning context. Do not describe a generated demo pattern as a real commercial result.
