# Secret giả trong lịch sử Git — ghi nhận checkpoint 4

- Scanner và phiên bản: Gitleaks phiên bản 8.30.1.
- Commit chứa token giả: Commit 1bdd849 (1bdd849922156c868a5ee9293d68f5b72e242d2c).
- File, rule và kết quả quét lịch sử: File lab-fake-secret.txt dòng 1, rule ID lab24-synthetic-token. Lệnh gitleaks git --config .gitleaks.toml --redact --verbose . phát hiện 1 finding là token giả mô phỏng trong lịch sử commit.
- Kết quả quét file hiện tại: Lệnh gitleaks dir --config .gitleaks.toml . và pre-commit run --all-files đều trả về trạng thái sạch, không có secret nào trong thư mục làm việc hiện tại.
- Nếu đây là credential thật, cần xử lý thế nào: Cần lập tức thu hồi và rotate khóa xác thực trên hệ thống quản lý dịch vụ để vô hiệu hóa token cũ, sau đó cấp phát credential mới và rà soát nhật ký truy cập để xác định các hoạt động đáng ngờ.
- Vì sao xoá file khỏi HEAD hoặc pin dependency vẫn chưa đủ: Việc xóa file ở commit sau chỉ loại bỏ tệp khỏi trạng thái HEAD hiện tại, nội dung chuỗi xác thực vẫn nằm nguyên vẹn trong lịch sử git và bất kỳ ai có quyền truy cập repo đều có thể đọc lại. Pin dependency và pre-commit hook chỉ bảo vệ các thay đổi trong tương lai, không thể làm mất hiệu lực của credential đã từng bị lộ nếu chưa thực hiện rotate.
