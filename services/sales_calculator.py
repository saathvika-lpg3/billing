
from __future__ import annotations

from dataclasses import dataclass


def money(value: float) -> str:
    return f"Rs {value:,.2f}"


@dataclass
class SalesLine:
    item_name: str
    pack_name: str
    hsn: str
    unit: str
    qty: float
    free_qty: float
    mrp: float
    rate: float
    scheme: float
    discount_amount: float
    gst_rate: float
    item_id: int = 0
    pack_id: int = 0
    pack_size: float = 1
    stock_qty: float = 0
    source_item_id: int = 0
    source_doc_id: int = 0
    source_doc_no: str = ""
    max_qty: float = 0
    max_free_qty: float = 0
    tax_mode: str = ""


@dataclass
class ComputedLine:
    source: SalesLine
    gross: float
    taxable: float
    cgst: float
    sgst: float
    igst: float
    gst_total: float
    line_total: float


class SalesCalculator:
    def __init__(self, company_state: str = "") -> None:
        self.company_state = company_state.strip().lower()

    def compute_line(self, line: SalesLine, place_of_supply: str = "") -> ComputedLine:
        billable_qty = max(max(line.qty, 0) - max(line.free_qty, 0), 0)
        gross = round(billable_qty * max(line.rate, 0), 2)
        taxable = round(max(gross - max(line.discount_amount, 0), 0), 2)
        gst_total = round(taxable * max(line.gst_rate, 0) / 100, 2)
        use_igst = bool(place_of_supply.strip() and self.company_state and place_of_supply.strip().lower() != self.company_state)
        if use_igst:
            cgst = 0.0
            sgst = 0.0
            igst = gst_total
        else:
            cgst = round(gst_total / 2, 2)
            sgst = round(gst_total - cgst, 2)
            igst = 0.0
        return ComputedLine(line, gross, taxable, cgst, sgst, igst, gst_total, round(taxable + gst_total, 2))

    def totals(self, lines: list[ComputedLine]) -> dict[str, float]:
        taxable = round(sum(row.taxable for row in lines), 2)
        cgst = round(sum(row.cgst for row in lines), 2)
        sgst = round(sum(row.sgst for row in lines), 2)
        igst = round(sum(row.igst for row in lines), 2)
        gross = round(sum(row.gross for row in lines), 2)
        discount = round(sum(row.source.discount_amount for row in lines), 2)
        total = round(sum(row.line_total for row in lines), 2)
        rounded = round(total)
        return {
            "gross": gross,
            "discount": discount,
            "taxable": taxable,
            "cgst": cgst,
            "sgst": sgst,
            "igst": igst,
            "gst_total": round(cgst + sgst + igst, 2),
            "round_off": round(rounded - total, 2),
            "grand_total": float(rounded),
        }
