"""Clean orders, reconcile Pandas with SQL, and generate reproducible reports."""

import json
import re
import sqlite3
from datetime import date
from decimal import Decimal, InvalidOperation
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
SALES_COLUMNS = ["order_id", "order_date", "customer_id", "product_id", "quantity",
                 "unit_price_bdt", "discount_pct", "status"]
DB_COLUMNS = ["order_id", "order_date", "customer_id", "product_id", "quantity",
              "unit_price_paisa", "discount_pct", "status"]
STATUSES = {"completed", "returned", "cancelled"}


def require_columns(frame, columns, label):
    missing = sorted(set(columns) - set(frame.columns))
    if missing:
        raise ValueError(f"{label} is missing columns: {', '.join(missing)}")


def parse_money(value):
    """Parse BDT text to exact paisa; reject negative amounts and fractions of a paisa."""
    text = str(value).strip().replace("BDT", "").replace("৳", "").replace(",", "").strip()
    try:
        number = Decimal(text)
        if not number.is_finite() or number < 0 or number * 100 != (number * 100).to_integral_value():
            return None
        if number > Decimal("1000000000"):
            return None
        return int(number * 100)
    except (InvalidOperation, ValueError):
        return None


def parse_integer(value):
    try:
        number = Decimal(str(value).strip())
        if number.is_finite() and number == number.to_integral_value() and abs(number) <= 1_000_000:
            return int(number)
    except (InvalidOperation, ValueError):
        pass
    return None


def normalize_references(customers, products):
    customer_columns = ["customer_id", "city", "region", "segment"]
    product_columns = ["product_id", "product_name", "category", "unit_cost_bdt"]
    require_columns(customers, customer_columns, "customers.csv")
    require_columns(products, product_columns, "products.csv")
    customers = customers[customer_columns].copy()
    products = products[product_columns].copy()
    for frame in (customers, products):
        for column in frame:
            frame[column] = frame[column].fillna("").astype(str).str.strip()
        if frame.empty or frame.eq("").any().any():
            raise ValueError("Reference tables must be nonempty and have no blank fields.")
    for frame, key in ((customers, "customer_id"), (products, "product_id")):
        frame[key] = frame[key].str.upper()
        if frame[key].duplicated().any():
            raise ValueError(f"Duplicate {key} in reference table; a join would double-count sales.")
    products["unit_cost_paisa"] = products["unit_cost_bdt"].map(parse_money)
    if products["unit_cost_paisa"].isna().any():
        raise ValueError("Product unit costs must be valid nonnegative BDT amounts.")
    products["unit_cost_paisa"] = products["unit_cost_paisa"].astype("int64")
    return customers, products.drop(columns="unit_cost_bdt")


def clean_orders(raw, customers, products):
    """One row per order; keep the first valid ID and audit every rejected source row."""
    require_columns(raw, SALES_COLUMNS, "sales_raw.csv")
    customer_ids = set(customers["customer_id"])
    product_ids = set(products["product_id"])
    cleaned, rejected, seen = [], [], set()
    for index, original in enumerate(raw[SALES_COLUMNS].fillna("").to_dict("records"), 2):
        row = {key: str(value).strip() for key, value in original.items()}
        row["order_id"] = row["order_id"].upper()
        row["customer_id"] = row["customer_id"].upper()
        row["product_id"] = row["product_id"].upper()
        row["status"] = row["status"].lower()
        reasons = []
        if not row["order_id"]:
            reasons.append("missing_order_id")
        try:
            if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", row["order_date"]):
                raise ValueError("Expected YYYY-MM-DD")
            row["order_date"] = date.fromisoformat(row["order_date"]).isoformat()
        except ValueError:
            reasons.append("invalid_date")
        if row["customer_id"] not in customer_ids:
            reasons.append("unknown_customer")
        if row["product_id"] not in product_ids:
            reasons.append("unknown_product")
        quantity = parse_integer(row["quantity"])
        discount = parse_integer(row["discount_pct"])
        price = parse_money(row["unit_price_bdt"])
        if quantity is None or quantity <= 0:
            reasons.append("invalid_quantity")
        if discount is None or not 0 <= discount <= 100:
            reasons.append("invalid_discount")
        if price is None or price <= 0:
            reasons.append("invalid_price")
        if row["status"] not in STATUSES:
            reasons.append("invalid_status")
        if not reasons and row["order_id"] in seen:
            reasons.append("duplicate_order_id")
        if reasons:
            rejected.append({"source_row": index, **original, "reason": "|".join(reasons)})
            continue
        seen.add(row["order_id"])
        cleaned.append({"order_id": row["order_id"], "order_date": row["order_date"],
                        "customer_id": row["customer_id"], "product_id": row["product_id"],
                        "quantity": quantity, "unit_price_paisa": price,
                        "discount_pct": discount, "status": row["status"]})
    return (pd.DataFrame(cleaned, columns=DB_COLUMNS),
            pd.DataFrame(rejected, columns=["source_row", *SALES_COLUMNS, "reason"]))


