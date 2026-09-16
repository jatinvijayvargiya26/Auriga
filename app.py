import json
import mimetypes
from threading import Lock
from datetime import date, datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from pricing_engine import PricingConfig, PricingError, SeatTier, calculate_booking


PORT = 8000
ROOT = Path(__file__).parent
CONFIG = PricingConfig(
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
MOVIES = {
    "interstellar": {
        "name": "Interstellar",
        "genre": "Sci-Fi",
        "experience": "Mind Bending",
        "show_time": "7:30 PM",
    },
    "midnight-run": {
        "name": "Midnight Run",
        "genre": "Thriller",
        "experience": "Edge of Your Seat",
        "show_time": "9:45 PM",
    },
    "the-last-laugh": {
        "name": "The Last Laugh",
        "genre": "Comedy",
        "experience": "Feel Good",
        "show_time": "6:15 PM",
    },
}
SEAT_LAYOUT = {
    "Silver": ("A", "B", "C"),
    "Gold": ("D", "E", "F"),
    "Recliner": ("G", "H"),
}
SEATS = {
    f"{row}{number}": {"id": f"{row}{number}", "row": row, "number": number, "tier": tier}
    for tier, rows in SEAT_LAYOUT.items()
    for row in rows
    for number in range(1, 8)
}
TODAY = date.today().isoformat()
BOOKED_SEATS_BY_DATE = {TODAY: {"A2", "A5", "B3", "C6"}}
BOOKING_SEQUENCE = 0
SEAT_LOCK = Lock()


def money(amount_paise: int) -> str:
    return f"{amount_paise // 100}.{amount_paise % 100:02d}"


def validate_customer(customer: object) -> dict:
    if not isinstance(customer, dict):
        raise PricingError("please enter customer details")
    name = str(customer.get("name", "")).strip()
    mobile = str(customer.get("mobile", "")).strip()
    email = str(customer.get("email", "")).strip()
    membership = customer.get("membership")
    if not name:
        raise PricingError("full name is required")
    if not mobile.isdigit() or len(mobile) not in (10, 11, 12):
        raise PricingError("mobile number must contain 10 to 12 digits")
    if email and ("@" not in email or "." not in email.rsplit("@", 1)[-1]):
        raise PricingError("please enter a valid email address")
    if membership not in ("Member", "Non-Member"):
        raise PricingError("please select membership status")
    return {"name": name, "mobile": mobile, "email": email, "membership": membership}


def bill_response(bill, movie: dict, is_member: bool, customer: dict, show_date: str, booking_id: str) -> dict:
    booking_time = datetime.now().astimezone()
    return {
        "receipt_number": booking_id,
        "booking_id": booking_id,
        "booking_date": booking_time.strftime("%d %b %Y"),
        "booking_time": booking_time.strftime("%I:%M %p"),
        "show_date": datetime.strptime(show_date, "%Y-%m-%d").strftime("%d %B %Y"),
        "customer": customer,
        "movie": movie,
        "payment_status": "Payment pending",
        "member_booking": is_member,
        "line_items": [
            {
                "name": name,
                "quantity": quantity,
                "unit_price": money(CONFIG.tiers[name].price_paise),
                "total": money(total),
            }
            for name, quantity, total in bill.line_items
            if quantity > 0
        ],
        "ticket_count": bill.ticket_count,
        "base_ticket_total": money(bill.base_ticket_total_paise),
        "festival_discount": money(bill.festival_discount_paise),
        "member_discount": money(bill.member_discount_paise),
        "discounted_subtotal": money(bill.discounted_subtotal_paise),
        "convenience_fee": money(bill.convenience_fee_paise),
        "gst": money(bill.gst_paise),
        "final_booking_total": money(bill.final_booking_total_paise),
    }


def seat_response(seat_ids: list[str]) -> dict:
    categories = {
        tier: [seat_id for seat_id in seat_ids if SEATS[seat_id]["tier"] == tier]
        for tier in SEAT_LAYOUT
    }
    return {
        "seats": [SEATS[seat_id] for seat_id in seat_ids],
        "categories": {tier: ids for tier, ids in categories.items() if ids},
    }


class BillingHandler(BaseHTTPRequestHandler):
    def _send_json(self, payload: dict, status: int = 200) -> None:
        encoded = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)

    def do_GET(self) -> None:
        if self.path == "/api/seats":
            self._handle_booking(TODAY)
            return
        if self.path.startswith("/api/seats?"):
            show_date = self.path.split("date=", 1)[-1].split("&", 1)[0]
            self._handle_booking(show_date)
            return
        requested_path = self.path.split("?", 1)[0]
        relative_path = "index.html" if requested_path == "/" else requested_path.lstrip("/")
        file_path = (ROOT / relative_path).resolve()
        if ROOT not in file_path.parents and file_path != ROOT:
            self._send_json({"error": "Not found"}, 404)
            return

        if not file_path.is_file():
            self._send_json({"error": "Not found"}, 404)
            return

        content = file_path.read_bytes()
        self.send_response(200)
        content_type = mimetypes.guess_type(file_path.name)[0] or "application/octet-stream"
        self.send_header("Content-Type", content_type)
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(content)))
        self.end_headers()
        self.wfile.write(content)

    def do_POST(self) -> None:
        if self.path == "/api/seats":
            self._handle_booking(TODAY)
            return
        if self.path != "/api/calculate":
            self._send_json({"error": "Not found"}, 404)
            return

        try:
            length = int(self.headers.get("Content-Length", "0"))
            request = json.loads(self.rfile.read(length))
            show_date = request.get("show_date", TODAY)
            try:
                datetime.strptime(show_date, "%Y-%m-%d")
            except (TypeError, ValueError):
                raise PricingError("please choose a valid show date")
            customer = validate_customer(request.get("customer"))
            movie = MOVIES.get(request.get("movie_id", "interstellar"))
            if movie is None:
                raise PricingError("please choose a valid movie")
            seat_ids = request.get("seats")
            if not isinstance(seat_ids, list) or not seat_ids:
                raise PricingError("select at least one available seat")
            if len(set(seat_ids)) != len(seat_ids):
                raise PricingError("a seat cannot be selected twice")
            if any(not isinstance(seat_id, str) or seat_id not in SEATS for seat_id in seat_ids):
                raise PricingError("one or more selected seats are invalid")
            with SEAT_LOCK:
                booked_seats = BOOKED_SEATS_BY_DATE.setdefault(show_date, set())
                if any(seat_id in booked_seats for seat_id in seat_ids):
                    raise PricingError("one or more selected seats are already booked")
                quantities = {
                    tier_name: sum(SEATS[seat_id]["tier"] == tier_name for seat_id in seat_ids)
                    for tier_name in CONFIG.tiers
                }
            bill = calculate_booking(
                quantities,
                CONFIG,
                is_member=customer["membership"] == "Member",
            )
            with SEAT_LOCK:
                BOOKED_SEATS_BY_DATE[show_date].update(seat_ids)
                global BOOKING_SEQUENCE
                BOOKING_SEQUENCE += 1
                booking_id = f"CVM-{show_date.replace('-', '')}-{BOOKING_SEQUENCE:03d}"
            response = bill_response(
                bill, movie, customer["membership"] == "Member", customer, show_date, booking_id
            )
            response.update({"seats": seat_response(seat_ids)})
            self._send_json(response)
        except (ValueError, TypeError, json.JSONDecodeError, PricingError) as error:
            self._send_json({"error": str(error)}, 400)

    def _handle_booking(self, show_date: str) -> None:
        try:
            datetime.strptime(show_date, "%Y-%m-%d")
        except (TypeError, ValueError):
            self._send_json({"error": "please choose a valid show date"}, 400)
            return
        with SEAT_LOCK:
            booked_seats = BOOKED_SEATS_BY_DATE.setdefault(show_date, set())
            self._send_json({
                "show_date": show_date,
                "layout": SEAT_LAYOUT,
                "seats": [
                    {**seat, "status": "booked" if seat_id in booked_seats else "available"}
                    for seat_id, seat in SEATS.items()
                ],
            })

    def log_message(self, format_string: str, *args) -> None:
        print(f"{self.address_string()} - {format_string % args}")


if __name__ == "__main__":
    server = ThreadingHTTPServer(("127.0.0.1", PORT), BillingHandler)
    print(f"Auriga billing desk running at http://127.0.0.1:{PORT}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping billing desk")
    finally:
        server.server_close()
