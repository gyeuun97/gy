import unittest

from waterprice.volume import parse_counts, parse_liters, parse_unit_liters


class ParseUnitLitersTest(unittest.TestCase):
    def test_liter_and_milliliter(self):
        self.assertEqual(parse_unit_liters("삼다수 2L"), 2.0)
        self.assertEqual(parse_unit_liters("백산수 500ml"), 0.5)
        self.assertEqual(parse_unit_liters("생수 1.5리터"), 1.5)
        self.assertEqual(parse_unit_liters("생수 500 mL"), 0.5)

    def test_ignores_brand_numbers_without_unit(self):
        self.assertEqual(parse_unit_liters("아이시스 8.0 2L"), 2.0)

    def test_rejects_out_of_range_volume(self):
        self.assertIsNone(parse_unit_liters("업소용 물탱크 500L"))
        self.assertIsNone(parse_unit_liters("샘플 10ml"))

    def test_no_volume(self):
        self.assertIsNone(parse_unit_liters("그냥 생수"))


class ParseCountsTest(unittest.TestCase):
    def test_korean_count_units(self):
        self.assertEqual(parse_counts("2L 12병"), [12])
        self.assertEqual(parse_counts("500ml 20입"), [20])
        self.assertEqual(parse_counts("300ml 40pet"), [40])

    def test_multiplier_form(self):
        self.assertEqual(parse_counts("2L x 24"), [24])
        self.assertEqual(parse_counts("2L *6"), [6])

    def test_ignores_month_and_single_count(self):
        self.assertEqual(parse_counts("유통기한 24개월"), [])
        self.assertEqual(parse_counts("2L 1병"), [])

    def test_ignores_absurd_count(self):
        self.assertEqual(parse_counts("1000개"), [])


class ParseLitersTest(unittest.TestCase):
    def test_pack_totals(self):
        self.assertEqual(parse_liters("제주 삼다수 2L 12병"), 24.0)
        self.assertEqual(parse_liters("백산수 500ml 20입"), 10.0)
        self.assertEqual(parse_liters("무라벨 생수 300ml 40pet"), 12.0)

    def test_nested_counts_multiply(self):
        self.assertEqual(parse_liters("생수 2L 6개 x 2박스"), 24.0)

    def test_duplicate_count_counted_once(self):
        # "24개입 x24" 는 같은 수량을 두 번 적은 것이므로 24번만 곱한다.
        self.assertEqual(parse_liters("스파클 2L 24개입 x24"), 48.0)

    def test_single_bottle(self):
        self.assertEqual(parse_liters("삼다수 2L"), 2.0)

    def test_unparsable(self):
        self.assertIsNone(parse_liters("평범한 생수"))
        self.assertIsNone(parse_liters(""))


if __name__ == "__main__":
    unittest.main()
