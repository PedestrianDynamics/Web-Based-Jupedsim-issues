"""V&V test registry — derived view over the standards coverage manifest.

The single source of truth is ``standards/coverage.json``. This module exposes
``TEST_MAP`` (a ``{pytest-class-prefix: (name, reference, criterion)}`` dict)
for tooling that wants to join pytest results to standard metadata. To change a
criterion or add a test, edit the manifest, not this file.
"""

import json
import pathlib

_MANIFEST = pathlib.Path(__file__).resolve().parents[2] / "standards" / "coverage.json"


def _build_map() -> dict:
    data = json.loads(_MANIFEST.read_text())
    mapping = {}
    for std in data["standards"]:
        for t in std["tests"]:
            ref = t.get("test")
            if not ref:
                continue
            cls = ref.split("::")[0]
            name = f"{t['id']} {t['name']}"
            mapping[cls] = (name, std["name"], t.get("criterion", ""))
    return mapping


TEST_MAP = _build_map()
