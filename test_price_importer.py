import unittest

from price_importer import clean_csv, clean_price_list, normalize_name, parse_price_paise


MESSY = """Seat Class,Price
Silver,180
silver, ₹180
SILVER,180.00
 Silver , ₹180.00
Gold,250
gold, ₹250.00
Recliner,450
RECLINER,450
Silver,
Gold,-250
,,
Premium,₹550
"""


class PriceImporterTests(unittest.TestCase):
    def test_normalizes_names_and_currency(self) -> None:
        self.assertEqual(normalize_name("  silver   "), "Silver")
        self.assertEqual(parse_price_paise("Rs. 180.00"), 18000)
        self.assertEqual(parse_price_paise("INR 1,250"), 125000)

    def test_reports_clean_rows_duplicates_rejections_and_conflict(self) -> None:
        report = clean_price_list(MESSY)
        self.assertEqual(report.clean_prices, {"Silver": 18000, "Gold": 25000, "Recliner": 45000, "Premium": 55000})
        self.assertEqual(report.imported, 4)
        self.assertEqual(report.deduplicated, 5)
        self.assertEqual(report.rejected, 3)
        self.assertEqual(report.conflict_count, 0)
        self.assertEqual([row.status for row in report.rows if row.raw_price == "-250"], ["Rejected"])

    def test_conflicting_duplicate_is_not_cleaned_automatically(self) -> None:
        report = clean_price_list("Seat Class,Price\nSilver,180\nsilver,200\nSILVER,180\n")
        self.assertEqual(report.clean_prices, {})
        self.assertEqual(report.conflicts, {"Silver": [2, 3, 4]})
        self.assertTrue(all(row.status == "Conflict" for row in report.rows))

    def test_rejects_missing_columns_and_exports_clean_data(self) -> None:
        with self.assertRaisesRegex(ValueError, "Seat Class and Price"):
            clean_price_list("Name,Amount\nSilver,180")
        report = clean_price_list("Seat Class,Price\nSilver,180\n")
        self.assertEqual(clean_csv(report), "Seat Class,Price\r\nSilver,180.00\r\n")


if __name__ == "__main__":
    unittest.main()
