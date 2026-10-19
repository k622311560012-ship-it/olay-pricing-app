"""Hàm dùng chung cho các trang: đọc file (có cache), định dạng tiền/%, tên SKU ngắn, màu biểu đồ."""
import os

import pandas as pd
import streamlit as st

APP_DIR = os.path.dirname(os.path.abspath(__file__))
ID_COLS = {c: str for c in ["sku_id", "combo_sku_id", "component_sku_id", "matched_sku_id", "decision_id"]}

# ------------------------------------------------------------------ màu dùng chung mọi trang
ACCENT = "#1F3B73"      # phương án đề xuất / màu nhấn
OLAY = "#A3195B"        # OLAY (cố định)
COMP = "#B8BFC9"        # đối thủ
GRAY = "#9AA4B1"        # các phương án khác
LIGHT = "#E6EAF0"       # nền / cột phụ
WARN = "#B23B3B"        # cảnh báo

PA_LABELS = {
    "hien_trang": "Hiện trạng",
    "match_doi_thu": "Luôn match đối thủ",
    "giam_sau": "Giảm sâu 30%",
    "toi_uu_tu_do": "Tối ưu tự do",
    "toi_uu_guardrail": "Đề xuất (tối ưu + guardrail)",
    "oracle": "Trần lý thuyết",
}
CT_LABELS = {"BAU": "Ngày thường", "CAMP": "Ngày CAMP (15, 25)", "DD": "Ngày đôi (DD)"}
RC_LABELS = {"none": "—", "guardrail": "Guardrail", "inventory": "Tồn kho", "min_price": "Giá sàn",
             "legal_cap": "Trần 50%", "sv_max_30%": "Trần voucher 30%"}
RET24_CREAM = "1734365615002977539"


def path(*parts):
    return os.path.join(APP_DIR, *parts)


@st.cache_data
def read_csv(rel_path):
    """Đọc CSV theo đường dẫn tương đối với app.py. Trả về None nếu chưa có file."""
    p = path(*rel_path.split("/"))
    if not os.path.exists(p):
        return None
    return pd.read_csv(p, dtype=ID_COLS, keep_default_na=False, na_values=[""])


# ------------------------------------------------------------------ định dạng
def num(x, digits=1):
    """Số kiểu Việt Nam: 1.234,5."""
    if x is None or pd.isna(x):
        return "–"
    s = f"{x:,.{digits}f}"
    return s.replace(",", "X").replace(".", ",").replace("X", ".")


def vnd(x, unit="đ"):
    """Giá sản phẩm: 372020 -> '372.020đ'."""
    if x is None or pd.isna(x):
        return "–"
    return f"{'-' if x < 0 else ''}{num(abs(x), 0)}{unit}"   # '-' ASCII để st.metric hiện mũi tên đúng chiều


def money(x, sign=False):
    """Tiền lớn rút gọn: 25,95 tỷ đ; 291 triệu đ; 85,3 nghìn đ."""
    if x is None or pd.isna(x):
        return "–"
    s = "-" if x < 0 else ("+" if sign and x > 0 else "")
    a = abs(x)
    if a >= 1e9:
        body = f"{num(a / 1e9, 2)} tỷ đ"
    elif a >= 1e6:
        body = f"{num(a / 1e6, 0 if a >= 1e8 else (1 if a >= 1e7 else 2))} triệu đ"
    elif a >= 1e4:
        body = f"{num(a / 1e3, 0)} nghìn đ"
    else:
        body = f"{num(a, 0)}đ"
    return s + body


def pct(x, digits=1, sign=False):
    """Tỷ lệ 0–1 -> '12,5%'."""
    if x is None or pd.isna(x):
        return "–"
    return (("+" if x > 0 else "") if sign else "") + num(100 * x, digits) + "%"


def pct_points(x, digits=2, sign=True):
    """Giá trị đã là % (1.13) -> '+1,13%'."""
    if x is None or pd.isna(x):
        return "–"
    return (("+" if x > 0 else "") if sign else "") + num(x, digits) + "%"


# ------------------------------------------------------------------ tên SKU
_FORM = {"cream": "Kem", "cream_day": "Kem ngày", "cream_night": "Kem đêm", "serum": "Serum"}


@st.cache_data
def _names():
    p = read_csv("app_data/product.csv").set_index("sku_id")
    bom = read_csv("app_data/bom.csv")

    def single(s, with_size=True):
        r = p.loc[s]
        line, form = r["product_line"], _FORM.get(r["form"], r["form"])
        if form == "Serum" and "Serum" in line:
            form = ""
        size = f" {r['size_g']}g" if r["size_g"] else f" {r['size_ml']}ml"
        return " ".join(x for x in [line, form] if x) + (size if with_size else "")

    short = {s: single(s) for s in p.index[p["product_type"] == "single"]}
    for c, g in bom.groupby("combo_sku_id"):
        comps = g["component_sku_id"].tolist()
        lines = {p.at[x, "product_line"] for x in comps}
        if len(lines) == 1:
            line = lines.pop()
            parts = [_FORM.get(p.at[x, "form"], "") for x in comps]
            short[c] = f"Combo {line} " + " + ".join(parts)
        else:
            short[c] = "Combo " + " + ".join(single(x, with_size=False) for x in comps)
    dup = pd.Series(short).duplicated(keep=False)
    for s in dup[dup].index:
        short[s] += f" ·{s[-4:]}"
    full = p["product_name"].str.replace(r"^\[Miền Bắc\]\s*", "", regex=True).str.strip().to_dict()
    return short, full


def short_name(sku):
    return _names()[0].get(sku, sku)


def full_name(sku):
    return _names()[1].get(sku, sku)


# ------------------------------------------------------------------ bố cục / biểu đồ
def page_header(title, conclusion):
    st.header(title)
    st.markdown(f"**{conclusion}**")


def style_fig(fig, height=360, legend=True):
    fig.update_layout(template="plotly_white", height=height, margin=dict(l=10, r=10, t=40, b=10),
                      font=dict(family="sans-serif", size=13, color="#1C2430"), title_font=dict(size=15),
                      showlegend=legend, legend=dict(orientation="h", y=-0.18, x=0))
    return fig


@st.cache_data
def campaign_days(d0, d1):
    cal = read_csv("app_data/campaign_calendar.csv")
    c = cal[(cal["campaign_type"] != "BAU") & cal["date"].between(d0, d1)]
    return c[["date", "campaign_type"]].values.tolist()


def data_note():
    st.caption("Dữ liệu mô phỏng cho môn Advanced Business Analytics (FTU). Không có dữ liệu khách hàng thật.")
