# Auriga: Multiplex Pricing Engine

This project implements the booking flow:

```text
Ticket price
	-> seat-tier availability
	-> base ticket total
	-> festival flat discount
	-> member percentage discount, capped
	-> discounted subtotal
	-> per-ticket convenience fee
	-> GST
	-> final booking total
```

## Design

- Money is represented as integer paisa, avoiding floating-point errors.
- Seat tiers, prices, capacity, discounts, fees, and GST are configuration-driven.
- A booking is rejected when a tier is unknown, unavailable, or has an invalid quantity.
- Discounts cannot reduce the ticket subtotal below zero.
- Member discount rates and GST use basis points: `1000` means 10%.
- GST is calculated on the discounted subtotal plus the convenience fee, then rounded to the nearest paisa.
- `Bill` returns every amount needed for a line-by-line customer receipt.

## Run the tests

```bash
python -m unittest -v
```

## Run the local billing website

```bash
python app.py
```

Open [http://127.0.0.1:8000](http://127.0.0.1:8000) in your browser. Select ticket quantities, optionally enable the member offer, and press **Calculate receipt**. The page sends the booking to the same pricing engine covered by the tests.

The booking desk now uses a configurable auditorium with date-scoped availability. Enter customer details, choose a show date, select seats, and use **Confirm booking / Generate bill**. Bookings are stored in the running server session by show date, so a normal browser refresh preserves availability; **New day / Refresh** moves to the next date and clears temporary form selection. Customer details and the unique `CVM-YYYYMMDD-NNN` booking ID are included on screen and in the printable receipt.

## Example

```python
from pricing_engine import PricingConfig, SeatTier, calculate_booking

config = PricingConfig(
		tiers={
				"Silver": SeatTier("Silver", 20000, 100),
				"Gold": SeatTier("Gold", 30000, 50),
				"Recliner": SeatTier("Recliner", 50000, 10),
		},
		festival_discount_paise=10000,
		member_discount_basis_points=1000,
		member_discount_cap_paise=5000,
		convenience_fee_paise=300,
		gst_basis_points=1800,
)

bill = calculate_booking({"Gold": 2, "Silver": 1}, config, is_member=True)
print(bill.total_rupees)
```