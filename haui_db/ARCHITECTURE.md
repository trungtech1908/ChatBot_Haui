# Kiến trúc hệ thống hỏi đáp quy chế HaUI

Hệ thống trả lời câu hỏi của sinh viên Trường Đại học Công nghiệp Hà Nội về quy chế, quy định (học bổng, học phí, đào tạo, rèn luyện, chính sách) và kết hợp với dữ liệu cá nhân của chính sinh viên đó. Kiến trúc theo hướng Planner – Executor: một LLM lập kế hoạch gọi công cụ, các công cụ (RAG, Text2SQL, Compute) thu thập bằng chứng, sau đó sinh câu trả lời và kiểm định trước khi trả về.

## 0. Danh sách file

| File | Nội dung |
|---|---|
| `ARCHITECTURE.md` | Tài liệu này |
| `01_schema.sql` | 41 bảng: 40 trong schema `core` (34 gốc + 6 giảng dạy bổ sung), 1 trong `private` |
| `../backend/assets/seed/02_seed_tham_so.sql` | Tham số lấy từ văn bản: thang điểm, hệ số tín chỉ, đơn giá 2025-2026, khoản thu, mức trần miễn giảm, loại học bổng, đối tượng, chính sách |
| `03_views_chatbot.sql` | 27 view trong schema `chatbot` (thứ duy nhất Text2SQL nhìn thấy) và phân quyền |
| `../backend/assets/seed/04_sample_data.sql` | Dữ liệu mẫu 62 sinh viên, chốt 31/08/2026 |
| `05_text2sql_context.md` | Quy tắc, thuật ngữ và 16 ví dụ SQL đã chạy thử cho Text2SQL Agent |
| `../backend/scripts/gen_sample_data.py` | Script sinh `04_sample_data.sql` (tất định) |

Thứ tự nạp: `01 → 02 → 03 → 04` trên PostgreSQL 14+. Khi chạy app, nguồn chính là model SQLAlchemy + Alembic và `backend/src/chatbot_haui/db/sql/views.sql`; `01`, `03` là bản tài liệu giữ khớp với nguồn đó. Phần triển khai khác thiết kế: mục 11.

## 1. Luồng tổng thể

```text
 USER ──► API Gateway ── xác thực, lấy ma_sv từ session (LLM không bao giờ thấy/sửa)
              │
              ▼
       ┌───────────────┐   6 lượt hội thoại gần nhất
       │ Query Rewriter│ ─► câu hỏi độc lập, không còn đại từ "thế còn", "môn đó"
       └──────┬────────┘
              ▼
       ┌───────────────┐   out_of_scope / chitchat / da_co_trong_lich_su
       │    Router     │ ───────────────────────────────► Direct Responder ─► END
       └──────┬────────┘
              │ can_tra_cuu
              ▼
       ┌───────────────┐
       │  Memory Read  │   Mem0 + Qdrant Cloud: sở thích, chủ đề quan tâm, mục tiêu
       └──────┬────────┘
              ▼
       ┌───────────────┐   ← profile (v_sinh_vien), tóm tắt hội thoại, memories
       │    Planner    │ ─► Plan dạng DAG
       └──────┬────────┘
              ▼
       ┌───────────────┐
       │   Executor    │   chạy bước theo depends_on, song song khi không phụ thuộc
       └──┬─────┬────┬─┘
          ▼     ▼    ▼
         RAG   SQL  Compute
          └─────┬────┘
                ▼
       ┌───────────────┐
       │  Aggregator   │   gom bằng chứng, giữ nguồn (Điều/Khoản, số QĐ, view)
       └──────┬────────┘
              ▼
       ┌───────────────┐
       │   Generator   │   câu trả lời có trích dẫn, nêu giả định
       └──────┬────────┘
              ▼
       ┌───────────────┐   OK ────────────────────► END
       │   Validator   │   THIEU_BANG_CHUNG ───────► Planner   (tối đa 1 lần)
       └───────────────┘   KHANG_DINH_SAI ─────────► Generator (tối đa 1 lần)
                           KHONG_THE_TRA_LOI ──────► Fallback ─► END

 END ──(bất đồng bộ)──► Memory Write: Mem0 trích xuất theo whitelist → lọc bằng code → Qdrant Cloud
```

So với bản thiết kế ban đầu, có năm thay đổi chính. Thêm Query Rewriter để câu hỏi nối tiếp không làm hỏng retrieval. Router chỉ là bộ phân loại rẻ để có đường tắt, không trùng vai trò với Planner. Plan là DAG có phụ thuộc chứ không phải danh sách tool song song. Thêm tool Compute vì LLM không đáng tin khi tính toán và so ngưỡng. Validator phân loại lý do thất bại thay vì cứ thất bại là lập lại kế hoạch. Thêm bộ nhớ dài hạn bằng Mem0 + Qdrant Cloud, chỉ lưu những loại thông tin được phép (mục 2.10).

## 2. Thành phần

### 2.1 API Gateway và phiên làm việc

Sinh viên đăng nhập, gateway xác thực và gắn `ma_sv` vào state. Mọi truy vấn DB của phiên đó chạy trong một transaction mà việc đầu tiên là `SELECT set_config('app.ma_sv', :ma_sv, true)`. Giá trị này đến từ session, không đi qua bất kỳ prompt nào, nên LLM không có cách nào thay đổi phạm vi dữ liệu.

Đầu phiên, gateway đọc sẵn `chatbot.v_sinh_vien` (một dòng: khóa, bậc, ngành, khối ngành, loại CTĐT, số học kỳ thiết kế, diện học bổng đầu vào) và đưa vào state dưới tên `profile`. Planner và RAG dùng profile này mà không cần gọi tool.

### 2.2 Query Rewriter

Model nhỏ. Đầu vào là câu hỏi hiện tại và tối đa 6 lượt gần nhất. Đầu ra là một câu hỏi tự đứng được. Ví dụ, sau câu "Kỳ trước em có đủ điều kiện học bổng không?" mà sinh viên hỏi tiếp "Thế thiếu điều kiện nào?", câu viết lại là "Kỳ gần nhất em thiếu điều kiện nào để được xét học bổng khuyến khích học tập?". Nếu câu đã tự đứng được thì giữ nguyên.

