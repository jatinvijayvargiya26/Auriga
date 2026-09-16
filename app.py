import json
import mimetypes
from datetime import date, datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import Lock
from urllib.parse import parse_qs, urlparse

from pricing_engine import PricingConfig, PricingError, SeatTier, calculate_booking
from price_importer import PriceImportReport, clean_csv, clean_price_list

PORT = 8000
ROOT = Path(__file__).parent
CONFIG_PATH = ROOT / "cinema_config.json"
DATA_LOCK = Lock()
BOOKED_SEATS_BY_DATE: dict[str, set[str]] = {}
BOOKINGS: list[dict] = []
BOOKING_SEQUENCE = 0
TODAY = date.today().isoformat()
PENDING_PRICE_IMPORT: PriceImportReport | None = None
IMPORT_HISTORY_PATH = ROOT / "price_import_history.json"
CLEAN_PRICE_EXPORT_PATH = ROOT / "clean-seat-prices.csv"


def load_config() -> dict:
    return json.loads(CONFIG_PATH.read_text())


def save_config(config: dict) -> None:
    CONFIG_PATH.write_text(json.dumps(config, indent=2) + "\n")


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


def build_seats(config: dict) -> dict:
    return {
        f"{row}{number}": {"id": f"{row}{number}", "row": row, "number": number, "tier": tier}
        for tier, category in config["categories"].items() if category.get("active", True)
        for row in category["rows"]
        for number in range(1, category["seats_per_row"] + 1)
    }


def active_offer(config: dict, show_date: str, movie_id: str) -> dict | None:
    for offer in config.get("offers", []):
        if not offer.get("active") or not offer.get("start_date") <= show_date <= offer.get("end_date"):
            continue
        if offer.get("applicable_movies") and movie_id not in offer["applicable_movies"]:
            continue
        if movie_id in offer.get("excluded_movies", {}):
            return None
        return offer
    return None


def get_show(config: dict, show_date: str, movie_id: str) -> dict:
    shows = [show for show in config.get("shows", []) if show.get("active", True) and show["date"] == show_date and show["movie_id"] == movie_id]
    if shows:
        return shows[0]
    movie = next((item for item in config["movies"] if item["id"] == movie_id), None)
    if not movie:
        raise PricingError("please choose a valid movie")
    return {"time": movie.get("show_time", "7:30 PM"), "price_overrides": {}}


def movie_for(config: dict, movie_id: str) -> dict:
    movie = next((item for item in config["movies"] if item["id"] == movie_id and item.get("active", True)), None)
    if not movie:
        raise PricingError("please choose a valid active movie")
    return movie


def pricing_for(config: dict, movie: dict, show: dict, show_date: str, movie_id: str, customer: dict) -> tuple[PricingConfig, dict]:
    prices = dict(movie["prices"])
    prices.update(show.get("price_overrides", {}))
    offer = active_offer(config, show_date, movie_id) if movie.get("discount_eligible", True) else None
    settings = config["settings"]
    pricing = PricingConfig(
        tiers={name: SeatTier(name, int(price), 9999) for name, price in prices.items()},
        festival_discount_paise=int(offer.get("discount_paise", 0)) if offer else 0,
        festival_discount_basis_points=int(offer.get("discount_basis_points", 0)) if offer else 0,
        member_discount_basis_points=int(settings["member_discount_basis_points"]),
        member_discount_cap_paise=int(settings["member_discount_cap_paise"]),
        convenience_fee_paise=int(settings["convenience_fee_paise"]),
        gst_basis_points=int(settings["gst_basis_points"]),
    )
    reason = None if offer else (movie.get("discount_reason") or ("No active eligible offer" if movie.get("demand") != "Highly Demanded" else "Highly Demanded Movie"))
    return pricing, {"offer": offer, "festival_reason": reason}


def seat_payload(config: dict, show_date: str) -> dict:
    seats = build_seats(config)
    booked = BOOKED_SEATS_BY_DATE.setdefault(show_date, set())
    return {"show_date": show_date, "seats": [{**seat, "status": "booked" if seat_id in booked else "available"} for seat_id, seat in seats.items()]}


