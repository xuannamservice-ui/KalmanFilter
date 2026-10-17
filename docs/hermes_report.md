Tôi đã tạo thành công tập lệnh Python `simulation.py` trong thư mục `DKF_WSN_Experiment/`.

Về trọng số Metropolis, tôi đã diễn giải `d_i` là bậc (degree) của nút `i` dựa trên ngữ cảnh lý thuyết đồ thị và các công thức đồng thuận Metropolis-Hastings tiêu chuẩn. Nếu có bất kỳ sự không nhất quán nào trong kết quả, tôi sẽ xem xét lại giả định này.

Tiếp theo, tôi sẽ tiến hành chạy mô phỏng theo hai kịch bản đã định:
1.  **Kịch bản 1 (KB1):** Với `Rs` trong `{60m, 28m}` và `L` trong `{1, 2, 3, 5, 10}`.
2.  **Kịch bản 2 (KB2):** Cố định `Rs = 28m`, `L = 5`, và `p_loss` trong `{0%, 10%, 20%, 30%}`.

Tôi sẽ viết một tập lệnh chính để điều phối các lần chạy mô phỏng này, thu thập dữ liệu kết quả vào các tệp JSON, sau đó tạo đồ thị và báo cáo cuối cùng.

Bây giờ, tôi sẽ bắt đầu với việc tạo tập lệnh để chạy KB1 và lưu kết quả.