### 2.3 Router

Model nhỏ hoặc classifier, trả về một trong bốn nhãn:

| Nhãn | Ví dụ | Xử lý |
|---|---|---|
| `chitchat` | "Chào bạn", "Cảm ơn nhé" | Direct Responder |
| `out_of_scope` | "Viết giúp em bài luận", "Giá vàng hôm nay" | Direct Responder: từ chối lịch sự, nói rõ phạm vi |
| `da_co_trong_lich_su` | Hỏi lại đúng điều vừa được trả lời trong phiên | Direct Responder dùng câu trả lời cũ |
| `can_tra_cuu` | Mọi câu về quy chế hoặc dữ liệu cá nhân | Planner |

Nhãn `da_co_trong_lich_su` chỉ áp dụng trong cùng phiên. Không tái sử dụng câu trả lời có số liệu cá nhân giữa các phiên, vì dữ liệu có thể đã thay đổi.

### 2.4 Planner

Model mạnh nhất trong hệ thống. Đầu vào gồm câu hỏi đã viết lại, `profile`, tóm tắt hội thoại, danh sách tool kèm mô tả, và 3–5 plan mẫu. Đầu ra là JSON theo schema:

```json
{
  "steps": [
    {
      "id": "s1",
      "tool": "rag | sql | compute",
      "input": { "...": "có thể tham chiếu {profile.x} hoặc {s1.output}" },
      "depends_on": [],
      "purpose": "lấy gì, để làm gì"
    }
  ],
  "answer_focus": "câu trả lời cuối cần nêu những ý nào"
}
```

Các dạng plan chính:

**Chỉ quy chế.** "Điều kiện xét học bổng khuyến khích là gì?"

```json
{"steps": [
  {"id": "s1", "tool": "rag",
   "input": {"query": "điều kiện xét học bổng khuyến khích học tập", "filter": {"van_ban": "HocBong"}},
   "depends_on": []}
]}
```

**Chỉ dữ liệu cá nhân.** "Em còn nợ bao nhiêu?"

```json
{"steps": [
  {"id": "s1", "tool": "sql", "input": {"question": "Số tiền còn nợ theo từng kỳ và hạn nộp"}, "depends_on": []}
]}
```

**Kết hợp, song song.** "Kỳ trước em có đủ điều kiện học bổng không?" Nhờ view `v_xet_hb` đã tính sẵn điều kiện, hai bước không phụ thuộc nhau và chạy song song. RAG chỉ để trích dẫn căn cứ.

```json
{"steps": [
  {"id": "s1", "tool": "sql", "input": {"question": "Kết quả xét điều kiện học bổng KKHT kỳ gần nhất"}, "depends_on": []},
  {"id": "s2", "tool": "rag", "input": {"query": "điều kiện và xếp loại học bổng khuyến khích học tập"}, "depends_on": []}
]}
```

**Kết hợp, tuần tự SQL rồi RAG.** "Môn em trượt có được học cải thiện ở kỳ hè không?"

```json
{"steps": [
  {"id": "s1", "tool": "sql", "input": {"question": "Các môn em đang bị điểm F"}, "depends_on": []},
  {"id": "s2", "tool": "rag", "input": {"query": "học lại, học cải thiện, học kỳ phụ đối với học phần {s1.output.mon}"}, "depends_on": ["s1"]}
]}
```

**Kết hợp có tính toán.** "Kỳ tới em đăng ký 18 tín chỉ lý thuyết thì học phí khoảng bao nhiêu?"

```json
{"steps": [
  {"id": "s1", "tool": "sql", "input": {"question": "Đơn giá tín chỉ áp dụng cho em"}, "depends_on": []},
  {"id": "s2", "tool": "rag", "input": {"query": "hệ số tín chỉ học phí lý thuyết, thực hành"}, "depends_on": []},
  {"id": "s3", "tool": "compute", "input": {"expr": "18 * he_so_ly_thuyet * don_gia"}, "depends_on": ["s1", "s2"]}
]}
```

Quy tắc cho Planner: tối đa 5 bước; không tạo bước SQL cho thông tin đã có trong `profile`; câu hỏi về người khác thì trả plan rỗng kèm lý do để đi thẳng tới Fallback.

### 2.5 Executor

Code thuần, không phải LLM. Executor sắp xếp topo theo `depends_on`, chạy song song các bước cùng tầng, thay thế tham chiếu `{sN.output...}` bằng kết quả thật. Mỗi bước có timeout (RAG 8 giây, SQL 5 giây, Compute 1 giây). Bước lỗi được ghi `status = error` và tiếp tục; Validator sẽ quyết định có lập lại kế hoạch hay không.

### 2.6 Tool: RAG Agent

**Nạp tài liệu.** 13 văn bản trong `chunks.json` cần làm sạch trước khi embed (xem mục 9): bỏ Điều bị lặp, bổ sung Điều bị thiếu từ bản gốc, sửa bảng OCR lệch cột.

**Cắt chunk theo cấu trúc pháp quy.** Tách theo Chương → Điều → Khoản bằng regex trên các mẫu `Chương`, `Điều N.`, `N.`, `a)`. Mỗi chunk mặc định là một Điều; Điều dài hơn khoảng 800 token thì tách theo Khoản. Mỗi chunk được gắn tiền tố ngữ cảnh, ví dụ `[QĐ 725/QĐ-ĐHCN – Quy định xét học bổng – Điều 7. Học bổng KKHT – Khoản 1]`, để chunk tự đứng được khi retrieve.

**Metadata mỗi chunk:**

| Trường | Ví dụ | Dùng để |
|---|---|---|
| `van_ban` | `HocBong` | lọc theo văn bản |
| `so_qd`, `ngay_ban_hanh` | `725/QĐ-ĐHCN`, `2024-06-03` | trích dẫn |
| `hieu_luc_tu`, `hieu_luc_den` | `2024-06-03`, `null` | loại văn bản hết hiệu lực |
| `ap_dung_bac`, `ap_dung_khoa_tu/den`, `ap_dung_hinh_thuc` | `dai_hoc`, `null`, `chinh_quy` | lọc theo profile sinh viên |
| `chuong`, `dieu`, `khoan` | `II`, `7`, `1` | trích dẫn, đi theo tham chiếu chéo |
| `tham_chieu` | `["HocBong:4", "HocBong:5"]` | các Điều mà chunk này nhắc tới |

