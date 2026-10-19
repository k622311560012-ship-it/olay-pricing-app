import plotly.express as px
import streamlit as st

from common import ACCENT, data_note, page_header, read_csv, style_fig

seg = read_csv("results/segment_voucher.csv")
ev = read_csv("results/voucher_eval.csv")

if seg is None and ev is None:
    page_header("Voucher theo nhóm khách", "Đang chờ kết quả Model 2.")
    st.info("Trang này sẽ tự hiển thị đề xuất voucher theo nhóm khách và kết quả đánh giá khi Model 2 hoàn thành.")
    data_note()
    st.stop()

page_header("Voucher theo nhóm khách", "Đề xuất voucher nhắm mục tiêu theo nhóm khách hàng (Model 2).")

if seg is not None:
    st.subheader("Đề xuất voucher theo nhóm khách")
    st.dataframe(seg, hide_index=True)
    num_cols = seg.select_dtypes("number").columns.tolist()
    cat_cols = [c for c in seg.columns if c not in num_cols]
    if num_cols and cat_cols:
        c1, c2 = st.columns(2)
        x = c1.selectbox("Nhóm theo", cat_cols)
        y = c2.selectbox("Chỉ số", num_cols)
        st.plotly_chart(style_fig(px.bar(seg, x=x, y=y, color_discrete_sequence=[ACCENT]), legend=False))
else:
    st.info("Đang chờ kết quả Model 2: đề xuất voucher theo nhóm khách.")

if ev is not None:
    st.subheader("Đánh giá voucher")
    st.dataframe(ev, hide_index=True)
else:
    st.info("Đang chờ kết quả Model 2: đánh giá voucher.")

data_note()
