"""
tools.py
--------
PHASE 5 of the Duracell Battery Supply Chain AI Agent: the agent's TOOLS.

A "tool" is just a plain Python function that does something real against our
data. In Phase 6 we'll hand this list of tools to the AI and let it CHOOSE which
one to run for each question. That choosing is what turns a chatbot into an agent.

Each tool here:
  - takes simple inputs,
  - does one clear job against duracell.db (or the SOP),
  - returns a short, readable string the AI can use in its answer.

None of these tools expose cost/margin data, so they're safe for an Analyst
(that's the Phase 4 thinking carried forward).

You can test the tools on their own:
  python tools.py
"""

import os
import sqlite3

HERE = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(HERE, "duracell.db")


def _conn():
    return sqlite3.connect(DB_PATH)


# ---------------------------------------------------------------------------
# TOOL 1 - check how much stock of a product we have, by warehouse
# ---------------------------------------------------------------------------
def check_inventory(product: str) -> str:
    """Show current stock of a product (matched by name or SKU) in each warehouse."""
    conn = _conn()
    rows = conn.execute(
        """
        SELECT p.name, w.name, i.quantity_on_hand, i.reorder_point
        FROM inventory i
        JOIN products p   ON p.sku = i.sku
        JOIN warehouses w ON w.warehouse_id = i.warehouse_id
        WHERE p.name LIKE ? OR p.sku LIKE ?
        ORDER BY i.quantity_on_hand ASC
        """,
        (f"%{product}%", f"%{product}%"),
    ).fetchall()
    conn.close()

    if not rows:
        return f"No product found matching '{product}'."

    lines = [f"Inventory for '{product}':"]
    for name, wh, qty, reorder in rows:
        flag = "  <-- BELOW reorder point" if qty < reorder else ""
        lines.append(f"  {name} at {wh}: {qty} on hand (reorder at {reorder}){flag}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# TOOL 2 - find every product at risk of running out (below reorder point)
# ---------------------------------------------------------------------------
def find_stockout_risks(limit: int = 10) -> str:
    """List products whose stock has dropped below their reorder point."""
    conn = _conn()
    rows = conn.execute(
        """
        SELECT p.name, w.name, i.quantity_on_hand, i.reorder_point, p.product_line
        FROM inventory i
        JOIN products p   ON p.sku = i.sku
        JOIN warehouses w ON w.warehouse_id = i.warehouse_id
        WHERE i.quantity_on_hand < i.reorder_point
        ORDER BY i.quantity_on_hand ASC
        LIMIT ?
        """,
        (limit,),
    ).fetchall()
    conn.close()

    if not rows:
        return "Good news: no products are below their reorder point."

    lines = [f"{len(rows)} product(s) at stockout risk (lowest first):"]
    for name, wh, qty, reorder, line in rows:
        lines.append(f"  [{line}] {name} at {wh}: {qty} on hand (reorder at {reorder})")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# TOOL 3 - look up the status of one specific order
# ---------------------------------------------------------------------------
def get_order_status(order_id: str) -> str:
    """Return the status, customer, and dates for a given order id."""
    conn = _conn()
    row = conn.execute(
        """
        SELECT o.order_id, c.name, o.order_date, o.status, o.requested_ship_date
        FROM orders o
        JOIN customers c ON c.customer_id = o.customer_id
        WHERE o.order_id = ?
        """,
        (order_id.upper(),),
    ).fetchone()
    conn.close()

    if not row:
        return f"No order found with id '{order_id}'."
    oid, cust, odate, status, req_ship = row
    return (f"Order {oid} for {cust}: status = {status}. "
            f"Ordered {odate}, requested ship by {req_ship}.")


# ---------------------------------------------------------------------------
# TOOL 4 - find shipments that are running late
# ---------------------------------------------------------------------------
def find_delayed_shipments(limit: int = 10) -> str:
    """List delayed shipments, most-delayed first."""
    conn = _conn()
    rows = conn.execute(
        """
        SELECT s.shipment_id, s.order_id, s.carrier, s.delay_days, c.name
        FROM shipments s
        JOIN orders o    ON o.order_id = s.order_id
        JOIN customers c ON c.customer_id = o.customer_id
        WHERE s.status = 'Delayed'
        ORDER BY s.delay_days DESC
        LIMIT ?
        """,
        (limit,),
    ).fetchall()
    conn.close()

    if not rows:
        return "No delayed shipments right now."

    lines = [f"{len(rows)} delayed shipment(s) (worst first):"]
    for sid, oid, carrier, delay, cust in rows:
        lines.append(f"  {sid} (order {oid}, {cust}): {delay} days late via {carrier}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# TOOL 5 - search the SOP document (reuses your Phase 3 RAG)
# ---------------------------------------------------------------------------
def search_sop(question: str) -> str:
    """Find the most relevant SOP policy sections for a question."""
    # Imported here so the database tools above work even if the RAG store
    # (ChromaDB) isn't built yet.
    from phase3_rag import get_collection, retrieve
    collection = get_collection()
    chunks = retrieve(collection, question, k=2)
    return "Relevant SOP sections:\n\n" + "\n\n---\n\n".join(chunks)


# A simple list so later phases (and you) can see all tools in one place.
ALL_TOOLS = [
    check_inventory,
    find_stockout_risks,
    get_order_status,
    find_delayed_shipments,
    search_sop,
]


if __name__ == "__main__":
    print("Testing the database tools:\n")
    print(find_stockout_risks(limit=3))
    print()
    print(check_inventory("Procell"))
    print()
    print(find_delayed_shipments(limit=3))
    print()
    # get_order_status needs a real id; grab one to demo:
    sample = sqlite3.connect(DB_PATH).execute("SELECT order_id FROM orders LIMIT 1").fetchone()[0]
    print(get_order_status(sample))