def bill_response(bill, config: dict, pricing: PricingConfig, movie: dict, show: dict, customer: dict, show_date: str, booking_id: str, seat_ids: list[str], price_meta: dict) -> dict:
    categories = {tier: [seat for seat in seat_ids if build_seats(config)[seat]["tier"] == tier] for tier in config["categories"]}
    return {
        "booking_id": booking_id, "receipt_number": booking_id,
        "booking_date": datetime.now().strftime("%d %b %Y"), "booking_time": datetime.now().strftime("%I:%M %p"),
        "show_date": datetime.strptime(show_date, "%Y-%m-%d").strftime("%d %B %Y"),
        "customer": customer, "movie": {**movie, "show_time": show["time"]},
        "payment_status": "Booking confirmed", "festival_reason": price_meta["festival_reason"],
        "seats": {"seats": [{"id": seat} for seat in seat_ids], "categories": {key: value for key, value in categories.items() if value}},
        "line_items": [{"name": name, "quantity": quantity, "unit_price": money(pricing.tiers[name].price_paise), "total": money(total)} for name, quantity, total in bill.line_items if quantity],
        "ticket_count": bill.ticket_count, "base_ticket_total": money(bill.base_ticket_total_paise),
        "festival_discount": money(bill.festival_discount_paise), "member_discount": money(bill.member_discount_paise),
        "discounted_subtotal": money(bill.discounted_subtotal_paise), "convenience_fee": money(bill.convenience_fee_paise),
        "gst": money(bill.gst_paise), "final_booking_total": money(bill.final_booking_total_paise),
    }


class BillingHandler(BaseHTTPRequestHandler):
    def _json_body(self) -> dict:
        length = int(self.headers.get("Content-Length", "0"))
        return json.loads(self.rfile.read(length))

    def _send_json(self, payload: dict, status: int = 200) -> None:
        encoded = json.dumps(payload).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path == "/api/config":
            with DATA_LOCK: self._send_json(load_config())
            return
        if parsed.path == "/api/seats":
            show_date = parse_qs(parsed.query).get("date", [TODAY])[0]
            with DATA_LOCK: self._send_json(seat_payload(load_config(), show_date))
            return
        if parsed.path == "/api/bookings":
            with DATA_LOCK: self._send_json({"bookings": BOOKINGS})
            return
        if parsed.path == "/api/admin/import-history":
            if IMPORT_HISTORY_PATH.is_file():
                self._send_json(json.loads(IMPORT_HISTORY_PATH.read_text()))
            else:
                self._send_json({"history": []})
            return
        if parsed.path == "/api/admin/price-import/download":
            if PENDING_PRICE_IMPORT is None and not CLEAN_PRICE_EXPORT_PATH.is_file():
                self._send_json({"error": "No cleaned price list is ready"}, 404)
                return
            content = clean_csv(PENDING_PRICE_IMPORT).encode() if PENDING_PRICE_IMPORT else CLEAN_PRICE_EXPORT_PATH.read_bytes()
            self.send_response(200)
            self.send_header("Content-Type", "text/csv")
            self.send_header("Content-Disposition", "attachment; filename=clean-seat-prices.csv")
            self.send_header("Content-Length", str(len(content)))
            self.end_headers(); self.wfile.write(content)
            return
        relative = "index.html" if parsed.path == "/" else ("admin.html" if parsed.path == "/admin" else parsed.path.lstrip("/"))
        file_path = (ROOT / relative).resolve()
        if ROOT not in file_path.parents or not file_path.is_file():
            self._send_json({"error": "Not found"}, 404)
            return
        content = file_path.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", mimetypes.guess_type(file_path.name)[0] or "application/octet-stream")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(content)))
        self.end_headers(); self.wfile.write(content)

    def do_PUT(self) -> None:
        if self.path != "/api/admin/config": self._send_json({"error": "Not found"}, 404); return
        try:
            config = self._json_body()
            validate_config(config)
            with DATA_LOCK: save_config(config)
            self._send_json(config)
        except (ValueError, TypeError, KeyError, PricingError, json.JSONDecodeError) as error:
            self._send_json({"error": str(error)}, 400)

    def do_PATCH(self) -> None:
        global PENDING_PRICE_IMPORT
        if self.path == "/api/admin/price-import/preview":
            try:
                request = self._json_body()
                report = clean_price_list(str(request.get("content", "")), str(request.get("filename", "price-list.csv")))
                with DATA_LOCK: PENDING_PRICE_IMPORT = report
                self._send_json(report.to_dict())
            except (ValueError, TypeError) as error:
                self._send_json({"error": str(error)}, 400)
            return
        if self.path == "/api/admin/price-import/apply":
            if PENDING_PRICE_IMPORT is None:
                self._send_json({"error": "Review a price list before applying it"}, 400)
                return
            with DATA_LOCK:
                config = load_config()
                for name, price_paise in PENDING_PRICE_IMPORT.clean_prices.items():
                    if name in config["categories"]:
                        config["categories"][name]["price_paise"] = price_paise
                    else:
                        config["categories"][name] = {"price_paise": price_paise, "rows": ["I"], "seats_per_row": 7, "active": False}
                    for movie in config["movies"]:
                        movie.setdefault("prices", {})[name] = price_paise
                validate_config(config)
                save_config(config)
                summary = PENDING_PRICE_IMPORT.to_dict()
                CLEAN_PRICE_EXPORT_PATH.write_text(clean_csv(PENDING_PRICE_IMPORT))
                summary["status"] = "Completed with warnings" if summary["rejected"] or summary["conflicts_count"] else "Completed"
                history = json.loads(IMPORT_HISTORY_PATH.read_text()).get("history", []) if IMPORT_HISTORY_PATH.is_file() else []
                history.insert(0, {key: summary[key] for key in ("filename", "total_rows", "imported", "deduplicated", "rejected", "conflicts_count", "status")})
                IMPORT_HISTORY_PATH.write_text(json.dumps({"history": history}, indent=2) + "\n")
                PENDING_PRICE_IMPORT = None
            self._send_json(summary)
            return
        self._send_json({"error": "Not found"}, 404)

    def do_POST(self) -> None:
        if self.path != "/api/calculate": self._send_json({"error": "Not found"}, 404); return
        try:
            request = self._json_body(); show_date = request.get("show_date", TODAY)
            datetime.strptime(show_date, "%Y-%m-%d")
            customer = validate_customer(request.get("customer"))
            with DATA_LOCK: config = load_config()
            movie = movie_for(config, request.get("movie_id", "")); show = get_show(config, show_date, movie["id"])
            seats = build_seats(config); seat_ids = request.get("seats", [])
            if not seat_ids or len(set(seat_ids)) != len(seat_ids) or any(seat not in seats for seat in seat_ids): raise PricingError("selected seats are invalid or empty")
            with DATA_LOCK:
                booked = BOOKED_SEATS_BY_DATE.setdefault(show_date, set())
                if booked.intersection(seat_ids): raise PricingError("one or more selected seats are already booked")
            pricing, meta = pricing_for(config, movie, show, show_date, movie["id"], customer)
            quantities = {tier: sum(seats[item]["tier"] == tier for item in seat_ids) for tier in config["categories"]}
            bill = calculate_booking(quantities, pricing, is_member=customer["membership"] == "Member")
            with DATA_LOCK:
                global BOOKING_SEQUENCE
                BOOKED_SEATS_BY_DATE[show_date].update(seat_ids); BOOKING_SEQUENCE += 1
                booking_id = f"CVM-{show_date.replace('-', '')}-{BOOKING_SEQUENCE:03d}"
                response = bill_response(bill, config, pricing, movie, show, customer, show_date, booking_id, seat_ids, meta)
                BOOKINGS.append(response)
            self._send_json(response)
        except (ValueError, TypeError, KeyError, PricingError, json.JSONDecodeError) as error:
            self._send_json({"error": str(error)}, 400)