**Truy hồi.** Dùng hybrid: BM25 (sau khi tách từ tiếng Việt) kết hợp dense embedding đa ngôn ngữ hỗ trợ tiếng Việt, hợp nhất bằng Reciprocal Rank Fusion, rồi rerank bằng cross-encoder và lấy top 5. Văn bản pháp quy có nhiều cụm cần khớp chính xác ("Điều 12", "loại Khá", "học kỳ phụ"), nên dùng riêng dense sẽ bị hụt. Bộ lọc metadata lấy từ `profile`: chỉ lấy chunk còn hiệu lực và áp dụng cho bậc, khóa, hình thức của sinh viên.

**Vòng tự đánh giá (tối đa 2 vòng).** Một LLM nhỏ trả lời câu hỏi "Các đoạn này đã đủ để trả lời câu hỏi con chưa?". Nếu chưa, có hai cách: đi theo `tham_chieu` (nhiều Điều viết "theo quy định tại Điều 4", nên lấy thẳng Điều 4 qua metadata sẽ hiệu quả hơn tìm lại), hoặc viết lại truy vấn. Vòng này chỉ đánh giá đủ hay chưa đủ bằng chứng; việc câu trả lời cuối có đúng hay không là việc của Validator.

**Đầu ra:** danh sách `{chunk_id, text, van_ban, so_qd, dieu, khoan, score}`.

### 2.7 Tool: Text2SQL Agent

**Ngữ cảnh prompt.** Gồm DDL kèm comment của 24 view trong `03_views_chatbot.sql` (vài nghìn token, đưa hết vào prompt được, chưa cần schema linking), quy tắc và bảng thuật ngữ trong `05_text2sql_context.md`, và 3 ví dụ gần nhất lấy từ bộ few-shot.

**Kiểm tra SQL trước khi chạy.** Parse bằng thư viện SQL parser (ví dụ `sqlglot`), không dùng regex:

| Quy tắc | Lý do |
|---|---|
| Đúng một câu lệnh, gốc là `SELECT` (cho phép `WITH`) | chặn ghi dữ liệu, chặn nối nhiều lệnh |
| Mọi bảng tham chiếu đều thuộc schema `chatbot` | chặn đọc `core`, `private`, catalog hệ thống |
| Cấm hàm `set_config`, `current_setting`, `pg_sleep`, `dblink`, `lo_*`, `pg_read_*` | chặn đổi `app.ma_sv`, chặn đọc file, chặn làm treo |
| Có `LIMIT` ≤ 50, thiếu thì tự thêm | giới hạn kích thước kết quả |
| Output là chuỗi `UNSUPPORTED` → dừng, trả về cho Planner | câu hỏi về người khác |

**Thực thi.** `BEGIN READ ONLY` → `set_config('app.ma_sv', ...)` → câu SQL → `COMMIT`. Kết nối bằng role thuộc `chatbot_reader` (đã có `statement_timeout = 5s`). Nếu lỗi, đưa thông báo lỗi đã lược bớt về cho LLM sinh lại, tối đa 2 lần. Lỗi thô không bao giờ trả cho người dùng, vì nó làm lộ cấu trúc schema.

**Đầu ra:** `{sql, columns, rows (≤ 50), row_count, empty: bool}`. Kết quả rỗng là thông tin hợp lệ (ví dụ "không nợ môn nào"), không phải lỗi.

### 2.8 Tool: Compute

Chỉ nhận biểu thức số học và so sánh trên các biến lấy từ bước trước, đánh giá bằng một evaluator an toàn (không `eval` Python). Dùng cho các phép như nhân đơn giá, cộng khoản thu, so điểm với ngưỡng. Những phép tính cố định đã được đưa vào view (`v_xet_hb`, `v_cong_no`, `v_so_du`), nên Compute chủ yếu phục vụ câu hỏi giả định kiểu "nếu em đăng ký X tín chỉ thì…".

### 2.9 Aggregator, Generator, Validator

**Aggregator** gom kết quả các bước thành danh sách bằng chứng, mỗi mục có `id` và nguồn: `[QĐ 725, Điều 7, Khoản 1]` hoặc `[chatbot.v_xet_hb]`. Nếu hai chunk từ hai văn bản có hiệu lực khác nhau mâu thuẫn, ưu tiên văn bản mới hơn và ghi chú lại.

**Generator** viết câu trả lời tiếng Việt với bốn yêu cầu. Mỗi con số và mỗi điều kiện phải gắn với một bằng chứng. Trích dẫn dạng "theo Điều 7 Quy định xét học bổng (QĐ 725/QĐ-ĐHCN)". Nêu rõ giả định khi câu hỏi mơ hồ, ví dụ "mình lấy học kỳ gần nhất là HK2 2025-2026". Với học bổng thì chỉ nói "đủ điều kiện tham gia xét", không hứa "sẽ được nhận".

**Validator** là LLM cỡ vừa, trả JSON:

```json
{"verdict": "OK | THIEU_BANG_CHUNG | KHANG_DINH_SAI | KHONG_THE_TRA_LOI",
 "loi": ["câu 'GPA 3.8' không có trong bằng chứng"],
 "thieu": ["chưa trả lời ý hạn nộp"]}
```

| Verdict | Xử lý |
|---|---|
| `OK` | trả lời |
| `THIEU_BANG_CHUNG` | quay lại Planner kèm danh sách ý còn thiếu, tối đa 1 lần |
| `KHANG_DINH_SAI` | quay lại Generator kèm danh sách lỗi, tối đa 1 lần |
| `KHONG_THE_TRA_LOI` | Fallback: nói rõ không tìm thấy căn cứ, gợi ý liên hệ Phòng Công tác sinh viên hoặc Phòng Đào tạo |

Hết lượt thử mà vẫn chưa `OK` thì cũng đi Fallback. Không lặp vô hạn.

### 2.10 Bộ nhớ

Có hai tầng bộ nhớ.

