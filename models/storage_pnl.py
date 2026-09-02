#!/usr/bin/env python3
"""70평 상가 셀프스토리지 손익 모델 (청주 기준).

수집한 청주 실단가와 실제 상가 매물 임대료를 입력으로,
점유율·임대료·시설비 시나리오별 월 손익과 투자 회수기간을 계산한다.
"""
PYEONG_M2 = 3.305785

# ── 공간 설계 ───────────────────────────────────────────────
GROSS_PYEONG = 70
EFFICIENCY = 0.65          # 복도·전실·기계실 제외 후 유닛 순면적 비율

# 유닛 구성: (명칭, 개당 유효바닥㎡, 개수, 월 단가)
# 단가는 청주 경쟁사 정가와 할인가 사이의 신규 진입 가격대로 설정
UNIT_MIX = [
    ("로커 S (2단적층)", 0.5, 30,  50_000),
    ("워크인 M",         1.5, 30,  95_000),
    ("워크인 L",         2.2, 25, 130_000),
    ("워크인 XL",        3.0, 12, 165_000),
]

# ── 비용 시나리오 ──────────────────────────────────────────
# 임대료: 청주 실매물 기준 (가경동 2층 평당 1.41만 ~ 송절동 신축 3층 평당 3.86만)
RENT_SCENARIOS = {"저가(외곽·지하·구축 2층)": 1.5, "중간(일반 2층)": 2.2, "고가(신축 대로변)": 3.9}
CAPEX_PER_PYEONG = {"직접시공": 1_300_000, "프랜차이즈": 1_800_000}
FRANCHISE_FEE = 17_000_000   # 가맹비 1000 + 보증금 500 + 교육비 200

MGMT_FEE_PER_PYEONG = 5_000  # 건물 관리비
FIXED_OPEX = 600_000         # 전기·보안(캡스)·청소·방역
MARKETING = 400_000
INSURANCE_ETC = 150_000      # 보험·세무·잡비
CARD_FEE_RATE = 0.02

OCCUPANCY_RAMP = [(6, 0.60), (12, 0.80), (24, 0.85)]


def layout():
    net_m2 = GROSS_PYEONG * PYEONG_M2 * EFFICIENCY
    used = sum(a * n for _, a, n, _ in UNIT_MIX)
    full_revenue = sum(n * p for _, _, n, p in UNIT_MIX)
    units = sum(n for _, _, n, _ in UNIT_MIX)
    return net_m2, used, units, full_revenue


def monthly_pnl(full_revenue, occupancy, rent_per_pyeong_manwon):
    revenue = full_revenue * occupancy
    rent = GROSS_PYEONG * rent_per_pyeong_manwon * 10_000
    opex = (rent + GROSS_PYEONG * MGMT_FEE_PER_PYEONG + FIXED_OPEX
            + MARKETING + INSURANCE_ETC + revenue * CARD_FEE_RATE)
    return revenue, rent, opex, revenue - opex


