"""
phase3_rag.py
-------------
PHASE 3 of the Duracell Battery Supply Chain AI Agent: RAG over the SOP document.

The "open-book exam" in code. In plain words this file:
  1. Reads the policy document (docs/supply_chain_sop.md).
  2. Cuts it into small chunks (one per section).
  3. Stores those chunks in a tiny local vector database (ChromaDB), which turns
     each chunk into "meaning numbers" (embeddings) for free, on your computer.
  4. When you ask a question, it RETRIEVES the most relevant chunks, then asks
     Claude to GENERATE an answer using ONLY those chunks - and shows its sources.

Run it:
  python phase3_rag.py
  python phase3_rag.py "How fast must I restock Procell items?"

Good to know: you can run this WITHOUT a Claude API key - it will still show you
the chunks it retrieved (the "open book" pages). Add your key in .env to get the
final written answer.
"""

import os
import sys
import re

import chromadb
from dotenv import load_dotenv

# Load the secret API key from the .env file (if present)
load_dotenv()

HERE = os.path.dirname(os.path.abspath(__file__))
SOP_PATH = os.path.join(HERE, "docs", "supply_chain_sop.md")
STORE_PATH = os.path.join(HERE, "rag_store")          # the vector DB lives here
COLLECTION = "duracell_sop"

# The Claude model to use for writing the final answer.
# Haiku is cheap and fast - great for learning. You can swap in a
# bigger model (e.g. "claude-sonnet-5-5") for richer answers.
CLAUDE_MODEL = "claude-haiku-5-5"


# ---------------------------------------------------------------------------
# STEP 1 - Chunking: cut the document into sections
# ---------------------------------------------------------------------------
def load_and_chunk(path):
    """Split the SOP markdown into one chunk per '## ' section."""
    with open(path, "r", encoding="utf-8") as f:
        text = f.read()

    # Split the text wherever a line starts with "## " (a section heading).
    # The (?=...) keeps the heading attached to the section it belongs to.
    parts = re.split(r"(?=^##\s)", text, flags=re.MULTILINE)

    chunks = []
    for part in parts:
        part = part.strip()
        # Keep only real sections (they start with "## "), skip the title block.
        if part.startswith("##"):
            chunks.append(part)
    return chunks


# ---------------------------------------------------------------------------
# STEP 2 - Build the vector database (only needs to happen once)
# ---------------------------------------------------------------------------
def get_collection():
    """Open the local vector DB, filling it from the SOP the first time."""
    client = chromadb.PersistentClient(path=STORE_PATH)
    collection = client.get_or_create_collection(name=COLLECTION)

    # If it's empty, this is the first run - load the document in.
    if collection.count() == 0:
        print("First run: reading the SOP and building the vector index...")
        chunks = load_and_chunk(SOP_PATH)
        collection.add(
            documents=chunks,                          # the text of each chunk
            ids=[f"chunk-{i}" for i in range(len(chunks))],  # a label for each
        )
        print(f"  stored {len(chunks)} chunks in the vector database.\n")
    return collection


# ---------------------------------------------------------------------------
# STEP 3 - Retrieve: find the chunks closest in meaning to the question
# ---------------------------------------------------------------------------
def retrieve(collection, question, k=3):
    """Return the k most relevant chunks for the question."""
    results = collection.query(query_texts=[question], n_results=k)
    return results["documents"][0]   # a list of chunk texts


# ---------------------------------------------------------------------------
# STEP 4 - Generate: ask Claude to answer using ONLY the retrieved chunks
# ---------------------------------------------------------------------------
def generate_answer(question, chunks):
    """Send the question + retrieved chunks to Claude and return its answer."""
    import anthropic

    client = anthropic.Anthropic()  # reads ANTHROPIC_API_KEY from the environment

    # We paste the retrieved chunks into the prompt and tell Claude to use ONLY
    # them. This is the heart of RAG - the model answers from the "open book".
    context = "\n\n---\n\n".join(chunks)
    prompt = f"""You are a Duracell supply-chain assistant. Answer the question
using ONLY the policy sections provided below. If the answer is not in them,
say you don't have that policy. Quote the relevant rule and name its section.

POLICY SECTIONS:
{context}

QUESTION: {question}
"""

    message = client.messages.create(
        model=CLAUDE_MODEL,
        max_tokens=400,
        messages=[{"role": "user", "content": prompt}],
    )
    # The reply can contain several blocks (e.g. Claude's "thinking" first),
    # so keep only the text blocks - that's the written answer.
    return "".join(b.text for b in message.content if b.type == "text")


# ---------------------------------------------------------------------------
# Put it together
# ---------------------------------------------------------------------------
def main():
    # Use the question from the command line, or a sensible default.
    question = sys.argv[1] if len(sys.argv) > 1 else \
        "How quickly must we restock Procell items that are below reorder point?"

    print(f"\nQUESTION: {question}\n")

    collection = get_collection()
    chunks = retrieve(collection, question, k=3)

    print("RETRIEVED these policy sections (the 'open book' pages):")
    for i, c in enumerate(chunks, 1):
        first_line = c.splitlines()[0]
        print(f"  {i}. {first_line}")
    print()

    if os.getenv("ANTHROPIC_API_KEY"):
        print("CLAUDE'S ANSWER (grounded in the sections above):\n")
        print(generate_answer(question, chunks))
    else:
        print("(No ANTHROPIC_API_KEY found in .env, so skipping the written answer.)")
        print("Retrieval works! Add your key to .env to see Claude write the answer.")
    print()


if __name__ == "__main__":
    main()
