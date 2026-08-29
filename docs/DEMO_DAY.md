# Demo Day Runbook — SupplyChain-AgenticHub

Kịch bản trình diễn, phương án dự phòng và chuẩn bị Q&A cho vòng Chung kết
MLAI Hackathon 2026. Chiếm **20%** tổng điểm ("Sản phẩm chạy trực tiếp mượt mà
tại Demo Day, kỹ năng thuyết trình & trả lời hội đồng").

> Mọi con số trong tài liệu này đều **đo thật** trên máy dev, không phải ước
> lượng. Chạy lại bằng `PYTHONPATH=. backend/venv/bin/python -m backend.app.benchmark.report`.

---

## 1. Trước khi lên sân khấu (T-15 phút)

```bash
./run_demo.sh --check      # preflight, không khởi động gì
```

Preflight kiểm tra: venv Python 3.12, `ortools`/`fastapi`/`numpy` import được,
`node_modules` tồn tại, có/không `OPENAI_API_KEY`, và **cổng 3000/8008 còn trống**.

> ⚠️ **Lỗi đã thực sự xảy ra khi thử nghiệm:** cổng 3000 bị chiếm, Vite âm thầm
> nhảy sang 3001 trong khi banner vẫn ghi 3000. Trên sân khấu điều này trông
> như "app hỏng". Script nay dùng `--strictPort` và **báo lỗi to** thay vì trôi
> sang cổng khác. Nếu gặp: `FRONTEND_PORT=3100 ./run_demo.sh`.

```bash
./run_demo.sh              # khởi động thật
```

Chỉ trình diễn khi thấy đủ 3 dòng xanh: backend healthy → frontend serving →
**proxy verified end-to-end**.

**Checklist:**
- [ ] `./run_demo.sh --check` pass
- [ ] `pytest backend/tests/ -q` → 42 passed, 2 skipped
- [ ] Mở sẵn 3 tab: Dashboard `:3000`, Swagger `:8008/docs`, video dự phòng
- [ ] Tắt thông báo hệ thống, đặt terminal cỡ chữ lớn
- [ ] **Đã quay video dự phòng** (mục 4)
- [ ] Bản `frontend/dist` đã build sẵn (`pnpm build`) phòng khi Vite lỗi

---

## 2. Kịch bản 5 phút

### Mở đầu (30 giây) — nêu vấn đề, không nói kiến trúc

> "Một doanh nghiệp sản xuất mỗi ngày xử lý hàng trăm hóa đơn đầu vào, định
> tuyến hàng chục xe giao hàng, và tra cứu quy chế nội bộ liên tục. Bốn việc
> này hiện do bốn bộ phận làm thủ công. Chúng tôi tự động hóa cả bốn, với ràng
> buộc độ trễ dưới 200ms."

### Phần 1 (60s) — Invoice: **điểm mạnh nhất, diễn đầu tiên**

Dán hóa đơn sạch → kết quả tức thì, badge **`FAST-PATH`** màu xanh.

| Điểm nhấn | Số liệu |
|---|---|
| Độ trễ | ~0.03 ms |
| Định khoản | TK 152 / TK 331 đúng Thông tư 200 |
| Đối soát | tiền hàng + thuế = tổng |

Sau đó dán **hóa đơn khó** (đây là phần ăn điểm):

```
Số: 4521. Đơn vị: CÔNG TY LUẬT TNHH MINH KHUÊ.
Hàng hóa: Phí tư vấn pháp lý quý III.
Cộng tiền hàng: 80,000,000 VND. Tổng cộng tiền thanh toán: 95,000,000 VND.
```

Kết quả: badge chuyển **`LLM SLOW-PATH`** màu tím, hiện đủ 3 trigger
`LOW_CONFIDENCE` + `MATH_MISMATCH` + `UNKNOWN_VENDOR`, và dòng đối chiếu
~~TK 152~~ → **TK 642**.

> 🔑 **BẮT BUỘC có `OPENAI_API_KEY` cho phần này.** Không có key, hệ thống vẫn
> chạy nhưng panel hiện màu **hổ phách `UNAVAILABLE`** và giữ nguyên TK 152 —
> tức khán giả thấy trigger nhưng **không thấy LLM sửa sai**, mất đúng phần ăn
> điểm. Kiểm tra bằng `./run_demo.sh --check`: phải thấy dòng
> *"OPENAI_API_KEY configured — LLM escalation ACTIVE"*.
>
> Nếu không có key: bỏ hóa đơn khó khỏi kịch bản, thay bằng câu nói
> *"nhánh LLM đã triển khai và có test, chúng tôi trình bày ở phần kiến trúc"*
> rồi mở thẳng `llm_escalation.py` — **đừng** để hội đồng thấy panel hổ phách
> mà không giải thích.

> "Regex đoán sai thành TK 152 vì không có từ khóa nào khớp. Hệ thống tự phát
> hiện độ tin cậy thấp, số học lệch, thiếu mã số thuế — và chuyển sang LLM.
> Đây là Dual-Speed Routing: nhanh cho 100% ca thường, chính xác cho phần đuôi."

### Phần 2 (60s) — VRP: **trực quan nhất**

Chạy 6 điểm giao, 2 xe, `CLEAR` → đổi sang `HEAVY_RAIN`.

| Thời tiết | Quãng đường | Thời gian | Solver |
|---|---|---|---|
| CLEAR | 22.66 km | 45.3 phút | 4.69 ms |
| HEAVY_RAIN | **31.73 km** | **88.8 phút** | 1.78 ms |

> "Cùng bộ điểm giao, mưa lớn làm hệ số tăng 1.4 lần — lộ trình được tính lại,
> thời gian gần gấp đôi. Đây là Google OR-Tools, bộ giải CVRP viết bằng C++."

### Phần 3 (45s) — Demand

SKU có xu hướng tăng, `supplier_reliability=0.75`:
ROP **1137.31**, Safety Stock **81.71**, rủi ro đứt gãy **100%** →
hệ thống tự đề xuất PO khẩn 1706 đơn vị. Độ trễ 0.43 ms.

> "Công thức tồn kho an toàn chuẩn: z·σ·√LT với mức phục vụ 95%."

### Phần 4 (40s) — RAG

Hỏi bằng **từ ngữ không có trong tài liệu**: *"Xe không giao kịp vì đường ngập
thì làm sao?"* → vẫn trả đúng `SOP-LOG-02, Điều 9, Trang 42`, badge **`BM25`**
(hoặc **`SEMANTIC`** màu tím nếu có key), rê chuột thấy điểm truy xuất.

Rồi hỏi một câu **ngoài phạm vi**: *"Giá cổ phiếu VNM hôm nay thế nào?"* →
hệ thống **từ chối trả lời**, confidence 0.50.

> "Điểm này quan trọng: bản trước trả lời sai nhưng vẫn báo độ tin cậy 0.85.
> Chúng tôi sửa cách chấm điểm sang BM25 có chuẩn hóa độ dài, và thêm ngưỡng
> từ chối. Thà nói không biết còn hơn tự tin sai."

Hỏi lại câu cũ → cache hit, 0.00 ms.

### Phần 5 (60s) — Benchmark: **chốt bằng sự trung thực**

Chạy `/api/benchmark/run?samples=1000` live.

| | Kết quả |
|---|---|
| Mean / P95 | **0.31 ms** / **1.07 ms** (ngưỡng 200 ms) |
| Accuracy in-distribution | 100.00% |
| **Held-out (hàng chưa từng gặp)** | **25.00%** |

> "Chúng tôi báo cáo cả con số không đẹp. 100% là *trong phân phối* — bộ dữ
> liệu sinh từ 6 mẫu nhà cung cấp. Trên hóa đơn lạ, luật regex chỉ đạt 25%,
> đúng bằng mức đoán bừa. Đó chính là lý do định lượng để chúng tôi xây nhánh
> LLM, chứ không phải để cho có."

**Đây là câu ăn điểm lớn nhất.** Hầu hết đội sẽ khoe 99%; đội trình bày được
giới hạn của chính mình và cách khắc phục sẽ nổi bật với hội đồng học thuật.

---

## 3. Q&A — câu hỏi gần như chắc chắn được hỏi

**H: F1-score tính thế nào?**
Macro-F1 thật: precision/recall từng lớp TK rồi lấy trung bình, code tại
`backend/app/benchmark/evaluator.py::_macro_f1`. Chỉ báo cáo cho 2 domain có
nhãn phân loại (invoice, RAG). Logistics chấm bằng **kiểm định khả thi** (mọi
điểm giao đúng 1 lần, không xe nào vượt tải), Demand chấm bằng **tính lại công
thức** — F1 theo lớp không có nghĩa ở đó nên để trống thay vì điền số giả.

**H: Tại sao accuracy đúng tròn 100%? Có phải fit vào test set không?**
Đúng, và chúng tôi nói rõ điều đó. 100% là in-distribution trên dữ liệu sinh từ
6 template. Vì vậy chúng tôi bổ sung tập held-out: fast-path chỉ đạt **25%**,
bằng baseline đoán bừa TK 152. Con số này được khóa trong
`backend/tests/test_generalization.py` để không âm thầm trôi.

**H: Dataset lấy từ đâu? Có phải dữ liệu thật không?**
Không. Dữ liệu **tự sinh** (`backend/app/benchmark/generator.py`) mô phỏng hóa
đơn VAT Việt Nam. Chúng tôi không tuyên bố đây là dữ liệu doanh nghiệp thật.
Đó là lý do tập held-out quan trọng.

**H: OpenAI được dùng ở chỗ nào?**
`backend/app/agents/llm_escalation.py` — Structured Outputs
(`chat.completions.parse` + Pydantic schema, `temperature=0`) buộc mô hình trả
đúng 1 trong 4 tài khoản VAS. Kích hoạt khi confidence < 0.85, lệch số học,
hoặc thiếu MST. Đo được: **0/2500** hóa đơn sạch cần escalate, **8/8** hóa đơn
lộn xộn thì có.

**H: Mất mạng giữa demo thì sao?**
Hệ thống **giữ nguyên kết quả fast-path** và ghi trạng thái `UNAVAILABLE`/
`FAILED`, không bao giờ ném lỗi. Có 2 test riêng cho hai đường degrade này.
Demo vẫn chạy bình thường không cần internet.

**H: Sao độ trễ chỉ 0.3ms mà không phải vài chục ms?**
Vì fast-path là tất định: regex + OR-Tools C++ + tra cứu in-memory, không gọi
mạng. Nhánh LLM mới tốn ~1-2 giây, nhưng chỉ chạm vào phần đuôi. Chúng tôi báo
cáo tách bạch hai con số thay vì trộn lẫn.

**H: RAG này có phải RAG thật không?**
Có hai tầng. Tầng nhanh là **BM25** (có IDF và chuẩn hóa độ dài), tầng semantic
là **OpenAI embeddings + cosine similarity**, vector tài liệu tính một lần lúc
khởi động. Thiếu key thì tự động lùi về BM25 và ghi rõ `LEXICAL_FALLBACK`.

Đo trên tập câu hỏi diễn đạt lại: BM25 đạt **10/10** câu dễ nhưng chỉ **4/6**
câu khó (từ vựng không giao nhau) — đó chính là chỗ embeddings có giá trị.
Thành thật mà nói, với kho chỉ **4 tài liệu** thì BM25 đã gần đủ; lợi ích của
embeddings sẽ rõ hơn khi kho tài liệu lớn lên.

**H: Sao biết hệ thống không "bịa" câu trả lời?**
Nó không sinh văn bản — chỉ trích nguyên văn điều khoản kèm số trang. Và có
**ngưỡng từ chối**: BM25 < 2.0 hoặc cosine < 0.30 thì trả "không tìm thấy".
Ngưỡng 2.0 suy ra từ số đo: câu trong phạm vi ≥ 3.40, ngoài phạm vi ≤ 1.17.

**H: Điểm khác biệt so với đội khác?**
Ba điểm: (1) kết hợp LLM với **bộ giải toán tất định** OR-Tools thay vì chỉ
prompt; (2) **Dual-Speed Routing** có kiểm chứng, không phải khẩu hiệu — báo
cáo cả tỉ lệ escalate; (3) chúng tôi **công bố giới hạn** của hệ thống kèm số
đo, thay vì chỉ khoe con số đẹp.

**H: Triển khai thực tế cho doanh nghiệp thế nào?**
Bốn agent tách biệt qua FastAPI, có thể bật/tắt độc lập. Nhánh LLM tắt được
theo từng request (`allow_escalation=false`) cho môi trường không được gọi
API ngoài. Định khoản theo Thông tư 200 nên khớp sổ sách VN.

### Câu hỏi khó — chuẩn bị sẵn tinh thần

**H: 4 tài liệu SOP thì gọi gì là "kho tài liệu khổng lồ"?**
Nhận sai. README đã sửa lại đúng mô tả. Kiến trúc cho phép nạp thêm tài liệu,
nhưng bản demo chỉ có 4 — chúng tôi không tuyên bố nhiều hơn thực tế.

**H: Có bao nhiêu phần trăm code do AI sinh ra?**
Trả lời trung thực; thể lệ chỉ cấm **đạo mã không khai báo**, không cấm dùng
AI (BTC còn tài trợ ChatGPT Pro). Nhấn mạnh phần thiết kế: tiêu chí chấm điểm
từng domain, phát hiện bug nhãn trường, tập held-out — đó là phần tư duy.

---

## 4. Phương án dự phòng

| Sự cố | Xử lý |
|---|---|
| Cổng 3000 bị chiếm | `FRONTEND_PORT=3100 ./run_demo.sh` |
| Vite không lên | `cd frontend && pnpm build && npx vite preview --port 3000` |
| Backend chết | `tail -20 /tmp/agentichub_backend.log` |
| Mất mạng | Không ảnh hưởng — chỉ nhánh LLM tắt, tự degrade |
| Máy chiếu hỏng UI | Demo bằng Swagger `:8008/docs` — mọi endpoint gọi được trực tiếp |
| Hỏng toàn bộ | Chiếu **video dự phòng** |

### Video dự phòng (bắt buộc quay trước)

Quay 4-5 phút đúng kịch bản mục 2, màn hình 1080p, không cắt ghép giữa các
thao tác (hội đồng cần thấy nó chạy thật). Lưu **offline** trên máy, không
phụ thuộc mạng.

```bash
# Ví dụ với ffmpeg trên Linux
ffmpeg -f x11grab -s 1920x1080 -i :0.0 -f pulse -i default \
       -c:v libx264 -preset fast -crf 23 demo_backup.mp4
```

---

## 5. Lệnh bỏ túi

```bash
./run_demo.sh --check                                    # preflight
./run_demo.sh                                            # khởi động
PYTHONPATH=. backend/venv/bin/pytest backend/tests/ -q   # 28 passed
PYTHONPATH=. backend/venv/bin/python -m backend.app.benchmark.report
curl -s "http://localhost:8008/api/benchmark/run?samples=1000" | python3 -m json.tool
```
