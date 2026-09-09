"""M2. LLM-as-judge for answer correctness.

Rubric (commit changes to this; it's part of the eval definition):
  1 = answer conveys the same facts as gold_answer; extra correct detail is fine.
  0 = missing a required fact, states a wrong fact, or answers when it should abstain.

Use a different model from the generator. Report agreement with human labels on the
30-question subset (data/gold/human_labels.jsonl) next to every correctness number.
"""
