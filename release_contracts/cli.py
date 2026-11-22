from __future__ import annotations

import argparse
from pathlib import Path

from .model import load_claims, load_compatibility, validate_release_data


CI_CLAIMS = "release_contracts/claims.json"
CI_COMPATIBILITY = "release_contracts/compatibility.json"


def _ci_contract_paths(claims: str, compatibility: str) -> tuple[Path, Path]:
    """Resolve CI-controlled static paths, never filesystem-touch raw CLI paths.

    CI only accepts these two reviewable, fixed repository files. A developer
    may still supply other local JSON explicitly in normal operator mode.
    """
    if claims != CI_CLAIMS or compatibility != CI_COMPATIBILITY:
        raise ValueError("CI release inputs must match the fixed repository manifest paths")
    root = Path.cwd().resolve(strict=True)
    if not root.is_dir():
        raise ValueError("CI working directory unavailable")
    claim_file = root / "release_contracts" / "claims.json"
    compatibility_file = root / "release_contracts" / "compatibility.json"
    for target in (claim_file, compatibility_file):
        # Only trusted, code-constant paths reach filesystem operations.
        # The resolved target must not escape via a symlink or junction.
        if not target.resolve(strict=True).is_relative_to(root) or not target.is_file():
            raise ValueError("CI release input escapes repository or is unavailable")
    return claim_file, compatibility_file


def main() -> int:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)
    validate = sub.add_parser("validate")
    validate.add_argument("--claims", required=True)
    validate.add_argument("--compatibility", required=True)
    validate.add_argument(
        "--ci-contract-files",
        action="store_true",
        help="In CI, only allow the two statically named repository release JSON files.",
    )
    args = parser.parse_args()

    try:
        if args.ci_contract_files:
            claims_path, compatibility_path = _ci_contract_paths(
                args.claims, args.compatibility
            )
        else:
            # Explicit local operator file selection, not a network service.
            claims_path = Path(args.claims)
            compatibility_path = Path(args.compatibility)
        claims = load_claims(claims_path)
        compatibility = load_compatibility(compatibility_path)
    except (OSError, ValueError) as exc:
        # Never interpolate operator paths or raw JSON into CI error output.
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
