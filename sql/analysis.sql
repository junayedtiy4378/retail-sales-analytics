-- SQLite dialect. Money stays in integer paisa (100 paisa = 1 BDT).
-- Each named query is executed by analyze.py and exported as a CSV.

-- name: kpis
SELECT COUNT(*) AS clean_orders,
       SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) AS completed_orders,
       SUM(net_sales_paisa) AS net_sales_paisa,
       SUM(gross_profit_paisa) AS gross_profit_paisa
FROM sales_analysis;

-- name: monthly_sales
SELECT substr(order_date, 1, 7) AS month,
       COUNT(*) AS orders,
       SUM(net_sales_paisa) AS net_sales_paisa,
       SUM(gross_profit_paisa) AS gross_profit_paisa
FROM sales_analysis
WHERE status = 'completed'
GROUP BY substr(order_date, 1, 7)
ORDER BY month;

-- name: regional_sales
SELECT region, COUNT(*) AS orders,
       SUM(net_sales_paisa) AS net_sales_paisa,
       SUM(gross_profit_paisa) AS gross_profit_paisa
FROM sales_analysis
WHERE status = 'completed'
GROUP BY region
ORDER BY region;

-- name: category_sales
SELECT category, COUNT(*) AS orders,
       SUM(net_sales_paisa) AS net_sales_paisa,
       SUM(gross_profit_paisa) AS gross_profit_paisa
FROM sales_analysis
WHERE status = 'completed'
GROUP BY category
ORDER BY category;

-- name: top_customers_per_region
WITH customer_totals AS (
    SELECT region, customer_id, SUM(net_sales_paisa) AS net_sales_paisa
    FROM sales_analysis
    WHERE status = 'completed'
    GROUP BY region, customer_id
), ranked AS (
    SELECT *, DENSE_RANK() OVER (
        PARTITION BY region ORDER BY net_sales_paisa DESC
    ) AS regional_rank
    FROM customer_totals
)
SELECT * FROM ranked WHERE regional_rank <= 3
ORDER BY region, regional_rank, customer_id;

-- name: repeat_customers
SELECT customer_id, COUNT(*) AS completed_orders,
       SUM(net_sales_paisa) AS net_sales_paisa
FROM sales_analysis
WHERE status = 'completed'
GROUP BY customer_id
HAVING COUNT(*) >= 3
ORDER BY net_sales_paisa DESC, customer_id;

-- name: category_revenue_share
SELECT category, SUM(net_sales_paisa) AS net_sales_paisa,
       ROUND(100.0 * SUM(net_sales_paisa) /
           NULLIF(SUM(SUM(net_sales_paisa)) OVER (), 0), 2) AS sales_share_pct
FROM sales_analysis
WHERE status = 'completed'
GROUP BY category
ORDER BY net_sales_paisa DESC, category;

-- name: above_average_orders
SELECT order_id, product_name, region, net_sales_paisa
FROM sales_analysis
WHERE status = 'completed' AND net_sales_paisa > (
    SELECT AVG(net_sales_paisa) FROM sales_analysis WHERE status = 'completed'
)
ORDER BY net_sales_paisa DESC, order_id;
