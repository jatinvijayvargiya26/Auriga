"""Paisa-accurate multiplex ticket pricing."""

from dataclasses import dataclass
from typing import Mapping


class PricingError(ValueError):
    """Raised when a booking cannot be priced."""


@dataclass(frozen=True)
class SeatTier:
    name: str
    price_paise: int
    available_quantity: int


@dataclass(frozen=True)
class PricingConfig:
    tiers: Mapping[str, SeatTier]
    festival_discount_paise: int = 0
    festival_discount_basis_points: int = 0
    member_discount_basis_points: int = 0
    member_discount_cap_paise: int = 0
    convenience_fee_paise: int = 0
    gst_basis_points: int = 0


@dataclass(frozen=True)
class Bill:
    line_items: tuple[tuple[str, int, int], ...]
    ticket_count: int
    base_ticket_total_paise: int
    festival_discount_paise: int
    member_discount_paise: int
    discounted_subtotal_paise: int
    convenience_fee_paise: int
    gst_paise: int
    final_booking_total_paise: int

    @property
    def total_rupees(self) -> str:
        return format_paise(self.final_booking_total_paise)


def _validate_non_negative(name: str, value: int) -> None:
    if value < 0:
        raise PricingError(f"{name} cannot be negative")


def _percentage_paise(amount_paise: int, basis_points: int) -> int:
    return (amount_paise * basis_points + 5000) // 10000


def format_paise(amount_paise: int) -> str:
    _validate_non_negative("amount_paise", amount_paise)
    return f"₹{amount_paise // 100}.{amount_paise % 100:02d}"


def calculate_booking(
    quantities: Mapping[str, int],
    config: PricingConfig,
    *,
    is_member: bool = False,
) -> Bill:
    """Calculate a booking in this order: tickets, discounts, fee, then GST."""
    for field_name in (
        "festival_discount_paise",
        "festival_discount_basis_points",
        "member_discount_basis_points",
        "member_discount_cap_paise",
        "convenience_fee_paise",
        "gst_basis_points",
    ):
        _validate_non_negative(field_name, getattr(config, field_name))

    if config.member_discount_basis_points > 10000:
        raise PricingError("member discount cannot exceed 100 percent")
    if config.festival_discount_basis_points > 10000:
        raise PricingError("festival discount cannot exceed 100 percent")
    if config.gst_basis_points > 10000:
        raise PricingError("GST cannot exceed 100 percent")

    line_items: list[tuple[str, int, int]] = []
    ticket_count = 0
    base_total = 0

    for tier_name, quantity in quantities.items():
        if tier_name not in config.tiers:
            raise PricingError(f"unknown seat tier: {tier_name}")
        if quantity < 0:
            raise PricingError(f"quantity for {tier_name} cannot be negative")

        tier = config.tiers[tier_name]
        _validate_non_negative(f"price for {tier_name}", tier.price_paise)
        _validate_non_negative(f"availability for {tier_name}", tier.available_quantity)
        if quantity > tier.available_quantity:
            raise PricingError(
                f"{tier_name} has only {tier.available_quantity} ticket(s) available"
            )

        line_total = tier.price_paise * quantity
        line_items.append((tier.name, quantity, line_total))
        ticket_count += quantity
        base_total += line_total

    if ticket_count == 0:
        raise PricingError("at least one ticket is required")

    festival_percentage_discount = _percentage_paise(base_total, config.festival_discount_basis_points)
    festival_discount = min(config.festival_discount_paise + festival_percentage_discount, base_total)
    after_festival = base_total - festival_discount

    member_discount = 0
    if is_member:
        member_discount = min(
            _percentage_paise(after_festival, config.member_discount_basis_points),
            config.member_discount_cap_paise,
            after_festival,
        )

    discounted_subtotal = after_festival - member_discount
    convenience_fee = config.convenience_fee_paise * ticket_count
    taxable_amount = discounted_subtotal + convenience_fee
    gst = _percentage_paise(taxable_amount, config.gst_basis_points)

    return Bill(
        line_items=tuple(line_items),
        ticket_count=ticket_count,
        base_ticket_total_paise=base_total,
        festival_discount_paise=festival_discount,
        member_discount_paise=member_discount,
        discounted_subtotal_paise=discounted_subtotal,
        convenience_fee_paise=convenience_fee,
        gst_paise=gst,
        final_booking_total_paise=taxable_amount + gst,
    )
