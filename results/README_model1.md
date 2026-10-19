# Model 1 – Giá (OLAY × TikTok Shop): mô tả file kết quả

Tất cả file trong thư mục này do `pricing.ipynb` sinh ra (Restart & Run All). Mọi con số đưa lên slide và web phải lấy từ các file này.

## Quy ước chung
- **`sku_id`** là chuỗi 19 chữ số. Luôn đọc dạng chuỗi (`dtype={"sku_id": str}`), không đọc dạng số.
- **Ba loại giá** (đơn vị VND/sp):
  - `live_price`: giá niêm yết của loại phiên trong deal_plan.
  - `a` (giá sau seller voucher, "gia_sau_sv" / "gia_de_xuat"): = live_price × (1 − seller voucher). Brand thu số tiền này, phí sàn tính trên nó.
  - `final` (giá khách trả, "gia_khach_tra"): = a − VXP(a). VXP do TikTok chịu, theo bậc: < 200k → 0%; 200–300k → 13%; 300–500k → 14%; ≥ 500k → 15%.
- **Hai kiểu tỷ lệ:**
  - Cột tên có `pct` ở **cuối** (vd `chenh_lech_vs_hien_trang_pct`) đã nhân 100: 1,13 nghĩa là 1,13%.
  - Cột seller voucher (`seller_voucher_*`, `sv`, `voucher_*_trung_vi`) là tỷ lệ 0–1: 0,11 nghĩa là 11%.
  - Ngoại lệ: `comp_drop_pct` của `what_if` cũng là tỷ lệ 0–1 (0,05 = 5%).
- **Lợi nhuận** = lợi nhuận đóng góp của brand = số đơn × [q̄ × (a − phí(a) − giá vốn) − 3.000đ].
  - phí(a) = 17% hoa hồng + 6% thanh toán + 5% Voucher Xtra (trần 50k) + 5% Campaign Plus (trần 50k).
  - Giá vốn = 35% × base_price.
- **Doanh thu** = số sp × a.
- **Chi phí voucher** = số sp × (live_price − a), tức tổng seller voucher brand chịu.
- **Loại phiên:** BAU = ngày thường; CAMP = 15 và 25 hằng tháng; DD = ngày đôi (gồm Mega 9.9, 10.10, 12.12 và 11.11).
- **Train / test:** train = 01/10/2025–30/09/2026. Test = 01–15/10/2026 (có 10.10 Mega và CAMP 15/10).
- **Hai bộ cầu khác nhau:**
  - Số "dự kiến" (`*_du_kien`, What-if, bước 4–7) tính theo **mô hình**.
  - Số "đánh giá" (`pricing_eval*`, `guardrail_curve`, `pricing_sensitivity`, `guardrail_gain_split`) tính theo **cầu thật** (`truth_sku`, kỳ vọng, không nhiễu).

Tên trang web bên dưới là gợi ý theo cấu trúc Model 1; nhóm đổi lại cho khớp site.

| File | Trang web |
|---|---|
| `elasticity_compare.csv`, `elasticity_by_sku.csv`, `demand_model_compare.csv` | Mô hình nhu cầu |
| `price_recommendation.csv`, `price_recommendation_free.csv`, `price_recommendation_summary.csv` | Đề xuất giá |
| `model_params.csv` (+ `pricing_core.what_if`) | What-if |
| `inventory_sim_test.csv` | Tồn kho / Đề xuất giá (cảnh báo hết hàng) |
| `competitor_alerts.csv`, `competitor_response.csv` | Đối thủ |
| `pricing_eval.csv`, `pricing_eval_annual.csv`, `guardrail_curve.csv`, `pricing_sensitivity.csv`, `guardrail_gain_split.csv` | Đánh giá & ROI |

---

## Trang Đề xuất giá

### `price_recommendation.csv` – phương án đề xuất chính (`toi_uu_guardrail`)
96 dòng = 32 SKU × 3 loại phiên. Guardrail gồm 3 ràng buộc:
- Thang giá khách trả DD ≤ CAMP ≤ BAU.
- Voucher BAU ≤ mức hiện tại + 2 điểm %.
- Voucher ≥ mức hiện tại − 3 điểm % ở cả 3 loại phiên.

