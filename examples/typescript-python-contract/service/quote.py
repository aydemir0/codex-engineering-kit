"""Price quote endpoint over JSON on standard input and output."""

import json
import sys


def quote(quantity: object) -> dict[str, int | str]:
    if type(quantity) is not int or not 1 <= quantity <= 10_000:
        return {"error": "invalid-quantity"}
    unit_cents = 1125 if quantity >= 3 else 1250
    return {"totalCents": quantity * unit_cents}


if __name__ == "__main__":
    request = json.load(sys.stdin)
    print(json.dumps(quote(request.get("quantity"))))