def validate_config(config: dict) -> None:
    if not isinstance(config, dict) or not config.get("movies") or not config.get("categories"): raise PricingError("movies and categories are required")
    settings = config.get("settings", {})
    for key in ("member_discount_basis_points", "member_discount_cap_paise", "convenience_fee_paise", "gst_basis_points"):
        value = int(settings.get(key, 0))
        if value < 0 or (key in ("gst_basis_points", "member_discount_basis_points") and value > 10000): raise PricingError(f"invalid {key}")
    movie_ids = set()
    for movie in config["movies"]:
        if not movie.get("name") or movie.get("id") in movie_ids: raise PricingError("movie names and IDs must be unique")
        movie_ids.add(movie["id"])
        if any(int(value) < 0 for value in movie.get("prices", {}).values()): raise PricingError("movie prices cannot be negative")
    for category in config["categories"].values():
        if not category.get("rows") or int(category.get("seats_per_row", 0)) <= 0: raise PricingError("invalid seat configuration")
    for offer in config.get("offers", []):
        try:
            start = datetime.strptime(offer["start_date"], "%Y-%m-%d")
            end = datetime.strptime(offer["end_date"], "%Y-%m-%d")
        except (KeyError, ValueError):
            raise PricingError("festival dates must use YYYY-MM-DD")
        if end < start or int(offer.get("discount_paise", 0)) < 0 or int(offer.get("discount_basis_points", 0)) < 0 or int(offer.get("discount_basis_points", 0)) > 10000:
            raise PricingError("invalid festival offer dates or discount")


if __name__ == "__main__":
    print(f"CineVista management system running at http://127.0.0.1:{PORT}")
    ThreadingHTTPServer(("127.0.0.1", PORT), BillingHandler).serve_forever()
