"""
phase4_security.py
------------------
PHASE 4 of the Duracell Battery Supply Chain AI Agent: data security + audit log.

Two enterprise must-haves, in plain code:

  1. ROLE-BASED ACCESS CONTROL (RBAC)
     Each user has a role. The role decides what data they're allowed to see.
       - Analyst: inventory, orders, shipments - but NOT unit_cost (margin data).
       - Manager: everything, including cost.
     So the SAME request returns DIFFERENT columns depending on who asks.

  2. AUDIT LOG
     Every data access is recorded (who, when, what) in an audit_log table.
     If anyone ever asks "who looked at cost data?", the answer is in the log.

These rules come straight from Section 4 of docs/supply_chain_sop.md.
No API key needed - this is pure database security.

Run it:
  python phase4_security.py
"""

import os
import sqlite3

HERE = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(HERE, "duracell.db")

# ---------------------------------------------------------------------------
# The security rules: which columns each role is NOT allowed to see.
# ---------------------------------------------------------------------------
ALL_PRODUCT_COLUMNS = ["sku", "name", "product_line", "unit_cost", "pack_size"]

ROLE_HIDDEN_COLUMNS = {
    "Analyst": {"unit_cost"},   # Analysts cannot see cost / margin data
    "Manager": set(),           # Managers can see everything (nothing hidden)
}


def get_conn():
    return sqlite3.connect(DB_PATH)


# ---------------------------------------------------------------------------
# The audit log: record every access so it can be reviewed later.
# ---------------------------------------------------------------------------
def ensure_audit_table(conn):
    """Create the audit_log table the first time (safe to call every run)."""
    conn.execute("""
        CREATE TABLE IF NOT EXISTS audit_log (
            ts     TEXT,   -- when it happened
            user   TEXT,   -- who did it
            role   TEXT,   -- their role
            action TEXT,   -- what they did
            detail TEXT    -- extra info (e.g. which columns were returned)
        )
    """)
    conn.commit()


def log_access(conn, user, role, action, detail=""):
    """Write one line to the audit log."""
    conn.execute(
        "INSERT INTO audit_log VALUES (datetime('now'), ?, ?, ?, ?)",
        (user, role, action, detail),
    )
    conn.commit()


# ---------------------------------------------------------------------------
# A role-aware data function: returns product data WITHOUT the columns the
# caller's role isn't allowed to see - and logs the access either way.
# ---------------------------------------------------------------------------
def get_products(conn, user, role):
    # Unknown role? Deny, and log the denied attempt (security teams want this).
    if role not in ROLE_HIDDEN_COLUMNS:
        log_access(conn, user, role, "DENIED", "unknown role")
        raise PermissionError(f"Role '{role}' is not recognized - access denied.")

    hidden = ROLE_HIDDEN_COLUMNS[role]
    # Build the list of columns this role IS allowed to see.
    visible = [c for c in ALL_PRODUCT_COLUMNS if c not in hidden]

    # We only ever SELECT the allowed columns - the hidden ones never leave the DB.
    sql = f"SELECT {', '.join(visible)} FROM products"
    rows = conn.execute(sql).fetchall()

    log_access(conn, user, role, "READ products", f"columns={visible}")
    return visible, rows


# ---------------------------------------------------------------------------
# Demo: run the exact same request as an Analyst and as a Manager.
# ---------------------------------------------------------------------------
def show(user, role, visible, rows):
    print(f"\n--- {user} (role: {role}) asked to see products ---")
    print("   columns returned:", visible)
    print(f"   {'unit_cost VISIBLE' if 'unit_cost' in visible else 'unit_cost HIDDEN'}")
    print("   first row:", rows[0])


def main():
    conn = get_conn()
    ensure_audit_table(conn)

    # Same data, two different people:
    v1, r1 = get_products(conn, user="priya.intern", role="Analyst")
    show("priya.intern", "Analyst", v1, r1)

    v2, r2 = get_products(conn, user="dan.manager", role="Manager")
    show("dan.manager", "Manager", v2, r2)

    # An unknown role is refused:
    print("\n--- someone with an unknown role tries ---")
    try:
        get_products(conn, user="mystery.user", role="Guest")
    except PermissionError as e:
        print("  ", e)

    # Show the audit trail we just created:
    print("\n=== AUDIT LOG (every access was recorded) ===")
    for row in conn.execute("SELECT * FROM audit_log ORDER BY ts DESC LIMIT 5"):
        print("  ", row)

    conn.close()
    print("\nSee how the Analyst never got unit_cost, and every access was logged?")
    print("That's role-based access control + auditing - enterprise-safe by design.")


if __name__ == "__main__":
    main()
