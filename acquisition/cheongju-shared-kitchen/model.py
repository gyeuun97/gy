"""청주 사창동 배달 공유주방 인수 검토용 손익 추정.

매도자 제시 숫자를 출발점으로, 부가세·퇴직금·종합소득세를 차례로 빼서
'사장 통장에 실제로 남는 돈'을 시나리오별로 본다. 모든 금액 단위는 만원.

    python3 acquisition/cheongju-shared-kitchen/model.py
"""

# 매도자 제시 월별 매출 (원)
MONTHLY_SALES = {
    "2025-07": 145_203_700, "2025-08": 159_842_400, "2025-09": 153_892_300,
    "2025-10": 160_062_300, "2025-11": 236_019_801, "2025-12": 265_118_550,
    "2026-01": 261_190_400, "2026-02": 242_506_500, "2026-03": 277_713_300,
    "2026-04": 228_300_200, "2026-05": 300_915_200, "2026-06": 231_910_367,
    "2026-07": 268_408_000, "2026-08": 263_582_400,
}

# 매도자 제시 월 손익 (만원) — 평균 매출정보 차트
SELLER = {
    "sales": 26_000, "materials": 8_500, "labor": 2_800, "rent": 120,
    "utilities": 300, "other": 12_000, "profit": 2_280,
}

PRICE = {"goodwill": 4_000, "facility": 2_000}  # 영업권리금 + 시설권리금

PLATFORM_DEDUCTION = 0.40  # 매도자: 총매출 대비 정산률 약 60%
STAFF = 8


def vat_estimate(sales, materials, platform_rate=PLATFORM_DEDUCTION,
                 taxable_material_share=0.5, other_taxable=1_500):
    """월 납부 부가세 추정 (만원). 매출은 부가세 포함 금액으로 가정.

    - 매출세액: 매출 / 11
    - 매입세액: 배달앱 수수료·배달비·광고(차감액의 90%), 과세 식자재,
      공과금·월세·포장재 등 기타 과세 매입
    - 의제매입세액: 면세 농축수산물 × 8/108 (개인 음식점, 과세표준 2억 초과)
    - 매출 10억 초과라 신용카드매출세액공제는 없음
    """
    output = sales / 11
    taxable_inputs = (sales * platform_rate * 0.9
                      + materials * taxable_material_share
                      + SELLER["utilities"] + SELLER["rent"] + other_taxable)
    deemed = materials * (1 - taxable_material_share) * 8 / 108
    return output - taxable_inputs / 11 - deemed


def income_tax_annual(taxable):
    """종합소득세 + 지방소득세 (만원, 2024년 이후 세율표, 공제 무시)."""
    brackets = [  # (상한, 세율, 누진공제)
        (1_400, 0.06, 0), (5_000, 0.15, 126), (8_800, 0.24, 576),
        (15_000, 0.35, 1_544), (30_000, 0.38, 1_994), (50_000, 0.40, 2_594),
        (100_000, 0.42, 3_594), (float("inf"), 0.45, 6_594),
    ]
    for cap, rate, deduction in brackets:
        if taxable <= cap:
            return (taxable * rate - deduction) * 1.1
    raise AssertionError


def scenario(name, sales, vat_included=False):
    """매도자 이익률 구조를 유지한 채 매출만 바꿔본 월 손익."""
    scale = sales / SELLER["sales"]
    variable = (SELLER["materials"] + SELLER["other"]) * scale
    fixed = SELLER["labor"] + SELLER["rent"] + SELLER["utilities"]
    pre = sales - variable - fixed
    vat = 0 if vat_included else vat_estimate(sales, SELLER["materials"] * scale)
    severance = SELLER["labor"] / 12  # 퇴직급여 적립 (인건비에 미포함 가정)
    before_tax = pre - vat - severance
    tax = income_tax_annual(before_tax * 12) / 12
    return name, sales, pre, vat, severance, before_tax, tax, before_tax - tax


def main():
    sales = list(MONTHLY_SALES.values())
    last12 = sales[-12:]
    since_nov = sales[4:]
    print("== 매출 검증 ==")
    print(f"최근 12개월 합계 : {sum(last12)/1e8:,.1f}억 (매도자 주장 '약 30억')")
    print(f"'25.11 이후 월평균 : {sum(since_nov)/len(since_nov)/1e4:,.0f}만원 "
          f"(최저 {min(since_nov)/1e4:,.0f} / 최고 {max(since_nov)/1e4:,.0f})")
    h2_2025 = sum(sales[:6])
    h1_2026 = sum(sales[6:12])
    print(f"부가세 대조용 공급가액 추정 — 2025년 2기: {h2_2025/1.1/1e8:,.2f}억, "
          f"2026년 1기: {h1_2026/1.1/1e8:,.2f}억")

    print("\n== 월 손익 시나리오 (만원) ==")
    header = ("시나리오", "매출", "매도자식이익", "부가세", "퇴직적립",
              "세전", "소득세", "세후")
    print(" | ".join(header))
    rows = [
        scenario("매도자 숫자 그대로(부가세 이미 반영)", 26_000, vat_included=True),
        scenario("기준: 부가세 미반영이라면", 26_000),
        scenario("비수기 (매출 2.3억)", 23_000),
        scenario("브랜드 1개 이탈 (매출 -25%)", 19_500),
    ]
    for r in rows:
        print(f"{r[0]} | " + " | ".join(f"{v:,.0f}" for v in r[1:]))

    total = PRICE["goodwill"] + PRICE["facility"]
    print(f"\n권리금 합계 {total:,}만원")
    for r in rows:
        months = total / r[-1] if r[-1] > 0 else float("inf")
        print(f"  {r[0]}: 세후 기준 회수 {months:.1f}개월")


if __name__ == "__main__":
    main()
