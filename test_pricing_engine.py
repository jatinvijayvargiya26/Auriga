import unittest

from pricing_engine import PricingConfig, PricingError, SeatTier, calculate_booking


class PricingEngineTests(unittest.TestCase):
    def setUp(self) -> None:
        self.config = PricingConfig(
            tiers={
                "Silver": SeatTier("Silver", 20000, 10),
                "Gold": SeatTier("Gold", 30000, 5),
                "Recliner": SeatTier("Recliner", 50000, 2),
            },
            festival_discount_paise=10000,
            member_discount_basis_points=1000,
            member_discount_cap_paise=5000,
            convenience_fee_paise=300,
            gst_basis_points=1800,
        )

    def test_calculates_the_full_pipeline(self) -> None:
        bill = calculate_booking(
            {"Silver": 2, "Gold": 1}, self.config, is_member=True
        )

        self.assertEqual(bill.base_ticket_total_paise, 70000)
        self.assertEqual(bill.festival_discount_paise, 10000)
        self.assertEqual(bill.member_discount_paise, 5000)
        self.assertEqual(bill.discounted_subtotal_paise, 55000)
        self.assertEqual(bill.convenience_fee_paise, 900)
        self.assertEqual(bill.gst_paise, 10062)
        self.assertEqual(bill.final_booking_total_paise, 65962)
        self.assertEqual(bill.total_rupees, "₹659.62")

    def test_rejects_sold_out_tier(self) -> None:
        with self.assertRaisesRegex(PricingError, r"only 2 ticket\(s\) available"):
            calculate_booking({"Recliner": 3}, self.config)

    def test_member_discount_is_capped(self) -> None:
        config = PricingConfig(
            tiers={"Gold": SeatTier("Gold", 100000, 2)},
            member_discount_basis_points=5000,
            member_discount_cap_paise=1000,
        )

        bill = calculate_booking({"Gold": 1}, config, is_member=True)

        self.assertEqual(bill.member_discount_paise, 1000)

    def test_rejects_empty_booking(self) -> None:
        with self.assertRaisesRegex(PricingError, "at least one ticket"):
            calculate_booking({}, self.config)


if __name__ == "__main__":
    unittest.main()
