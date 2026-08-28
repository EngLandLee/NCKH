import pytest
from backend.app.agents.invoice_agent import InvoiceAgent, InvoiceRawInput

def test_invoice_extraction_and_gl_mapping():
    agent = InvoiceAgent()
    sample_text = """
    HÓA ĐƠN GIÁ TRỊ GIA TĂNG (VAT INVOICE)
    Mẫu số: 01GTKT0/001 - Ký hiệu: AA/26E - Số: 0019284
    Đơn vị bán hàng: CÔNG TY TNHH VẬT LIỆU XÂY DỰNG TOÀN CẦU
    Mã số thuế: 0312345678
    Tên hàng hóa, dịch vụ: Thép cuộn xây dựng Hòa Phát D10 (Nguyên vật liệu sản xuất)
    Đơn giá: 10,000,000 VND
    Cộng tiền hàng: 50,000,000 VND
    Thuế suất GTGT: 10%
    Tiền thuế GTGT: 5,000,000 VND
    Tổng cộng tiền thanh toán: 55,000,000 VND
    Hình thức thanh toán: Chuyển khoản (Chưa thanh toán)
    """
    input_data = InvoiceRawInput(raw_text=sample_text, filename="invoice_0019284.txt")
    result = agent.process(input_data)

    assert result.invoice_number == "0019284"
    assert result.subtotal == 50000000.0
    assert result.vat_amount == 5000000.0
    assert result.total_amount == 55000000.0
    assert result.debit_account == "TK 152" # Nguyên vật liệu
    assert result.credit_account == "TK 331" # Phải trả người bán
    assert result.confidence_score >= 0.90
    assert result.status == "APPROVED"