Riêng Retinol24 kem đêm và 2 combo chứa nó có điều chỉnh tồn kho cho 01–11/10.

| Cột | Ý nghĩa | Đơn vị |
|---|---|---|
| sku_id | mã SKU | chuỗi 19 số |
| campaign_type | BAU / CAMP / DD | |
| gia_hien_tai | giá sau seller voucher trong deal_plan | VND/sp |
| gia_de_xuat | giá sau seller voucher đề xuất | VND/sp |
| luong_ban_du_kien | số sản phẩm bán/ngày của loại phiên đó, ở giá đề xuất (mô hình) | sp/ngày |
| loi_nhuan_du_kien | lợi nhuận đóng góp/ngày của loại phiên đó | VND/ngày |
| rang_buoc_cham | ràng buộc quyết định mức giá: min_price / legal_cap / inventory / guardrail / none | |
| ly_do | 1 câu giải thích | |
| seller_voucher_hien_tai | voucher hiện tại (trên live_price) | tỷ lệ 0–1 |
| seller_voucher_de_xuat | voucher đề xuất. Lưu 6 chữ số thập phân để tính lại đúng giá tại ngưỡng VXP 200k/300k/500k | tỷ lệ 0–1 |
| gia_khach_tra_de_xuat | giá khách trả sau VXP | VND/sp |

Với loại DD, lượng bán và lợi nhuận là **trung bình một ngày DD trong năm** (8 ngày DD thường, 3 ngày Mega, 1 ngày 11.11).

### `price_recommendation_free.csv` – bản tự do (`toi_uu_tu_do`)
Cột giống file trên. Không có guardrail, không điều chỉnh tồn kho. Dùng để so sánh: bản tự do ra gần như "giảm giá mọi ngày".

### `price_recommendation_summary.csv`
Mỗi dòng 1 loại phiên.

| Cột | Ý nghĩa | Đơn vị |
|---|---|---|
| gia_sau_sv_vs_base_* | trung vị (giá sau seller voucher / base_price) của hiện trạng, tự do, guardrail | tỷ lệ |
| sv_* | trung vị seller voucher | tỷ lệ 0–1 |

---

## Trang What-if

### `model_params.csv`
32 dòng, mỗi dòng 1 SKU. Toàn bộ là tham số **mô hình**, không lấy từ truth.

Công thức:
`đơn/ngày = base_orders_bau × hệ số campaign × (final / ref_final_price)^elasticity_eb × (mức giá đối thủ / comp_level_ref)^gamma_comp`

| Cột | Ý nghĩa | Đơn vị |
|---|---|---|
| elasticity_eb | độ co giãn giá sau co empirical Bayes; dùng cho tối ưu | không đơn vị (âm) |
| elasticity_se | sai số chuẩn của elasticity_eb | |
| elasticity_sku | độ co giãn ước lượng riêng từng SKU (chưa co, nhiễu) | |
| gamma_comp | độ nhạy theo mức giá đối thủ (đối thủ giảm 1% → đơn OLAY giảm ≈ γ%) | |
| base_orders_bau | số đơn/ngày BAU ở giá BAU hiện tại, ngày thường, tháng 10 | đơn/ngày |
| campaign_mult_camp / _dd / _mega / _peak | hệ số nhân so với BAU: CAMP, DD thường, Mega, 11.11 | lần |
| unit_cogs | giá vốn = 35% base_price | VND/sp |
| min_price | giá sàn của giá sau seller voucher | VND/sp |
| base_price | giá Live BAU chuẩn | VND/sp |
| ref_final_price | giá khách trả BAU hiện tại, mốc của base_orders_bau | VND/sp |
| comp_level_ref | mức giá đối thủ ngày BAU (trung bình comp_price/comp_regular_price của need_group), mốc của γ | tỷ lệ (1 = đúng giá niêm yết) |
| comp_level_bau / _camp / _dd | mức giá đối thủ bình thường từng loại ngày | tỷ lệ |
| qty_per_order | số sản phẩm trung bình/đơn | sp/đơn |

