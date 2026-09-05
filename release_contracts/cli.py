from __future__ import annotations

import argparse
from pathlib import Path

from .model import load_claims, load_compatibility, validate_release_data


def main() -> int:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)
    validate = sub.add_parser("validate")
    validate.add_argument("--claims", required=True)
    validate.add_argument("--compatibility", required=True)
    args = parser.parse_args()

    claims = load_claims(Path(args.claims))
    compatibility = load_compatibility(Path(args.compatibility))
    errors = validate_release_data(claims, compatibility)
    if errors:
        for error in errors:
            print(f"FAIL: {error}")
        return 1
    print(
        f"PASS: {len(claims)} claims and {len(compatibility)} compatibility surfaces validated"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
