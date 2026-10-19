"""Generate original synthetic data; never downloads or uses customer information."""

import csv
import random
from datetime import date, timedelta
from pathlib import Path


def write_csv(path, rows):
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def main():
    destination = Path(__file__).resolve().parents[1] / "data" / "raw"
    destination.mkdir(parents=True, exist_ok=True)
    rng = random.Random(2026)
    places = [("Dhaka", "Dhaka"), ("Chattogram", "Chattogram"),
              ("Sylhet", "Sylhet"), ("Khulna", "Khulna")]
    customers = []
    for i in range(1, 81):
        city, region = places[(i - 1) % len(places)]
        customers.append({"customer_id": f"C{i:03}", "city": city, "region": region,
                          "segment": rng.choice(["Consumer", "Consumer", "Small Business"])})
    catalog = [
        ("Headphones", "Electronics", "1999.50", "1200.00"),
        ("Wireless Mouse", "Electronics", "750.00", "420.00"),
        ("Keyboard", "Electronics", "1250.75", "800.00"),
        ("Monitor", "Electronics", "17500.00", "14000.00"),
        ("Notebook Set", "Office", "200.00", "110.00"),
        ("Desk Lamp", "Office", "1450.00", "950.00"),
        ("Water Bottle", "Home", "550.00", "300.00"),
        ("Storage Box", "Home", "450.00", "260.00"),
        ("Backpack", "Accessories", "1490.00", "900.00"),
        ("Phone Stand", "Accessories", "350.00", "180.00"),
        ("Python Workbook", "Books", "850.00", "550.00"),
        ("SQL Practice Book", "Books", "700.00", "440.00"),
    ]
    products = [{"product_id": f"P{i:03}", "product_name": name, "category": category,
                 "list_price_bdt": price, "unit_cost_bdt": cost}
                for i, (name, category, price, cost) in enumerate(catalog, 1)]
    sales = []
    for i in range(1, 481):
        product = rng.choice(products)
        amount = product["list_price_bdt"]
        if i % 37 == 0:
            amount = f"BDT {float(amount):,.2f}"
        status = rng.choices(["completed", "returned", "cancelled"], [86, 8, 6])[0]
        sales.append({
            "order_id": f"O{i:04}",
            "order_date": (date(2026, 1, 1) + timedelta(days=rng.randrange(180))).isoformat(),
            "customer_id": f"C{rng.randrange(1, 81):03}",
            "product_id": product["product_id"],
            "quantity": str(rng.randrange(1, 5)),
            "unit_price_bdt": amount,
            "discount_pct": str(rng.choice([0, 0, 5, 10, 15])),
            "status": f" {status.upper()} " if i % 41 == 0 else status,
        })
    duplicates = [dict(row) for row in sales[:12]]
    defects = [("customer_id", ""), ("customer_id", "C999"), ("product_id", "P999"),
               ("order_date", "2026-02-30"), ("quantity", "0"),
               ("discount_pct", "110"), ("unit_price_bdt", "unknown"),
               ("status", "processing")]
    invalid = []
    for i, (column, value) in enumerate(defects, 1):
        row = dict(sales[20 + i])
        row.update(order_id=f"BAD{i:03}")
        row[column] = value
        invalid.append(row)
    rows = sales + duplicates + invalid
    rng.shuffle(rows)
    write_csv(destination / "customers.csv", customers)
    write_csv(destination / "products.csv", products)
    write_csv(destination / "sales_raw.csv", rows)
    print(f"Wrote {len(rows)} raw rows, {len(customers)} customers, {len(products)} products.")


if __name__ == "__main__":
    main()
