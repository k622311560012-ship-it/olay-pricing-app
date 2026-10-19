import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from common import (ACCENT, GRAY, PA_LABELS, data_note, money, num, page_header, pct_points, read_csv,
                    short_name, style_fig)

annual = read_csv("results/pricing_eval_annual.csv")
test = read_csv("results/pricing_eval.csv")
a = annual.set_index("phuong_an")
g, h = a.loc["toi_uu_guardrail"], a.loc["hien_trang"]

viol = int(g["so_vi_pham_rang_buoc"])
page_header("Tổng quan",
            f"Phương án đề xuất tăng lợi nhuận {pct_points(g['chenh_lech_vs_hien_trang_pct'], sign=False)}/năm "
            f"(≈{money(g['loi_nhuan'] - h['loi_nhuan'])})"
            + (" mà không vi phạm ràng buộc nào." if viol == 0 else f", còn {viol} vi phạm ràng buộc."))
st.caption("Đánh giá trên dữ liệu mô phỏng có đáp án, quy 1 năm (329 ngày thường, 24 ngày CAMP, 12 ngày đôi). "
           "Lợi nhuận = lợi nhuận đóng góp của brand sau phí sàn, giá vốn và phí đơn.")

c = st.columns(4)
c[0].metric("Lợi nhuận/năm", money(g["loi_nhuan"]), money(g["loi_nhuan"] - h["loi_nhuan"], sign=True))
c[1].metric("Doanh thu/năm", money(g["doanh_thu"]), money(g["doanh_thu"] - h["doanh_thu"], sign=True))
c[2].metric("Chi phí voucher/năm", money(g["chi_phi_voucher"]), money(g["chi_phi_voucher"] - h["chi_phi_voucher"], sign=True),
            delta_color="inverse")
c[3].metric("Vi phạm ràng buộc", viol, f"{viol - int(h['so_vi_pham_rang_buoc'])} so với hiện trạng", delta_color="inverse")

# ------------------------------------------------------------------ 6 phương án
st.subheader("So sánh 6 phương án")
view = st.radio("Phạm vi", ["Quy 1 năm", "15 ngày test 01–15/10 (có tồn kho thật)"], horizontal=True, label_visibility="collapsed")
df = (annual if view == "Quy 1 năm" else test).copy()
df["ten"] = df["phuong_an"].map(PA_LABELS)
df = df.sort_values("chenh_lech_vs_hien_trang_pct")
fig = go.Figure(go.Bar(
    x=df["chenh_lech_vs_hien_trang_pct"], y=df["ten"], orientation="h",
    marker_color=[ACCENT if p == "toi_uu_guardrail" else GRAY for p in df["phuong_an"]],
    text=df["chenh_lech_vs_hien_trang_pct"].map(pct_points), textposition="outside", cliponaxis=False,
    hovertemplate="%{y}: %{text}<extra></extra>"))
fig.add_vline(x=0, line_color="#1C2430", line_width=1)
lo, hi = df["chenh_lech_vs_hien_trang_pct"].min(), df["chenh_lech_vs_hien_trang_pct"].max()
fig.update_xaxes(title="Lợi nhuận so với hiện trạng (%)", ticksuffix="%", zeroline=False,
                 range=[min(lo, 0) * 1.35 - 0.3, max(hi, 0) * 1.35 + 0.3])
st.plotly_chart(style_fig(fig, 320, legend=False))

with st.expander("Bảng chi tiết 6 phương án"):
    t = pd.DataFrame({
        "Phương án": df["ten"], "Lợi nhuận": df["loi_nhuan"].map(money),
        "So với hiện trạng": df["chenh_lech_vs_hien_trang_pct"].map(pct_points),
        "Doanh thu": df["doanh_thu"].map(money), "Chi phí voucher": df["chi_phi_voucher"].map(money),
        "Số đơn": df["so_don"].map(lambda x: num(x, 0)), "Vi phạm ràng buộc": df["so_vi_pham_rang_buoc"].astype(int),
    }).iloc[::-1]
    if "doanh_so_mat_do_het_hang" in df:
        t["Doanh số mất do hết hàng"] = df["doanh_so_mat_do_het_hang"].iloc[::-1].map(money).values
    st.dataframe(t, hide_index=True)
    st.caption("Trần lý thuyết = tối ưu khi biết chính xác độ nhạy giá thật (chỉ để tham chiếu). "
               "Vi phạm ràng buộc gồm: dưới giá sàn, khách trả dưới 50% giá gốc, ngày đôi đắt hơn ngày CAMP hoặc CAMP đắt hơn ngày thường.")

# ------------------------------------------------------------------ đường guardrail
st.subheader("Nới trần voucher ngày thường thì lợi nhuận tăng bao nhiêu?")
gc = read_csv("results/guardrail_curve.csv")
lab = {"+0": "Giữ nguyên", "+2": "+2 điểm %", "+4": "+4 điểm %", "+6": "+6 điểm %", "tu_do": "Không giới hạn"}
fig = go.Figure(go.Scatter(
    x=gc["tran_bau"].map(lab), y=gc["loi_nhuan_tang_pct"], mode="lines+markers+text",
    line=dict(color=GRAY, width=2), text=gc["loi_nhuan_tang_pct"].map(pct_points), textposition="top center",
    marker=dict(size=[16 if t == "+2" else 9 for t in gc["tran_bau"]],
                color=[ACCENT if t == "+2" else GRAY for t in gc["tran_bau"]])))
fig.update_yaxes(title="Lợi nhuận/năm so với hiện trạng", ticksuffix="%", rangemode="tozero")
fig.update_xaxes(title="Trần voucher ngày thường so với hiện tại")
st.plotly_chart(style_fig(fig, 260, legend=False))
st.caption("Điểm đậm là phương án đề xuất (+2 điểm %). Nới thêm thì lãi hơn trên mô hình, "
           "nhưng càng dựa vào giả định khách không quen dần với giá thấp.")

# ------------------------------------------------------------------ tồn kho
sim = read_csv("results/inventory_sim_test.csv")
short = sim[sim["fill"] < 0.999].groupby("sku_id")["date"].agg(["min", "max", "count"])
if len(short):
    lines = "; ".join(f"{short_name(s)} ({r['min'][8:]}–{r['max'][8:]}/10)" for s, r in short.iterrows())
    st.warning(f"**Cảnh báo tồn kho:** {lines}. Đã bỏ voucher để giãn hàng nhưng vẫn thiếu, kể cả ngày 10.10. "
               "Cần Supply chain đẩy lô hàng về 12/10.")

data_note()
