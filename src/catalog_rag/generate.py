"""M2. Generation with citations and abstention.

Prompt contract:
  - Answer only from the provided course records.
  - Cite course codes inline like [ECEN 350].
  - If the records do not contain the answer, reply exactly: "Not in the catalog."
Provider selected by LLM_PROVIDER in .env (anthropic | openai | tamu).
"""
