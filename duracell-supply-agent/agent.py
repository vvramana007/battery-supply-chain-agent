"""
agent.py
--------
PHASE 6 of the Duracell Battery Supply Chain AI Agent: the agent brain (LangGraph).

This is where it all comes together. We take:
  - Claude (the smart model), and
  - your tools from tools.py (the agent's hands),
and let LangGraph run the think -> act -> look -> repeat loop automatically.

How the loop works (LangGraph handles all of this for you):
  1. Claude reads the question.
  2. It decides whether to call a tool, and which one, with what inputs.
  3. The tool runs; its result goes back to Claude.
  4. Claude decides if it needs another tool, or if it's ready to answer.
  5. It writes the final answer.

Needs your Claude API key in .env. Each question costs a fraction of a cent.

Run it:
  python agent.py
  python agent.py "Which Procell items are low, and is order ORD-1027 delayed?"
"""

import os
import sys
from dotenv import load_dotenv

load_dotenv()

from langchain_anthropic import ChatAnthropic
from langchain_core.tools import StructuredTool
from langgraph.prebuilt import create_react_agent

import tools as T

CLAUDE_MODEL = "claude-haiku-5-5"

# Tell the agent who it is and how to behave.
SYSTEM_PROMPT = (
    "You are a Duracell supply-chain assistant. Answer questions about battery "
    "inventory, orders, shipments, and company SOPs by using the provided tools. "
    "Always base your answer on what the tools return. If a tool returns nothing, "
    "say so plainly instead of guessing. Keep answers short and clear."
)


def build_agent():
    """Wire Claude + the tools into a LangGraph agent."""
    # 1. Turn our plain Python functions into tools the agent can call.
    #    StructuredTool reads each function's name, type hints, and docstring
    #    so Claude knows what each tool does and what inputs it needs.
    lc_tools = [StructuredTool.from_function(fn) for fn in T.ALL_TOOLS]

    # 2. The model. (Newer Claude models don't take a temperature setting.)
    model = ChatAnthropic(model=CLAUDE_MODEL)

    # 3. create_react_agent builds the whole think->act->look->repeat graph.
    return create_react_agent(model, lc_tools)


def ask(agent, question):
    """Run one question through the agent and show its work."""
    print(f"\nQUESTION: {question}\n")

    result = agent.invoke({
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": question},
        ]
    })

    # Walk the conversation and show every tool the agent chose to use.
    # This makes the agent's "thinking" visible - great for learning.
    print("--- the agent's steps ---")
    for msg in result["messages"]:
        tool_calls = getattr(msg, "tool_calls", None)
        if tool_calls:
            for tc in tool_calls:
                print(f"  [chose tool] {tc['name']}  inputs={tc['args']}")

    # The last message is the agent's final written answer.
    # .text keeps only the written text (skipping any "thinking" blocks).
    print("\n--- final answer ---")
    print(result["messages"][-1].text)
    print()


def main():
    if not os.getenv("ANTHROPIC_API_KEY"):
        print("No ANTHROPIC_API_KEY found in .env - add your key to run the agent.")
        return

    question = sys.argv[1] if len(sys.argv) > 1 else \
        "Which products are at risk of running out, and are any shipments delayed?"

    agent = build_agent()
    ask(agent, question)


if __name__ == "__main__":
    main()
