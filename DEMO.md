# 🎬 Kịch Bản Demo — Khai Thác Dữ Liệu Nhóm 7

> **Đề tài:** Phân Tích và Dự Đoán Khu Vực Tiềm Năng Phát Triển Chung Cư và Mức Giá Quận Thủ Đức  
> **Thời gian demo dự kiến:** 10–15 phút

---

## ⚡ Chuẩn Bị Trước Khi Demo

> Thực hiện các bước này **trước khi gặp giáo viên**.

```bash
# 1. Clone project về máy (hoặc mở thư mục project)
cd ptdlkd

# 2. Cài thư viện (nếu chưa cài)
pip install pandas numpy geopandas shapely

# 3. Chạy toàn bộ pipeline để sinh data.json
python src/run_all.py

# 4. Mở sẵn trình duyệt với file webapp/index.html
start webapp/index.html
```

Kết quả mong đợi sau khi chạy `run_all.py`:
```
Total wards loaded: 36
Total apartments loaded: 525
Apartments inside Thủ Đức region after spatial join: 151
POIs in Thủ Đức - Hospital: 16, Mall: 12, Metro: 8, University: 31
ALL DATA MINING PROCESSES COMPLETED SUCCESSFULLY!
```

---

## 🎤 Slide 0 — Giới Thiệu (1 phút)

**Nói:** _"Đây là đồ án môn Khai Thác Dữ Liệu của nhóm 7. Đề tài phân tích dữ liệu chung cư tại TP Thủ Đức để tìm khu vực tiềm năng và dự đoán phân khúc giá, sử dụng 6 thuật toán tự cài đặt."_

**Mở Terminal, chạy lại pipeline để giáo viên thấy output trực tiếp:**

```bash
python src/run_all.py
```

Chỉ vào từng dòng output và giải thích:
- `Spatial join` → ghép chung cư vào phường theo tọa độ GPS
- `POIs` → lọc bệnh viện, TTTM, ga metro, trường ĐH trong Thủ Đức
- 6 thuật toán chạy tuần tự → xuất `webapp/data.json`

---

## 🌐 Slide 1 — Mở Web App & Tab Dashboard (2 phút)

**Thao tác:** Mở `webapp/index.html` trên trình duyệt (đã mở sẵn).

### Tab 1: Dashboard
- Chỉ vào **các thẻ thống kê** ở đầu trang:
  - 151 chung cư, 36 phường, giá TB 93.4M/m²
- Chỉ vào **biểu đồ phân phối giá** (bar chart):
  - _"Phần lớn chung cư thuộc phân khúc Trung Bình (42%)"_
- Chỉ vào **bảng Top 5 phường** có nhiều chung cư nhất

---

## 🗺️ Slide 2 — Bản Đồ Tương Tác (2 phút)

**Thao tác:** Click vào **Tab 2: Bản Đồ**

1. **Choropleth mặc định** (PotentialScore):
   - _"Màu càng đậm = phường có tiềm năng càng cao"_
   - Chỉ vào **An Phú, Thảo Điền, Bình Thọ** — màu đậm nhất

2. **Đổi layer** → chọn "Mật độ chung cư":
   - _"Có thể thấy rõ khu vực tập trung chung cư nhiều nhất"_

3. **Click vào marker chung cư** (icon nhà):
   - Popup hiện tên, giá/m², phường
   
4. **Toggle POI** → bật tắt lớp Bệnh viện / Metro:
   - _"Dữ liệu POI được lọc từ OpenStreetMap qua Overpass API"_

---

## 🔗 Slide 3 — Apriori (2 phút)

**Thao tác:** Click vào **Tab 3: Apriori**

**Giải thích nhanh:**
> _"Apriori tìm các tập phổ biến và luật kết hợp từ tập giao dịch — mỗi chung cư là 1 giao dịch gồm: quận, khoảng cách tới POI, phân khúc giá."_

**Thao tác demo:**
1. Để nguyên `minSupport = 0.15`, `minConfidence = 0.6` → nhấn **"Chạy Apriori"**
2. Chỉ vào bảng luật kết hợp kết quả:
   - Ví dụ luật: `{Quận 2, GầnTTTM} → {GầnBệnhViện}` (Conf: 1.00)
   - _"Confidence = 1.0 có nghĩa là 100% chung cư ở Quận 2 gần TTTM cũng gần bệnh viện"_
3. **Thay đổi tham số**: tăng `minSupport = 0.3` → chạy lại → số luật giảm xuống
   - _"Đây là thao tác thay đổi ngưỡng trực tiếp trên trình duyệt"_

---

## 🧱 Slide 4 — Rough Set / Tập Thô (2 phút)

**Thao tác:** Click vào **Tab 4: Tập Thô**

**Giải thích:**
> _"Rough Set phân tích xem tập thuộc tính nào là đủ để phân lớp phân khúc giá."_

**Chỉ vào các phần:**
1. **Mức độ phụ thuộc** γ(C, D):
   - _"γ = 0.xx có nghĩa là xx% đối tượng được phân lớp chính xác bằng tập điều kiện"_
