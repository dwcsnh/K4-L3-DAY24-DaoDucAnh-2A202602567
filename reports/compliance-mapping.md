# Compliance mapping — ghi nhận checkpoint 5

| Nguồn / yêu cầu | Control đã làm | Evidence file:dòng | Giới hạn |
|---|---|---|---|
| Luật 91/2025/QH15 | Nhận diện và che giấu dữ liệu định danh cá nhân gồm CCCD, số điện thoại, số tài khoản, email; phân loại dữ liệu restricted và kiểm soát truy cập theo vai trò | agent/pii.py:14-63, agent/policy.py:44-50, agent/runner.py:65-98 | Dùng quy tắc biểu thức chính quy trên dữ liệu mô phỏng, chưa xác minh toàn bộ các điều khoản chi tiết của văn bản gốc |
| NĐ 356/2025/NĐ-CP | Ràng buộc mục đích xử lý theo vai trò và ghi nhật ký kiểm toán chuỗi băm phục vụ truy vết trách nhiệm giải trình | agent/policy.py:53-56, agent/ledger.py:12-68, reports/ledger.jsonl:1-23 | Chuỗi băm lưu trên tệp cục bộ chưa có mốc thời gian ngoài độc lập, điều khoản cụ thể ghi nhận chưa xác minh |
| Luật AI 134/2025/QH15 | Ngăn ngừa mô hình tự động hành động vượt quyền bằng cơ chế ủy quyền OBO có hạn giờ và phân tách hai luồng Run A và Run B | agent/runner.py:32-60, agent/policy.py:36-41, agent/policy.py:58-69 | Đánh giá trên môi trường mô phỏng cục bộ, chưa xác minh quy chuẩn kỹ thuật hệ thống AI chính thức |
| OWASP ASI01, ASI03, ASI04 | ASI01: tách bạch dữ liệu không tin cậy khỏi quyết định gọi dữ liệu; ASI03: giao thoa quyền hạn người dùng và agent; ASI04: cấm egress khi dữ liệu phân loại restricted | agent/runner.py:53-90, agent/policy.py:27-34, agent/runner.py:101-125, reports/attack-after.log:1 | Kiểm thử trên 4 kịch bản injection nội bộ và đích nhận cố định tại máy cục bộ |

Chỉ ghi nhận các căn cứ đã đối chiếu sơ bộ trong bài lab. Mô phỏng kỹ thuật không thay thế cho kết luận pháp lý chính thức.
