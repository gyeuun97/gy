#!/usr/bin/env python3
"""사업계획서용 5개년 추정 재무 — 탑연리 2층 70평 셀프스토리지 (자가건물).

입력: floorplan.py 배치 결과(110개, 만실 879만원)
자금: 소진공 성장기반자금(시설) 직접대출 가정
"""
FULL = 8_790_000          # 만실 월매출
UNITS = 110
LOAN = 90_000_000         # 대출 원금
RATE = 0.032              # 기준 2.96 + 가산 0.6 − 비수도권 0.2 − 여성 0.3 ≈ 3.06 → 보수적 3.2%
GRACE_Y, TERM_Y = 3, 8    # 3년 거치 5년 분할
CAPEX = 91_000_000
DEP_Y = 5                 # 시설 감가상각 5년 정액
FIXED_M = 350_000 + 250_000 + 150_000 + 200_000 + 400_000 + 150_000   # 임대료 0 (자가)
CARD = 0.02

def occ(month):
    if month <= 6:  return 0.15 + 0.45 * month / 6
    if month <= 12: return 0.60 + 0.20 * (month - 6) / 6
    return min(0.85, 0.80 + 0.05 * (month - 12) / 12)

years = []
bal = LOAN
for y in range(1, 6):
    rev = sum(FULL * occ(m) for m in range((y-1)*12+1, y*12+1))
    opex = FIXED_M * 12 + rev * CARD
    interest = bal * RATE
    principal = 0 if y <= GRACE_Y else LOAN / (TERM_Y - GRACE_Y)
    dep = CAPEX / DEP_Y if y <= DEP_Y else 0
    ebitda = rev - opex
    ebit = ebitda - dep
    pretax = ebit - interest
    tax = max(0, pretax) * 0.15          # 종합소득세 15% 구간 가정
    net = pretax - tax
    cash = ebitda - interest - principal - tax
    bal -= principal
    avg_occ = sum(occ(m) for m in range((y-1)*12+1, y*12+1)) / 12
    years.append(dict(y=y, occ=avg_occ, rev=rev, opex=opex, ebitda=ebitda, dep=dep,
                      interest=interest, principal=principal, pretax=pretax, tax=tax,
                      net=net, cash=cash, bal=bal))

W = lambda v: f"{v/10000:>9,.0f}"
print(f"{'구분(만원)':<14}" + "".join(f"{'%d년차'%y['y']:>10}" for y in years))
print("─"*66)
rows = [("평균 점유율", lambda y: f"{y['occ']:>9.0%}"),
        ("매출액", lambda y: W(y['rev'])),
        ("운영비", lambda y: W(-y['opex'])),
        ("영업이익(EBITDA)", lambda y: W(y['ebitda'])),
        ("감가상각", lambda y: W(-y['dep'])),
        ("이자비용", lambda y: W(-y['interest'])),
        ("세전이익", lambda y: W(y['pretax'])),
        ("소득세(15%)", lambda y: W(-y['tax'])),
        ("당기순이익", lambda y: W(y['net'])),
        ("원금상환", lambda y: W(-y['principal'])),
        ("현금흐름", lambda y: W(y['cash'])),
        ("대출잔액(기말)", lambda y: W(y['bal']))]
for label, f in rows:
    print(f"{label:<14}" + "".join(f(y) for y in years))
cum = 0
print("─"*66)
line = f"{'누적현금':<14}"
for y in years:
    cum += y['cash']; line += W(cum)
print(line)
print(f"\n5년 누적 현금흐름 {cum/10000:,.0f}만원 | 5년 누적 순이익 {sum(y['net'] for y in years)/10000:,.0f}만원")
print(f"DSCR(3년차) = EBITDA {years[2]['ebitda']/10000:,.0f} / 원리금 {(years[2]['interest']+years[2]['principal'])/10000:,.0f} = {years[2]['ebitda']/(years[2]['interest']+years[2]['principal']):.2f}")
print(f"DSCR(4년차, 상환개시) = {years[3]['ebitda']/(years[3]['interest']+years[3]['principal']):.2f}")

# 월 기준 손익분기
fixed_m = FIXED_M + LOAN*RATE/12
bep = fixed_m / (FULL*(1-CARD))
print(f"\n월 고정비(이자 포함, 거치기간) {fixed_m/10000:,.0f}만원 → BEP 점유율 {bep:.1%} ({UNITS*bep:.0f}개)")
fixed_m2 = FIXED_M + (LOAN*RATE + LOAN/(TERM_Y-GRACE_Y))/12
bep2 = fixed_m2 / (FULL*(1-CARD))
print(f"월 고정비(원리금 포함, 상환기간) {fixed_m2/10000:,.0f}만원 → BEP 점유율 {bep2:.1%} ({UNITS*bep2:.0f}개)")
