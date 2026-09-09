# Writing gold questions

One JSON object per line in `gold_set.jsonl`. You write these by hand. That's the point:
you know the CE degree plan, so you can say what the right answer is.

Rules:
- Write the question the way a sophomore would actually type it. Not "Enumerate the prerequisite courses for ECEN 350." Just "what do I need before ECEN 350?"
- `gold_course_ids` = every course record a correct answer has to draw from. For a prereq question about ECEN 350, that's `["ECEN 350"]` (the record holds the prereq string). For "what can I take after ECEN 350", it's every course that lists 350 as a prereq.
- `gold_answer` = the answer in one or two sentences, checked against the catalog page, not from memory.
- `not_in_catalog` questions have `answerable: false` and empty `gold_course_ids`. They should sound plausible: professors, grade distributions, section times, "is it hard."
- Tag `dept` with the department the answer lives in. Cross-dept questions: pick the primary.
- Aim for 40 factual / 25 prereq / 20 multi_hop / 15 not_in_catalog.

First 30 (M0) can be all factual + prereq. Add the rest for M1.

Keep a separate `human_labels.jsonl` (M2) with `{"id": ..., "answer": <generated>, "label": 0|1}` for the 30 you grade by hand.
