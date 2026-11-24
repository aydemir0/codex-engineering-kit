import unittest

from quote import quote


class QuoteTests(unittest.TestCase):
    def test_discount_threshold(self) -> None:
        self.assertEqual(quote(2), {"totalCents": 2500})
        self.assertEqual(quote(3), {"totalCents": 3375})

    def test_invalid_quantity(self) -> None:
        for quantity in (0, -1, 10_001, True, "3", 3.5):
            with self.subTest(quantity=quantity):
                self.assertEqual(quote(quantity), {"error": "invalid-quantity"})
