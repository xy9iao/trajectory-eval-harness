"""Recorded keyword taxonomies and requirement patterns over the JD corpus.

These definitions ARE the method behind archived numbers: the
occupation/industry buckets feed profile_jd_domains.py (finding 001) and
the reference sampler's stratification; the requirement patterns feed
profile_jd_requirements.py (the rubric weight rationale, p0 report §2).
Do not edit terms without revising the findings/report sections that cite
the resulting counts.

Method caveat (recorded in finding 001): keyword matching is coarse and
cross-axis terms (e.g. "financial") can hit both an occupation and an
industry, so counts are directional, not exact.

Requirement-pattern notes (recorded so the counts are auditable):
- must-language counts must / require / requires / required / requirement(s).
- years counts numeric year phrases incl. ranges ("5+ years", "3-5 years",
  "3 to 5 years") and the bare "years of experience" idiom.
- degrees counts degree-level tokens only. Bare "ms"/"bs" are excluded (32
  unique JDs match \\bms\\b, dominated by "MS Office"/"MS SQL"); "associate"
  is excluded ("sales associate" job titles); "associate degree" is still
  caught via "degree".
"""

import re

OCCUPATION = {
    "software eng": [
        "software engineer",
        "software developer",
        "full stack",
        "backend",
        "back-end",
        "frontend",
        "front-end",
    ],
    "data/ML": ["data engineer", "data analyst", "data scientist", "machine learning"],
    "devops/infra": ["devops", "site reliability", "cloud engineer", "platform engineer"],
    "hardware eng": [
        "electrical engineer",
        "electronic engineer",
        "mechanical engineer",
        "hardware",
    ],
    "accounting/fin": ["accountant", "accounting", "bookkeeper", "financial analyst", "auditor"],
    "business/PM": ["business analyst", "product manager", "project manager", "program manager"],
    "sales/mktg": ["sales", "marketing", "account executive"],
    "healthcare": ["nurse", "physician", "clinical", "medical assistant"],
    "hr/admin": ["human resources", "recruiter", "office manager", "administrative"],
}

INDUSTRY = [
    "finance",
    "financial",
    "banking",
    "bank",
    "fintech",
    "healthcare",
    "health care",
    "medical",
    "hospital",
    "insurance",
    "retail",
    "e-commerce",
    "government",
    "federal",
    "defense",
    "manufacturing",
    "automotive",
    "telecom",
    "education",
    "pharmaceutical",
    "energy",
    "oil",
    "aerospace",
]

PATTERNS = {
    "must/required language": re.compile(r"\b(must|require[sd]?|requirements?)\b"),
    "years requirement": re.compile(
        r"\b\d+\s*(?:\+|-|–|to\s*\d+)?\s*years?\b|\byears?\s+of\s+experience\b"
    ),
    "degree mention": re.compile(r"\b(bachelor'?s?|master'?s?|degree|ph\.?d|doctorate|mba|bsms)\b"),
}


def word(term: str, text: str) -> bool:
    return re.search(r"\b" + re.escape(term) + r"\b", text) is not None


def occupation_bucket(jd_lower: str) -> str:
    """First matching bucket in OCCUPATION order; 'none' if no bucket hits."""
    for label, terms in OCCUPATION.items():
        if any(word(t, jd_lower) for t in terms):
            return label
    return "none"
