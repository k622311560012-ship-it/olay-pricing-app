import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from common import (ACCENT, COMP, GRAY, OLAY, RET24_CREAM, WARN, data_note, full_name, money, num, page_header, pct,
                    read_csv, short_name, style_fig, vnd)

rec = read_csv("results/price_recommendation.csv")
floor = read_csv("app_data/price_floor.csv")
sim = read_csv("results/inventory_sim_test.csv")
inv = read_csv("app_data/inventory.csv")

m = rec.merge(floor[["sku_id", "campaign_type", "base_price", "min_price", "legal_min_customer_price"]],
              on=["sku_id", "campaign_type"])
m["cach_san"] = m["gia_de_xuat"] / m["min_price"] - 1
m["cach_tran"] = m["gia_khach_tra_de_xuat"] / m["legal_min_customer_price"] - 1
n_floor, n_legal = int((m["cach_san"] < 0).sum()), int((m["cach_tran"] < 0).sum())
ret_short = sim[(sim["sku_id"] == RET24_CREAM) & (sim["fill"] < 0.999)]["date"]

page_header("Ràng buộc Finance & Supply chain",
            ("Không dòng nào dưới giá sàn hay dưới 50% giá gốc; " if n_floor + n_legal == 0 else
             f"{n_floor + n_legal} dòng vi phạm giá sàn/trần 50%; ")
            + f"ràng buộc đang chạm thật là tồn kho của {short_name(RET24_CREAM)} (thiếu {len(ret_short)} ngày, gồm 10.10).")

# ------------------------------------------------------------------ giá sàn & trần 50%
st.subheader("Giá sàn và mức giảm tối đa 50%")
c = st.columns(3)
c[0].metric("Dòng dưới giá sàn", n_floor)
c[1].metric("Dòng khách trả dưới 50% giá gốc", n_legal)
c[2].metric("Khoảng cách tới giá sàn (nhỏ nhất)", pct(m["cach_san"].min()))
st.caption("Giá sàn: giá sau voucher thấp nhất để brand còn lãi ít nhất 10% giá niêm yết gốc. "
           f"Giá đề xuất trung vị ≈ {num((m['gia_de_xuat'] / m['base_price']).median(), 2)} × giá gốc, "
           f"cao hơn giá sàn (≈ {num((m['min_price'] / m['base_price']).median(), 2)} × giá gốc).")

m = m.sort_values("cach_san")
tbl = pd.DataFrame({
    "SKU": m["sku_id"].map(short_name), "Phiên": m["campaign_type"], "Giá niêm yết gốc": m["base_price"].map(vnd),
    "Giá sàn": m["min_price"].map(vnd), "Giá đề xuất": m["gia_de_xuat"].map(vnd), "Cách giá sàn": m["cach_san"].map(pct),
    "Khách trả đề xuất": m["gia_khach_tra_de_xuat"].map(vnd), "Khách trả tối thiểu (50%)": m["legal_min_customer_price"].map(vnd),
    "Cách mức 50%": m["cach_tran"].map(pct), "Tên đầy đủ": m["sku_id"].map(full_name),
})
st.markdown("10 dòng gần giá sàn nhất")
st.dataframe(tbl.head(10), hide_index=True)
with st.expander(f"Xem {len(tbl) - 10} dòng còn lại"):
    st.dataframe(tbl.iloc[10:], hide_index=True)

