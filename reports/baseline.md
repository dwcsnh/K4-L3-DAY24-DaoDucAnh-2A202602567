# Baseline

1. Agent có identity mỗi run chưa? Dẫn file/hàm:
Agent chưa có identity riêng cho mỗi lần chạy trong hàm _naive_loop tại agent/loop.py từ dòng 27 đến 54 vì không khởi tạo hay lưu giữ định danh agent_id hoặc run_id.

2. Ai cho phép http_post? Dẫn file/hàm:
Không có cơ chế chính sách nào cho phép mà hàm _naive_loop tại agent/loop.py dòng 44 tự ý gọi trực tiếp tools.http_post theo chỉ thị trích xuất từ tài liệu.

3. Nếu gửi sai PII ra sink, bằng chứng ở đâu? Dẫn file/hàm:
Bằng chứng nằm tại reports/sink.log do hàm do_POST trong make_handler tại sink/sink.py từ dòng 42 đến dòng 47 ghi lại toàn bộ nội dung dữ liệu nhận được.

