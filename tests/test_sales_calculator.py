
from services.sales_calculator import SalesCalculator, SalesLine


def test_sales_calculator_intrastate_split():
    calc = SalesCalculator("Telangana")
    line = SalesLine("Item", "1 PCS", "1905", "PCS", 10, 1, 50, 40, 0, 20, 18)
    result = calc.compute_line(line, "Telangana")
    assert result.taxable == 340
    assert result.gst_total == 61.2
    assert result.cgst == 30.6
    assert result.sgst == 30.6
    totals = calc.totals([result])
    assert totals["grand_total"] == 401


def test_sales_calculator_interstate_igst():
    calc = SalesCalculator("Telangana")
    line = SalesLine("Item", "1 PCS", "1905", "PCS", 5, 0, 100, 100, 0, 0, 5)
    result = calc.compute_line(line, "Karnataka")
    assert result.igst == 25
    assert result.cgst == 0
    assert result.sgst == 0
