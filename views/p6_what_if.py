import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

import pricing_core as pc
from common import (ACCENT, GRAY, OLAY, data_note, full_name, money, num, pct, pct_points, read_csv, short_name,
                    style_fig, vnd)

mp = read_csv("results/model_params.csv")
rec = read_csv("results/price_recommendation.csv").set_index(["sku_id", "campaign_type"])
deal = read_csv("app_data/deal_plan.csv").set_index(["sku_id", "campaign_type"])
TYPES = {"BAU": "Ngày thường", "CAMP": "Ngày CAMP (15, 25)", "DD": "Ngày đôi (trung bình năm)",
         "DD_THUONG": "Ngày đôi thường", "MEGA": "Mega (9.9, 10.10, 12.12)", "PEAK": "11.11"}

st.header("What-if")
head = st.empty()

c1, c2 = st.columns([3, 2])
skus = sorted(mp["sku_id"], key=short_name)
sku = c1.selectbox("SKU", skus, index=skus.index("1734365470027580675") if "1734365470027580675" in skus else 0,
                   format_func=short_name, help="Chọn SKU để xem tên đầy đủ bên dưới")
ct = c2.selectbox("Loại phiên", list(TYPES), format_func=TYPES.get)
plan_ct = "DD" if ct in ("DD", "DD_THUONG", "MEGA", "PEAK") else ct
sv_cur = float(deal.at[(sku, plan_ct), "seller_voucher_pct"])
sv_rec = float(rec.at[(sku, plan_ct), "seller_voucher_de_xuat"])
st.caption(full_name(sku))

c1, c2, c3, c4 = st.columns(4)
sv = c1.slider("Seller voucher", 0.0, 30.0, round(100 * sv_rec * 2) / 2, 0.5, format="%.1f%%") / 100
eps_scale = c2.slider("Độ nhạy giá của khách", 0.5, 1.5, 1.0, 0.05, format="× %.2f",
                      help="1,0 = như mô hình ước lượng; 1,3 = khách nhạy giá hơn 30%")
comp_drop = c3.slider("Đối thủ giảm thêm", 0, 30, 0, 1, format="%d%%")  / 100
vxp_on = c4.toggle("TikTok trợ giá (VXP)", value=True)

kw = dict(elasticity_scale=eps_scale, comp_drop_pct=comp_drop, vxp_on=vxp_on)
w = pc.what_if(sku, ct, sv, **kw)
w_cur = pc.what_if(sku, ct, sv_cur, **kw)
w_rec = pc.what_if(sku, ct, sv_rec, **kw)

grid = np.round(np.arange(0, 0.3001, 0.005), 4)
curve = pd.DataFrame([pc.what_if(sku, ct, g, **kw) for g in grid])
curve["ok"] = curve["vi_pham"].map(len) == 0
best = curve[curve["ok"]].loc[lambda d: d["loi_nhuan_ngay"].idxmax()]
head.markdown(f"**{short_name(sku)}, {TYPES[ct].lower()}: mức voucher có lợi nhuận cao nhất là {pct(best['seller_voucher_pct'])}; "
              f"hệ thống đề xuất {pct(sv_rec)} (đã tính guardrail).**")

if w["vi_pham"]:
    msg = {"min_price": f"giá sau voucher {vnd(w['gia_sau_sv'])} thấp hơn giá sàn",
           "legal_cap": f"khách trả {vnd(w['gia_khach_tra'])} dưới 50% giá niêm yết gốc",
           "sv_ngoai_0_30pct": "voucher ngoài khoảng 0–30%"}
    st.error("Không được phép: " + "; ".join(msg.get(v, v) for v in w["vi_pham"]) + ".")

m = st.columns(5)
m[0].metric("Giá sau voucher", vnd(w["gia_sau_sv"]), vnd(w["gia_sau_sv"] - w_cur["gia_sau_sv"]), delta_color="off")
m[1].metric("Khách trả", vnd(w["gia_khach_tra"]), f"TikTok trợ {vnd(w['vxp'])}" if w["vxp"] else "không trợ giá",
            delta_color="off", delta_arrow="off")
