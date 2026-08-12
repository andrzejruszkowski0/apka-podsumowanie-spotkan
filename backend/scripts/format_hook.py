"""PostToolUse hook: runs `ruff format` on the file just written/edited, if
it's a .py file under backend/. Invoked with the venv's own interpreter so
`ruff` (backend/requirements-dev.txt) resolves without extra PATH setup.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


def main() -> int:
    payload = json.load(sys.stdin)
    file_path = payload.get("tool_input", {}).get("file_path", "")
    if not file_path:
        return 0

    path = Path(file_path)
    if path.suffix != ".py":
        return 0
    if "backend" not in path.parts:
        return 0

    subprocess.run([sys.executable, "-m", "ruff", "format", str(path)], check=False)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