2. **Reduct** tìm được:
   - _"Reduct là tập thuộc tính tối giản — bỏ bớt mà vẫn giữ được khả năng phân lớp như dùng đầy đủ thuộc tính"_
3. **Bảng xấp xỉ** dưới/trên theo phân khúc:
   - _"Accuracy = |Lower| / |Upper|. Nếu = 1 thì phân khúc đó hoàn toàn xác định được"_

---

## 🌳 Slide 5 — Phân Lớp: ID3 + Naive Bayes (2 phút)

**Thao tác:** Click vào **Tab 5: Phân Lớp**

### Cây quyết định ID3
1. Chỉ vào **cây quyết định dạng visual**:
   - _"Thuộc tính gốc là [district_discrete] — có Information Gain cao nhất"_
   - _"Mỗi nhánh là một giá trị của thuộc tính, lá cây là phân khúc giá dự đoán"_
2. Chỉ vào **độ chính xác** (Accuracy ~70-80%)

### Naive Bayes dự đoán trực tuyến
3. **Demo live prediction** — nhập vào form:
   - Khoảng cách bệnh viện: `Gần`
   - Khoảng cách TTTM: `Gần`  
   - Khoảng cách Metro: `Xa`
   - Khoảng cách ĐH: `Gần`
   - Quận: `Quận 2`
4. Nhấn **Dự Đoán** → hiện kết quả phân khúc
   - _"Kết quả tính từ xác suất có điều kiện P(class|features) theo công thức Bayes"_

---

## 🔵 Slide 6 — Gom Cụm: K-Means + Kohonen SOM (2 phút)

**Thao tác:** Click vào **Tab 6: Gom Cụm**

### K-Means (K=3)
1. Chỉ vào **scatter plot** phân cụm:
   - _"36 phường được gom thành 3 cụm theo: giá TB, mật độ CC, số POI"_
   - _"Cụm 0 = tiềm năng cao, cụm 1 = trung bình, cụm 2 = thấp"_
2. Chỉ vào **bảng liệt kê phường theo cụm**

### Kohonen SOM
3. Chỉ vào **heatmap SOM 10×10**:
   - _"Mỗi ô là một nơ-ron. Màu đậm hơn = nhiều phường được ánh xạ vào ô đó"_
   - _"SOM học không có giám sát — tự tổ chức để phường tương tự nằm gần nhau"_

---

## 🏆 Slide 7 — Kết Quả & Kết Luận (1 phút)

**Thao tác:** Click vào **Tab 7: Kết Luận**

1. Chỉ vào **bảng Top 10 phường tiềm năng**:
   - _"An Phú, Thảo Điền là top đầu — phù hợp thực tế thị trường BĐS"_
2. Chỉ vào **choropleth PotentialScore** trên bản đồ cuối trang
3. Đọc công thức:
   ```
   PotentialScore = 0.22·z(GiaTrungBinh) + 0.18·z(MatDoChungCu)
                  + 0.14·z(metro_cnt) + ...
   ```
   - _"Trọng số được xác định dựa trên độ tương quan Pearson của từng biến với giá chung cư"_

---

## ❓ Câu Hỏi Thường Gặp Từ Giáo Viên

| Câu hỏi | Trả lời gợi ý |
|---------|--------------|
| Sao không dùng sklearn? | Môn yêu cầu tự cài đặt thuật toán để hiểu bản chất. Chúng em chỉ dùng numpy/pandas |
| Tại sao chọn K=3 cho K-Means? | Thử nhiều K, K=3 cho Inertia giảm rõ nhất (elbow method) và phù hợp 3 phân khúc thị trường |
| Apriori với dữ liệu không gian thì transaction là gì? | Mỗi chung cư = 1 transaction gồm: tên quận, nhóm khoảng cách tới 4 POI, phân khúc giá |
| Rough Set có ứng dụng gì thực tế? | Tìm tập thuộc tính tối giản giúp giảm chi phí thu thập dữ liệu mà vẫn giữ độ chính xác |
| Dữ liệu lấy từ đâu? | Web crawling từ batdongsan.com.vn + OpenStreetMap (Overpass API) + GADM (GeoJSON) |

---

## 📁 File Quan Trọng Cần Biết

| File | Vai trò |
|------|---------|
| `src/run_all.py` | Chạy toàn bộ pipeline → sinh `webapp/data.json` |
| `src/apriori.py` | Thuật toán Apriori tự cài đặt |
| `src/rough_set.py` | Rough Set & tìm Reduct |
| `src/decision_tree_id3.py` | Cây quyết định ID3 |
| `src/naive_bayes.py` | Naive Bayes phân lớp |
| `src/kmeans_clustering.py` | K-Means tự cài |
| `src/kohonen_som.py` | Kohonen SOM tự cài |
| `webapp/index.html` | Giao diện demo (mở bằng browser) |
| `webapp/data.json` | Kết quả tổng hợp (sinh tự động) |
