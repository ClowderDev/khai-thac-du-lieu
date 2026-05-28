# Phân Tích và Dự Đoán Khu Vực Tiềm Năng Phát Triển Chung Cư và Mức Giá Quận Thủ Đức

> **Môn học:** Khai Thác Dữ Liệu  
> **Nhóm 7** – Trường Đại Học Công Nghệ Thông Tin, ĐHQG-HCM

---

## 📋 Giới Thiệu

Đồ án phân tích và khai thác dữ liệu bất động sản tại **Thành phố Thủ Đức (TP.HCM)**, tích hợp:

- **151 chung cư** (sau spatial join) thuộc 36 phường
- **4 loại POI** (Bệnh viện, TTTM, Ga Metro, Trường ĐH)
- **6 thuật toán khai thác dữ liệu** tự cài đặt (không dùng sklearn)
- **Web App tương tác** với bản đồ Leaflet.js và biểu đồ Chart.js

---

## 🏗️ Cấu Trúc Thư Mục

```
ptdlkd/
├── Dataset/                    # Dữ liệu đầu vào
│   ├── hcm_apartment.csv       # Dữ liệu chung cư HCM
│   ├── hospital.csv            # Bệnh viện
│   ├── mall.csv                # Trung tâm thương mại
│   ├── metro.csv               # Ga Metro
│   ├── university.csv          # Trường đại học
│   ├── Quận 2.geojson          # Ranh giới phường Quận 2
│   ├── Quận 9.geojson          # Ranh giới phường Quận 9
│   └── Thủ Đức.geojson         # Ranh giới phường Thủ Đức
│
├── src/                        # Source code khai thác dữ liệu
│   ├── data_preprocessing.py   # Tiền xử lý, spatial join, POI
│   ├── apriori.py              # Thuật toán Apriori (tập phổ biến, luật kết hợp)
│   ├── rough_set.py            # Rough Set (xấp xỉ, reduct)
│   ├── decision_tree_id3.py    # Cây quyết định ID3
│   ├── naive_bayes.py          # Naive Bayes
│   ├── kmeans_clustering.py    # K-Means Clustering
│   ├── kohonen_som.py          # Kohonen SOM (Self-Organizing Map)
│   └── run_all.py              # Điều phối toàn bộ pipeline → sinh webapp/data.json
│
├── webapp/                     # Giao diện web demo
│   ├── index.html              # Trang chính (7 tabs)
│   ├── style.css               # Thiết kế CSS (dark mode, glassmorphism)
│   ├── app.js                  # Logic JS (Leaflet, Chart.js, Apriori JS)
│   ├── data.json               # Kết quả đã tính (sinh bởi run_all.py)
│   └── thu_duc_wards.geojson   # Ranh giới phường cho Leaflet
│
├── phan_tich_theo_phuong_6_quan/  # Output trung gian (sinh tự động)
│   ├── mo_ta_thu_duc_theo_phuong.csv
│   ├── mo_ta_thu_duc_model_input_python.csv
│   └── mo_ta_thu_duc_potential_python.csv
│
├── demo.py                     # Script demo terminal (dùng trình bày)
└── README.md
```

---

## ⚙️ Cài Đặt

### Yêu Cầu

| Công cụ | Phiên bản tối thiểu |
|---------|---------------------|
| Python  | 3.9+                |
| pip     | 23+                 |

### Cài Thư Viện

```bash
pip install pandas numpy geopandas shapely
```

> **Lưu ý Windows:** `geopandas` trên Windows đôi khi cần cài theo thứ tự sau:
> ```bash
> pip install wheel
> pip install pipwin
> pipwin install gdal
> pipwin install fiona
> pip install geopandas shapely
> ```
> Hoặc dùng Anaconda/Miniconda:
> ```bash
> conda install geopandas
> ```

---

## 🚀 Chạy Nhanh

### Bước 1 – Tạo dữ liệu phân tích

Chạy toàn bộ pipeline xử lý và khai thác dữ liệu:

```bash
python src/run_all.py
```

Pipeline thực hiện:
1. Đọc dữ liệu chung cư và ranh giới phường (GeoJSON)
2. Spatial Join – nối chung cư vào phường tương ứng theo tọa độ
3. Tính khoảng cách tối thiểu đến 4 loại POI
4. Rời rạc hóa thuộc tính (phân khúc giá, khoảng cách)
5. Chạy 6 thuật toán khai thác dữ liệu
6. Tính PotentialScore và xếp hạng 36 phường
7. Xuất kết quả ra `webapp/data.json` và `webapp/thu_duc_wards.geojson`

### Bước 2 – Mở Web App

Sau khi bước 1 hoàn thành, mở trình duyệt:

```bash
# Windows
start webapp/index.html

# macOS
open webapp/index.html

# Linux
xdg-open webapp/index.html
```

### Bước 3 – Chạy Demo Terminal (tùy chọn)

Dùng để trình bày trực tiếp cho giáo viên:

```bash
python demo.py
```

---

## 📊 Các Thuật Toán Đã Cài Đặt

Tất cả thuật toán được **tự cài đặt từ đầu**, chỉ sử dụng `numpy` và `pandas`.

### 1. Apriori – `src/apriori.py`

