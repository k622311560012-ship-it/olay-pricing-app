"""OLAY × TikTok Shop – prototype tối ưu giá & voucher (Streamlit).

Chạy:  streamlit run app.py
App chỉ đọc CSV trong results/ và app_data/, không huấn luyện mô hình.
"""
import streamlit as st

st.set_page_config(page_title="OLAY × TikTok Shop – Giá & Voucher", layout="wide")

pages = [
    st.Page("views/p1_tong_quan.py", title="Tổng quan", icon=":material/dashboard:", default=True),
    st.Page("views/p2_de_xuat_gia.py", title="Đề xuất giá", icon=":material/sell:"),
    st.Page("views/p3_voucher_nhom_khach.py", title="Voucher theo nhóm khách", icon=":material/groups:"),
    st.Page("views/p4_gia_doi_thu.py", title="Giá đối thủ", icon=":material/compare_arrows:"),
    st.Page("views/p5_rang_buoc.py", title="Ràng buộc Finance & Supply chain", icon=":material/rule:"),
    st.Page("views/p6_what_if.py", title="What-if", icon=":material/tune:"),
]
nav = st.navigation(pages)

with st.sidebar:
    st.markdown("**OLAY × TikTok Shop**  \nTối ưu giá & voucher")
    st.caption("Dữ liệu mô phỏng, không có dữ liệu khách hàng thật.")

nav.run()