**Bộ nhớ phiên** dùng checkpointer của LangGraph, lưu vào PostgreSQL của hệ thống. Nó giữ 6 lượt gần nhất cộng một bản tóm tắt cuộn khi hội thoại dài, phục vụ Query Rewriter và Router.

**Bộ nhớ dài hạn** dùng Mem0 ở chế độ OSS: Mem0 chạy như thư viện ngay trong tiến trình của app, không cần Mem0 server. Vector và nội dung memory lưu trên Qdrant Cloud, trong collection `haui_chatbot_memory`, tách riêng khỏi collection văn bản quy chế.

#### Được lưu và không được lưu

Nguyên tắc: memory giữ những gì **chỉ có trong hội thoại**, tức những thứ DB không có. Những gì DB đã có thì luôn lấy từ DB, vì DB là dữ liệu mới nhất.

| Được lưu | Ví dụ |
|---|---|
| Cách giao tiếp | xưng "em", thích trả lời ngắn, muốn có trích dẫn Điều khoản |
| Chủ đề đang quan tâm | đang tìm hiểu học bổng KKHT, quan tâm khoản nợ học phí kỳ này, hỏi về điều kiện tốt nghiệp |
| Mục tiêu, dự định sinh viên tự nói | muốn đạt học bổng loại Giỏi, định học cải thiện môn Giải tích ở kỳ hè, định bảo lưu |
| Câu hỏi còn dang dở | hỏi thủ tục xin miễn giảm nhưng chưa hỏi tiếp phần hồ sơ |

| Không được lưu | Lý do |
|---|---|
| Con số học vụ, tài chính: điểm, GPA, số tín chỉ, số tiền, số dư | DB đã có và luôn mới hơn; lưu vào memory chỉ tạo bản sao dễ cũ |
| Hoàn cảnh nhạy cảm: hộ nghèo, cận nghèo, khuyết tật, dân tộc, mồ côi, bệnh | dữ liệu nhạy cảm, nằm trên cloud bên ngoài; chính sách được hưởng đã có trong `sv_chinh_sach` |
| Kỷ luật, cảnh báo học tập, buộc thôi học | như trên; đã có trong `ky_luat`, `ket_qua_hk` |
| Thông tin định danh: SĐT, địa chỉ, CCCD, ngày sinh | không phục vụ câu hỏi quy chế nào |
| Thông tin về người khác | không thuộc phạm vi dữ liệu của sinh viên đang đăng nhập |

Tên chủ đề như "điểm", "học phí", "học bổng", "nợ môn" được phép xuất hiện trong memory. Chỉ con số cụ thể và các loại hoàn cảnh nhạy cảm là bị chặn. Nhờ vậy bot vẫn nhớ được "em đang lo về khoản nợ học phí kỳ này", còn con số nợ thì lấy mới từ `v_cong_no` mỗi lần hỏi.

#### Cách thực thi

Quy tắc trên được thực thi ở ba chỗ, không chỉ dựa vào prompt:

| Bước | Cơ chế |
|---|---|
| Định danh | `user_id` là HMAC của `ma_sv` với khóa bí mật (`MEMORY_SALT`), trên cloud không có mã sinh viên thật |
| Trích xuất | thay prompt trích xuất mặc định của Mem0 bằng prompt chỉ cho phép 4 loại ở bảng "Được lưu", yêu cầu bỏ mọi con số và hoàn cảnh cá nhân |
| Lọc sau trích xuất | code kiểm tra từng memory Mem0 vừa tạo hoặc cập nhật: còn chữ số, hoặc chứa từ khóa thuộc bảng "Không được lưu" (hộ nghèo, khuyết tật, dân tộc, kỷ luật, cảnh báo, số điện thoại…) thì xóa ngay |
| Lọc khi đọc | chạy lại bộ lọc trên kết quả `search` trước khi đưa vào prompt, phòng trường hợp memory cũ lọt qua |
| Xóa | khi sinh viên yêu cầu: `delete_all(user_id)` trên Qdrant, cùng với dữ liệu trong DB |

Cần lọc bằng code vì LLM trích xuất có thể bỏ sót quy tắc trong prompt. Nếu muốn kiểm soát chặt hơn nữa, có thể tự trích xuất bằng một LLM nhỏ với schema JSON cố định gồm đúng 4 loại trên, rồi ghi vào Mem0 ở dạng nguyên văn, không để Mem0 tự suy luận.

#### Vị trí trong đồ thị

**Memory Read** chạy ngay trước Planner: `search(câu hỏi, user_id)`, lấy top 5, đưa vào state `memories`. Planner dùng memory để hiểu ngữ cảnh ("em muốn đạt học bổng loại Giỏi" → khi sinh viên hỏi "kỳ này em cần bao nhiêu điểm", Planner biết cần lấy ngưỡng loại Giỏi). Generator dùng memory cho giọng văn và độ dài. Memory không được dùng làm bằng chứng cho con số trong câu trả lời và không đi vào Text2SQL.

**Memory Write** chạy bất đồng bộ sau END: `add([user, assistant], user_id)`, rồi lọc. Lỗi ở bước này không ảnh hưởng câu trả lời.

Cấu hình cần: `QDRANT_URL`, `QDRANT_API_KEY`, `OPENAI_API_KEY` (cho trích xuất và embedding), `MEMORY_SALT`. `embedding_model_dims` phải khớp model embedding; đổi model thì tạo collection mới. Mem0 OSS có thể ghi lịch sử thay đổi memory ra một file SQLite cục bộ; cần xác định vị trí file này theo phiên bản đang dùng để đưa vào quy trình xóa dữ liệu.

## 3. State và đồ thị

State dùng chung cho mọi node (phù hợp để dựng bằng LangGraph):

```python
class State(TypedDict):
    ma_sv: str                  # từ session; không đưa vào prompt
    profile: dict               # 1 dòng v_sinh_vien
    history: list[dict]
    query: str
    query_rewritten: str
    route: str                  # chitchat | out_of_scope | da_co_trong_lich_su | can_tra_cuu
    memories: list[str]         # từ Mem0, đã lọc: sở thích, chủ đề, mục tiêu
    plan: dict
    results: dict[str, dict]    # step_id -> {status, output, source}
    evidence: list[dict]
    draft: str
    verdict: dict
    replan_count: int
    regen_count: int
```

