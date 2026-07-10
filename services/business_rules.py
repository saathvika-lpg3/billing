from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class BusinessProfile:
    code: str
    name: str
    required_fields: tuple[str, ...]
    optional_fields: tuple[str, ...] = ()
    hidden_fields: tuple[str, ...] = ()
    columns: tuple[str, ...] = ()
    gst_required: bool = True
    print_template_type: str = "A4 GST Invoice"
    printer_profile: str = "A4 Laser"
    validation_rules: dict[str, Any] = field(default_factory=dict)


BUSINESS_PROFILES: dict[str, BusinessProfile] = {
    "retail": BusinessProfile(
        code="retail",
        name="Retail POS",
        required_fields=("item", "qty", "rate", "gst", "payment_mode"),
        columns=("sr_no", "item", "qty", "rate", "gst", "amount"),
        print_template_type="POS Receipt",
        printer_profile="Thermal / A4",
        validation_rules={"fast_billing": True, "stock_required_for_sales": True},
    ),
    "pharmacy": BusinessProfile(
        code="pharmacy",
        name="Pharmacy",
        required_fields=("product", "batch", "expiry", "qty", "mrp", "rate", "gst", "hsn"),
        columns=("sr_no", "item", "batch", "expiry", "hsn", "qty", "mrp", "rate", "discount", "gst", "amount"),
        print_template_type="Pharmacy Invoice",
        validation_rules={"batch_required": True, "expiry_required": True, "expired_batch_blocked": True},
    ),
    "distributor_wholesale": BusinessProfile(
        code="distributor_wholesale",
        name="Distributor / Wholesale",
        required_fields=("item", "hsn", "qty", "unit", "mrp", "rate", "free_qty", "discount", "taxable", "gst", "amount"),
        optional_fields=("customer_gstin", "po_no", "transport_details", "credit_terms", "route", "salesman"),
        hidden_fields=("batch", "expiry", "cgst_item", "sgst_item", "igst_item"),
        columns=("sr_no", "item", "hsn", "qty", "unit", "mrp", "rate", "free", "discount", "taxable", "gst", "amount"),
        print_template_type="Distributor Invoice",
        validation_rules={"approved_read_only": True},
    ),
    "fmcg": BusinessProfile(
        code="fmcg",
        name="FMCG Distribution",
        required_fields=("product", "category", "qty", "free_qty", "mrp", "rate", "gst"),
        columns=("sr_no", "item", "hsn", "qty", "free", "mrp", "rate", "scheme", "discount", "taxable", "gst", "amount"),
        print_template_type="Distributor Invoice",
        validation_rules={"free_qty_supported": True, "scheme_supported": True},
    ),
    "trading": BusinessProfile(
        code="trading",
        name="Trading GST",
        required_fields=("product", "hsn", "qty", "unit", "rate", "gst", "taxable"),
        columns=("sr_no", "item", "hsn", "qty", "unit", "rate", "discount", "taxable", "gst", "amount"),
        validation_rules={"unit_required": True},
    ),
    "manufacturing": BusinessProfile(
        code="manufacturing",
        name="Manufacturing",
        required_fields=("item", "raw_material_finished_goods_type", "batch_lot_no", "unit", "qty", "warehouse", "rate", "gst"),
        columns=("sr_no", "item", "batch", "warehouse", "unit", "qty", "rate", "taxable", "gst", "amount"),
        print_template_type="A4 Tax Invoice",
        validation_rules={"warehouse_required": True, "batch_lot_tracking": True},
    ),
    "service": BusinessProfile(
        code="service",
        name="Service Billing",
        required_fields=("service_description", "sac", "qty_hours", "rate", "gst", "taxable"),
        columns=("sr_no", "description", "hsn", "qty", "rate", "discount", "taxable", "gst", "amount"),
        print_template_type="Service Invoice",
        validation_rules={"customer_required": True, "service_item_allowed": True},
    ),
    "warehouse": BusinessProfile(
        code="warehouse",
        name="Warehouse / Picking",
        required_fields=("warehouse", "product", "qty", "unit", "stock_availability", "rate", "gst"),
        columns=("sr_no", "item", "warehouse", "unit", "qty", "rate", "gst", "amount"),
        print_template_type="Warehouse Picking Slip",
        validation_rules={"warehouse_required": True, "stock_availability_required": True},
    ),
    "multi_branch": BusinessProfile(
        code="multi_branch",
        name="Multi Branch",
        required_fields=("branch", "customer_supplier", "product", "qty", "rate", "gst", "invoice_series"),
        optional_fields=("warehouse", "cost_center", "employee", "branch_gstin", "discount"),
        columns=("sr_no", "item", "hsn", "qty", "rate", "taxable", "gst", "amount"),
        print_template_type="Branch-Specific Invoice",
        validation_rules={"branch_required": True, "invoice_series_required": True},
    ),
    "electronics": BusinessProfile(
        code="electronics",
        name="Electronics",
        required_fields=("product", "qty", "rate", "gst"),
        columns=("sr_no", "item", "model", "serial", "imei", "warranty", "hsn", "qty", "rate", "gst", "amount"),
        validation_rules={"serial_warranty_supported": True},
    ),
    "restaurant": BusinessProfile(
        code="restaurant",
        name="Restaurant",
        required_fields=("item", "qty", "rate", "table_no"),
        gst_required=False,
        columns=("sr_no", "item", "qty", "rate", "amount"),
        print_template_type="POS Receipt",
        validation_rules={"kot_supported": True},
    ),
    "real_estate": BusinessProfile(
        code="real_estate",
        name="Real Estate",
        required_fields=("project", "unit", "customer", "amount"),
        gst_required=False,
        columns=("sr_no", "description", "amount"),
        print_template_type="Booking Receipt",
        validation_rules={"project_unit_required": True},
    ),
}


