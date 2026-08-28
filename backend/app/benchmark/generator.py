import json
import random
from typing import Dict, Any, List

def generate_benchmark_dataset(sample_size: int = 100000) -> Dict[str, Any]:
    records = []
    vendors = [
        ("CÔNG TY TNHH VẬT LIỆU XÂY DỰNG TOÀN CẦU", "0312345678", "Thép cuộn D10", "TK 152"),
        ("TẬP ĐOÀN HÓA CHẤT ĐỨC GIANG", "0100987654", "Hóa chất phụ gia bê tông", "TK 152"),
        ("CÔNG TY CỔ PHẦN BAO BÌ NHỰA TÂN TIẾN", "0301122334", "Bao bì màng ghép", "TK 152"),
        ("CÔNG TY TNHH LINH KIỆN ĐIỆN TỬ SAMSUNG", "2300554433", "Vi mạch bán dẫn MCU-32", "TK 156"),
        ("CÔNG TY CP THIẾT BỊ ĐO LƯỜNG CÔNG NGHIỆP", "0309988776", "Đồng hồ đo áp suất", "TK 153"),
        ("TỔNG CÔNG TY DỊCH VỤ VẬN TẢI SAO MAI", "0311223344", "Cước vận chuyển container", "TK 642")
    ]

    for i in range(sample_size):
        r_type = i % 4
        if r_type == 0: # Invoice
            v_name, tax, item, gl = random.choice(vendors)
            subtotal = random.randint(5, 500) * 1_000_000
            vat = int(subtotal * 0.10)
            total = subtotal + vat
            text = f"Số: {100000 + i}. Đơn vị: {v_name}. Mã số thuế: {tax}. Hàng hóa: {item}. Cộng tiền hàng: {subtotal:,} VND. Tiền thuế GTGT: {vat:,} VND. Tổng cộng tiền thanh toán: {total:,} VND. Chuyển khoản."
            records.append({
                "id": f"INV-{i}",
                "domain": "invoice",
                "payload": {"raw_text": text, "filename": f"inv_{i}.txt"},
                "ground_truth_label": gl,
                "ground_truth_total": total
            })
        elif r_type == 1: # Demand
            sku = f"SKU-{random.randint(100, 999)}"
            base_d = random.randint(50, 200)
            hist = [base_d + random.randint(-15, 20) for _ in range(10)]
            records.append({
                "id": f"DMD-{i}",
                "domain": "demand",
                "payload": {
                    "sku_id": sku,
                    "historical_demand": hist,
                    "current_stock": random.randint(100, 600),
                    "lead_time_days": 7
                },
                "ground_truth_label": "DEMAND_VALID"
            })
        elif r_type == 2: # Logistics VRP
            stops = [
                {"id": s, "name": f"Stop {s}", "lat": 10.77 + random.uniform(-0.05, 0.05), "lng": 106.70 + random.uniform(-0.05, 0.05), "demand": 10}
                for s in range(1, 5)
            ]
            records.append({
                "id": f"VRP-{i}",
                "domain": "logistics",
                "payload": {
                    "depot": (10.7769, 106.7009),
                    "stops": stops,
                    "vehicle_count": 2,
                    "vehicle_capacity": 60,
                    "weather": random.choice(["CLEAR", "RAIN", "HEAVY_RAIN"])
                },
                "ground_truth_label": "VRP_VALID"
            })
        else: # SOP RAG
            queries = [
                ("Quy trình thanh toán tạm ứng cần giấy tờ gì?", "SOP-KT-04"),
                ("Nguyên vật liệu nhập kho hạch toán tài khoản nào?", "SOP-KT-01"),
                ("Khi nào kích hoạt Reorder Point tồn kho an toàn?", "SOP-KHO-05"),
                ("Xử lý thế nào khi giao hàng trễ do ngập lụt?", "SOP-LOG-02")
            ]
            q, doc_id = random.choice(queries)
            records.append({
                "id": f"RAG-{i}",
                "domain": "rag",
                "payload": {"query": q},
                "ground_truth_label": doc_id
            })

    return {
        "version": "2.0",
        "dataset_name": "operations_benchmark_v2.json",
        "total_records": len(records),
        "records": records
    }
