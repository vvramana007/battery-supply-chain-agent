"""
setup_database.py
-----------------
PHASE 1 of the Duracell Battery Supply Chain AI Agent.

What this script does, in plain words:
  1. Invents realistic (but FAKE) Duracell supply-chain data:
     products, warehouses, inventory, customers, orders, and shipments.
  2. Saves that data as CSV files in the /data folder (so you can open and look at it).
  3. Loads all of it into a single SQLite database file called "duracell.db".

Why we do this:
  A Forward Deployed Engineer always starts from the business's data.
  Before any AI, you need a database the AI can later ask questions against.
  SQLite is a tiny database that lives in one file - perfect for learning.
  (At Duracell the real data lives in Snowflake, but the SQL ideas are identical.)

How to run it:
  python setup_database.py
"""

import csv
import os
import random
import sqlite3
from datetime import date, timedelta

# random.seed(42) makes the "random" data come out the SAME every time you run it.
# That matters so your numbers don't change under you while you're learning.
random.seed(42)

HERE = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(HERE, "data")
DB_PATH = os.path.join(HERE, "duracell.db")
os.makedirs(DATA_DIR, exist_ok=True)


# ---------------------------------------------------------------------------
# 1. PRODUCTS  -  the batteries Duracell sells (SKU = a unique product code)
# ---------------------------------------------------------------------------
products = [
    # sku,        name,                       product_line,  unit_cost, pack_size
    ("DUR-AA-24",  "Coppertop AA",            "Consumer",     0.38, 24),
    ("DUR-AAA-24", "Coppertop AAA",           "Consumer",     0.36, 24),
    ("DUR-C-12",   "Coppertop C",             "Consumer",     0.72, 12),
    ("DUR-D-12",   "Coppertop D",             "Consumer",     0.80, 12),
    ("DUR-9V-8",   "Coppertop 9V",            "Consumer",     1.10, 8),
    ("OPT-AA-16",  "Optimum AA",              "Consumer",     0.55, 16),
    ("OPT-AAA-16", "Optimum AAA",             "Consumer",     0.53, 16),
    ("CR2032-20",  "Lithium Coin CR2032",     "Specialty",    0.22, 20),
    ("CR123-6",    "Lithium 123 Photo",       "Specialty",    1.45, 6),
    ("PRO-AA-24",  "Procell Constant AA",     "Procell",      0.30, 24),
    ("PRO-AAA-24", "Procell Constant AAA",    "Procell",      0.29, 24),
    ("PRO-9V-12",  "Procell 9V",              "Procell",      0.95, 12),
    ("RBL-AA-4",   "Rechargeable AA",         "Rechargeable", 2.10, 4),
    ("RBL-AAA-4",  "Rechargeable AAA",        "Rechargeable", 2.00, 4),
]

# ---------------------------------------------------------------------------
# 2. WAREHOUSES  -  the distribution centers that hold and ship stock
# ---------------------------------------------------------------------------
warehouses = [
    # id,   name,                    city,         state, region
    ("WH-BETHEL", "Bethel DC",        "Bethel",     "CT",  "Northeast"),
    ("WH-ATL",    "Atlanta DC",       "Atlanta",    "GA",  "Southeast"),
    ("WH-CHI",    "Chicago DC",       "Chicago",    "IL",  "Midwest"),
    ("WH-DAL",    "Dallas DC",        "Dallas",     "TX",  "South"),
    ("WH-RENO",   "Reno DC",          "Reno",       "NV",  "West"),
]

# ---------------------------------------------------------------------------
# 3. CUSTOMERS  -  the retailers that buy from Duracell
# ---------------------------------------------------------------------------
customers = [
    # id,     name,          channel,       region
    ("CUST-WMT", "Walmart",      "Mass Retail",  "National"),
    ("CUST-HD",  "Home Depot",   "Home Improve", "National"),
    ("CUST-AMZ", "Amazon",       "E-Commerce",   "National"),
    ("CUST-CST", "Costco",       "Club",         "National"),
    ("CUST-TGT", "Target",       "Mass Retail",  "National"),
    ("CUST-BBY", "Best Buy",     "Electronics",  "National"),
    ("CUST-WGN", "Walgreens",    "Drug",         "National"),
]