# ------------------------------------------------------------------ Retinol24 kem đêm
with st.container(border=True):
    st.subheader(f"{short_name(RET24_CREAM)}: tồn kho 01–15/10")
    s = sim[sim["sku_id"] == RET24_CREAM]
    real = inv[(inv["sku_id"] == RET24_CREAM) & (inv["date"] >= "2026-10-01")]
    fig = go.Figure()
    fig.add_bar(x=s["date"], y=s["need_total"], name="Nhu cầu (gồm 2 combo chứa SKU này)", marker_color=COMP)
    fig.add_scatter(x=s["date"], y=s["open_stock"], name="Tồn đầu ngày", mode="lines+markers", line=dict(color=OLAY, width=3))
    inb = real[real["inbound_units"] > 0]
    fig.add_scatter(x=inb["date"], y=inb["inbound_units"], name="Hàng về", mode="markers+text",
                    text=inb["inbound_units"].map(lambda v: f"+{num(v, 0)}"), textposition="top center",
                    marker=dict(size=13, symbol="triangle-up", color=ACCENT))
    fig.add_vrect(x0="2026-10-09 12:00", x1="2026-10-10 12:00", fillcolor=WARN, opacity=0.12, line_width=0,
                  annotation_text="10.10", annotation_position="top left", annotation_font_color=WARN)
    fig.update_yaxes(title="sản phẩm", rangemode="tozero")
    st.plotly_chart(style_fig(fig, 340))
    c1, c2 = st.columns(2)
    c1.metric("Tồn 01/10", f"{num(real['opening_units'].iat[0], 0)} sp")
    c2.metric("Hàng về", ", ".join(f"{num(v, 0)} sp ngày {d[8:]}/{d[5:7]}" for d, v in zip(inb["date"], inb["inbound_units"])))
    st.error(f"**Giá không đủ cứu 10.10 — cần Supply chain đẩy lô hàng.** Đã bỏ voucher về 0% cho SKU này và 2 combo "
             f"chứa nó trong 01–11/10, nhưng vẫn thiếu hàng {ret_short.str[8:10].iloc[0]}–{ret_short.str[8:10].iloc[-1]}/10. "
             "Lô hàng về 12/10 đang trễ; cân nhắc tạm ngừng 2 combo để dành hàng.")

# ------------------------------------------------------------------ ngân sách voucher
st.subheader("Ngân sách khuyến mãi theo ngày")
pb = read_csv("app_data/promo_budget.csv")
r = st.select_slider("Khoảng ngày", options=sorted(pb["date"]), value=("2026-08-01", pb["date"].max()), key="pb_range",
                     format_func=lambda d: f"{d[8:]}/{d[5:7]}/{d[:4]}")
p = pb[pb["date"].between(*r)]
fig = go.Figure()
fig.add_bar(x=p["date"], y=p["spent_vnd"], name="Đã chi", marker_color=[WARN if a else ACCENT for a in p["alert_triggered"]])
fig.add_scatter(x=p["date"], y=p["budget_vnd"], name="Ngân sách", mode="lines", line=dict(color="#1C2430", dash="dot"))
fig.add_scatter(x=p["date"], y=p["budget_vnd"] * p["alert_pct"], name="Ngưỡng cảnh báo", mode="lines",
                line=dict(color=GRAY, dash="dash"))
fig.update_yaxes(title="đồng/ngày", rangemode="tozero")
st.plotly_chart(style_fig(fig, 320))
c = st.columns(3)
c[0].metric("Ngân sách (khoảng đã chọn)", money(p["budget_vnd"].sum()))
c[1].metric("Đã chi", money(p["spent_vnd"].sum()), pct(p["spent_vnd"].sum() / p["budget_vnd"].sum()) + " ngân sách",
            delta_color="off")
c[2].metric("Ngày vượt ngưỡng cảnh báo", int(p["alert_triggered"].sum()))
st.caption("Cột đỏ: ngày chi vượt ngưỡng cảnh báo.")

# ------------------------------------------------------------------ tồn kho các SKU khác
with st.expander("Tồn kho 01–15/10 của các SKU khác"):
    singles = sorted(sim.loc[sim["open_stock"].notna(), "sku_id"].unique(), key=short_name)
    sku = st.selectbox("SKU", singles, format_func=short_name)
    s = sim[sim["sku_id"] == sku]
    fig = go.Figure()
    fig.add_bar(x=s["date"], y=s["need_total"], name="Nhu cầu (gồm combo)", marker_color=COMP)
    fig.add_scatter(x=s["date"], y=s["open_stock"], name="Tồn đầu ngày", mode="lines+markers", line=dict(color=OLAY, width=3))
    fig.update_yaxes(title="sản phẩm", rangemode="tozero")
    st.plotly_chart(style_fig(fig, 300))
    st.write("Đủ hàng cả giai đoạn." if (s["fill"] >= 0.999).all() else f"Thiếu hàng {int((s['fill'] < 0.999).sum())} ngày.")

data_note()
