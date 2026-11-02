"""Non-counted native host check; never starts Codex, login, or a model call."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from runtime.assurance.native_host import NativeHostError, require_native_host


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--codex", required=True, type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    try:
        result = {"status": "PASS", **require_native_host(args.codex)}
    except NativeHostError as error:
        result = {"status": "BLOCKED", "reasonCode": str(error), "diagnostic": error.diagnostic.to_dict(), "modelInvoked": False}
    result.update(kind="NON_COUNTED_NATIVE_HOST_CAPABILITY", profileAuthentication="NOT_CHECKED",
                  pluginDiscovery="NOT_CHECKED", productTaskExecution="NOT_TESTED")
    if args.output:
        with args.output.open("x", encoding="utf-8") as handle:
            json.dump(result, handle, indent=2)
    print(json.dumps(result, indent=2))
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
