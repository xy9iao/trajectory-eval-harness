"""D3-① as a CI assertion (design decision 7a): provider specifics live in
agent/client.py and NOWHERE else in agent/ or eval/. A provider string
appearing anywhere else is a compatibility-layer leak — red build, no code
review vigilance required."""

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ALLOWED = ROOT / "agent" / "client.py"
PROVIDER_PATTERN = re.compile(r"deepseek|openai", re.IGNORECASE)


def test_provider_strings_only_in_client_module() -> None:
    offenders = []
    for directory in ("agent", "eval"):
        for path in (ROOT / directory).rglob("*.py"):
            if path == ALLOWED:
                continue
            for lineno, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
                if PROVIDER_PATTERN.search(line):
                    offenders.append(f"{path.relative_to(ROOT)}:{lineno}: {line.strip()}")
    assert not offenders, "provider strings outside agent/client.py:\n" + "\n".join(offenders)
