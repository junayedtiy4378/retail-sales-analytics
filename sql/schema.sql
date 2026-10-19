PRAGMA foreign_keys = ON;

CREATE TABLE customers (
    customer_id TEXT PRIMARY KEY,
    city TEXT NOT NULL,
    region TEXT NOT NULL,
    segment TEXT NOT NULL
);

CREATE TABLE products (
    product_id TEXT PRIMARY KEY,
    product_name TEXT NOT NULL,
    category TEXT NOT NULL,
    unit_cost_paisa INTEGER NOT NULL CHECK (unit_cost_paisa >= 0)
);

CREATE TABLE sales (
    order_id TEXT PRIMARY KEY,
    order_date TEXT NOT NULL,
    customer_id TEXT NOT NULL REFERENCES customers(customer_id),
    product_id TEXT NOT NULL REFERENCES products(product_id),
    quantity INTEGER NOT NULL CHECK (quantity > 0),
    unit_price_paisa INTEGER NOT NULL CHECK (unit_price_paisa > 0),
    discount_pct INTEGER NOT NULL CHECK (discount_pct BETWEEN 0 AND 100),
    status TEXT NOT NULL CHECK (status IN ('completed', 'returned', 'cancelled'))
);

CREATE VIEW sales_analysis AS
WITH booked AS (
    SELECT sales.*,
           CASE WHEN status = 'completed' THEN
               CAST((quantity * unit_price_paisa * (100 - discount_pct) + 50) / 100 AS INTEGER)
               ELSE 0 END AS net_sales_paisa
    FROM sales
)
SELECT b.*, c.city, c.region, c.segment, p.product_name, p.category,
       CASE WHEN b.status = 'completed' THEN b.quantity * p.unit_cost_paisa
            ELSE 0 END AS cost_paisa,
       b.net_sales_paisa - CASE WHEN b.status = 'completed'
            THEN b.quantity * p.unit_cost_paisa ELSE 0 END AS gross_profit_paisa
FROM booked AS b
INNER JOIN customers AS c ON b.customer_id = c.customer_id
INNER JOIN products AS p ON b.product_id = p.product_id;
