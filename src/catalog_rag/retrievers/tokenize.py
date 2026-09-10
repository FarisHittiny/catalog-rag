"""Shared tokenizer. `fuse_codes=True` adds one token per course code so "ECEN 350",
"ECEN350" and "ecen 350" all produce ["ecen", "350", "ecen350"]."""
from __future__ import annotations

import re

TOKEN_RE = re.compile(r"[a-z0-9]+")
CODE_RE = re.compile(r"\b([A-Z]{3,4})\s?(\d{3}[A-Z]?)\b", re.IGNORECASE)


def tokenize(s: str, fuse_codes: bool = False) -> list[str]:
    if fuse_codes:
        s = CODE_RE.sub(lambda m: f"{m[1]} {m[2]} {m[1]}{m[2]}", s)
    return TOKEN_RE.findall(s.lower())


def extract_codes(s: str) -> list[str]:
    """Canonical course ids named in s ("ECEN 350"), in order of first appearance, deduplicated."""
    out: list[str] = []
    for m in CODE_RE.finditer(s):
        cid = f"{m[1].upper()} {m[2].upper()}"
        if cid not in out:
            out.append(cid)
    return out