| Cạnh | Điều kiện |
|---|---|
| `rewriter → router` | luôn |
| `router → direct` | `route != can_tra_cuu` |
| `router → memory_read → planner` | `route == can_tra_cuu` |
| `planner → fallback` | plan rỗng (câu hỏi ngoài phạm vi dữ liệu) |
| `planner → executor → aggregator → generator → validator` | luôn |
| `validator → planner` | `THIEU_BANG_CHUNG` và `replan_count < 1` |
| `validator → generator` | `KHANG_DINH_SAI` và `regen_count < 1` |
| `validator → END / fallback` | các trường hợp còn lại |
| `END → memory_write` | bất đồng bộ, sau khi đã trả lời |

Ngân sách LLM mỗi câu hỏi: đường tắt 2 lần gọi (rewriter, router); câu hỏi tra cứu thông thường 6–8 lần (rewriter, router, planner, 1–2 lần RAG judge, 1 lần SQL, generator, validator), cộng 1 lần trích xuất memory chạy nền không tính vào độ trễ. Rewriter, Router và RAG judge dùng model nhỏ để giữ độ trễ.

## 4. Cơ sở dữ liệu

### 4.1 Nguyên tắc chia dữ liệu giữa DB và RAG

DB lưu sự kiện (điểm, đăng ký, giao dịch, quyết định) và kết quả chính thức do hệ thống đào tạo tính (TB học kỳ, xếp loại, cảnh báo, điểm rèn luyện). Bảng số liệu trong văn bản (đơn giá, mức trần, khoản thu, thang điểm, hệ số) cũng vào DB, dưới dạng bảng tham số có năm học hoặc thời gian hiệu lực. Điều kiện dạng văn xuôi (tiêu chí xét, hồ sơ, thủ tục) để ở RAG. Riêng điểm xét học bổng có công thức phức tạp nên được viết sẵn thành view, không để LLM tự sinh SQL.

### 4.2 Ba schema

| Schema | Nội dung | Ai truy cập |
|---|---|---|
| `core` | 34 bảng nghiệp vụ | owner của view, hệ thống nghiệp vụ |
| `private` | `tai_khoan` | chỉ dịch vụ đăng nhập |
| `chatbot` | 24 view | role `chatbot_reader` |

### 4.3 Các bảng trong `core`

| Nhóm | Bảng |
|---|---|
| Danh mục đào tạo (9) | `khoa`, `khoi_nganh`, `nganh`, `nien_khoa`, `ctdt`, `hoc_ky`, `mon`, `nhom_tu_chon`, `ctdt_mon` |
| Sinh viên (4) | `sinh_vien` (gồm cả thông tin cá nhân, không đưa vào view), `bien_dong`, `ky_luat`, `thanh_tich` |
| Học tập (7) | `thang_diem`, `lop_hp`, `dang_ky`, `diem_hp`, `ket_qua_hk`, `ren_luyen`, `dk_tot_nghiep` |
| Học bổng (3) | `loai_hb`, `muc_hb`, `hoc_bong` |
| Đối tượng và chính sách (6) | `doi_tuong`, `sv_doi_tuong`, `chinh_sach`, `sv_chinh_sach`, `muc_tran`, `tham_so` |
| Học phí và tài chính (5) | `he_so_tc`, `don_gia`, `khoan_thu`, `phai_thu`, `giao_dich` |

Các quyết định thiết kế quan trọng:

`hoc_ky.ma_hk` có năm học (`'20251'`) và cột `ma_hk_chinh` để gộp học kỳ phụ vào học kỳ chính, đúng yêu cầu của cả Quy chế đào tạo lẫn quy định học bổng. `diem_hp` lưu mỗi lần học một dòng, có `lan_hoc` và `chinh_thuc`, vì điểm xét học bổng chỉ tính học phần học lần đầu còn điểm tích lũy lấy lần cao nhất. `mon` có tín chỉ thành phần (`tc_lt`, `tc_dac_thu`, `tc_th`) để tính số tín chỉ học phí, và cờ `xet_hb` đặt tường minh vì quy định có cụm "và các môn học khác (nếu có)". Miễn giảm học phí được mô hình theo mức trần khối ngành (`muc_tran`) cộng chính sách được duyệt có thời hạn (`sv_chinh_sach`), không phải một tỷ lệ phần trăm trên học phí thực tế. Mỗi dòng học phí trong `phai_thu` lưu lại `n_hp`, `he_so_lop`, `don_gia` tại thời điểm tính, nên luôn giải thích được con số. `giao_dich` giữ trạng thái hiện tại; số dư và công nợ được tính từ sổ cái này.

### 4.4 Các view trong `chatbot`

| View | Trả lời câu hỏi kiểu |
|---|---|
| `v_sinh_vien` | em học khóa nào, ngành gì, CTĐT loại gì |
| `v_diem` | điểm môn X, môn nào trượt, môn nào chưa có điểm |
| `v_ket_qua_hk` | GPA, xếp loại, điểm rèn luyện, cảnh báo |
| `v_xet_hb` | có đủ điều kiện học bổng không, thiếu điều kiện nào |
| `v_tien_do` | còn thiếu môn nào trong CTĐT |
| `v_tot_nghiep` | đủ chuẩn ngoại ngữ, GDTC, GDQP chưa |
| `v_hoc_phi` | học phí từng môn và công thức |
| `v_phai_thu` | từng khoản phải nộp, đã trả, còn nợ |
| `v_cong_no` | tổng nợ theo kỳ, hạn nộp |
| `v_giao_dich` | lịch sử nộp và nhận tiền |
| `v_so_du` | số dư tài khoản cá nhân |
| `v_don_gia` | đơn giá tín chỉ áp dụng cho em |
| `v_hoc_bong` | học bổng đã nhận |
| `v_chinh_sach` | chính sách miễn giảm, hỗ trợ đang hưởng |
| `v_ky_luat` | có đang bị kỷ luật không (không lộ nội dung vi phạm) |
| `ref_thang_diem`, `ref_he_so_tc`, `ref_don_gia`, `ref_khoan_thu`, `ref_muc_tran`, `ref_loai_hb`, `ref_muc_hb`, `ref_chinh_sach`, `ref_hoc_ky` | dữ liệu chung, không gắn với sinh viên |