def main():
    net_m2, used, units, full_revenue = layout()
    print("=" * 78)
    print(f"■ 공간 설계 — {GROSS_PYEONG}평 상가")
    print("=" * 78)
    print(f"  총면적            {GROSS_PYEONG}평 ({GROSS_PYEONG*PYEONG_M2:.1f}㎡)")
    print(f"  유닛 순면적       {net_m2:.1f}㎡ (효율 {EFFICIENCY:.0%}) / 배치 {used:.1f}㎡")
    print(f"  총 유닛 수        {units}개\n")
    print(f"  {'타입':<18}{'바닥㎡':>7}{'개수':>6}{'순면적㎡':>10}{'월단가':>10}{'만실매출':>12}")
    print("  " + "─" * 65)
    for name, area, n, price in UNIT_MIX:
        print(f"  {name:<18}{area:>7.1f}{n:>6}{area*n:>10.1f}{price:>10,}{price*n:>12,}")
    print("  " + "─" * 65)
    print(f"  {'만실 월매출':<18}{'':>7}{units:>6}{used:>10.1f}{'':>10}{full_revenue:>12,}")
    print(f"  평당 만실매출: {full_revenue/GROSS_PYEONG:,.0f}원/평\n")

    print("=" * 78)
    print("■ 월 손익 — 임대료 × 점유율")
    print("=" * 78)
    print(f"  {'임대료 시나리오':<22}{'월임대료':>10}{'점유율60%':>12}{'점유율80%':>12}{'점유율85%':>12}{'만실':>12}")
    print("  " + "─" * 74)
    for label, ppm in RENT_SCENARIOS.items():
        cells = []
        for occ in (0.60, 0.80, 0.85, 1.00):
            _, rent, _, profit = monthly_pnl(full_revenue, occ, ppm)
            cells.append(profit)
        print(f"  {label:<22}{GROSS_PYEONG*ppm*10_000:>10,.0f}"
              + "".join(f"{c:>12,.0f}" for c in cells))

    print("\n" + "=" * 78)
    print("■ 투자비 및 회수기간 (점유율 80% 안정화 기준)")
    print("=" * 78)
    for capex_label, per_p in CAPEX_PER_PYEONG.items():
        facility = GROSS_PYEONG * per_p
        fee = FRANCHISE_FEE if capex_label == "프랜차이즈" else 0
        total = facility + fee
        print(f"\n  [{capex_label}] 시설비 {facility:,}원"
              + (f" + 가맹비 등 {fee:,}원" if fee else "")
              + f" = 투자금 {total:,}원  (임대보증금 별도)")
        for label, ppm in RENT_SCENARIOS.items():
            _, _, _, profit = monthly_pnl(full_revenue, 0.80, ppm)
            if profit <= 0:
                print(f"    {label:<22} 월 {profit:>10,.0f}원  →  회수 불가")
            else:
                print(f"    {label:<22} 월 {profit:>10,.0f}원  →  {total/profit:>5.1f}개월"
                      f"  (연 수익률 {profit*12/total:>5.1%})")

    print("\n" + "=" * 78)
    print("■ 손익분기 점유율 (BEP)")
    print("=" * 78)
    for label, ppm in RENT_SCENARIOS.items():
        lo, hi = 0.0, 1.0
        for _ in range(60):
            mid = (lo + hi) / 2
            if monthly_pnl(full_revenue, mid, ppm)[3] < 0:
                lo = mid
            else:
                hi = mid
        print(f"  {label:<22} BEP 점유율 {hi:>6.1%}  "
              f"(유닛 {units*hi:>4.0f}개 / {units}개 계약 시 본전)")

    print("\n" + "=" * 78)
    print("■ 개업 1~2년차 누적 현금흐름 (중간 임대료·직접시공 기준)")
    print("=" * 78)
    ppm = RENT_SCENARIOS["중간(일반 2층)"]
    invest = GROSS_PYEONG * CAPEX_PER_PYEONG["직접시공"]
    cum = -invest
    print(f"  초기 투자 {-invest:,}원")
    for month in range(1, 25):
        occ = next((o for m, o in OCCUPANCY_RAMP if month <= m), OCCUPANCY_RAMP[-1][1])
        # 램프 구간은 선형 보간
        if month <= 6:
            occ = 0.15 + (0.60 - 0.15) * (month / 6)
        elif month <= 12:
            occ = 0.60 + (0.80 - 0.60) * ((month - 6) / 6)
        else:
            occ = min(0.85, 0.80 + 0.05 * ((month - 12) / 12))
        _, _, _, profit = monthly_pnl(full_revenue, occ, ppm)
        cum += profit
        if month in (3, 6, 9, 12, 18, 24):
            print(f"  {month:>2}개월차  점유율 {occ:>5.1%}  월손익 {profit:>10,.0f}원  "
                  f"누적 {cum:>13,.0f}원")


if __name__ == "__main__":
    main()