### Hàm `what_if` trong `pricing_core.py` (thư mục gốc dự án)
```python
import pricing_core as pc
pc.what_if("1734365470027580675", "BAU", 0.11, elasticity_scale=1.0, comp_drop_pct=0, vxp_on=True)
```
- **campaign_type:**
  - "BAU", "CAMP", "DD" (DD = trung bình ngày DD/Mega/11.11 như bộ tối ưu).
  - Hoặc "DD_THUONG", "MEGA", "PEAK".
- **elasticity_scale:** nhân ε (1,3 = khách nhạy giá hơn 30%).
- **comp_drop_pct:** đối thủ giảm thêm bao nhiêu so với mức bình thường của loại ngày (0,10 = 10%).
- **vxp_on=False:** giả sử không có VXP.

Kết quả trả về:

| Khóa | Ý nghĩa | Đơn vị |
|---|---|---|
| gia_sau_sv | giá sau seller voucher | VND/sp |
| vxp | VXP | VND/sp |
| gia_khach_tra | giá khách trả | VND/sp |
| so_don_ngay | số đơn | đơn/ngày |
| luong_ban_ngay | số sản phẩm | sp/ngày |
| doanh_thu_ngay | doanh thu | VND/ngày |
| loi_nhuan_ngay | lợi nhuận | VND/ngày |
| chi_phi_voucher_ngay | chi phí seller voucher | VND/ngày |
| vi_pham | danh sách ràng buộc bị vi phạm (min_price, legal_cap, sv_ngoai_0_30pct) | |

Đã kiểm tra: gọi `what_if` ở mức voucher đề xuất cho ra đúng `luong_ban_du_kien` và `loi_nhuan_du_kien` của cả 96 dòng `price_recommendation.csv`.

---

## Trang Mô hình nhu cầu

### `elasticity_compare.csv` – so sánh hệ số giá theo cách ước lượng
| Cột | Ý nghĩa |
|---|---|
| phien_ban | (a0) không campaign, không đối thủ; (a) không campaign; (b) không giá đối thủ; (c) đầy đủ, mô hình chính; (d) theo product_type; (e) từng SKU; (f) EB |
| nhom | tất cả / single / combo |
| eps_loglog, se_loglog | ε và sai số chuẩn, hồi quy log(đơn). Với (e), (f): trung bình nhóm và trung vị se |
| eps_poisson, se_poisson | ε và se theo Poisson GLM (giữ cả ngày 0 đơn) |
| gamma_loglog | γ đối thủ |
| so_voi_Bijmolt | ε − (−2,62), so với trung bình meta-analysis Bijmolt et al. 2005 |

### `elasticity_by_sku.csv` – 32 SKU
| Cột | Ý nghĩa | Đơn vị |
|---|---|---|
| product_name, product_type | tên, single/combo | |
| n_ngay | số ngày train có đơn > 0 | ngày |
| don_tb_ngay | số đơn trung bình | đơn/ngày |
| elasticity_sku, elasticity_se | ε riêng SKU và sai số chuẩn | |
| gamma_sku | γ riêng SKU (tham khảo) | |
| sd_log_gia | độ lệch chuẩn log giá khách trả, mọi ngày train | |
| sd_log_gia_trong_phien | độ lệch chuẩn log giá trong cùng campaign_tier (biến động dùng để ước lượng ε) | ≈ % biến động |
| elasticity_eb, elasticity_eb_se | ε sau co EB và sai số chuẩn | |
| he_so_co_B | B = τ²/(τ²+se²): tỷ trọng giữ lại của ε riêng (0 = kéo hẳn về trung bình nhóm) | 0–1 |

