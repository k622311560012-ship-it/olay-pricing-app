"""Model 1 – Giá (OLAY × TikTok Shop): các hàm lõi dùng chung cho notebook và trang web.

Chỉ cần pandas/numpy. Phí, VXP, giá vốn và giá sàn lấy từ params.py của nhóm (không viết lại).
Bản trong olay-app/: params.py nằm cùng thư mục; dự án gốc: params.py nằm trong code/.

Công thức (giải thích chi tiết trong pricing.ipynb):
    a        = live_price × (1 − seller_voucher_pct)          giá sau seller voucher, VND/sp
    final    = a − VXP(a)                                     giá khách trả, VND/sp (VXP do TikTok chịu)
    đơn/ngày = base_orders_bau × hệ số campaign
               × (final / ref_final_price)^ε
               × (mức giá đối thủ / comp_level_ref)^γ
    lợi nhuận/đơn = q̄ × (a − phí(a) − giá vốn) − 3.000đ
"""
import os
import sys

import numpy as np
import pandas as pd

_HERE = os.path.dirname(os.path.abspath(__file__))
for _p in (_HERE, os.path.join(_HERE, "code")):     # cùng thư mục (app) hoặc code/ (dự án gốc)
    if os.path.exists(os.path.join(_p, "params.py")) and _p not in sys.path:
        sys.path.insert(0, _p)
import params as P  # noqa: E402

MODEL_PARAMS_PATH = os.path.join(_HERE, "results", "model_params.csv")
DEAL_PLAN_PATH = next((p for p in (os.path.join(_HERE, "app_data", "deal_plan.csv"),
                                   os.path.join(_HERE, "data", "deal_plan.csv")) if os.path.exists(p)),
                      os.path.join(_HERE, "app_data", "deal_plan.csv"))

# Ngày DD trong 1 năm (campaign_calendar, năm train 01/10/2025–30/09/2026):
# 8 ngày DD thường, 3 ngày Mega (9.9, 10.10, 12.12), 1 ngày 11.11.
# Loại phiên "DD" của bộ tối ưu = trung bình có trọng số của 3 loại này.
DD_DAY_WEIGHTS = {"dd": 8, "mega": 3, "peak": 1}
CAMPAIGN_TYPES = ["BAU", "CAMP", "DD", "DD_THUONG", "MEGA", "PEAK"]


# ---------------------------------------------------------------- giá, phí, lợi nhuận / sản phẩm
def final_price(a, vxp_on=True):
    """Giá khách trả cho 1 sp khi giá sau seller voucher = a (VND)."""
    a = int(round(a))
    return a - P.vxp_unit(a) if vxp_on else a


def unit_cogs(base_price):
    """Giá vốn 1 sp = 35% × base_price."""
    return round(P.COGS_PCT * base_price)


def unit_margin(a, base_price):
    """Lợi nhuận đóng góp 1 sp trước phí/đơn: a − phí(a) − giá vốn (VND/sp)."""
    a = int(round(a))
    return a - sum(P.unit_fees(a)) - unit_cogs(base_price)


def profit_per_order(a, base_price, qty_per_order):
    """Lợi nhuận đóng góp 1 đơn: q̄ × lợi nhuận/sp − 3.000đ phí/đơn (VND/đơn)."""
    return qty_per_order * unit_margin(a, base_price) - P.FEE_ORDER


# ---------------------------------------------------------------- cầu
def demand_orders(base_orders, final, ref_final, elasticity, campaign_mult=1.0,
                  comp_level=1.0, comp_level_ref=1.0, gamma=0.0):
    """Số đơn/ngày theo mô hình log-log (cầu dạng nhân)."""
    return (base_orders * campaign_mult * (final / ref_final) ** elasticity
            * (comp_level / comp_level_ref) ** gamma)


def daily_result(orders, a, live_price, base_price, qty_per_order):
    """Lượng bán, doanh thu, lợi nhuận, chi phí seller voucher trong 1 ngày."""
    units = orders * qty_per_order
    return dict(so_don_ngay=orders, luong_ban_ngay=units,
                doanh_thu_ngay=units * a,
                loi_nhuan_ngay=orders * profit_per_order(a, base_price, qty_per_order),
                chi_phi_voucher_ngay=units * (live_price - a))


