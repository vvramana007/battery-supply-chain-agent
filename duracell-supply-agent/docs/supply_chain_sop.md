# Duracell Supply Chain — Standard Operating Procedures (SOP)

*This is a sample internal policy document. In Phase 3 we teach the AI agent to*
*read and answer questions from it using RAG. (Fictional, for learning only.)*

## 1. Reorder and stockout policy

- Every product at every distribution center (DC) has a **reorder point**.
- When `quantity_on_hand` falls **below** the reorder point, the item is at
  **stockout risk** and a replenishment order must be raised within 2 business days.
- Procell (professional) and Specialty lithium items are **priority**: raise
  replenishment within 1 business day because professional customers (hospitals,
  security, fire-safety) depend on them.

## 2. Order fulfillment priority

When stock is limited, fulfill orders in this order:
1. Professional / Procell channel customers.
2. Club and Mass Retail customers with contractual service levels (Walmart, Costco).
3. All other channels.

## 3. Shipment delay handling

- A shipment is **Delayed** if its delivery runs more than 1 day past plan.
- Any delay of **5 days or more** must be escalated to the customer's account
  manager and logged.
- Preferred carriers by region: Northeast/Southeast → FedEx; Midwest/South →
  UPS; West → Old Dominion.

## 4. Data access rules (used in Phase 4)

- **Analyst** role: may read inventory, orders, shipments. May NOT see `unit_cost`
  (that is sensitive margin data).
- **Manager** role: may read everything, including cost and margin.
- All questions and answers are written to an **audit log** for compliance.

## 5. Key definitions

- **SKU**: a unique product code (e.g. `DUR-AA-24` = Coppertop AA, 24-pack).
- **DC**: distribution center / warehouse.
- **On hand**: units physically available to ship right now.
- **Lead time**: days between placing a replenishment order and stock arriving.
