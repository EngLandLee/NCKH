import re
from typing import Dict, Any, Optional

class InvoiceRuleParser:
    def extract_fields(self, text: str) -> Dict[str, Any]:
        # Regex for invoice number: look for 'Số:' that is not preceded by 'Mẫu'
        inv_match = re.search(r"(?<!Mẫu\s)(?<!Ký\shiệu:\s)Số[:\s]*([0-9A-Za-z-]+)", text, re.IGNORECASE)
        inv_number = inv_match.group(1) if inv_match else "INV-UNKNOWN"

        # Regex for tax code (10 or 13 digits)
        tax_match = re.search(r"Mã số thuế[:\s]*([0-9]{10}(?:-[0-9]{3})?)", text, re.IGNORECASE)
        tax_code = tax_match.group(1) if tax_match else "0000000000"

        # Numbers extraction
        def parse_amount(pattern: str, default: float = 0.0) -> float:
            m = re.search(pattern, text, re.IGNORECASE)
            if m:
                clean_str = m.group(1).replace(",", "").replace(".", "").replace(" ", "").replace("VND", "").replace("đ", "")
                try:
                    return float(clean_str)
                except ValueError:
                    return default
            return default

        subtotal = parse_amount(r"Cộng tiền hàng[:\s]*([0-9.,]+)")
        vat_amount = parse_amount(r"Tiền thuế GTGT[:\s]*([0-9.,]+)")
        total_amount = parse_amount(r"Tổng cộng tiền thanh toán[:\s]*([0-9.,]+)")

        vat_rate = 10.0
        if "8%" in text:
            vat_rate = 8.0
        elif "0%" in text:
            vat_rate = 0.0

        # Auto-compute if missing
        if subtotal > 0 and vat_amount == 0:
            vat_amount = subtotal * (vat_rate / 100.0)
        if total_amount == 0 and subtotal > 0:
            total_amount = subtotal + vat_amount

        text_lower = text.lower()

        # GL Code assignment logic.
        # Classify on the line-item description only. "Hàng hóa:" is the field
        # *label* on every VAT invoice, so matching it against the whole
        # document would route tools and services to TK 156 as well.
        item_match = re.search(
            r"(?:Hàng hóa|Tên hàng hóa, dịch vụ|Diễn giải|Nội dung)[:\s]*([^.]+)",
            text,
            re.IGNORECASE,
        )
        item_text = (item_match.group(1) if item_match else text).lower()

        if any(k in item_text for k in ["dịch vụ", "vận chuyển", "cước", "logistics", "tiền điện", "tiền nước"]):
            debit_account = "TK 642"
        elif any(k in item_text for k in ["công cụ", "dụng cụ", "thiết bị", "đồng hồ", "máy đo"]):
            debit_account = "TK 153"
        elif any(k in item_text for k in ["nguyên vật liệu", "vật tư", "thép", "nhôm", "hóa chất", "bao bì", "màng ghép"]):
            debit_account = "TK 152"
        elif any(k in item_text for k in ["thành phẩm", "linh kiện", "vi mạch", "bán dẫn"]):
            debit_account = "TK 156"
        else:
            debit_account = "TK 152"

        credit_account = "TK 331" if "chưa thanh toán" in text_lower or "chuyển khoản" in text_lower else "TK 112"

        # Math validation & confidence
        expected_total = subtotal + vat_amount
        math_valid = abs(total_amount - expected_total) < 100.0 if (subtotal > 0 and total_amount > 0) else False

        confidence = 0.95 if (math_valid and inv_match and tax_match) else (0.75 if math_valid else 0.50)

        return {
            "invoice_number": inv_number,
            "tax_code": tax_code,
            "subtotal": subtotal,
            "vat_rate": vat_rate,
            "vat_amount": vat_amount,
            "total_amount": total_amount,
            "debit_account": debit_account,
            "credit_account": credit_account,
            "confidence_score": confidence,
            "math_valid": math_valid
        }
