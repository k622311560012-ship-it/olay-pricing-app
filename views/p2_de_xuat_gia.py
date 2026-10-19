from datetime import datetime

import pandas as pd
import streamlit as st

import pricing_core as pc
from common import CT_LABELS, RC_LABELS, data_note, full_name, money, page_header, pct, read_csv, short_name, vnd

STATUS = ["Chờ duyệt", "Duyệt", "Sửa", "Từ chối"]
STATUS_CODE = {"Duyệt": "approved", "Sửa": "edited", "Từ chối": "rejected"}


@st.cache_data
def current_profit(sku, ct, sv):
    return pc.what_if(sku, ct, sv)["loi_nhuan_ngay"]


rec_g = read_csv("results/price_recommendation.csv")
med = rec_g.groupby("campaign_type")["seller_voucher_de_xuat"].median()
n_big_g = int(((rec_g["seller_voucher_de_xuat"] - rec_g["seller_voucher_hien_tai"]).abs() > 0.05).sum())
page_header("Đề xuất giá",
            f"Giữ voucher ngày thường quanh {pct(med['BAU'], 0)} và tăng ngày campaign lên khoảng "
            + (pct(med['CAMP'], 0) if pct(med['CAMP'], 0) == pct(med['DD'], 0) else f"{pct(med['DD'], 0)}–{pct(med['CAMP'], 0)}")
            + f"; {n_big_g}/{len(rec_g)} dòng đổi hơn 5 điểm %.")

c0, c1, c2 = st.columns([1.4, 1, 2])
version = c0.radio("Phiên bản", ["Đề xuất (có guardrail)", "Tối ưu tự do (tham khảo)"], horizontal=True)
is_guard = version.startswith("Đề xuất")
rec = rec_g if is_guard else read_csv("results/price_recommendation_free.csv")
types = c1.multiselect("Loại phiên", ["BAU", "CAMP", "DD"], default=["BAU", "CAMP", "DD"], format_func=CT_LABELS.get)
skus = c2.multiselect("SKU", sorted(rec["sku_id"].unique(), key=short_name), format_func=short_name, placeholder="Tất cả SKU")
st.caption("Guardrail: ngày đôi ≤ CAMP ≤ ngày thường về giá khách trả; voucher ngày thường tăng tối đa 2 điểm %; "
           "voucher không giảm quá 3 điểm % (trừ khi thiếu hàng)." if is_guard else
           "Bản tự do: gần như cùng một mức voucher cho mọi loại phiên, tức 'giảm giá mọi ngày'. Chỉ để tham khảo.")

f = rec[rec["campaign_type"].isin(types)]
if skus:
    f = f[f["sku_id"].isin(skus)]
f = f.reset_index(drop=True)

# ------------------------------------------------------------------ bảng + duyệt
ver_code = "toi_uu_guardrail" if is_guard else "toi_uu_tu_do"
dec = st.session_state.setdefault("decisions", {})
nonce = st.session_state.setdefault("editor_nonce", 0)
ekey = f"ed_{ver_code}_{'-'.join(types)}_{len(skus)}_{hash(tuple(skus))}_{nonce}"

if f"base_{ekey}" not in st.session_state:
    rows = []
    for _, r in f.iterrows():
        cur_p = current_profit(r["sku_id"], r["campaign_type"], r["seller_voucher_hien_tai"])
        cur_f = pc.final_price(r["gia_hien_tai"])
        d = dec.get((ver_code, r["sku_id"], r["campaign_type"]), {})
        rows.append({
            "SKU": short_name(r["sku_id"]), "Phiên": r["campaign_type"],
            "Khách trả: hiện tại → đề xuất": f"{vnd(cur_f)} → {vnd(r['gia_khach_tra_de_xuat'])}",
            "Lợi nhuận/ngày: hiện tại → đề xuất": f"{money(cur_p)} → {money(r['loi_nhuan_du_kien'])}",
            "Voucher": f"{pct(r['seller_voucher_hien_tai'])} → {pct(r['seller_voucher_de_xuat'])}",
            "Ràng buộc": RC_LABELS.get(r["rang_buoc_cham"], r["rang_buoc_cham"]),
            "Trạng thái": d.get("trang_thai", "Chờ duyệt"),
            "Voucher sửa (%)": d.get("voucher_sua"),
            "Ghi chú": d.get("ghi_chu", ""),
            "Tên đầy đủ": full_name(r["sku_id"]),
        })
    st.session_state[f"base_{ekey}"] = pd.DataFrame(rows)
