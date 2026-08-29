"""Held-out generalization tests for the GL account classifier.

The benchmark dataset in data/operations_benchmark_v2.json is generated from
six vendor templates. A keyword classifier tuned on those templates scores
100% on it while having learned nothing transferable, so in-distribution
accuracy alone cannot tell us whether the invoice agent works.

These cases use vendors and line items that appear in NO template. They are
the honest measure of the fast path, and they are the quantified argument for
routing low-confidence invoices to an LLM.
"""
import pytest
from backend.app.solvers.pdf_parser import InvoiceRuleParser

# (line item, expected GL debit account) — none of these appear in the generator
HELD_OUT_INVOICES = [
    ("Xi măng PCB40 bao 50kg", "TK 152"),
    ("Cát san lấp mặt bằng", "TK 152"),
    ("Máy tính xách tay Dell Latitude", "TK 153"),
    ("Bàn ghế văn phòng", "TK 153"),
    ("Phí tư vấn pháp lý quý III", "TK 642"),
    ("Chi phí thuê kho bãi", "TK 642"),
    ("Điện thoại di động Samsung A55", "TK 156"),
    ("Tủ lạnh Toshiba nhập khẩu", "TK 156"),
]


def _invoice_text(item: str) -> str:
    return (
        f"Số: 999. Đơn vị: CÔNG TY TNHH ABC. Mã số thuế: 0312345678. "
        f"Hàng hóa: {item}. Cộng tiền hàng: 10,000,000 VND. "
        f"Tiền thuế GTGT: 1,000,000 VND. "
        f"Tổng cộng tiền thanh toán: 11,000,000 VND. Chuyển khoản."
    )


@pytest.mark.parametrize("item,expected", HELD_OUT_INVOICES)
def test_field_extraction_generalizes(item, expected):
    """Numeric extraction is template-independent and must always hold."""
    parsed = InvoiceRuleParser().extract_fields(_invoice_text(item))
    assert parsed["subtotal"] == 10_000_000
    assert parsed["vat_amount"] == 1_000_000
    assert parsed["total_amount"] == 11_000_000
    assert parsed["math_valid"] is True
    assert parsed["tax_code"] == "0312345678"


def test_held_out_gl_accuracy_is_measured_not_assumed():
    """Pin the held-out GL accuracy so regressions and improvements are visible.

    The rule-based fast path currently generalizes poorly: it defaults unknown
    line items to TK 152. This test records that fact rather than hiding it.
    Raise the lower bound as the classifier (or LLM escalation) improves.
    """
    parser = InvoiceRuleParser()
    correct = sum(
        1 for item, expected in HELD_OUT_INVOICES
        if parser.extract_fields(_invoice_text(item))["debit_account"] == expected
    )
    accuracy = correct / len(HELD_OUT_INVOICES)

    # Documented current behaviour: only the TK 152 majority class survives.
    assert accuracy >= 0.25, (
        f"Held-out GL accuracy regressed to {accuracy:.0%}; "
        "the fast path no longer classifies even the majority class."
    )


def test_line_item_label_is_not_treated_as_a_category():
    """Regression test for the field-label bug.

    'Hàng hóa:' is the field label on every VAT invoice. Matching it against
    the whole document made TK 153 and TK 642 unreachable, silently capping
    macro-F1 at 0.37 while accuracy still read 65%.
    """
    parser = InvoiceRuleParser()
    assert parser.extract_fields(_invoice_text("Cước vận chuyển container"))["debit_account"] == "TK 642"
    assert parser.extract_fields(_invoice_text("Đồng hồ đo áp suất"))["debit_account"] == "TK 153"
