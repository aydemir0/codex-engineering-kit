from __future__ import annotations

import unittest

from src.calculator import divide


class CalculatorTests(unittest.TestCase):
    def test_normal_division_is_preserved(self) -> None:
        self.assertEqual(divide(8, 2), 4)

    def test_divide_by_zero_raises_value_error(self) -> None:
        with self.assertRaisesRegex(
            ValueError,
            "^division by zero$",
        ):
            divide(8, 0)


if __name__ == "__main__":
    unittest.main()