carriers = ["FedEx", "UPS", "XPO", "Old Dominion", "JB Hunt"]
order_statuses = ["Delivered", "In Transit", "Processing", "Delayed", "Cancelled"]


def write_csv(filename, header, rows):
    """Save a list of rows to a CSV file in the /data folder."""
    path = os.path.join(DATA_DIR, filename)
    with open(path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(header)
        writer.writerows(rows)
    print(f"  wrote {len(rows):>4} rows -> data/{filename}")


# ---------------------------------------------------------------------------
# 4. INVENTORY  -  how much of each product sits in each warehouse right now
# ---------------------------------------------------------------------------
inventory_rows = []
today = date(2026, 10, 21)
for sku, *_ in products:
    for wh_id, *_ in warehouses:
        qty = random.randint(0, 9000)
        reorder_point = random.choice([1500, 2000, 2500, 3000])
        # A few items are deliberately below reorder point = a "stockout risk"
        last_updated = today - timedelta(days=random.randint(0, 5))
        inventory_rows.append([sku, wh_id, qty, reorder_point, last_updated.isoformat()])

# ---------------------------------------------------------------------------
# 5. ORDERS + ORDER ITEMS  -  what retailers ordered
# ---------------------------------------------------------------------------
order_rows = []
order_item_rows = []
shipment_rows = []

order_counter = 1000
for _ in range(400):
    order_counter += 1
    order_id = f"ORD-{order_counter}"
    cust = random.choice(customers)
    days_ago = random.randint(0, 120)
    order_date = today - timedelta(days=days_ago)
    status = random.choices(
        order_statuses, weights=[55, 15, 12, 13, 5], k=1
    )[0]
    requested_ship = order_date + timedelta(days=random.randint(2, 7))
    order_rows.append(
        [order_id, cust[0], order_date.isoformat(), status, requested_ship.isoformat()]
    )

    # Each order has 1-4 different products on it
    for sku_info in random.sample(products, random.randint(1, 4)):
        sku, name, line, unit_cost, pack = sku_info
        qty = random.randint(50, 800)
        # selling price = cost marked up a bit
        unit_price = round(unit_cost * random.uniform(1.4, 1.9), 2)
        order_item_rows.append([order_id, sku, qty, unit_price])

    # Build a shipment for orders that have actually shipped
    if status in ("Delivered", "In Transit", "Delayed"):
        origin = random.choice(warehouses)[0]
        ship_date = order_date + timedelta(days=random.randint(1, 6))
        planned_days = random.randint(2, 6)
        delay_days = 0
        if status == "Delayed":
            delay_days = random.randint(2, 10)
        delivery_date = ship_date + timedelta(days=planned_days + delay_days)
        ship_status = "Delivered" if status == "Delivered" else (
            "Delayed" if status == "Delayed" else "In Transit"
        )
        shipment_rows.append([
            f"SHP-{order_counter}", order_id, origin,
            ship_date.isoformat(),
            delivery_date.isoformat() if status != "In Transit" else "",
            random.choice(carriers), ship_status, delay_days,
        ])

# ---------------------------------------------------------------------------
# Save everything to CSV (so you can literally open and read the data)
# ---------------------------------------------------------------------------
print("\nGenerating fake Duracell supply-chain data...")
write_csv("products.csv",
          ["sku", "name", "product_line", "unit_cost", "pack_size"], products)
write_csv("warehouses.csv",
          ["warehouse_id", "name", "city", "state", "region"], warehouses)
write_csv("customers.csv",
          ["customer_id", "name", "channel", "region"], customers)
write_csv("inventory.csv",
          ["sku", "warehouse_id", "quantity_on_hand", "reorder_point", "last_updated"],
          inventory_rows)
write_csv("orders.csv",
          ["order_id", "customer_id", "order_date", "status", "requested_ship_date"],
          order_rows)
write_csv("order_items.csv",
          ["order_id", "sku", "quantity", "unit_price"], order_item_rows)
write_csv("shipments.csv",
          ["shipment_id", "order_id", "origin_warehouse", "ship_date",
           "delivery_date", "carrier", "status", "delay_days"], shipment_rows)


# ---------------------------------------------------------------------------
# Build the SQLite database from those CSVs
# ---------------------------------------------------------------------------
print("\nBuilding the SQLite database (duracell.db)...")
if os.path.exists(DB_PATH):
    os.remove(DB_PATH)

conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()

# A "schema" is just the list of tables and their columns.
cur.executescript("""
CREATE TABLE products (
    sku TEXT PRIMARY KEY,
    name TEXT,
    product_line TEXT,
    unit_cost REAL,
    pack_size INTEGER
);
CREATE TABLE warehouses (
    warehouse_id TEXT PRIMARY KEY,
    name TEXT,
    city TEXT,
    state TEXT,
    region TEXT
);
CREATE TABLE customers (
    customer_id TEXT PRIMARY KEY,
    name TEXT,
    channel TEXT,
    region TEXT
);
CREATE TABLE inventory (
    sku TEXT,
    warehouse_id TEXT,
    quantity_on_hand INTEGER,
    reorder_point INTEGER,
    last_updated TEXT,
    PRIMARY KEY (sku, warehouse_id)
);
CREATE TABLE orders (
    order_id TEXT PRIMARY KEY,
    customer_id TEXT,
    order_date TEXT,
    status TEXT,
    requested_ship_date TEXT
);
CREATE TABLE order_items (
    order_id TEXT,
    sku TEXT,
    quantity INTEGER,
    unit_price REAL
);
CREATE TABLE shipments (
    shipment_id TEXT PRIMARY KEY,
    order_id TEXT,
    origin_warehouse TEXT,
    ship_date TEXT,
    delivery_date TEXT,
    carrier TEXT,
    status TEXT,
    delay_days INTEGER
);
""")

cur.executemany("INSERT INTO products VALUES (?,?,?,?,?)", products)
cur.executemany("INSERT INTO warehouses VALUES (?,?,?,?,?)", warehouses)
cur.executemany("INSERT INTO customers VALUES (?,?,?,?)", customers)
cur.executemany("INSERT INTO inventory VALUES (?,?,?,?,?)", inventory_rows)
cur.executemany("INSERT INTO orders VALUES (?,?,?,?,?)", order_rows)
cur.executemany("INSERT INTO order_items VALUES (?,?,?,?)", order_item_rows)
cur.executemany("INSERT INTO shipments VALUES (?,?,?,?,?,?,?,?)", shipment_rows)

conn.commit()

# ---------------------------------------------------------------------------
# Quick sanity check: print a few counts so you KNOW it worked
# ---------------------------------------------------------------------------
print("\nDatabase built. Here is what's inside:")
for table in ["products", "warehouses", "customers", "inventory",
              "orders", "order_items", "shipments"]:
    count = cur.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
    print(f"  {table:<12} {count:>5} rows")

# One example business question answered with plain SQL:
print("\nExample question: 'Which items are below their reorder point (stockout risk)?'")
risky = cur.execute("""
    SELECT i.sku, p.name, w.name AS warehouse, i.quantity_on_hand, i.reorder_point
    FROM inventory i
    JOIN products p ON p.sku = i.sku
    JOIN warehouses w ON w.warehouse_id = i.warehouse_id
    WHERE i.quantity_on_hand < i.reorder_point
    ORDER BY i.quantity_on_hand ASC
    LIMIT 5
""").fetchall()
for row in risky:
    print(f"  {row[1]} at {row[2]}: {row[3]} on hand (reorder at {row[4]})")

conn.close()
print(f"\nDone. Your database is ready at: duracell.db")
print("Next: open the CSVs in the /data folder and look at your data.")
