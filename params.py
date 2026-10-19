"""Tham số dùng chung cho toàn bộ dataset (đã chốt với nhóm)."""
import datetime as dt

SEED = 20261019
START = dt.date(2025, 10, 1)
END = dt.date(2026, 10, 15)
TRAIN_END = dt.date(2026, 9, 30)
CRM_SNAPSHOT = dt.date(2026, 9, 30)

# Seller voucher mặc định (chỉ để điền dòng lỗi)
DEFAULT_SV = {"DD": 0.15, "CAMP": 0.12, "BAU": 0.09}

# Phí brand chịu (tính trên giá sau mọi seller voucher, theo đơn vị sản phẩm)
FEE_COMMISSION = 0.17
FEE_PAYMENT = 0.06
FEE_VOUCHER_XTRA = 0.05
FEE_VOUCHER_XTRA_CAP = 50_000
FEE_CAMPAIGN_PLUS = 0.05
FEE_CAMPAIGN_PLUS_CAP = 50_000
FEE_ORDER = 3_000            # mỗi đơn
COGS_PCT = 0.35              # x Giá Live BAU
MIN_MARGIN_PCT = 0.10        # x Giá Live BAU
LEGAL_CAP = 0.50             # giảm tối đa so với Giá Live BAU

# VXP (TikTok chịu), tính trên giá sau seller voucher / 1 sản phẩm
VXP_TIERS = [  # (từ, đến, tỷ lệ, trần)
    (0, 200_000, 0.00, 0),
    (200_000, 300_000, 0.13, 117_000),
    (300_000, 500_000, 0.14, 240_000),
    (500_000, None, 0.15, 300_000),
]


def vxp_unit(price):
    """VXP cho 1 sản phẩm theo giá sau seller voucher."""
    for lo, hi, r, cap in VXP_TIERS:
        if price >= lo and (hi is None or price < hi):
            return int(round(min(price * r, cap)))
    return 0


def unit_fees(p):
    """Phí brand chịu cho 1 sản phẩm có giá sau seller voucher = p (chưa gồm phí/đơn)."""
    com = round(p * FEE_COMMISSION)
    pay = round(p * FEE_PAYMENT)
    vx = round(min(p * FEE_VOUCHER_XTRA, FEE_VOUCHER_XTRA_CAP))
    cp = round(min(p * FEE_CAMPAIGN_PLUS, FEE_CAMPAIGN_PLUS_CAP))
    return com, pay, vx, cp


def min_price_for(base_price):
    """Giá sau seller voucher thấp nhất mà lợi nhuận đóng góp/đơn (1 sp) >= MIN_MARGIN x base."""
    cogs = round(COGS_PCT * base_price)
    need = MIN_MARGIN_PCT * base_price
    lo, hi = 0, base_price * 2
    for _ in range(60):
        mid = (lo + hi) / 2
        c = mid - sum(unit_fees(mid)) - FEE_ORDER - cogs
        if c >= need:
            hi = mid
        else:
            lo = mid
    return int(-(-hi // 1000) * 1000)  # làm tròn lên nghìn