base = st.session_state[f"base_{ekey}"]

big = (f["seller_voucher_de_xuat"] - f["seller_voucher_hien_tai"]).abs() > 0.05
styled = base.style.apply(lambda row: ["background-color: #FFF4D6" if big.iat[row.name] else "" for _ in row], axis=1)
edited = st.data_editor(
    styled, key=ekey, hide_index=True, height=min(36 * (len(base) + 1) + 4, 560),
    disabled=[c for c in base.columns if c not in ("Trạng thái", "Voucher sửa (%)", "Ghi chú")],
    column_config={
        "SKU": st.column_config.TextColumn(width="medium", help="Tên đầy đủ ở cột cuối"),
        "Phiên": st.column_config.TextColumn(width="small"),
        "Voucher": st.column_config.TextColumn("Voucher (phụ)", width="small"),
        "Trạng thái": st.column_config.SelectboxColumn(options=STATUS, required=True, width="small"),
        "Voucher sửa (%)": st.column_config.NumberColumn(min_value=0.0, max_value=30.0, step=0.5, format="%.1f",
                                                         help="Chỉ dùng khi Trạng thái = Sửa"),
        "Tên đầy đủ": st.column_config.TextColumn(width="large"),
    })
st.caption(f"{len(f)} dòng. Nền vàng nhạt: voucher đổi hơn 5 điểm %. Giá khách trả đã trừ trợ giá của TikTok. "
           "Lợi nhuận/ngày theo mô hình, tính cho một ngày của loại phiên đó.")

# Ghi chú Serum Retinol24 ngày DD
dp = read_csv("app_data/deal_plan.csv").set_index(["sku_id", "campaign_type"])
RS = "1734365470027580675"
if (RS, "DD") in dp.index and RS in set(rec["sku_id"]):
    rr = rec.set_index(["sku_id", "campaign_type"])
    live_dd, live_bau = dp.at[(RS, "DD"), "live_price"], dp.at[(RS, "BAU"), "live_price"]
    st.caption(f"Vì sao {short_name(RS)} ngày đôi đề xuất {pct(rr.at[(RS, 'DD'), 'seller_voucher_de_xuat'], 0)}: "
               f"giá niêm yết ngày đôi là {vnd(live_dd)}, cao hơn ngày thường {vnd(live_bau)} "
               f"({pct(live_dd / live_bau - 1, 0, sign=True)}), nên voucher lớn hơn nhưng khách trả "
               f"{vnd(rr.at[(RS, 'DD'), 'gia_khach_tra_de_xuat'])}, ngang ngày CAMP ({vnd(rr.at[(RS, 'CAMP'), 'gia_khach_tra_de_xuat'])}).")

