#!/usr/bin/env python3
"""Generate infra/.env from .env.example with development defaults.

Idempotent: refuses to overwrite an existing .env unless --force is passed.
Run via `make env` or directly:

    python scripts/gen-env.py [--force]

The SECRET_KEY is freshly generated each time the file is written.
"""

from __future__ import annotations

import argparse
import secrets
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
EXAMPLE = REPO_ROOT / ".env.example"
DEFAULT_DEST = REPO_ROOT / "infra" / ".env"

# (example line prefix, dev replacement) — applied in order over the example.
DEV_OVERRIDES: dict[str, str] = {
    "APP_ENV=": "APP_ENV=development",
    "DEBUG=": "DEBUG=true",
    "CORS_ORIGINS=": (
        "CORS_ORIGINS=http://localhost:5173,http://localhost:8080"
    ),
    "MAX_UPLOAD_SIZE=": "MAX_UPLOAD_SIZE=100MB",
}


def render_env(example: Path) -> str:
    """Return the dev .env content derived from the example file."""
    if not example.is_file():
        raise FileNotFoundError(f"missing {example} — cannot generate .env")

    lines: list[str] = []
    secret = secrets.token_urlsafe(32)
    for line in example.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            lines.append(line)
            continue
        key, _, _ = stripped.partition("=")
        if key == "SECRET_KEY":
            lines.append(f"SECRET_KEY={secret}")
        else:
            lines.append(DEV_OVERRIDES.get(f"{key}=", line))

    # Safety net: never emit an empty SECRET_KEY, even if the example lacks it.
    if not any(l.startswith("SECRET_KEY=") and len(l) > len("SECRET_KEY=") for l in lines):
        lines.append(f"SECRET_KEY={secret}")
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--force",
        action="store_true",
        help="overwrite an existing .env instead of skipping",
    )
    args = parser.parse_args(argv)

    if DEFAULT_DEST.is_file() and not args.force:
        print(f"[SKIP] {DEFAULT_DEST} already exists (use --force to regenerate)")
        return 0

    try:
        content = render_env(EXAMPLE)
    except FileNotFoundError as e:
        print(f"[ERROR] {e}", file=sys.stderr)
        return 1

    DEFAULT_DEST.parent.mkdir(parents=True, exist_ok=True)
    DEFAULT_DEST.write_text(content, encoding="utf-8")
    print(f"[OK] Generated {DEFAULT_DEST} (dev defaults + random SECRET_KEY)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
