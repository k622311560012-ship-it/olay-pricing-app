import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from common import (ACCENT, COMP, GRAY, LIGHT, OLAY, RC_LABELS, RET24_CREAM, WARN, campaign_days, data_note, money,
                    num, page_header, pct_points, read_csv, short_name, style_fig, vnd)

comp = read_csv("app_data/comp_ppu_daily.csv")
olay = read_csv("app_data/olay_ppu_daily.csv")
pairs = read_csv("app_data/comp_pairs.csv")
al = read_csv("results/competitor_alerts.csv")
cr = read_csv("results/competitor_response.csv")
tot = cr[cr["sku_id"] == "TONG"].set_index("phuong_an")

page_header("Giá đối thủ",
            f"{len(al)} lần đối thủ đổi giá bất thường trong 01–15/10 cần người duyệt xem. Với đợt C01 giảm 22%, "
            f"giữ giá và phát voucher nhắm mục tiêu tốt hơn match giá "
            f"({pct_points(tot.at['chuyen_voucher', 'loi_nhuan_vs_giu_gia_pct'])} so với "
            f"{pct_points(tot.at['match', 'loi_nhuan_vs_giu_gia_pct'])} lợi nhuận, so với giữ giá).")

# ------------------------------------------------------------------ biểu đồ
st.subheader("Giá OLAY và đối thủ cùng phân khúc")
skus = sorted(pairs["sku_id"].unique(), key=short_name)
c1, c2, c3 = st.columns([1.6, 1.4, 2])
default = "1734365584002745603"
sku = c1.selectbox("SKU OLAY", skus, index=skus.index(default) if default in skus else 0, format_func=short_name)
mode = c2.radio("Hiển thị", ["Giá/ml (g)", "Chỉ số giá OLAY/đối thủ"], horizontal=True)
dates = sorted(comp["date"].unique())
d0, d1 = c3.select_slider("Khoảng ngày", options=dates, value=("2026-08-01", dates[-1]),
                          format_func=lambda d: f"{d[8:]}/{d[5:7]}/{d[:4]}")

comps = pairs.loc[pairs["sku_id"] == sku, "comp_product_id"].tolist()
o = olay[(olay["sku_id"] == sku) & olay["date"].between(d0, d1)].set_index("date")
fig = go.Figure()
for d, ct in campaign_days(d0, d1):
    end = (pd.Timestamp(d) + pd.Timedelta(days=1)).strftime("%Y-%m-%d")
    fig.add_vrect(x0=d, x1=end, fillcolor=LIGHT, opacity=0.9, line_width=0, layer="below")
dashes = ["solid", "dash", "dot", "dashdot", "longdash", "longdashdot"]
for i, cid in enumerate(comps):
    c = comp[(comp["comp_product_id"] == cid) & comp["date"].between(d0, d1)].set_index("date")
    name = f"{c['competitor_brand'].iat[0]} {c['comp_product'].iat[0]}"
    y = c["comp_price_per_unit"] if mode.startswith("Giá") else o["olay_price_per_unit"] / c["comp_price_per_unit"]
    fig.add_trace(go.Scatter(x=y.index, y=y.values, name=name, line=dict(color=COMP if cid != "C01" else GRAY, width=1.6,
                                                                         dash=dashes[i % len(dashes)]),
                             hovertemplate=f"{name}<br>%{{x}}: %{{y:,.2f}}<extra></extra>"))
if mode.startswith("Giá"):
    fig.add_trace(go.Scatter(x=o.index, y=o["olay_price_per_unit"], name=f"OLAY {short_name(sku)}",
                             line=dict(color=OLAY, width=3), hovertemplate="OLAY<br>%{x}: %{y:,.0f}đ<extra></extra>"))
    fig.update_yaxes(title="Giá khách trả / ml (g)", rangemode="tozero", ticksuffix="đ")
else:
    fig.add_hline(y=1, line_color=OLAY, line_width=2, annotation_text="OLAY = đối thủ", annotation_position="bottom right")
    fig.update_yaxes(title="Giá/ml OLAY ÷ giá/ml đối thủ", rangemode="tozero")
if d0 <= "2026-10-06" <= d1:
    fig.add_vrect(x0="2026-10-06", x1="2026-10-09", fillcolor=WARN, opacity=0.15, line_width=0,
                  annotation_text="C01 −22%", annotation_position="top left", annotation_font_color=WARN)