PERMISSION_CATALOG: dict[str, tuple[tuple[str, str], ...]] = {
    "Billing": (
        ("sale", "Sales bill entry"),
        ("sales_view", "Sales list / view"),
        ("print_bills", "Print bills"),
        ("sale_return", "Sales return"),
        ("sale_cancel", "Sales cancellation"),
        ("receipt", "Receipt entry"),
        ("receipt_cancel", "Receipt cancellation"),
    ),
    "Purchase": (
        ("purchase", "Purchase entry"),
        ("purchase_return", "Purchase return"),
        ("purchase_cancel", "Purchase cancellation"),
        ("payment", "Payment entry"),
        ("payment_cancel", "Payment cancellation"),
    ),
    "Stock": (
        ("stock_view", "Stock view"),
        ("stock_out", "Vehicle stock out"),
        ("stock_out_cancel", "Stock-out cancellation"),
        ("items", "Product masters"),
        ("warehouses", "Warehouses"),
        ("stock_transfer", "Stock transfer"),
        ("stock_adjust", "Stock adjustment"),
    ),
    "Accounts": (
        ("expense", "Expense entry"),
        ("expense_cancel", "Expense cancellation"),
        ("accounts", "Accounts view"),
        ("day_book", "Day book"),
        ("outstanding", "Outstanding"),
    ),
    "Reports": (
        ("reports", "Reports"),
        ("audit", "Audit log"),
    ),
    "Closing": (
        ("closing", "Account closing"),
    ),
    "Admin": (
        ("developer_admin", "Developer admin"),
        ("users", "Users"),
        ("backup", "Backup / restore"),
        ("company", "Company settings"),
    ),
}


BUSINESS_TYPE_ALIASES: dict[str, str] = {
    "retail_supermarket": "retail",
    "pharmacy_medical": "pharmacy",
    "electronics_mobile": "electronics",
    "restaurant_food": "restaurant",
    "hotel_restaurant": "restaurant",
    "service_business": "service",
    "warehouse_based": "warehouse",
}

LINE_FIELD_ALIASES: dict[str, tuple[str, ...]] = {
    "item": ("item_name", "product"),
    "product": ("item_name", "product"),
    "batch": ("batch",),
    "expiry": ("expiry",),
    "qty": ("qty",),
    "mrp": ("mrp",),
    "rate": ("rate",),
    "gst": ("gst_rate", "gst"),
    "hsn": ("hsn",),
    "unit": ("unit",),
    "free_qty": ("free_qty",),
    "discount": ("discount",),
    "taxable": ("taxable",),
    "amount": ("amount",),
    "service_description": ("service_description",),
    "sac": ("sac",),
    "qty_hours": ("qty_hours",),
    "table_no": ("table_no",),
    "warehouse": ("warehouse",),
    "stock_availability": ("stock_availability",),
    "project": ("project",),
}