def check_constraints(a, final, min_price, base_price, seller_voucher_pct, sv_max=0.30):
    """Danh sách ràng buộc bị vi phạm (rỗng nếu hợp lệ)."""
    v = []
    if a < min_price:
        v.append("min_price")
    if final < P.LEGAL_CAP * base_price:
        v.append("legal_cap")
    if not 0 <= seller_voucher_pct <= sv_max + 1e-9:
        v.append("sv_ngoai_0_30pct")
    return v


# ---------------------------------------------------------------- what-if
_cache = {}


def load_model_params(path=MODEL_PARAMS_PATH):
    if path not in _cache:
        _cache[path] = pd.read_csv(path, dtype={"sku_id": str}).set_index("sku_id")
    return _cache[path]


def load_deal_plan(path=DEAL_PLAN_PATH):
    if path not in _cache:
        _cache[path] = (pd.read_csv(path, dtype={"sku_id": str}, keep_default_na=False, na_values=[""])
                          .set_index(["sku_id", "campaign_type"]))
    return _cache[path]


def campaign_multiplier(row, campaign_type):
    m = {"BAU": 1.0, "CAMP": row["campaign_mult_camp"], "DD_THUONG": row["campaign_mult_dd"],
         "MEGA": row["campaign_mult_mega"], "PEAK": row["campaign_mult_peak"]}
    if campaign_type == "DD":
        w = DD_DAY_WEIGHTS
        return (w["dd"] * row["campaign_mult_dd"] + w["mega"] * row["campaign_mult_mega"]
                + w["peak"] * row["campaign_mult_peak"]) / sum(w.values())
    return m[campaign_type]


def what_if(sku_id, campaign_type, seller_voucher_pct, elasticity_scale=1.0, comp_drop_pct=0,
            vxp_on=True, model_params=None, deal_plan=None):
    """Lượng bán, doanh thu, lợi nhuận/ngày của 1 SKU ở 1 mức seller voucher.

    sku_id             : chuỗi 19 chữ số
    campaign_type      : "BAU", "CAMP", "DD" (trung bình các ngày DD/Mega/11.11 trong năm, như bộ tối ưu),
                         hoặc "DD_THUONG", "MEGA", "PEAK" (11.11)
    seller_voucher_pct : 0–0,30, tính trên live_price của loại phiên trong deal_plan
                         (MEGA/PEAK/DD_THUONG dùng live_price của DD)
    elasticity_scale   : nhân ε_EB (vd 1,3 = khách nhạy giá hơn 30%)
    comp_drop_pct      : đối thủ giảm giá thêm bao nhiêu % so với mức bình thường của loại ngày (vd 0,05 = 5%)
    vxp_on             : False = giả sử TikTok không trợ giá VXP (khách trả đúng a)
    """
    mp = load_model_params() if model_params is None else model_params
    dp = load_deal_plan() if deal_plan is None else deal_plan
    if campaign_type not in CAMPAIGN_TYPES:
        raise ValueError(f"campaign_type phải thuộc {CAMPAIGN_TYPES}")
    row = mp.loc[sku_id]
    plan_type = "DD" if campaign_type in ("DD", "DD_THUONG", "MEGA", "PEAK") else campaign_type
    live = dp.at[(sku_id, plan_type), "live_price"]
    comp_ref_type = row["comp_level_dd"] if plan_type == "DD" else row[f"comp_level_{plan_type.lower()}"]

    a = int(round(live * (1 - seller_voucher_pct)))
    f = final_price(a, vxp_on)
    eps = row["elasticity_eb"] * elasticity_scale
    orders = demand_orders(row["base_orders_bau"], f, row["ref_final_price"], eps,
                           campaign_mult=campaign_multiplier(row, campaign_type),
                           comp_level=comp_ref_type * (1 - comp_drop_pct), comp_level_ref=row["comp_level_ref"],
                           gamma=row["gamma_comp"])
    out = dict(sku_id=sku_id, campaign_type=campaign_type, seller_voucher_pct=seller_voucher_pct,
               live_price=int(live), gia_sau_sv=a, vxp=a - f, gia_khach_tra=f, elasticity_dung=eps)
    out.update(daily_result(orders, a, live, row["base_price"], row["qty_per_order"]))
    out["vi_pham"] = check_constraints(a, f, row["min_price"], row["base_price"], seller_voucher_pct)
    # kiểu Python thuần để trả JSON cho web
    return {k: (float(v) if isinstance(v, (np.floating, float)) else int(v) if isinstance(v, np.integer) else v)
            for k, v in out.items()}


if __name__ == "__main__":
    print(what_if("1734365615002977539", "BAU", 0.11))