m[2].metric("Số đơn/ngày", num(w["so_don_ngay"], 1), num(w["so_don_ngay"] - w_cur["so_don_ngay"], 1))
m[3].metric("Doanh thu/ngày", money(w["doanh_thu_ngay"]), money(w["doanh_thu_ngay"] - w_cur["doanh_thu_ngay"], sign=True))
m[4].metric("Lợi nhuận/ngày", money(w["loi_nhuan_ngay"]), money(w["loi_nhuan_ngay"] - w_cur["loi_nhuan_ngay"], sign=True))
diff = w["loi_nhuan_ngay"] - w_rec["loi_nhuan_ngay"]
cmp = ("bằng" if abs(diff) < 1 else ("cao hơn" if diff > 0 else "thấp hơn"))
st.markdown(f"So với voucher hiện tại {pct(sv_cur)} (mũi tên ở trên). **So với đề xuất của hệ thống ({pct(sv_rec)}): "
            f"lợi nhuận/ngày {cmp}{'' if cmp == 'bằng' else ' ' + money(abs(diff))}.**")

# ------------------------------------------------------------------ đường lợi nhuận
fig = go.Figure()
fig.add_scatter(x=100 * curve["seller_voucher_pct"], y=curve["loi_nhuan_ngay"], mode="lines", name="Lợi nhuận/ngày",
                line=dict(color=GRAY, width=3), hovertemplate="Voucher %{x:.1f}%: %{y:,.0f}đ<extra></extra>")
bad = curve[~curve["ok"]]
if len(bad):
    fig.add_scatter(x=100 * bad["seller_voucher_pct"], y=bad["loi_nhuan_ngay"], mode="markers", name="Không được phép",
                    marker=dict(color="#B23B3B", size=6))
for x, y, lab, col, sym, size in [(sv_cur, w_cur["loi_nhuan_ngay"], "Hiện tại", GRAY, "circle", 11),
                                  (sv_rec, w_rec["loi_nhuan_ngay"], "Đề xuất", ACCENT, "diamond", 13),
                                  (sv, w["loi_nhuan_ngay"], "Đang chọn", OLAY, "star", 15)]:
    fig.add_scatter(x=[100 * x], y=[y], mode="markers", name=f"{lab}: {pct(x)}",
                    marker=dict(color=col, size=size, symbol=sym, line=dict(width=1, color="white")))
fig.update_xaxes(title="Seller voucher", ticksuffix="%")
fig.update_yaxes(title="Lợi nhuận/ngày")
st.plotly_chart(style_fig(fig, 380))
st.caption("Đường gãy đột ngột: giá chạm mốc 200.000đ / 300.000đ / 500.000đ, TikTok trợ thêm 13–15% nên giá khách trả giảm hẳn.")

# ------------------------------------------------------------------ đường guardrail
st.subheader("Nới trần voucher ngày thường thì lợi nhuận năm tăng bao nhiêu?")
gc = read_csv("results/guardrail_curve.csv")
lab = {"+0": "Giữ nguyên", "+2": "+2 điểm %", "+4": "+4 điểm %", "+6": "+6 điểm %", "tu_do": "Không giới hạn"}
fig = go.Figure(go.Bar(x=gc["tran_bau"].map(lab), y=gc["loi_nhuan_tang_pct"], text=gc["loi_nhuan_tang_pct"].map(pct_points),
                       textposition="outside", cliponaxis=False,
                       marker_color=[ACCENT if t == "+2" else GRAY for t in gc["tran_bau"]]))
fig.update_yaxes(title="Lợi nhuận/năm so với hiện trạng", ticksuffix="%", rangemode="tozero")
st.plotly_chart(style_fig(fig, 300, legend=False))
st.caption("Cột đậm là phương án đề xuất. Đánh giá trên dữ liệu mô phỏng có đáp án, quy 1 năm.")

data_note()
