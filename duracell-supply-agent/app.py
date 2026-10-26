"""
app.py
------
PHASE 7 of the Duracell Battery Supply Chain AI Agent: the web UI + audit log.

This turns your terminal agent into a simple web page a planner would actually
use. It brings the whole project together:
  - Phase 6 agent answers the questions,
  - Phase 4 roles decide what the user is allowed to ask (Analyst vs Manager),
  - Phase 4 audit log records every question (who, when, what).

Streamlit builds the web page from plain Python - no HTML or JavaScript needed.

Run it (this opens a web page in your browser):
  streamlit run app.py
"""

import os
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

from agent import build_agent
from phase4_security import get_conn, ensure_audit_table, log_access

# ---------------------------------------------------------------------------
# Build the agent once and reuse it (cache_resource = "make this only once").
# ---------------------------------------------------------------------------
@st.cache_resource
def load_agent():
    return build_agent()


def run_agent(agent, question, role, user):
    """Ask the agent a question, respecting the user's role; return answer + tools."""
    # The role is injected here so the agent knows who's asking. This is how
    # Phase 4's rules reach the agent: Analysts are refused cost/margin data.
    system_prompt = (
        "You are a Duracell supply-chain assistant. Use the provided tools to "
        "answer questions about inventory, orders, shipments, and SOPs. Base "
        "answers on tool results; if a tool returns nothing, say so.\n"
        f"The current user's role is '{role}'. "
        "If the role is 'Analyst' and they ask about cost, margin, or price, "
        "politely refuse and say that data is available to Managers only."
    )

    result = agent.invoke({
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": question},
        ]
    })

    # Collect which tools the agent chose, to show the user its working.
    tools_used = []
    for msg in result["messages"]:
        for tc in getattr(msg, "tool_calls", None) or []:
            tools_used.append(tc["name"])

    answer = result["messages"][-1].text   # text only, no "thinking" blocks
    return answer, tools_used


# ---------------------------------------------------------------------------
# The web page
# ---------------------------------------------------------------------------
st.set_page_config(page_title="Duracell Supply Chain Agent", page_icon="🔋")
st.title("🔋 Duracell Supply Chain Agent")
st.caption("Ask about inventory, orders, shipments, and company policies.")

# Sidebar: who are you? (role = Phase 4)
with st.sidebar:
    st.header("Who's asking")
    user = st.text_input("Your name", value="demo.user")
    role = st.selectbox("Your role", ["Analyst", "Manager"])
    st.caption("Analysts cannot see cost or margin data.")

# A few example questions so people know what to ask (helps adoption).
st.write("**Try asking:**")
st.write("- Which products are at risk of running out?")
st.write("- Is order ORD-1027 delayed?")
st.write("- How fast must we restock Procell items? (from the SOP)")
st.write("- What's our cost on Coppertop AA? (Analysts will be refused)")

question = st.text_input("Your question:")

if st.button("Ask") and question:
    if not os.getenv("ANTHROPIC_API_KEY"):
        st.error("No ANTHROPIC_API_KEY found. Add your key to the .env file.")
    else:
        with st.spinner("The agent is thinking..."):
            agent = load_agent()
            answer, tools_used = run_agent(agent, question, role, user)

        # Show the answer
        st.markdown("### Answer")
        st.write(answer)

        # Show which tools were used (transparency = trust)
        if tools_used:
            st.markdown("**Tools the agent used:** " + ", ".join(tools_used))

        # Write to the audit log (Phase 4)
        conn = get_conn()
        ensure_audit_table(conn)
        log_access(conn, user, role, "ASK", f"Q: {question}")
        conn.close()
        st.success("Logged to the audit trail.")

# Show the recent audit log so the logging is visible
with st.expander("View recent audit log"):
    conn = get_conn()
    ensure_audit_table(conn)
    rows = conn.execute(
        "SELECT ts, user, role, action, detail FROM audit_log ORDER BY ts DESC LIMIT 10"
    ).fetchall()
    conn.close()
    if rows:
        st.table(rows)
    else:
        st.write("No activity logged yet.")