FIELD_LABELS: dict[str, str] = {
    "item": "Product",
    "product": "Product",
    "batch": "Batch",
    "expiry": "Expiry date",
    "qty": "Quantity",
    "mrp": "MRP",
    "rate": "Rate",
    "gst": "GST",
    "hsn": "HSN",
    "unit": "Unit",
    "free_qty": "Free qty",
    "discount": "Discount",
    "taxable": "Taxable amount",
    "service_description": "Service description",
    "sac": "SAC code",
    "qty_hours": "Quantity / hours",
    "table_no": "Table number",
    "warehouse": "Warehouse",
    "stock_availability": "Stock availability",
    "project": "Project",
}


def normalize_business_type(code: str | None) -> str:
    normalized = str(code or "").strip().lower()
    return BUSINESS_TYPE_ALIASES.get(normalized, normalized)


def equivalent_business_type_codes(code: str | None) -> set[str]:
    normalized = normalize_business_type(code)
    equivalents: set[str] = {normalized}
    for alias, canonical in BUSINESS_TYPE_ALIASES.items():
        if canonical == normalized:
            equivalents.add(alias)
    return equivalents


def _line_has_value(line: dict[str, Any], keys: tuple[str, ...]) -> bool:
    return any(str(line.get(key) or "").strip() for key in keys)


def _required_line_field_error(profile: BusinessProfile, field_name: str, line: dict[str, Any]) -> str | None:
    keys = LINE_FIELD_ALIASES.get(field_name)
    if not keys:
        return None
    if _line_has_value(line, keys):
        return None
    label = FIELD_LABELS.get(field_name, field_name.replace("_", " ").title())
    return f"{label} is required for this business type."


def profile_for(code: str | None) -> BusinessProfile:
    normalized = normalize_business_type(code)
    return BUSINESS_PROFILES.get(normalized) or BUSINESS_PROFILES["distributor_wholesale"]


def profile_rows() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for profile in BUSINESS_PROFILES.values():
        rows.append(
            {
                "code": profile.code,
                "name": profile.name,
                "required_fields": ", ".join(profile.required_fields),
                "item_columns": ", ".join(profile.columns),
                "print_template": profile.print_template_type,
                "validation_rules": ", ".join(sorted(profile.validation_rules.keys())) or "standard",
            }
        )
    return rows


def profile_metadata(code: str | None) -> dict[str, object]:
    """Return UI-friendly metadata for a business profile.

    This includes required/optional/hidden fields, visible columns, print defaults
    and validation flags useful for wiring views.
    """
    profile = profile_for(code)
    visible_columns = tuple(c for c in profile.columns if c not in profile.hidden_fields)
    return {
        "code": profile.code,
        "name": profile.name,
        "required_fields": profile.required_fields,
        "optional_fields": profile.optional_fields,
        "hidden_fields": profile.hidden_fields,
        "columns": profile.columns,
        "visible_columns": visible_columns,
        "gst_required": profile.gst_required,
        "print_template_type": profile.print_template_type,
        "printer_profile": profile.printer_profile,
        "validation_rules": profile.validation_rules,
    }


def permission_keys() -> list[str]:
    keys: list[str] = []
    for group in PERMISSION_CATALOG.values():
        keys.extend(key for key, _label in group)
    return keys


def validate_item_line(profile_code: str | None, line: dict[str, Any], *, stock_check: bool = False) -> list[str]:
    profile = profile_for(profile_code)
    errors: list[str] = []
    item_name = str(line.get("item_name") or line.get("product") or "").strip()
    if not item_name:
        errors.append("Select a product.")
    qty = float(line.get("qty") or 0)
    if qty <= 0:
        errors.append("Quantity must be greater than zero.")
    rate = float(line.get("rate") or 0)
    if rate < 0:
        errors.append("Rate cannot be negative.")
    if profile.gst_required and line.get("gst_rate") in ("", None):
        errors.append("GST % is required.")

    if "mrp" in profile.required_fields:
        mrp = float(line.get("mrp") or 0)
        if mrp <= 0:
            errors.append("MRP is required for this business type.")

    if "hsn" in profile.required_fields and not str(line.get("hsn") or "").strip():
        errors.append("HSN is required for this business type.")
    if "unit" in profile.required_fields and not str(line.get("unit") or "").strip():
        errors.append("Unit is required.")

    if stock_check and profile.validation_rules.get("stock_required_for_sales"):
        stock_qty = float(line.get("stock_qty") or 0)
        free_qty = float(line.get("free_qty") or 0)
        if qty + free_qty > stock_qty:
            errors.append("Selected quantity is above available stock.")
    return errors