st.plotly_chart(style_fig(fig, 420))
st.caption("Nền xám: ngày CAMP và ngày đôi – giá đối thủ giảm ngày campaign là bình thường. "
           "Nền đỏ: đợt C01 (L'Oréal Revitalift kem ngày) giảm 22% từ 06/10. "
           + ("Giá OLAY là giá khách trả sau voucher và trợ giá TikTok." if mode.startswith("Giá")
              else "Trên 1: OLAY đắt hơn đối thủ tính theo ml (g)."))

# ------------------------------------------------------------------ cảnh báo
st.subheader("Cảnh báo cần duyệt")
st.dataframe(pd.DataFrame({
    "Thời điểm": al["snapshot_ts"].str[8:10] + "/" + al["snapshot_ts"].str[5:7] + " " + al["snapshot_ts"].str[11:16],
    "Đối thủ": al["competitor_brand"] + " " + al["comp_product"],
    "Thay đổi": al["pct_change_vs_prev"].map(lambda v: pct_points(100 * v, 1)),
    "Giá mới": al["comp_price"].map(vnd), "Hướng": al["huong"],
    "SKU OLAY bị ảnh hưởng": al["sku_olay_ghep"],
}), hide_index=True, height=280)
st.caption("Chỉ giữ các lần đổi giá rơi vào ngày thường; đổi giá trùng ngày campaign đã được loại.")

# ------------------------------------------------------------------ case C01
st.subheader("Case C01 giảm 22% (06–08/10): ba phương án cho 5 SKU OLAY")
LAB = {"khong_doi_thu_giam": "Tham chiếu: C01 không giảm", "giu_gia": "Giữ giá", "match": "Match giá/ml",
       "chuyen_voucher": "Giữ giá + voucher nhắm mục tiêu"}
order = ["khong_doi_thu_giam", "giu_gia", "match", "chuyen_voucher"]
t = tot.loc[order]
c1, c2 = st.columns([1.1, 1])
fig = go.Figure(go.Bar(
    x=[LAB[p] for p in order], y=t["loi_nhuan"],
    marker_color=[LIGHT, GRAY, GRAY, ACCENT], text=t["loi_nhuan"].map(money), textposition="outside", cliponaxis=False))
fig.update_yaxes(title="Lợi nhuận 3 ngày", rangemode="tozero")
c1.plotly_chart(style_fig(fig, 320, legend=False))
c2.dataframe(pd.DataFrame({
    "Phương án": [LAB[p] for p in order],
    "Lợi nhuận": t["loi_nhuan"].map(money).values,
    "So với giữ giá": t["loi_nhuan_vs_giu_gia_pct"].map(pct_points).values,
    "Số đơn": t["so_don"].map(lambda x: num(x, 0)).values,
    "Chi phí voucher": t["chi_phi_voucher"].map(money).values,
}), hide_index=True)
gamma = read_csv("results/model_params.csv")["gamma_comp"].iat[0]
c2.markdown(
    f"- Đối thủ giảm giá làm cầu OLAY giảm {num(100 * (1 - t.at['giu_gia', 'so_don'] / t.at['khong_doi_thu_giam', 'so_don']), 1)}%; "
    "mức giá có lợi nhất **không đổi**.\n"
    f"- Match: số đơn ×{num(t.at['match', 'so_don'] / t.at['giu_gia', 'so_don'], 1)} nhưng chi phí voucher "
    f"×{num(t.at['match', 'chi_phi_voucher'] / t.at['giu_gia', 'chi_phi_voucher'], 1)}.\n"
    "- Voucher nhắm mục tiêu 10% cho 20% đơn là **giả định**.")
st.caption(f"{short_name(RET24_CREAM)} cũng cạnh tranh với C01 nhưng đang hết hàng nên không đưa vào so sánh. "
           "Mô hình giả định độ nhạy giá không đổi khi đối thủ giảm giá; thực tế khách có thể nhạy giá hơn.")
with st.expander("Chi tiết từng SKU"):
    det = cr[(cr["sku_id"] != "TONG") & (cr["phuong_an"] != "loai_khoi_so_sanh")]
    st.dataframe(pd.DataFrame({
        "SKU": det["sku_id"].map(short_name), "Phương án": det["phuong_an"].map(LAB),
        "Khách trả": det["gia_khach_tra"].map(vnd), "Lợi nhuận 3 ngày": det["loi_nhuan"].map(money),
        "So với giữ giá": det["loi_nhuan_vs_giu_gia_pct"].map(pct_points),
        "Ràng buộc": det["rang_buoc_cham"].map(lambda x: RC_LABELS.get(x, x)),
    }), hide_index=True)

data_note()