`v_xet_hb` là view quan trọng nhất cho câu hỏi kết hợp. Nó tính theo QĐ 725 Điều 4 và 7: chỉ học phần học lần đầu trong học kỳ chính và học kỳ phụ gộp vào; loại GDTC, GDQP, CNTT, ngoại ngữ; kiểm tra TB xét ≥ 2.5, rèn luyện từ Tốt trở lên, không học phần nào dưới 2.0, đủ 15 tín chỉ (học kỳ cuối là 7), trong thời gian thiết kế, không bị kỷ luật, không trùng học bổng HaUI; rồi xếp loại. View chưa xử lý ngoại lệ "Nhà trường bố trí không đủ 15 tín chỉ" và việc kéo dài thời gian do bảo lưu.

## 5. Văn bản và nơi lưu

| Khóa trong `chunks.json` | Văn bản | Vào DB | Để ở RAG |
|---|---|---|---|
| `HocBong` | Quy định xét học bổng (QĐ 725/QĐ-ĐHCN, 03/06/2024) | `loai_hb`, `muc_hb`, cờ `mon.xet_hb`, logic `v_xet_hb` | điều kiện, thủ tục, hồ sơ |
| `HocBongNTB` | HB khuyến học Nguyễn Thanh Bình (QĐ 279/QĐ-ĐHCN) | `nganh.khoi_ntb`, `hoc_bong.dt_ntb` | đối tượng, điều kiện, tỷ lệ |
| `MucThuHP` | Mức thu học phí 2025-2026 (QĐ 778/QĐ-ĐHCN) | `don_gia` | phần diễn giải |
| `TinhHocPhi` | Quy định tính học phí lớp học phần | `he_so_tc`, `lop_hp.he_so`, snapshot trong `phai_thu` | bảng hệ số lớp theo sĩ số |
| `KhoanThu` | Các khoản thu 2025-2026 (QĐ 1659/QĐ-ĐHCN) | `khoan_thu` | đối tượng miễn, giảm |
| `ThuPhiKhongXemLai` | Thông báo phí không đến xem lại bài thi | `khoan_thu` (`PHI_XEM_LAI`) | quy trình |
| `ChinhSachSV` | Quy định thực hiện chính sách cho sinh viên | `doi_tuong`, `chinh_sach`, `muc_tran` | hồ sơ, thủ tục, thời hạn |
| `DRL` | Quy định đánh giá kết quả rèn luyện | `ren_luyen` | thang điểm chi tiết, quy trình |
| `DanhGiaKQHT` | Quy định đánh giá kết quả học tập | `thang_diem` | hoãn thi, phúc khảo |
| `QuyCheDaoTao` | Quy chế đào tạo | `ket_qua_hk`, `dk_tot_nghiep` | cảnh báo, thôi học, tốt nghiệp |
| `KhenThuongKyLuat` | Quy định khen thưởng, kỷ luật | `ky_luat` | hình thức, thời hạn, hệ quả |
| `CongNhanMonHocTamThoi` | Công nhận kết quả, chuyển đổi tín chỉ | điểm `R` trong `thang_diem` | toàn bộ |
| `QuyCheCTSV` | Quy chế công tác sinh viên | — | toàn bộ |

Số quyết định của các văn bản còn lại không có trong `chunks.json` (phần đầu văn bản bị cắt), cần điền từ bản gốc vào metadata.

## 6. Bảo mật và quyền riêng tư

Bảo vệ theo nhiều lớp, không lớp nào là duy nhất:

| Lớp | Cơ chế |
|---|---|
| Danh tính | `ma_sv` từ session, đặt bằng `set_config` trong code |
| Phạm vi dòng | mọi view `v_*` lọc theo `chatbot.ma_sv()`; không đặt phiên thì view trả 0 dòng |
| Phạm vi cột | view liệt kê cột tường minh; SĐT, địa chỉ, ngày sinh, dân tộc, nội dung vi phạm không có trong view nào |
| Quyền DB | `chatbot_reader` chỉ có `SELECT` trên schema `chatbot`; truy vấn thẳng `core` báo `permission denied` |
| Kiểm tra SQL | parser, whitelist schema, cấm `set_config` và các hàm nguy hiểm |
| Thực thi | transaction `READ ONLY`, `statement_timeout = 5s`, `LIMIT` |
| Lỗi | lỗi DB chỉ ghi log phía server |

Truy vấn tổng hợp trên dữ liệu người khác (xếp hạng lớp, GPA trung bình lớp, số người được học bổng) bị chặn ngay từ thiết kế: không view nào chứa dữ liệu của sinh viên khác, và quy tắc Text2SQL trả `UNSUPPORTED` cho loại câu này.

Dữ liệu điểm, tài chính và chính sách vẫn là dữ liệu cá nhân, một số thuộc loại nhạy cảm (khuyết tật, hộ nghèo, dân tộc). Khi kết quả SQL được đưa vào LLM qua API bên ngoài, dữ liệu này rời khỏi hệ thống và có thể ra nước ngoài. Cần rà soát theo Nghị định 13/2023/NĐ-CP và Luật Bảo vệ dữ liệu cá nhân 2025 trước khi triển khai thật. Các hướng giảm rủi ro: tự host model cho Generator và Validator; bỏ họ tên, mã sinh viên khỏi kết quả trước khi gửi; che dữ liệu trong log và trace; đặt thời hạn lưu log.

Bộ nhớ dài hạn lưu trên Qdrant Cloud, tức là ngoài hạ tầng của trường. Vì vậy nó chỉ giữ sở thích, chủ đề và mục tiêu, không giữ số liệu hay hoàn cảnh nhạy cảm, và dùng `user_id` đã băm (mục 2.10). API key của cluster chỉ cấp cho backend. Yêu cầu xóa dữ liệu của sinh viên phải xóa cả trong DB lẫn trong collection memory.

## 7. Đánh giá

**Bộ câu hỏi.** Khoảng 150 câu, chia theo loại:

