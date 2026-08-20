import unittest

from waterprice.compare import cheapest, prepare, rank
from waterprice.models import Offer


def offer(source, title, price):
    return Offer(source=source, title=title, price=price, mall=source)


class PrepareTest(unittest.TestCase):
    def test_computes_unit_price(self):
        prepared = prepare([offer("naver", "삼다수 2L 12병", 12000)])
        self.assertEqual(len(prepared), 1)
        self.assertEqual(prepared[0].liters, 24.0)
        self.assertEqual(prepared[0].unit_price, 500.0)

    def test_drops_non_water_products(self):
        self.assertEqual(prepare([offer("naver", "정수기 필터 2L", 9900)]), [])

    def test_drops_unknown_volume_by_default(self):
        self.assertEqual(prepare([offer("naver", "생수 대용량", 9900)]), [])

    def test_keeps_unknown_volume_when_requested(self):
        prepared = prepare([offer("naver", "생수 대용량", 9900)], include_unknown=True)
        self.assertEqual(len(prepared), 1)
        self.assertIsNone(prepared[0].unit_price)

    def test_min_liters_filter(self):
        self.assertEqual(prepare([offer("naver", "생수 500ml", 900)], min_liters=2.0), [])


class RankTest(unittest.TestCase):
    def setUp(self):
        self.offers = prepare([
            offer("coupang", "삼다수 2L 6병", 7200),      # 600원/L
            offer("naver", "백산수 2L 12병", 10800),      # 450원/L
            offer("coupang", "아이시스 500ml 20입", 4000),  # 400원/L
        ])

    def test_sorts_by_unit_price(self):
        self.assertEqual([o.unit_price for o in rank(self.offers)], [400.0, 450.0, 600.0])

    def test_sorts_by_display_price(self):
        self.assertEqual([o.price for o in rank(self.offers, by="price")], [4000, 7200, 10800])

    def test_unknown_unit_price_goes_last(self):
        mixed = prepare(
            [offer("naver", "생수 대용량", 100), offer("naver", "삼다수 2L 6병", 7200)],
            include_unknown=True,
        )
        self.assertIsNone(rank(mixed)[-1].unit_price)

    def test_cheapest_per_source(self):
        self.assertEqual(cheapest(self.offers, "coupang").unit_price, 400.0)
        self.assertEqual(cheapest(self.offers, "naver").unit_price, 450.0)
        self.assertIsNone(cheapest(self.offers, "gmarket"))


if __name__ == "__main__":
    unittest.main()
