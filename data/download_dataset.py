"""Fetch the P0 dataset (cnamuangtoun/resume-job-description-fit) into data/raw/.

The dataset declares no license, so its text is never committed (Decision 5);
this pinned-revision script + checksums make the pull reproducible instead.
"""

import hashlib
import sys
import urllib.request
from pathlib import Path

REPO = "cnamuangtoun/resume-job-description-fit"
REVISION = (
    "08978e21714984bb417547d2c0f9b477f5298163"  # dataset repo commit, last modified 2024-07-25
)
CHECKSUMS = {
    "train.csv": "b86fa488a21258015de1750633a9ac410f701ff96bf533f68978dbe3adec6d40",
    "test.csv": "f3c48f4cc3559bf192ebb9c241a30c601b5b8b3eee6f1656dd4d26dfd4b0887a",
}
RAW_DIR = Path(__file__).resolve().parent / "raw"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> int:
    RAW_DIR.mkdir(exist_ok=True)
    failures = 0
    for name, expected in CHECKSUMS.items():
        target = RAW_DIR / name
        if not target.exists():
            url = f"https://huggingface.co/datasets/{REPO}/resolve/{REVISION}/{name}"
            print(f"downloading {name} @ {REVISION[:8]}")
            urllib.request.urlretrieve(url, target)
        actual = sha256(target)
        if actual == expected:
            print(f"{name}: ok")
        else:
            print(f"{name}: CHECKSUM MISMATCH (expected {expected}, got {actual})")
            failures += 1
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