| Loại | Số câu | Ví dụ |
|---|---|---|
| Chỉ quy chế | 40 | "Học kỳ phụ là gì?", "Bị khiển trách thì bao lâu hết hiệu lực?" |
| Chỉ dữ liệu cá nhân | 35 | "GPA của em?", "Em còn nợ bao nhiêu?" |
| Kết hợp | 35 | "Em có đủ điều kiện học bổng không?", "Môn em trượt có được học hè không?" |
| Hội thoại nhiều lượt | 15 | chuỗi 3–4 câu nối tiếp |
| Ngoài phạm vi, không trả lời được | 10 | quy định không đề cập |
| Tấn công | 15 | hỏi dữ liệu người khác, chèn `set_config`, prompt injection |

**Chỉ số theo tầng.**

| Tầng | Chỉ số |
|---|---|
| Router | accuracy trên 4 nhãn |
| Planner | chọn đúng tool, đúng thứ tự phụ thuộc |
| RAG | Recall@5 theo (văn bản, Điều, Khoản) đúng |
| Text2SQL | execution accuracy: so tập kết quả với SQL chuẩn |
| Câu trả lời | faithfulness (mọi khẳng định có bằng chứng), trích dẫn đúng Điều |
| Bảo mật | tỷ lệ chặn đúng câu tấn công, yêu cầu 100% |

**Sinh viên mẫu để kiểm thử.** Trong `04_sample_data.sql`:

| Tình huống | Mã SV |
|---|---|
| HB HaUI toàn khóa / năm nhất / 5 triệu | 2025619166 / 2025637924 / 2025628155 |
| Khuyết tật: miễn học phí, nhận HB NTB | 2024619567 |
| DTTS hộ nghèo: miễn học phí, hỗ trợ chi phí học tập | 2025646999 |
| Hộ cận nghèo, học lực xuất sắc, đủ điều kiện tham gia xét KKHT | 2023655593 |
| Học lực giỏi (TB xét 3,57) nhưng trượt điều kiện HB kỳ gần nhất vì rèn luyện 68 điểm | 2024628144 |
| Mồ côi cha: nhận HB NTB | 2024633657 |
| Cha bị TNLĐ: giảm 50% học phí | 2023629820 |
| Kỷ luật cảnh cáo / khiển trách | 2023619595 / 2024642770 |
| Bảo lưu rồi quay lại | 2023634292 |
| Buộc thôi học | 2024643553 |
| Có điểm I | 2024658893 |
| Olympic quốc gia, HB tài trợ | 2023617043 |
| Còn nợ học phí | 2023654041, 2022632465, 2023625316, 2024619980, 2024639830, 2025651790, 2023655593 |
| K17 chưa tốt nghiệp vì thiếu ngoại ngữ | 2022632465, 2022659727 |
| Có kỳ thực tập doanh nghiệp (K17) | 2022612814, 2022623840 |
| Có ca thi không đủ điều kiện dự thi | 2025629882, 2023654041 |

Mật khẩu mọi tài khoản mẫu = mã sinh viên. Dữ liệu sinh bởi `backend/scripts/gen_sample_data.py`; từ 25/09/2026 script tất định (trước đó phụ thuộc `PYTHONHASHSEED`, nên bảng này đã được cập nhật theo bản sinh lại).

## 8. Vận hành

Mọi node ghi trace (ví dụ Langfuse hoặc LangSmith) với input, output, độ trễ, số token; dữ liệu cá nhân trong trace phải được che. Có thể cache kết quả RAG theo câu hỏi đã chuẩn hóa vì văn bản ít thay đổi; không cache kết quả SQL giữa các phiên. Trong câu trả lời có số liệu tài chính, nêu thời điểm dữ liệu ("số liệu cập nhật đến ngày …") vì DB có thể là bản sao đồng bộ có độ trễ. Khi có quyết định mới (đơn giá năm học mới, khoản thu mới), thêm dòng vào bảng tham số và nạp văn bản mới vào RAG với `hieu_luc_tu`; văn bản cũ được đặt `hieu_luc_den` chứ không xóa.

## 9. Vấn đề đã biết

**Dữ liệu văn bản (`chunks.json`).** Nhiều Điều bị lặp: `DanhGiaKQHT` (15 lần), `ChinhSachSV` (12), `QuyCheCTSV` (11), `CongNhanMonHocTamThoi` (8), `KhenThuongKyLuat` (8), `DRL` (7), `HocBong` (3). Có Điều bị thiếu: `QuyCheDaoTao` thiếu Điều 1–2 (trong khi Điều 2 về thời gian học tối đa được các Điều sau viện dẫn), `ChinhSachSV` thiếu Điều 9, 15, 16 (Điều 15 là đối tượng chính sách nội trú, được phần mức hưởng tham chiếu), `DanhGiaKQHT` thiếu Điều 13–16 và 28–29, `QuyCheCTSV` thiếu Điều 1, 7, 10. Bảng khoản thu bị OCR lệch cột. Phần đầu nhiều văn bản mất số quyết định.

**Số liệu chưa có.** Mức tiền học bổng KKHT (theo Quy chế chi tiêu nội bộ) và mức học bổng NTB không có trong văn bản; dữ liệu mẫu đang dùng số minh họa có ghi chú rõ. Đơn giá học phí chỉ có năm học 2025-2026.

**Quy tắc cần xác nhận.** Điều kiện "không có học phần nào dưới 2.0" không nói rõ phạm vi; `v_xet_hb` đang xét mọi học phần có điểm quy đổi trong kỳ. Hệ số lớp theo yêu cầu và phạm vi áp dụng của quy định tính học phí (sinh viên nhập học từ 01/07/2025 hay mọi sinh viên từ ngày đó) cần hỏi lại phòng Tài chính.

**Dữ liệu mẫu.** Tổng tín chỉ mỗi CTĐT khoảng 113–120, thấp hơn thực tế. Tên môn, mã môn, lớp là giả lập hợp lý, không phải danh mục thật của trường.

## 10. Lộ trình