### `demand_model_compare.csv` – sai số dự báo số đơn/ngày, 01–15/10, bỏ ngày hết hàng
| Cột | Ý nghĩa | Đơn vị |
|---|---|---|
| mo_hinh | naive / log-log EB / LightGBM | |
| loai_ngay | Tổng / BAU / CAMP / DD-Mega 10.10 | |
| so_sku_ngay | số SKU-ngày được chấm | |
| tong_don_thuc, tong_don_du_bao | tổng số đơn thực tế / dự báo | đơn |
| bias_pct | tổng dự báo lệch so với tổng thực | % |
| wape | Σ\|thực − dự báo\| / Σ thực | tỷ lệ (0,25 = sai 25%) |

---

## Trang Tồn kho

### `inventory_sim_test.csv` – mô phỏng 01–15/10 theo ngày ở giá guardrail (sau điều chỉnh tồn kho), cầu theo mô hình
| Cột | Ý nghĩa | Đơn vị |
|---|---|---|
| date, sku_id, campaign_type | ngày, SKU, loại phiên | |
| sv, a, final | voucher, giá sau voucher, giá khách trả của ngày đó | tỷ lệ 0–1; VND/sp |
| orders_dem | nhu cầu | đơn/ngày |
| demand | nhu cầu | sp/ngày |
| sold | bán được (sau khi chặn bởi tồn kho) | sp/ngày |
| fill | sold / demand (1 = đủ hàng) | 0–1 |
| open_stock | tồn đầu ngày sau khi nhận hàng về; chỉ có ở SKU đơn | sp |
| need_total | tổng nhu cầu lên SKU đơn = chính nó + các combo chứa nó; chỉ có ở SKU đơn | sp/ngày |

---

## Trang Đối thủ

### `competitor_alerts.csv` – cảnh báo đổi giá đối thủ (change_flag = 1) trong 01–15/10, **chỉ giữ ngày BAU**
| Cột | Ý nghĩa | Đơn vị |
|---|---|---|
| snapshot_ts, date | thời điểm chụp giá (4 lần/ngày) | |
| loai_ngay | luôn là BAU sau khi lọc | |
| comp_product_id, competitor_brand, comp_product, need_group | sản phẩm đối thủ | |
| comp_regular_price, comp_price | giá niêm yết, giá bán | VND |
| pct_change_vs_prev | thay đổi so với snapshot trước | tỷ lệ (−0,215 = giảm 21,5%) |
| huong | giảm giá / tăng giá (hết đợt giảm) | |
| sku_olay_ghep | số SKU OLAY được ghép với sản phẩm đối thủ này | SKU |

### `competitor_response.csv` – case C01 giảm 22%, 06–08/10, 5 SKU OLAY (Retinol24 kem đêm bị loại vì hết hàng)
Mỗi SKU có 4 dòng phương án:
- `khong_doi_thu_giam`: tham chiếu, giá guardrail nếu C01 không giảm.
- `giu_gia`: giữ giá guardrail.
- `match`: hạ giá giữ chỉ số giá/ml so với C01.
- `chuyen_voucher`: voucher nhắm mục tiêu 10% cho 20% đơn. Tỷ lệ này là giả định.

Ngoài ra có dòng `TONG` (tổng 5 SKU) và dòng `loai_khoi_so_sanh` (Retinol24 kem đêm).

| Cột | Ý nghĩa | Đơn vị |
|---|---|---|
| seller_voucher_pct | voucher | tỷ lệ 0–1 |
| gia_sau_sv, gia_khach_tra | giá | VND/sp |
| chi_so_gia_ml_vs_C01 | (giá khách trả OLAY/ml) ÷ (giá C01/ml trong đợt giảm) | tỷ lệ |
| chi_so_gia_ml_vs_C01_truoc_dot_giam | cùng chỉ số trước đợt giảm (mục tiêu của `match`) | tỷ lệ |
| so_don, luong_ban | tổng 3 ngày | đơn; sp |
| doanh_thu, loi_nhuan | tổng 3 ngày | VND |
| chi_phi_seller_voucher, chi_phi_voucher_nham_muc_tieu, chi_phi_voucher | tổng 3 ngày; chi_phi_voucher = tổng hai loại | VND |
| loi_nhuan_vs_giu_gia_pct | so với `giu_gia` | % |
| rang_buoc_cham | none / min_price / sv_max_30% / inventory | |
| ghi_chu | giả định / ghi chú | |

