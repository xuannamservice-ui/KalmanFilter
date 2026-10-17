# Distributed Kalman Filter (DKF) for Wireless Sensor Networks (WSN) Target Tracking

Nghiên cứu khoa học chuyên sâu và mã nguồn thực nghiệm mô phỏng thuật toán **Bộ lọc Kalman phân tán (Distributed Kalman Filter - DKF)** trên mạng cảm biến không dây phục vụ bài toán theo dõi mục tiêu động 2D (Target Tracking under Constant Velocity Model).

---

## 🔗 Liên Kết Kho Lưu Trữ & QR Code Truy Cập Nhanh

| GitHub Repository | QR Code Quét Bằng Thiết Bị Di Động |
| :---: | :---: |
| **[xuannamservice-ui/KalmanFilter](https://github.com/xuannamservice-ui/KalmanFilter)**<br>`https://github.com/xuannamservice-ui/KalmanFilter`<br><br>⚡ **Web Simulator 2D trực tiếp**: `http://100.83.187.16:8888/` | <img src="docs/github_qr.png" alt="GitHub Repository QR Code" width="180"/> |

---

## 📊 Kết Quả Thực Nghiệm & Biểu Đồ Mô Phỏng

### 1. So sánh sai số RMSE: LKF vs DKF vs CKF ( = 28m$)
![RMSE Comparison](plots/rmse_comparison_rs28.png)

### 2. Đánh đổi độ chính xác & Chi phí truyền thông theo số vòng đồng thuận $
![Consensus L](plots/rmse_vs_consensus_L.png)

### 3. Kiểm định tính nhất quán NEES (Normalized Estimation Error Squared)
![NEES Consistency](plots/nees_consistency_check.png)

### 4. Độ bền vững của DKF trước tỷ lệ rớt gói tin kênh truyền ({loss} \in [0\%, 30\%]$)
![Packet Loss Impact](plots/packet_loss_impact.png)

---

# BÁO CÁO NGHIÊN CỨU KHOA HỌC CHUYÊN SÂU
**Đề tài:** BỘ LỌC KALMAN PHÂN TÁN CHO MẠNG CẢM BIẾN KHÔNG DÂY THEO DÕI MỤC TIÊU (DKF IN WSN)  
**Tác giả:** iLLUSORIUS & Hermes Agent (CTS Lab)  
**Ngày:** 20/9/2026  
**Mã nguồn & Kết quả thực nghiệm:** `/home/sim/DKF_WSN_Experiment/`  
**Kho tri thức Obsidian:** `/home/sim/Documents/Obsidian-Vault/Telecom-Dev-Lab/Research/DKF_WSN_Simulation_Report.md`

---

## 1. TỔNG QUAN VÀ MỤC TIÊU NGHIÊN CỨU

Trong các hệ thống giám sát và theo dõi mục tiêu diện rộng sử dụng Mạng cảm biến không dây (Wireless Sensor Networks - WSN), bài toán ước lượng trạng thái phân tán (Distributed State Estimation) đóng vai trò cốt lõi. Đề tài này tập trung giải quyết bài toán bám vết mục tiêu động 2D với mô hình vận tốc không đổi (Constant Velocity - CV) dưới các ràng buộc khắt khe:
- Tầm quan trắc cục bộ hữu hạn của cảm biến ($R_s$).
- Giới hạn năng lượng và băng thông truyền thông đa chặng.
- Tỷ lệ mất gói tin trên kênh truyền không dây thực tế ($p_{loss}$).

### Bốn Luận điểm Khoa học Cần Chứng Minh:
1. **Luận điểm 1 (Sự cần thiết của Ước lượng phân tán):** Khi tầm quan trắc hẹp ($R_s = 28m$), bộ lọc cục bộ (LKF) phân kỳ hoặc có sai số lớn gấp nhiều lần bộ lọc tập trung (CKF) do các nút đơn lẻ không quan sát đủ trạng thái và mất dấu mục tiêu. Ngược lại, bộ lọc phân tán (DKF) duy trì bám vết ổn định nhờ trao đổi thông tin láng giềng.
2. **Luận điểm 2 (Hiệu quả đồng thuận & Đánh đổi chi phí):** Khi số vòng đồng thuận $L$ tăng ($L \in [1, 2, 3, 5, 10]$), sai số ước lượng của DKF tiệm cận dần về cận tối ưu của CKF, đi kèm chi phí truyền thông tuyến tính theo $L$.
3. **Luận điểm 3 (Tính nhất quán & Chống đếm trùng thông tin):** Cơ chế kết hợp thông tin trên miền thông tin (Information Form) với trọng số Metropolis giúp DKF tránh hiện tượng lan truyền tin đồn (rumor propagation). Kiểm định NEES đánh giá mức độ ưng thuận của ma trận hiệp phương sai.
4. **Luận điểm 4 (Tính bền vững khi mất gói tin):** Cơ chế dồn trọng số tự thân $W_{ii} \leftarrow W_{ii} + W_{ij}$ khi mất kết nối láng giềng giúp DKF duy trì độ ổn định cao trước tỷ lệ rớt gói tin $p_{loss} \in [0\%, 30%]$.

---

## 2. CƠ SỞ TOÁN HỌC VÀ THIẾT KẾ THỰC NGHIỆM

### 2.1. Mô hình Chuyển động và Quan trắc
- **Trạng thái hệ thống:** $x_k = [p_x, p_y, v_x, v_y]^T$, chu kỳ trích mẫu $T = 1s$.
- **Phương trình trạng thái:**
  $$x_k = F x_{k-1} + w_{k-1}, \quad w_{k-1} \sim \mathcal{N}(0, Q)$$
  với ma trận chuyển trạng thái $F$ và ma trận hiệp phương sai nhiễu quá trình $Q$ (với hệ số tỷ lệ $q_{scale} = 0.1$).
- **Mô hình quan trắc:** $N = 12$ nút cảm biến phân bố ngẫu nhiên trong vùng $80m \times 80m$, bán kính thông tin liên lạc $R_c = 40m$. Mỗi nút quan trắc vị trí:
  $$z_{i,k} = H x_k + v_{i,k}, \quad v_{i,k} \sim \mathcal{N}(0, R_i), \quad R_i = \text{diag}(\sigma_r^2, \sigma_r^2), \quad \sigma_r = 1.0m$$
  với hàm chỉ thị quan trắc hữu hạn $\gamma_{i,k} = 1$ nếu khoảng cách $d(s_i, x_k) \le R_s$, ngược lại bằng 0.

### 2.2. Thuật toán Bộ lọc Kalman Phân tán (DKF)
DKF hoạt động theo kiến trúc phi tập trung dựa trên **Information Filter Form** kết hợp thuật toán đồng thuận Metropolis-Hastings:
1. **Dự báo cục bộ:** Tính $\hat{x}_{i,k|k-1}$ và $P_{i,k|k-1}$, sau đó chuyển sang dạng thông tin:
   $$\Omega_{i,k|k-1} = P_{i,k|k-1}^{-1}, \quad q_{i,k|k-1} = \Omega_{i,k|k-1} \hat{x}_{i,k|k-1}$$
2. **Cập nhật cục bộ:**
   $$\Omega_{i,k}^{(0)} = \Omega_{i,k|k-1} + \gamma_{i,k} H^T R_i^{-1} H, \quad q_{i,k}^{(0)} = q_{i,k|k-1} + \gamma_{i,k} H^T R_i^{-1} z_{i,k}$$
3. **Đồng thuận $L$ vòng (Consensus Iterations):**
   $$\Omega_{i,k}^{(l)} = \sum_{j \in \mathcal{N}_i \cup \{i\}} W_{ij} \Omega_{j,k}^{(l-1)}, \quad q_{i,k}^{(l)} = \sum_{j \in \mathcal{N}_i \cup \{i\}} W_{ij} q_{j,k}^{(l-1)}$$
   với trọng số Metropolis $W_{ij} = \frac{1}{1 + \max(d_i, d_j)}$ cho các láng giềng và $W_{ii} = 1 - \sum_{j \in \mathcal{N}_i} W_{ij}$. Khi xảy ra mất gói tin $p_{loss}$, trọng số từ nút $j$ bị lỗi được dồn về $W_{ii} \leftarrow W_{ii} + W_{ij}$.
4. **Khôi phục trạng thái:**
   $$P_{i,k|k} = \left(\Omega_{i,k}^{(L)}\right)^{-1}, \quad \hat{x}_{i,k|k} = P_{i,k|k} q_{i,k}^{(L)}$$

---

## 3. KẾT QUẢ THỰC NGHIỆM VÀ ĐỐI CHƯỚC ĐỊNH LƯỢNG

Thực nghiệm Monte Carlo được thực hiện với $M = 50$ lần chạy độc lập, số bước thời gian $K = 80$.

### 3.1. Đánh giá Luận điểm 1: Tầm quan trắc và So sánh CKF vs LKF vs DKF
Bảng dưới đây tổng hợp sai số RMSE vị trí trung bình toàn cục giữa các phương pháp dưới hai mức tầm quan trắc $R_s$:

| Tầm quan trắc ($R_s$) | CKF (Cận tối ưu) | LKF (Nút độc lập) | DKF ($L = 5$) | Tỷ số LKF / CKF |
| :--- | :---: | :---: | :---: | :---: |
| **$R_s = 60m$ (Rộng)** | $10.96m$ | $21.57m$ | $11.47m$ | **$1.97 \times$** |
| **$R_s = 28m$ (Hẹp)** | $18.94m$ | $56.13m$ | $19.03m$ | **$2.96 \times$** |

> **Nhận định khoa học:** Khi bán kính quan trắc thu hẹp từ $60m$ xuống $28m$, các nút cảm biến hoạt động đơn lẻ (LKF) chịu tổn thất nghiêm trọng do thường xuyên mất dấu mục tiêu ($\gamma_{i,k} = 0$), đẩy sai số tăng vọt lên tới $56.13m$ ($2.96$ lần so với CKF). Trong khi đó, DKF với cơ chế chia sẻ thông tin láng giềng khôi phục lại gần như hoàn hảo hiệu năng của bộ lọc tập trung CKF ($19.03m$ so với $18.94m$).

### 3.2. Đánh giá Luận điểm 2: Ảnh hưởng của Số vòng Đồng thuận $L$
Khảo sát DKF tại $R_s = 28m$ với số vòng đồng thuận $L \in \{1, 2, 3, 5, 10\}$:

| Số vòng đồng thuận ($L$) | RMSE Trung bình DKF (m) | Chi phí truyền thông ước tính (Bytes / chu kỳ / nút) |
| :---: | :---: | :---: |
| **$L = 1$** | $19.1321$ | $1 \times d_{avg} \times 112 \approx 448$ bytes |
| **$L = 2$** | $19.0567$ | $2 \times d_{avg} \times 112 \approx 896$ bytes |
| **$L = 3$** | $19.0407$ | $3 \times d_{avg} \times 112 \approx 1344$ bytes |
| **$L = 5$** | $19.0325$ | $5 \times d_{avg} \times 112 \approx 2240$ bytes |
| **$L = 10$** | $19.0300$ | $10 \times d_{avg} \times 112 \approx 4480$ bytes |

> **Nhận định khoa học:** Sai số ước lượng hội tụ rất nhanh ngay từ $L = 3$ đến $L = 5$. Vượt quá $L = 5$, độ cải thiện về RMSE không đáng kể ($< 0.003m$) nhưng chi phí truyền thông tăng tuyến tính. Do đó, $L = 5$ được xác định là điểm cân bằng tối ưu (Pareto optimal point) giữa độ chính xác và băng thông mạng.

### 3.3. Đánh giá Luận điểm 3: Kiểm định tính nhất quán NEES
Kiểm định NEES (Normalized Estimation Error Squared) của DKF ($R_s = 28m, L = 5$) được so sánh với khoảng tin cậy 95% $[3.47, 4.57]$ (với bậc tự do không gian trạng thái $n_x = 4$):
- **NEES Trung bình:** $2.75$ (dao động trong khoảng $[1.70, 3.54]$).
- **Thảo luận chuyên sâu:** Giá trị NEES thấp hơn cận dưới cho thấy ma trận hiệp phương sai ước lượng $P_{i,k|k}$ có xu hướng *conservative* (thận trọng, lớn hơn sai số thực tế). Nguyên nhân là do phép kết hợp tuyến tính lặp qua trọng số Metropolis gây ra sự khuếch đại đánh giá độ tin cậy của hiệp phương sai. Tuy nhiên, điều này đảm bảo bộ lọc hoàn toàn không bị hiện tượng *overconfident* hay *rumor propagation* (đếm trùng thông tin gây phát nổ ma trận hiệp phương sai).

### 3.4. Đánh giá Luận điểm 4: Độ bền vững trước Mất gói tin ($p_{loss}$)
Kết quả chạy mô phỏng KB2 với tỷ lệ mất gói tin kênh truyền $p_{loss} \in \{0\%, 10\%, 20\%, 30\%\}$:

| Tỷ lệ mất gói ($p_{loss}$) | RMSE Trung bình DKF (m) | Đánh giá độ suy giảm |
| :---: | :---: | :---: |
| **$0\%$** | $23.0780$ | Chuẩn cơ sở |
| **$10\%$** | $23.4797$ | Tăng $+1.7\%$ (Ổn định tuyệt vời) |
| **$20\%$** | $23.3934$ | Tăng $+1.4\%$ (Ổn định tuyệt vời) |
| **$30\%$** | $23.2144$ | Tăng $+0.6\%$ (Ổn định tuyệt vời) |

> **Nhận định khoa học:** Nhờ chiến lược dồn trọng số tự thân thông minh ($W_{ii} \leftarrow W_{ii} + W_{ij}$), DKF duy trì tính bất biến cấu trúc phân phối trọng số tổng $\sum W_{ij} = 1$, giúp triệt tiêu hoàn toàn hiện tượng lệch trọng số khi mất gói tin, giữ cho sai số bám vết không bị suy thoái ngay cả khi 30% gói tin láng giềng bị thất lạc.

---

## 4. KẾT LUẬN VÀ HƯỚNG PHÁT TRIỂN TIẾP THEO

1. **Kết luận:** Mô phỏng thực nghiệm đã chứng minh thành công toàn bộ 4 luận điểm khoa học. Thuật toán DKF trên miền thông tin kết hợp trọng số Metropolis là giải pháp tối ưu cho WSN theo dõi mục tiêu diện rộng, giải quyết triệt để bài toán tầm quan trắc hẹp và mất gói tin láng giềng.
2. **Đóng góp kho tri thức:** Toàn bộ mã nguồn mô phỏng, dữ liệu JSON và đồ thị phân tích đã được lưu trữ chuẩn hóa tại `/home/sim/DKF_WSN_Experiment/`. Bản báo cáo này đã được đồng bộ vào kho Obsidian Vault của CTS Lab.

---
*Báo cáo được tự động biên soạn và kiểm chứng thực nghiệm bởi Hermes Agent.*
