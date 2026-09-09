"""Scrape course descriptions from catalog.tamu.edu into data/processed/courses.jsonl.

The catalog is CourseLeaf static HTML. Each course is a <div class="courseblock"> with
<p class="courseblocktitle"> and <p class="courseblockdesc">. The parser is tolerant about
where the "Credits N." line lives (title vs. description) and strips cross-listed codes
out of the title. Still: VERIFY against one saved page before trusting the output
(run once with --save-html, then open data/raw/ecen.html and spot-check a course).

Usage:
    python -m catalog_rag.scrape --depts ECEN --depts CSCE
    python -m catalog_rag.scrape --depts ECEN --from-html data/raw/ecen.html   # offline re-parse
"""
from __future__ import annotations

import re
from pathlib import Path

import httpx
import typer
from bs4 import BeautifulSoup
from rich import print

from .models import Course
from .prereq_graph import parse_prereq_string

BASE = "https://catalog.tamu.edu/undergraduate/course-descriptions/{dept}/"
RAW = Path("data/raw")
OUT = Path("data/processed/courses.jsonl")

CODE_RE = re.compile(r"\b([A-Z]{3,4})\s(\d{3}[A-Z]?)\b")
# Leading run of codes in a title: "ECEN 350/CSCE 350 Computer Architecture and Design"
LEAD_CODES_RE = re.compile(r"^((?:[A-Z]{3,4}\s\d{3}[A-Z]?\s*/\s*)*[A-Z]{3,4}\s\d{3}[A-Z]?)\s*(.*)$", re.S)
CREDITS_RE = re.compile(r"Credits?\s*(\d+(?:\.\d+)?(?:\s*(?:to|-|or)\s*\d+)?)")
# Field separators in CourseLeaf desc: "Prerequisite: ...; Cross Listing: ...; Corequisite: ..."
_STOP = r"(?=(?:[.;]\s*(?:Cross Listing|Corequisite|Prerequisite)s?:)|$)"
PREREQ_RE = re.compile(r"Prerequisites?:\s*(.*?)" + _STOP, re.S)
COREQ_RE = re.compile(r"Corequisites?:\s*(.*?)" + _STOP, re.S)
XLIST_RE = re.compile(r"Cross Listing:\s*(.*?)" + _STOP, re.S)


def _clean(s: str) -> str:
    return re.sub(r"\s+([.;,:)])", r"\1", " ".join(s.split()))


def fetch(dept: str, save_html: bool) -> str:
    url = BASE.format(dept=dept.lower())
    r = httpx.get(url, timeout=30, follow_redirects=True, headers={"User-Agent": "catalog-rag/0.1"})
    r.raise_for_status()
    if save_html:
        RAW.mkdir(parents=True, exist_ok=True)
        (RAW / f"{dept.lower()}.html").write_text(r.text, encoding="utf-8")
    return r.text


def parse_title(title_text: str) -> tuple[str, list[str], str] | None:
    """'ECEN 350/CSCE 350 Computer Architecture and Design' -> ('ECEN 350', ['CSCE 350'], title)."""
    title_text = _clean(title_text)
    m = LEAD_CODES_RE.match(title_text)
    if not m:
        return None
    codes = [f"{a} {b}" for a, b in CODE_RE.findall(m.group(1))]
    rest = m.group(2)
    rest = CREDITS_RE.split(rest)[0]  # drop trailing "Credits 3. ..." if it's in the title
    return codes[0], codes[1:], rest.strip(" .")


def parse(html: str, dept: str, catalog_year: str, url: str) -> list[Course]:
    soup = BeautifulSoup(html, "lxml")
    courses: list[Course] = []
    for block in soup.select("div.courseblock"):
        title_el = block.select_one(".courseblocktitle")
        desc_el = block.select_one(".courseblockdesc")
        if not title_el:
            continue
        title_text = _clean(title_el.get_text(" ", strip=True))
        parsed = parse_title(title_text)
        if not parsed:
            print(f"[yellow]unparsed title:[/] {title_text[:80]}")
            continue
        course_id, title_xlist, title = parsed
        d, num = course_id.split(" ", 1)
        if d != dept.upper():
            # e.g. a CSCE-primary crosslisted entry rendered on the ECEN page; keep the page's dept.
            pass
        desc = _clean(desc_el.get_text(" ", strip=True)) if desc_el else ""

        credits_m = CREDITS_RE.search(title_text) or CREDITS_RE.search(desc)
        credits = credits_m.group(1) if credits_m else ""

        prereq_raw = _clean(m.group(1)) if (m := PREREQ_RE.search(desc)) else ""
        coreq_raw = m.group(1) if (m := COREQ_RE.search(desc)) else ""
        xlist_raw = m.group(1) if (m := XLIST_RE.search(desc)) else ""
        crosslisted = [f"{a} {b}" for a, b in CODE_RE.findall(xlist_raw)] or title_xlist
        crosslisted = [c for c in dict.fromkeys(crosslisted) if c != course_id]

        courses.append(
            Course(
                course_id=course_id,
                dept=d,
                number=num,
                title=title,
                credits=credits,
                description=desc,
                prereq_raw=prereq_raw.rstrip(". "),
                prereqs=parse_prereq_string(prereq_raw),
                coreqs=[f"{a} {b}" for a, b in CODE_RE.findall(coreq_raw)],
                crosslisted=crosslisted,
                catalog_year=catalog_year,
                source_url=url,
            )
        )
    return courses


def main(
    depts: list[str] = typer.Option(["ECEN", "CSCE"], help="Department prefixes (repeat the flag)"),
    catalog_year: str = "2026-2027",
    save_html: bool = True,
    from_html: Path | None = typer.Option(None, help="Parse a saved page instead of fetching (one dept)"),
    out: Path = OUT,
):
    out.parent.mkdir(parents=True, exist_ok=True)
    total = 0
    with out.open("w", encoding="utf-8") as f:
        for dept in depts:
            url = BASE.format(dept=dept.lower())
            html = from_html.read_text(encoding="utf-8") if from_html else fetch(dept, save_html)
            courses = parse(html, dept, catalog_year, url)
            n_prereq = sum(1 for c in courses if c.prereqs)
            for c in courses:
                f.write(c.model_dump_json() + "\n")
            print(f"[green]{dept}[/]: {len(courses)} courses, {n_prereq} with parsed prereqs")
            total += len(courses)
    print(f"wrote {total} courses to {out}")


if __name__ == "__main__":
    typer.run(main)
