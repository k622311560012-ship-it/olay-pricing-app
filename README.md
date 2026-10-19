# OLAY × TikTok Shop – prototype tối ưu giá & voucher

App Streamlit 6 trang cho môn Advanced Business Analytics (FTU).

> **Dữ liệu là mô phỏng.** Mọi bảng trong `app_data/` và `results/` được sinh từ bộ dữ liệu giả lập của nhóm. App **không chứa dữ liệu khách hàng thật**, không chứa bảng đơn hàng (`sales.csv`) hay đáp án mô phỏng (`truth_*.csv`).

## Chạy trên máy
```bash
python -m venv .venv
.venv\Scripts\activate          # macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```
Mở http://localhost:8501.

## Deploy lên Streamlit Community Cloud
Đẩy cả thư mục `olay-app/` lên GitHub (không đẩy `.venv/`, đã có trong `.gitignore`), rồi chọn `app.py` làm main file. Mọi đường dẫn file tính tương đối theo vị trí `app.py`.

## Các trang
| Trang | Nội dung | File dùng |
|---|---|---|
| 1. Tổng quan | KPI lợi nhuận, doanh thu, chi phí voucher; so 6 phương án; cảnh báo tồn kho | `results/pricing_eval_annual.csv`, `results/pricing_eval.csv`, `results/inventory_sim_test.csv`, `app_data/inventory.csv` |
| 2. Đề xuất giá | Bảng đề xuất (guardrail / tự do), lọc, nút Duyệt / Sửa / Từ chối, tải `decision_log.csv` | `results/price_recommendation*.csv` |
| 3. Voucher theo nhóm khách | Kết quả Model 2 (tự hiện khi có file) | `results/segment_voucher.csv`, `results/voucher_eval.csv` |
| 4. Giá đối thủ | Giá/ml theo thời gian, cảnh báo, case C01 | `app_data/comp_ppu_daily.csv`, `app_data/olay_ppu_daily.csv`, `results/competitor_alerts.csv`, `results/competitor_response.csv` |
| 5. Ràng buộc Finance & Supply chain | Giá sàn, trần 50%, ngân sách voucher, tồn kho, SKU bị giới hạn | `app_data/price_floor.csv`, `app_data/promo_budget.csv`, `results/inventory_sim_test.csv` |
| 6. What-if | Thanh trượt voucher, ε, đối thủ, VXP → `pricing_core.what_if`; đường guardrail | `results/model_params.csv`, `app_data/deal_plan.csv`, `results/guardrail_curve.csv` |

## Cấu trúc
```
app.py              điều hướng 6 trang
common.py           đọc CSV (st.cache_data), định dạng 1.234.567đ
views/              6 trang
pricing_core.py     hàm lõi Model 1: giá khách trả, phí, lợi nhuận, cầu, what_if()
params.py           phí sàn, VXP, giá sàn của nhóm
results/            kết quả Model 1 (xem results/README_model1.md cho ý nghĩa từng cột)
app_data/           bảng nhỏ tổng hợp sẵn từ dữ liệu mô phỏng (sku_id đọc dạng chuỗi 19 số)
```
App chỉ đọc CSV, không huấn luyện mô hình. Để cập nhật số liệu: chạy lại `pricing.ipynb` ở dự án gốc, rồi chạy `build_app_data.py` để copy `results/` và tạo lại `app_data/`. Kết quả Model 2 chỉ cần bỏ vào `results/`.

Quyết định duyệt ở trang 2 chỉ lưu trong phiên trình duyệt. Hãy tải `decision_log.csv` trước khi đóng trang.