# Cập nhật quyết định từ bảng
errors = []
for i, r in edited.iterrows():
    src = f.iloc[i]
    k = (ver_code, src["sku_id"], src["campaign_type"])
    stt = r["Trạng thái"]
    if stt == "Chờ duyệt":
        dec.pop(k, None)
        continue
    sv_new = {"Duyệt": src["seller_voucher_de_xuat"], "Từ chối": src["seller_voucher_hien_tai"]}.get(stt)
    if stt == "Sửa":
        if pd.isna(r["Voucher sửa (%)"]):
            errors.append(f"{short_name(src['sku_id'])} ({src['campaign_type']}): nhập voucher sửa.")
            dec.pop(k, None)
            continue
        sv_new = r["Voucher sửa (%)"] / 100
        v = pc.what_if(src["sku_id"], src["campaign_type"], sv_new)["vi_pham"]
        if v:
            msg = {"min_price": "dưới giá sàn", "legal_cap": "khách trả dưới 50% giá gốc", "sv_ngoai_0_30pct": "ngoài 0–30%"}
            errors.append(f"{short_name(src['sku_id'])} ({src['campaign_type']}): voucher {pct(sv_new)} "
                          + ", ".join(msg.get(x, x) for x in v) + ".")
            dec.pop(k, None)
            continue
    old = dec.get(k, {})
    dec[k] = dict(created_ts=old.get("created_ts") if old.get("trang_thai") == stt and old.get("seller_voucher_chot") == sv_new
                  else datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                  sku_id=src["sku_id"], campaign_type=src["campaign_type"], phien_ban=ver_code, trang_thai=stt,
                  status=STATUS_CODE[stt], seller_voucher_hien_tai=src["seller_voucher_hien_tai"],
                  seller_voucher_de_xuat=src["seller_voucher_de_xuat"], seller_voucher_chot=sv_new,
                  voucher_sua=r["Voucher sửa (%)"] if stt == "Sửa" else None, ghi_chu=r["Ghi chú"] or "",
                  rang_buoc_cham=src["rang_buoc_cham"], ly_do_mo_hinh=src["ly_do"])
for e in errors:
    st.error("Chưa lưu – " + e)

b1, b2, b3 = st.columns([1.3, 1, 3])
if b1.button(f"Duyệt tất cả {len(f)} dòng đang lọc", type="primary"):
    for _, r in f.iterrows():
        dec[(ver_code, r["sku_id"], r["campaign_type"])] = dict(
            created_ts=datetime.now().strftime("%Y-%m-%d %H:%M:%S"), sku_id=r["sku_id"], campaign_type=r["campaign_type"],
            phien_ban=ver_code, trang_thai="Duyệt", status="approved", seller_voucher_hien_tai=r["seller_voucher_hien_tai"],
            seller_voucher_de_xuat=r["seller_voucher_de_xuat"], seller_voucher_chot=r["seller_voucher_de_xuat"],
            voucher_sua=None, ghi_chu="", rang_buoc_cham=r["rang_buoc_cham"], ly_do_mo_hinh=r["ly_do"])
    st.session_state["editor_nonce"] += 1
    st.rerun()
if b2.button("Xóa mọi quyết định"):
    dec.clear()
    st.session_state["editor_nonce"] += 1
    st.rerun()

with st.expander("Lý do của mô hình cho từng dòng"):
    st.dataframe(pd.DataFrame({"SKU": f["sku_id"].map(short_name), "Phiên": f["campaign_type"], "Lý do": f["ly_do"]}),
                 hide_index=True)

# ------------------------------------------------------------------ nhật ký
mine = [v for (ver, _, _), v in dec.items() if ver == ver_code]
if dec:
    log = pd.DataFrame(dec.values()).sort_values("created_ts").reset_index(drop=True)
    log.insert(0, "decision_id", [f"APP{i + 1:05d}" for i in range(len(log))])
    log.insert(2, "decision_type", "price_recommendation")
    log["proposed_by"] = "Model 1"
    log["approved_by"] = "Người duyệt (app)"
    log["old_value"] = log["seller_voucher_hien_tai"].map(lambda v: f"seller_voucher_pct={v:.4f}")
    log["new_value"] = log["seller_voucher_chot"].map(lambda v: f"seller_voucher_pct={v:.4f}")
    log = log.drop(columns=["trang_thai", "voucher_sua"])
    n = pd.Series([v["trang_thai"] for v in mine]).value_counts()
    b3.write(f"Đã duyệt {n.get('Duyệt', 0)} · sửa {n.get('Sửa', 0)} · từ chối {n.get('Từ chối', 0)} · "
             f"chờ {len(rec) - len(mine)}/{len(rec)}")
    b3.download_button("Tải nhật ký quyết định (CSV)", log.to_csv(index=False).encode("utf-8-sig"),
                       file_name="decision_log.csv", mime="text/csv")

data_note()