Khai thác **tập phổ biến** và **luật kết hợp** từ dữ liệu giao dịch chung cư.

| Tham số | Giá trị |
|---------|---------|
| minSupport | 0.15 (15%) |
| minConfidence | 0.60 (60%) |

- **Đầu vào:** Transaction list (mỗi chung cư = 1 giao dịch gồm: quận, khoảng cách POI, phân khúc giá)
- **Đầu ra:** Tập phổ biến + luật kết hợp có dạng `{Gần Metro, Quận 2} → {Giá Cao}`

### 2. Rough Set – `src/rough_set.py`

Phân tích **xấp xỉ tập thô** và tìm **reduct** (tập thuộc tính tối giản).

- **Đầu vào:** Bảng quyết định (5 thuộc tính điều kiện, 1 thuộc tính quyết định = phân khúc giá)
- **Đầu ra:** Mức độ phụ thuộc γ(C, D), xấp xỉ dưới/trên, các reduct tìm được

Các bước thực hiện:
1. Xây dựng quan hệ không phân biệt (Indiscernibility Relation)
2. Tính xấp xỉ dưới và xấp xỉ trên cho mỗi lớp quyết định
3. Tính độ chính xác (Accuracy = |Lower| / |Upper|)
4. Xây dựng ma trận phân biệt (Discernibility Matrix)
5. Tìm reduct bằng thuật toán tìm tập hitting tối giản

### 3. Decision Tree ID3 – `src/decision_tree_id3.py`

Xây dựng **cây quyết định** phân lớp phân khúc giá chung cư.

- **Tiêu chí phân chia:** Information Gain (Entropy)
- **Đầu ra:** Cấu trúc cây (JSON), độ chính xác, classification report

### 4. Naive Bayes – `src/naive_bayes.py`

Phân lớp theo **xác suất có điều kiện** (Gaussian + Categorical NB).

- **Đầu vào:** Thuộc tính rời rạc (khoảng cách POI, quận) + thuộc tính liên tục
- **Đầu ra:** Prior, Likelihood, Accuracy, dự đoán mẫu mới

### 5. K-Means – `src/kmeans_clustering.py`

**Gom cụm** 36 phường theo các chỉ số tiềm năng (K=3).

- **Đặc trưng:** GiaTrungBinh, MatDoChungCu, hospital_cnt, mall_cnt, metro_cnt, university_cnt
- **Đầu ra:** Nhãn cụm cho mỗi phường, inertia, tọa độ centroid

### 6. Kohonen SOM – `src/kohonen_som.py`

**Mạng nơ-ron tự tổ chức** (Self-Organizing Map) 10×10 grid.

- **Epochs:** 100 | **Learning rate:** 0.5 (giảm dần)
- **Đầu ra:** BMU (Best Matching Unit) cho mỗi phường, bản đồ SOM

---

## 🌐 Giao Diện Web App

Web App gồm **7 tabs** tương tác:

| Tab | Nội dung |
|-----|---------|
| 1. Dashboard | Thống kê tổng quan, biểu đồ phân phối giá |
| 2. Bản đồ | Leaflet map: choropleth, marker chung cư, POI |
| 3. Apriori | Chạy Apriori trực tiếp bằng JS, lọc luật |
| 4. Tập Thô | Ma trận phân biệt, xấp xỉ, reduct |
| 5. Phân Lớp | ID3 tree visualization, Naive Bayes dự đoán online |
| 6. Gom Cụm | K-Means scatter plot, Kohonen SOM heatmap |
| 7. Kết Luận | Xếp hạng PotentialScore, Top 10 phường tiềm năng |

---

## 📐 Phương Pháp Tính PotentialScore

PotentialScore cho mỗi phường được tính theo trọng số z-score:

```
PotentialScore = 0.22·z(GiaTrungBinh)   + 0.18·z(MatDoChungCu)
               + 0.12·z(hospital_cnt)   + 0.12·z(mall_cnt)
               + 0.14·z(metro_cnt)      + 0.12·z(university_cnt)
               − 0.04·z(dist_hospital)  − 0.02·z(dist_mall)
               − 0.03·z(dist_metro)     − 0.01·z(dist_university)
```

---

## 🗂️ Dữ Liệu

| File | Mô tả | Nguồn |
|------|-------|-------|
| `hcm_apartment.csv` | 396 chung cư HCM với giá/m², tọa độ | Web crawling |
| `hospital.csv` | Bệnh viện tại HCM | OpenStreetMap / Overpass API |
| `mall.csv` | Trung tâm thương mại | OpenStreetMap |
| `metro.csv` | Ga tàu điện metro | OpenStreetMap |
| `university.csv` | Trường đại học | OpenStreetMap |
| `*.geojson` | Ranh giới hành chính phường | GADM / OpenStreetMap |

---

## 👥 Nhóm Thực Hiện

| Họ tên | MSSV | Vai trò |
|--------|------|---------|
| Nguyễn Văn Dương Hùng | 22520520 | Trưởng nhóm |
| Trần Lê Vĩnh Bửu | 23520163 | Thành viên |
| Nguyễn Ngọc Thông | 23521528 | Thành viên |

**Giảng viên hướng dẫn:** Trần Văn Hải Triều

---

## 📄 License

MIT License – Chỉ dùng cho mục đích học thuật.
