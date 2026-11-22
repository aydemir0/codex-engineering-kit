from __future__ import annotations

import argparse
import json
from pathlib import Path

from .model import load_claims, load_compatibility, validate_release_data


def _bounded_input(candidate: Path, root: Path) -> Path:
    """Reject traversal, absolute outsiders and symlink escapes for CI data."""
    trusted_root = root.resolve(strict=True)
    if not trusted_root.is_dir():
        raise ValueError("release input root must be a directory")
    resolved = candidate.resolve(strict=True)
    if not resolved.is_relative_to(trusted_root):
        raise ValueError("release input must remain inside the configured root")
    if resolved.suffix.casefold() != ".json" or not resolved.is_file():
        raise ValueError("release input must be a JSON file")
    return resolved


def main() -> int:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)
    validate = sub.add_parser("validate")
    validate.add_argument("--claims", required=True)
    validate.add_argument("--compatibility", required=True)
    validate.add_argument(
        "--input-root",
        type=Path,
        default=None,
        help="Constrain CI JSON inputs to this directory (symlink escapes rejected).",
    )
    args = parser.parse_args()

    try:
        claims_path = Path(args.claims)
        compatibility_path = Path(args.compatibility)
        if args.input_root is not None:
            claims_path = _bounded_input(claims_path, args.input_root)
            compatibility_path = _bounded_input(compatibility_path, args.input_root)
        claims = load_claims(claims_path)
        compatibility = load_compatibility(compatibility_path)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        # Do not put operator-supplied filenames or raw JSON into CI logs.
        print(f"FAIL: release input could not be read or parsed ({type(exc).__name__})")
        return 1
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
