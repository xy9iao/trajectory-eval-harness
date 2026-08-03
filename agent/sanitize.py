"""Parse-seam sanitization — the MECHANISM half of P3's defense.

Applied where documents enter the system, so every downstream consumer
(prompt, evidence-quote resolution, trajectory offsets) sees the same text.
Sanitizing only the prompt would desynchronize quote resolution from the
document of record and manufacture spurious degradations.

Two operations, both purely mechanical — no model, no classifier, no judgment:

1. **Carrier stripping.** Zero-width and other invisible formatting characters
   are removed. They carry no information a reader can use and exist in a
   pasted resume for one reason: to break exact-string matching while staying
   readable to a model (P3 class D).

2. **Role-marker neutralization.** Text shaped like a prompt boundary — a
   fenced `--- SYSTEM ---` block, a line starting `ASSISTANT:`, an
   `### END OF RESUME ###` divider — is defanged by inserting a visible
   marker, NOT by deleting it. Deletion would destroy document offsets and
   silently discard content; the goal is only to stop the shape from reading
   as structure.

Deliberately NOT here: any attempt to detect "instructions" semantically.
That is the instruction-class defense, which this project measured at 0/3.
</summary>
"""

import re

# Zero-width and directionality controls. Ordinary text never needs these;
# a resume containing them is either machine-mangled or carrying a payload.
INVISIBLE = re.compile(r"[​-‏‪-‮⁠-⁤﻿­]")

# Shapes that read as prompt structure rather than document content.
ROLE_MARKERS = re.compile(
    r"(?im)^\s*(?:"
    r"(?:-{2,}|#{2,}|={2,}|\*{2,})\s*(?:system|assistant|user|end\s+of\s+\w+|"
    r"instructions?|prompt)\b.*"
    r"|(?:system|assistant|user)\s*:.*"
    r")$"
)

NEUTRALIZED = "[document text — not a system boundary] "


def strip_invisible(text: str) -> str:
    return INVISIBLE.sub("", text)


def neutralize_role_markers(text: str) -> str:
    return ROLE_MARKERS.sub(lambda m: NEUTRALIZED + m.group(0).strip(), text)


def sanitize(text: str) -> str:
    """Both operations, in the order that matters: strip carriers FIRST.

    A payload can hide a role marker from the pattern by seeding it with
    zero-width characters (`S​YSTEM:`), so carrier removal has to run
    before shape matching or the second defense is trivially bypassed by the
    first attack.
    """
    return neutralize_role_markers(strip_invisible(text))