def enrich_orders(clean, customers, products):
    data = clean.merge(customers, on="customer_id", validate="many_to_one")
    data = data.merge(products, on="product_id", validate="many_to_one")
    completed = data["status"].eq("completed")
    data["gross_sales_paisa"] = (data["quantity"] * data["unit_price_paisa"]).where(completed, 0)
    data["net_sales_paisa"] = (
        (data["quantity"] * data["unit_price_paisa"] * (100 - data["discount_pct"]) + 50) // 100
    ).where(completed, 0)
    data["cost_paisa"] = (data["quantity"] * data["unit_cost_paisa"]).where(completed, 0)
    data["gross_profit_paisa"] = data["net_sales_paisa"] - data["cost_paisa"]
    data["discount_paisa"] = data["gross_sales_paisa"] - data["net_sales_paisa"]
    data["month"] = data["order_date"].str[:7]
    return data.sort_values(["order_date", "order_id"]).reset_index(drop=True)


def summarize(data, raw_count, rejected_count):
    completed = data["status"].eq("completed")
    returned = data["status"].eq("returned")
    sales = int(data["net_sales_paisa"].sum())
    profit = int(data["gross_profit_paisa"].sum())
    count = int(completed.sum())
    return {
        "dataset": "Original synthetic retail sample; not a real business",
        "currency": "BDT",
        "raw_rows": raw_count, "clean_rows": len(data), "rejected_rows": rejected_count,
        "completed_orders": count, "returned_orders": int(returned.sum()),
        "cancelled_orders": int(data["status"].eq("cancelled").sum()),
        "units_sold": int(data.loc[completed, "quantity"].sum()),
        "net_sales_bdt": sales / 100,
        "gross_profit_bdt": profit / 100,
        "gross_margin_pct": round(profit / sales * 100, 2) if sales else None,
        "average_order_value_bdt": round(sales / count / 100, 2) if count else 0,
        "return_rate_pct": round(int(returned.sum()) / (count + int(returned.sum())) * 100, 2)
                           if count + int(returned.sum()) else 0,
    }


def aggregate(data, key):
    return (data.loc[data["status"].eq("completed")].groupby(key, as_index=False)
            .agg(orders=("order_id", "count"), net_sales_paisa=("net_sales_paisa", "sum"),
                 gross_profit_paisa=("gross_profit_paisa", "sum"))
            .sort_values(key).reset_index(drop=True))


def query_definitions():
    pieces = re.split(r"^-- name: ([a-z_]+)\s*$", (ROOT / "sql" / "analysis.sql").read_text(),
                      flags=re.MULTILINE)
    return dict(zip(pieces[1::2], pieces[2::2]))


def build_database(connection, clean, customers, products):
    connection.executescript((ROOT / "sql" / "schema.sql").read_text())
    customers.to_sql("customers", connection, if_exists="append", index=False)
    products.to_sql("products", connection, if_exists="append", index=False)
    clean[DB_COLUMNS].to_sql("sales", connection, if_exists="append", index=False)
    connection.commit()
    if connection.execute("PRAGMA foreign_key_check").fetchall():
        raise ValueError("Database contains invalid reference relationships.")
    return {name: pd.read_sql_query(query, connection) for name, query in query_definitions().items()}


def reconcile_sql(data, queries):
    """Stop report generation if independent SQL and Pandas calculations disagree."""
    kpis = queries["kpis"].iloc[0]
    expected = [len(data), int(data["status"].eq("completed").sum()),
                int(data["net_sales_paisa"].sum()), int(data["gross_profit_paisa"].sum())]
    if [int(kpis[name]) for name in ("clean_orders", "completed_orders", "net_sales_paisa",
                                   "gross_profit_paisa")] != expected:
        raise ValueError("SQL and Pandas KPI totals disagree.")
    for key, query in (("month", "monthly_sales"), ("region", "regional_sales"),
                       ("category", "category_sales")):
        try:
            pd.testing.assert_frame_equal(aggregate(data, key), queries[query], check_dtype=False)
        except AssertionError as exc:
            raise ValueError(f"SQL and Pandas disagree for {key}.") from exc


def export_money(data):
    """Expose readable BDT columns for Excel, CSV, Power BI, and Tableau."""
    result = data.copy()
    for column in list(result.columns):
        if column.endswith("_paisa"):
            result[column.replace("_paisa", "_bdt")] = result.pop(column) / 100
    return result


def run_analysis(source, destination):
    from retail_insights.reporting import write_reports

    source, destination = Path(source).resolve(), Path(destination).resolve()
    if source == destination or destination.is_relative_to(source) or source.is_relative_to(destination):
        raise ValueError("Input and output directories must not overlap.")
    customers = pd.read_csv(source / "customers.csv", dtype=str, keep_default_na=False)
    products = pd.read_csv(source / "products.csv", dtype=str, keep_default_na=False)
    raw = pd.read_csv(source / "sales_raw.csv", dtype=str, keep_default_na=False)
    customers, products = normalize_references(customers, products)
    clean, rejected = clean_orders(raw, customers, products)
    if clean.empty:
        raise ValueError("No valid orders remain. Review raw fields and customer/product IDs.")
    data = enrich_orders(clean, customers, products)
    summary = summarize(data, len(raw), len(rejected))
    with sqlite3.connect(":memory:") as connection:
        queries = build_database(connection, clean, customers, products)
        reconcile_sql(data, queries)
        destination.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(destination / "analysis.sqlite") as saved:
            connection.backup(saved)
    rejected.to_csv(destination / "rejected_rows.csv", index=False)
    export_money(data).to_csv(destination / "clean_sales.csv", index=False, float_format="%.2f")
    for name, table in queries.items():
        folder = destination / "sql_results"
        folder.mkdir(exist_ok=True)
        table.to_csv(folder / f"{name}.csv", index=False)
    (destination / "kpis.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    write_reports(destination, data, customers, products, rejected, summary, queries)
    return summary