**Giai đoạn 1: học phí và dữ liệu học tập.** Text2SQL trên `v_diem`, `v_ket_qua_hk`, `v_phai_thu`, `v_cong_no`, `v_hoc_phi`, `v_so_du`; RAG trên nhóm văn bản học phí. Đây là phần DB đã đầy đủ và ít rủi ro sai nhất.

**Giai đoạn 2: học bổng và chính sách.** Bật `v_xet_hb`, `v_hoc_bong`, `v_chinh_sach`; RAG trên `HocBong`, `HocBongNTB`, `ChinhSachSV`, `DRL`. Cần làm sạch `chunks.json` trước. Bật bộ nhớ dài hạn (Mem0 + Qdrant Cloud), kiểm tra bộ lọc trên log thật trước khi mở cho toàn bộ sinh viên.

**Giai đoạn 3: tiến độ và tốt nghiệp.** `v_tien_do`, `v_tot_nghiep`; RAG trên `QuyCheDaoTao`, `DanhGiaKQHT`, `KhenThuongKyLuat`. Bổ sung xử lý bảo lưu trong `v_xet_hb`.

Mỗi giai đoạn chỉ mở rộng khi bộ đánh giá của giai đoạn trước đạt ngưỡng đề ra.

## 11. Trạng thái triển khai (25/09/2026)

Luồng mục 1–3 đã chạy đủ trong `backend/src/chatbot_haui/ai/`. Các điểm khác thiết kế ở trên, kèm lý do:

| Mục | Thiết kế | Đang chạy | Lý do |
|---|---|---|---|
| 2.6 chunk | Theo Chương/Điều/Khoản, metadata `so_qd`, `dieu`, `hieu_luc`, `tham_chieu` | Giữ chunk cũ (theo tiêu đề markdown, lưu ở `backend/assets/chunks.json`), payload chỉ `source`, `raw_text`; thêm vector sparse BM25 | Chưa có bản OCR lưu lại; OCR lại cần GPU ≥ 8GB. Hệ quả: trích dẫn chỉ tới tên văn bản, chưa lọc theo hiệu lực/bậc/khóa, vòng tự đánh giá viết lại truy vấn thay vì đi theo `tham_chieu` |
| 2.6 BM25 | Sau khi tách từ tiếng Việt | Token = âm tiết + bigram âm tiết, IDF do Qdrant tính | Không thêm bộ tách từ; bigram giữ được cụm nhiều âm tiết |
| 2.4, 2.7 few-shot | 3–5 plan mẫu; 3 cặp SQL mẫu gần nhất | Không few-shot, chỉ quy tắc + thuật ngữ + mô tả view | `CLAUDE.md` cấm few-shot bằng ví dụ đã cung cấp; 16 ví dụ SQL ở `05` cũng là bộ test |
| 2.4 | Planner nhận câu đã viết lại | Planner, Generator, Validator nhận cả câu gốc và câu viết lại, phạm vi theo câu gốc | Rewriter (model nhỏ) từng thu hẹp phạm vi câu hỏi khi chạy thử |
| 2.5 timeout | RAG 8s, SQL 5s | RAG, SQL 45s mỗi bước (DB vẫn 5s) | Timeout bước tính cả thời gian gọi LLM bên trong (judge, sinh/sửa SQL) |
| 2.7 | — | Bỏ cột `ma_sv`, `ho_ten` khỏi kết quả SQL trước khi đưa vào LLM | Mục 6: không gửi định danh ra LLM ngoài |
| 2.9 | Generator nêu thời điểm dữ liệu | Thời điểm dữ liệu (`DATA_AS_OF`) là một mục bằng chứng | Validator chỉ thấy bằng chứng; ngày nằm ngoài bằng chứng bị bác là bịa |
| 3 | `aggregator → generator` luôn | Không có bằng chứng nào → thẳng Fallback | Tiết kiệm 2 lần gọi LLM cho kết cục chắc chắn là Fallback |
| 2.10 memory | Mem0 trích xuất bằng prompt đã thay, lọc sau | Tự trích xuất theo schema 4 loại (LLM nhỏ), lọc bằng code, ghi `add(infer=False)`; history Mem0 để trong RAM | Mem0 2.x chỉ thêm (không cập nhật/xóa) và lưu nguyên văn tin nhắn vào SQLite cục bộ |
| 2.10 phiên | Checkpointer, 6 lượt + tóm tắt | Như thiết kế, thread = tài khoản; "cùng phiên" = các lượt cách nhau ≤ 30 phút | Dùng cho nhãn `da_co_trong_lich_su` |
| Trả lời | — | Không stream token; gửi trạng thái từng bước rồi câu trả lời đã qua Validator | Validator chạy sau Generator và có thể bắt viết lại |
| 4 | 35 bảng, 24 view | 41 bảng, 27 view: thêm `giang_vien`, `lich_hoc`, `lich_thi`, `lich_thi_sv`, `doanh_nghiep`, `thuc_tap` và `v_lich_hoc`, `v_lich_thi`, `v_thuc_tap` | Giữ các trang Lịch học, Lịch thi, Thực tập của frontend; chatbot trả lời được lịch học/thi/thực tập |
| LLM | Model nhỏ / vừa / mạnh | Model chính (Gemini) và model nhỏ (Groq) ở hai provider, mỗi cỡ tự chuyển sang provider còn lại khi lỗi | Chia quota; free tier của cả hai provider đều thấp |

**Vấn đề còn mở**

- Câu hỏi công nợ "theo kỳ" (VD "học phí kỳ này") được hiểu là kỳ gần nhất có dữ liệu (đúng quy tắc mục `05`), nên câu trả lời có thể không nhắc khoản nợ quá hạn của kỳ trước. Cần quyết định nghiệp vụ: có luôn nêu nợ tồn các kỳ khác hay không.
- Quota free tier (Gemini preview theo request/ngày, Groq 8k token/phút) không đủ cho vận hành thật hay chạy đánh giá lớn.
- Chunk theo Điều/Khoản (hàng 1) để trích dẫn tới Điều/Khoản và lọc theo hiệu lực.
- Bộ đánh giá Text2SQL (execution accuracy), Router, Planner và câu tấn công theo mục 7 chưa có; `scripts/evaluate.py` mới đo câu trả lời và độ phủ văn bản của RAG.

