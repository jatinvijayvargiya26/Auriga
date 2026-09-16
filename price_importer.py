"""Clean and audit messy seat-class price-list CSV data."""

import csv
import io
import re
from collections import defaultdict
from dataclasses import asdict, dataclass
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP


@dataclass(frozen=True)
class ImportRow:
    row_number: int
    raw_seat_class: str
    raw_price: str
    normalized_seat_class: str
    normalized_price_paise: int | None
    status: str
    reason: str


@dataclass(frozen=True)
class PriceImportReport:
    filename: str
    rows: tuple[ImportRow, ...]
    clean_prices: dict[str, int]
    conflicts: dict[str, list[int]]
    imported: int
    deduplicated: int
    rejected: int

    @property
    def conflict_count(self) -> int:
        return len(self.conflicts)

    def to_dict(self) -> dict:
        return {
            "filename": self.filename,
            "rows": [asdict(row) for row in self.rows],
            "clean_prices": self.clean_prices,
            "conflicts": self.conflicts,
            "imported": self.imported,
            "deduplicated": self.deduplicated,
            "rejected": self.rejected,
            "conflicts_count": self.conflict_count,
            "total_rows": len(self.rows),
        }


def normalize_name(value: str) -> str:
    return " ".join(value.strip().split()).title()


def parse_price_paise(value: str) -> int:
    raw = value.strip()
    if not raw:
        raise ValueError("Missing price")
    if raw.startswith("-") or re.search(r"\(\s*[-\d]", raw):
        raise ValueError("Negative price")
    cleaned = re.sub(r"(?i)\b(?:inr|rs)\.?\s*", "", raw)
    cleaned = cleaned.replace("₹", "").replace(",", "").strip()
    if not re.fullmatch(r"\+?\d+(?:\.\d{1,2})?", cleaned):
        raise ValueError("Invalid price format")
    try:
        amount = Decimal(cleaned).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    except InvalidOperation as error:
        raise ValueError("Invalid price format") from error
    if amount < 0:
        raise ValueError("Negative price")
    return int(amount * 100)


def clean_price_list(content: str, filename: str = "price-list.csv") -> PriceImportReport:
    if not content.strip():
        raise ValueError("The price list file is empty")
    try:
        reader = csv.DictReader(io.StringIO(content))
    except csv.Error as error:
        raise ValueError("Unable to read the CSV price list") from error
    if not reader.fieldnames:
        raise ValueError("CSV must contain Seat Class and Price columns")
    headers = {" ".join(header.strip().lower().split()): header for header in reader.fieldnames if header}
    class_header = headers.get("seat class") or headers.get("seat category") or headers.get("class")
    price_header = headers.get("price") or headers.get("amount")
    if not class_header or not price_header:
        raise ValueError("CSV must contain Seat Class and Price columns")

    rows: list[ImportRow] = []
    valid_by_name: defaultdict[str, list[ImportRow]] = defaultdict(list)
    for row_number, raw in enumerate(reader, start=2):
        raw_name = str(raw.get(class_header) or "")
        raw_price = str(raw.get(price_header) or "")
        normalized_name = normalize_name(raw_name)
        if not normalized_name:
            rows.append(ImportRow(row_number, raw_name, raw_price, "", None, "Rejected", "Missing seat class"))
            continue
        try:
            price_paise = parse_price_paise(raw_price)
        except ValueError as error:
            rows.append(ImportRow(row_number, raw_name, raw_price, normalized_name, None, "Rejected", str(error)))
            continue
        item = ImportRow(row_number, raw_name, raw_price, normalized_name, price_paise, "Imported", "Valid")
        rows.append(item)
        valid_by_name[normalized_name].append(item)

    clean_prices: dict[str, int] = {}
    conflicts: dict[str, list[int]] = {}
    row_updates = {row.row_number: row for row in rows}
    imported = 0
    deduplicated = 0
    for name, candidates in valid_by_name.items():
        values = {candidate.normalized_price_paise for candidate in candidates}
        if len(values) > 1:
            conflicts[name] = [candidate.row_number for candidate in candidates]
            for candidate in candidates:
                row_updates[candidate.row_number] = ImportRow(**{**asdict(candidate), "status": "Conflict", "reason": f"Conflicting values for {name}"})
            continue
        clean_prices[name] = candidates[0].normalized_price_paise
        imported += 1
        for duplicate in candidates[1:]:
            deduplicated += 1
            row_updates[duplicate.row_number] = ImportRow(**{**asdict(duplicate), "status": "De-duplicated", "reason": f"Same as {name}"})

    final_rows = tuple(row_updates[number] for number in sorted(row_updates))
    return PriceImportReport(filename, final_rows, clean_prices, conflicts, imported, deduplicated, sum(row.status == "Rejected" for row in final_rows))


def clean_csv(report: PriceImportReport) -> str:
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Seat Class", "Price"])
    for name, price_paise in report.clean_prices.items():
        writer.writerow([name, format(Decimal(price_paise) / Decimal(100), ".2f")])
    return output.getvalue()