---

## Trang Đánh giá & ROI (chấm bằng cầu thật)

Phương án dùng chung cho các file dưới đây:
- `hien_trang`: deal_plan.
- `match_doi_thu`: repricer luôn giảm theo đối thủ giảm sâu nhất cùng need_group, chặn ở sàn và voucher 30%.
- `giam_sau`: voucher 30% hoặc chạm sàn mọi ngày.
- `toi_uu_tu_do`.
- `toi_uu_guardrail`.
- `oracle`: tối ưu bằng ε thật, chỉ để biết trần.

### `pricing_eval.csv` – giai đoạn test 01–15/10, có tồn kho thật (thiếu hàng = mất doanh số)
| Cột | Ý nghĩa | Đơn vị |
|---|---|---|
| loi_nhuan, doanh_thu, chi_phi_voucher | tổng 15 ngày, 32 SKU | VND |
| so_vi_pham_rang_buoc | = vp_min_price + vp_duoi_50pct_base + vp_dao_thang_gia_sku | |
| chenh_lech_vs_hien_trang_pct | lợi nhuận so với hiện trạng | % |
| vp_min_price, vp_duoi_50pct_base | số SKU-ngày dưới giá sàn / giá khách trả dưới 50% base | SKU-ngày |
| vp_dao_thang_gia_sku | số SKU có giá khách trả DD > CAMP hoặc CAMP > BAU | SKU |
| so_don | số đơn bán được | đơn |
| doanh_so_mat_do_het_hang | doanh thu mất vì thiếu hàng | VND |
| sku_ngay_thieu_hang | số SKU-ngày bị thiếu hàng | SKU-ngày |

### `pricing_eval_annual.csv` – quy 1 năm (365 ngày: BAU 329 / CAMP 24 / DD 12), không tính tồn kho
Cột như `pricing_eval.csv` (bỏ 2 cột tồn kho). Thêm cột `loi_nhuan_tang_them_vnd` = lợi nhuận − hiện trạng (VND/năm). **Dùng file này cho ROI.**

### `guardrail_curve.csv` – nới trần voucher BAU
| Cột | Ý nghĩa | Đơn vị |
|---|---|---|
| tran_bau | +0 / +2 / +4 / +6 điểm % so với voucher BAU hiện tại, hoặc tu_do | |
| voucher_bau/camp/dd_trung_vi | trung vị voucher đề xuất | tỷ lệ 0–1 |
| loi_nhuan_nam | lợi nhuận năm | VND |
| loi_nhuan_tang_pct | so với hiện trạng | % |

### `pricing_sensitivity.csv` – tối ưu bằng ε sai lệch rồi chấm bằng cầu thật
| Cột | Ý nghĩa | Đơn vị |
|---|---|---|
| eps_dung_de_toi_uu | EB × 0,5 / 0,7 / 0,9 / 1,0 / 1,1 / 1,3 / 1,5; ε từng SKU chưa co; ε thật | |
| phuong_an | toi_uu_tu_do / toi_uu_guardrail | |
| voucher_bau_trung_vi, voucher_dd_trung_vi | trung vị voucher | tỷ lệ 0–1 |
| loi_nhuan_nam | lợi nhuận năm | VND |
| chenh_lech_vs_hien_trang_pct | so với hiện trạng | % |

### `guardrail_gain_split.csv` – lợi nhuận tăng thêm của guardrail theo nhóm SKU (năm)
| Cột | Ý nghĩa | Đơn vị |
|---|---|---|
| nhom | 13 SKU bị đảo thang giá trong deal_plan / 19 SKU còn lại / Tổng | |
| hien_trang, guardrail, tu_do | lợi nhuận năm | VND |
| guardrail_tang_vnd | guardrail − hiện trạng | VND/năm |
| guardrail_tang_pct_nhom | % tăng trong nhóm | % |
| ty_trong_trong_tong_tang_pct | tỷ trọng của nhóm trong tổng phần tăng | % |
| tu_do_tang_pct_nhom | % tăng của bản tự do trong nhóm | % |
