# DPIA-lite — ghi nhận checkpoint 5

1. Loại dữ liệu và phân loại:
Hệ thống xử lý hai nhóm dữ liệu chính. Nhóm dữ liệu nội bộ (internal) gồm các tệp yêu cầu hỗ trợ (ticket) dạng Markdown trong corpus chứa thông tin sự vụ hỗ trợ khách hàng. Nhóm dữ liệu hạn chế (restricted) gồm thông tin định danh cá nhân của khách hàng trong data/customers.json bao gồm số căn cước công dân, số điện thoại, số tài khoản ngân hàng, họ tên và địa chỉ thư điện tử.

2. Mục đích xử lý và principal:
Mục đích xử lý gồm summarize-tickets để tổng hợp nội dung các yêu cầu hỗ trợ và support-reply để tra cứu thông tin hỗ trợ khách hàng. Các principal mô phỏng gồm `support_l1` (nhân viên hỗ trợ cấp 1, chỉ được dùng `search_docs` cho mục đích tóm tắt và phản hồi) và `dpo` (cán bộ bảo vệ dữ liệu, được phép dùng `search_docs` và `read_customer` cho mục đích tra cứu và kiểm toán bảo mật).

3. Dữ liệu đi qua những run/tool nào, endpoint nào:
Dữ liệu văn bản ticket chỉ đi vào Run A thông qua công cụ `search_docs`. Run A trích xuất số định danh ticket dạng số nguyên từ tên tệp và chuyển qua ranh giới sang Run B. Run B sử dụng số định danh ticket để đối chiếu trường `related_tickets` trong `customers.json`, sau đó gọi `read_customer` đối với khách hàng hợp lệ nếu chính sách cho phép. Dữ liệu khách hàng không bao giờ được chuyển ra ngoài qua công cụ `http_post` tới endpoint đích http://127.0.0.1:10024/reconcile vì bị chính sách kiểm soát chặn lại.

4. Bằng chứng deny/allow và giới hạn của mock:
Bằng chứng allow và deny được lưu đầy đủ trong reports/ledger.jsonl với 23 bản ghi có lý do rõ ràng, xác thực chuỗi băm thành công, trong đó thao tác `http_post` bị deny và các yêu cầu `read_customer` của `support_l1` bị deny. Tệp reports/attack-after.log rỗng chứng minh dữ liệu cá nhân không bị rò rỉ ra sink sau khi áp dụng kiểm soát. Giới hạn của hệ thống là mô hình MockLLM hoạt động dựa trên các mẫu từ khóa mô phỏng thay vì xử lý ngôn ngữ tự nhiên đầy đủ, đồng thời toàn bộ dữ liệu kiểm thử là dữ liệu tổng hợp cục bộ.
