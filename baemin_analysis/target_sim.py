"""월매출 목표(최종 1.5억) 시나리오: 브랜드별 판매 목표, 단계별 로드맵, 인력표, 고정비.

profit_sim.py의 단위경제(unit)와 수수료·부가세 가정을 그대로 쓰고,
매출 규모가 커질 때 바뀌는 인력·고정비만 단계별로 따로 둔다.
profit_sim.main()이 build_target_sheets(wb)를 불러 같은 엑셀에 시트를 추가한다.
"""
import math

from openpyxl.styles import Alignment, Font, PatternFill

import profit_sim as ps

TARGET = 150_000_000

# 플랜 B: 김치찜은 2~3인 세트 위주, 덮밥은 사이드 세트로 객단가 상향
PLAN_B = {"김치찜": dict(aov=24000, cost_rate=0.29), "제육덮밥": dict(aov=18000, cost_rate=0.32)}

DINNER_PEAK_SHARE = 0.30   # 18~20시 2시간에 하루 주문의 30%가 몰린다고 가정
NIGHT_PREMIUM_HOURLY = 14_500  # 5인 이상: 야간가산·4대보험 반영 평균 시급
SMALL_HOURLY = ps.HOURLY       # 5인 미만: 주휴·산재·고용 반영 시급

# 단계별 인력 배치 (사장 제외): (근무조, 시간대, 1일 근무시간, 인원)
STAGES = [
    dict(name="1단계 오픈~3개월", sales=35_000_000, staff=[
        ("점심", "11:00~15:00", 4, 1), ("저녁·야간", "17:00~01:00", 8, 1)]),
    dict(name="2단계 6개월", sales=70_000_000, staff=[
        ("점심", "11:00~15:00", 5, 1), ("저녁", "17:00~23:00", 6, 2), ("야간", "21:00~01:00", 4, 1)]),
    dict(name="3단계 12개월", sales=100_000_000, staff=[
        ("오전 준비", "09:00~13:00", 4, 1), ("점심", "11:00~16:00", 5, 2),
        ("저녁", "17:00~23:00", 6, 2), ("야간", "21:00~01:00", 4, 2)]),
    dict(name="4단계 18개월~ (목표)", sales=TARGET, staff=[
        ("오전 준비", "09:00~13:00", 4, 2), ("점심", "11:00~16:00", 5, 2),
        ("저녁", "17:00~23:00", 6, 4), ("야간", "21:00~01:00", 4, 2)]),
]

# 단계별 월 고정비 (원). 월세는 100만 원 고정, 나머지는 물량에 따라 증가
FIXED_STAGES = {
    "월세": [1_000_000] * 4,
    "관리비": [100_000] * 4,
    "전기": [350_000, 550_000, 750_000, 950_000],
    "가스": [300_000, 450_000, 600_000, 800_000],
    "수도": [80_000, 120_000, 160_000, 220_000],
    "통신·POS·주문접수": [70_000, 70_000, 90_000, 90_000],
    "음식물·폐기물": [50_000, 80_000, 120_000, 150_000],
    "보험 (화재·영업배상)": [50_000, 50_000, 80_000, 100_000],
    "세무 기장": [150_000, 150_000, 200_000, 250_000],
    "배민 광고 (4개 브랜드)": [600_000, 1_000_000, 1_400_000, 1_600_000],
    "위생·주방 소모품": [150_000, 250_000, 350_000, 500_000],
    "로열티·시스템 사용료 예비": [200_000, 300_000, 400_000, 500_000],
    "장비 수리·유지": [100_000, 150_000, 200_000, 250_000],
}

HEAD = PatternFill("solid", fgColor="2AC1BC")
SUB = PatternFill("solid", fgColor="E8F7F6")
WB = Font(bold=True, color="FFFFFF")
B = Font(bold=True)
WON = ps.WON


def money(won):
    """35_000_000 → '3,500만 원', 150_000_000 → '1억 5,000만 원'."""
    eok, man = divmod(won // 10_000, 10_000)
    return (f"{eok}억 " if eok else "") + (f"{man:,}만 " if man else "") + "원"


def brands(plan_b):
    out = []
    for b in ps.BRANDS:
        b = dict(b)
        for key, over in (PLAN_B.items() if plan_b else []):
            if b["name"].startswith(key):
                b.update(over)
        b["unit"] = ps.unit(b)
        out.append(b)
    return out


def orders_for(sales, bs):
    """목표 매출을 브랜드 비중대로 나눴을 때의 월 주문수."""
    avg = sum(b["share"] * b["unit"]["price"] for b in bs)
    total = sales / avg
    return total, [total * b["share"] for b in bs]


def labor(stage):
    daily_hours = sum(h * n for _, _, h, n in stage["staff"])
    headcount = sum(n for *_, n in stage["staff"])   # 하루 근무 인원 = 상시근로자 수 근사
    big = headcount >= 5
    hourly = NIGHT_PREMIUM_HOURLY if big else SMALL_HOURLY
    return dict(daily_hours=daily_hours, month_hours=daily_hours * 30, headcount=headcount,
                big=big, hourly=hourly, cost=daily_hours * 30 * hourly)


def stage_pnl(i, stage, bs):
    total, per = orders_for(stage["sales"], bs)
    var = {"식자재 원가": 0, "배민 중개·결제수수료": 0, "배달비": 0, "포장재": 0, "부가세 순부담": 0}
    contrib = 0
    for b, n in zip(bs, per):
        u = b["unit"]
        var["식자재 원가"] += u["food"] * n
        var["배민 중개·결제수수료"] += u["fees"] * n
        var["배달비"] += ps.DELIVERY_FEE * n
        var["포장재"] += b["pack"] * n
        var["부가세 순부담"] += u["vat"] * n
        contrib += u["contrib"] * n
    lab = labor(stage)
    fixed = sum(v[i] for v in FIXED_STAGES.values())
    profit = contrib - lab["cost"] - fixed
    return dict(total=total, per=per, var=var, contrib=contrib, labor=lab, fixed=fixed, profit=profit)


def header(ws, row, cols, col0=1):
    for c, h in enumerate(cols, col0):
        cell = ws.cell(row, c, h)
        cell.fill, cell.font = HEAD, WB
        cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)


def put(ws, r, c, v, fmt=None, font=None, fill=None):
    cell = ws.cell(r, c, v)
    if fmt:
        cell.number_format = fmt
    if font:
        cell.font = font
    if fill:
        cell.fill = fill
    return cell


def sheet_targets(wb):
    ws = wb.create_sheet("목표1.5억_브랜드별")
    put(ws, 1, 1, "월매출 1억 5천만 원 달성을 위한 브랜드별 판매 목표 (매출 = 즉시할인 후 실결제액)", font=Font(bold=True, size=13))
    r = 3
    for title, plan_b in (("플랜 A: 현재 메뉴 구성", False), ("플랜 B: 객단가 상향 (추천) — 김치찜 세트 위주 24,000원, 덮밥 사이드 세트 18,000원", True)):
        bs = brands(plan_b)
        total, per = orders_for(TARGET, bs)
        put(ws, r, 1, title, font=B, fill=SUB)
        r += 1
        header(ws, r, ["브랜드", "주문 비중", "객단가", "실결제 (할인 후)", "월 판매", "주 판매", "하루 판매",
                       "저녁 피크 시간당", "월 매출", "건당 공헌이익", "월 공헌이익"])
        r += 1
        sums = dict(n=0, sales=0, contrib=0)
        for b, n in zip(bs, per):
            u = b["unit"]
            vals = [(b["name"], None), (b["share"] * 100, ps.PCT), (b["aov"], WON), (u["price"], WON),
                    (n, '#,##0"건"'), (n / 30 * 7, '#,##0"건"'), (n / 30, '0.0"건"'),
                    (n / 30 * DINNER_PEAK_SHARE / 2, '0.0"건"'), (n * u["price"], WON),
                    (u["contrib"], WON), (n * u["contrib"], WON)]
            for c, (v, fmt) in enumerate(vals, 1):
                put(ws, r, c, round(v, 1) if isinstance(v, float) else v, fmt)
            sums["n"] += n
            sums["sales"] += n * u["price"]
            sums["contrib"] += n * u["contrib"]
            r += 1
        for c, (v, fmt) in {1: ("합계", None), 4: (sums["sales"] / sums["n"], WON), 5: (sums["n"], '#,##0"건"'),
                            6: (sums["n"] / 30 * 7, '#,##0"건"'), 7: (sums["n"] / 30, '0.0"건"'),
                            8: (sums["n"] / 30 * DINNER_PEAK_SHARE / 2, '0.0"건"'), 9: (sums["sales"], WON),
                            11: (sums["contrib"], WON)}.items():
            put(ws, r, c, v, fmt, font=B, fill=SUB)
        r += 1
        put(ws, r, 1, f"공헌이익률 {sums['contrib'] / sums['sales'] * 100:.1f}%  ·  "
                      f"저녁 피크 = 18~20시에 하루 주문의 {DINNER_PEAK_SHARE:.0%}가 몰린다는 가정")
        r += 3
    put(ws, r, 1, "현실성 점검", font=B)
    for line in [
        "• 4개 브랜드 가맹점 평균매출 합계는 월 약 8,900만 원 (제육대가 3.4억·명인김치찜 2.5억·불멸닭발 1.45억·도리당 3.3억/연 기준).",
        "  1.5억은 4개 브랜드가 동시에 평균의 약 1.7배를 해야 하는 상위 10% 수준입니다.",
        "• 김치찜 하루 77~85건은 상권 주문순위 2위 한찜두찜과 정면 경쟁하는 물량입니다.",
        "• 저녁 피크 시간당 30건 이상은 15평 안팎 주방의 한계에 가깝습니다. 화구·냉장고 수와 포장 동선을 실측하세요.",
    ]:
        r += 1
        put(ws, r, 1, line)
    ws.column_dimensions["A"].width = 30
    for col in "BCDEFGHIJK":
        ws.column_dimensions[col].width = 14


def sheet_roadmap(wb, results):
    ws = wb.create_sheet("단계별_로드맵")
    put(ws, 1, 1, "단계별 손익 로드맵 (플랜 B 메뉴 구성 기준, 월세 100만 원)", font=Font(bold=True, size=13))
    header(ws, 3, ["항목"] + [s["name"] for s in STAGES])
    rows = [("월매출 목표", lambda s, p: s["sales"], WON, B),
            ("월 주문 (4개 브랜드)", lambda s, p: p["total"], '#,##0"건"', None),
            ("하루 주문", lambda s, p: p["total"] / 30, '0.0"건"', B)]
    for k, b in enumerate(ps.BRANDS):
        rows.append((f"  └ {b['name']} 하루", lambda s, p, k=k: p["per"][k] / 30, '0.0"건"', None))
    rows += [(k, (lambda s, p, k=k: p["var"][k]), WON, None) for k in
             ("식자재 원가", "배민 중개·결제수수료", "배달비", "포장재", "부가세 순부담")]
    rows += [("공헌이익 (변동비 차감 후)", lambda s, p: p["contrib"], WON, B),
             ("인건비 (알바·직원)", lambda s, p: p["labor"]["cost"], WON, None),
             ("고정비", lambda s, p: p["fixed"], WON, None),
             ("영업이익 (사장 몫, 세전)", lambda s, p: p["profit"], WON, "profit"),
             ("영업이익률", lambda s, p: p["profit"] / s["sales"] * 100, ps.PCT, B),
             (f"사장 인건비 {ps.OWNER_WAGE // 10000}만 원 차감 후", lambda s, p: p["profit"] - ps.OWNER_WAGE, WON, "profit"),
             ("하루 근무 인원 (사장 제외)", lambda s, p: p["labor"]["headcount"], '0"명"', None),
             ("월 근무시간 합계", lambda s, p: p["labor"]["month_hours"], '#,##0"시간"', None),
             ("근로기준법", lambda s, p: "5인 이상: 야간·연장 가산, 4대보험" if p["labor"]["big"] else "5인 미만: 가산수당 의무 없음",
              None, None)]
    for i, (label, fn, fmt, font) in enumerate(rows, 4):
        put(ws, i, 1, label, font=B if font in (B, "profit") else None)
        for j, (s, p) in enumerate(zip(STAGES, results), 2):
            v = fn(s, p)
            f = font
            if font == "profit":
                f = Font(bold=True, color="C0392B" if v < 0 else "0F8F8A")
            put(ws, i, j, round(v, 1) if isinstance(v, float) else v, fmt, font=f)
    r = len(rows) + 6
    put(ws, r, 1, "읽는 법", font=B)
    for line in [
        "• 단계마다 늘어나는 건 인건비와 고정비입니다. 3단계부터 하루 근무 인원이 5명을 넘어 근로기준법 가산수당이 적용됩니다.",
        "• 4단계(1.5억)는 월세 100만 원 주방에서 가능한 상한선입니다. 주방이 좁으면 확장 이전 비용을 별도로 잡아야 합니다.",
        "• 수수료는 배민 최상위 구간(중개 7.8%, 배달비 3,400원) 기준이라 보수적인 추정입니다.",
    ]:
        r += 1
        put(ws, r, 1, line)
    ws.column_dimensions["A"].width = 34
    for col in "BCDE":
        ws.column_dimensions[col].width = 22


def sheet_staff(wb):
    ws = wb.create_sheet("단계별_인력표")
    put(ws, 1, 1, "단계별 인력 배치 (사장은 매일 10시간 근무, 아래는 사장 외 인력)", font=Font(bold=True, size=13))
    r = 3
    for s in STAGES:
        lab = labor(s)
        put(ws, r, 1, f"{s['name']} — 월매출 {money(s['sales'])}", font=B, fill=SUB)
        r += 1
        header(ws, r, ["근무조", "시간대", "1일 근무시간", "인원", "1일 인시", "월 인시", "적용 시급", "월 인건비"])
        r += 1
        for shift, time, h, n in s["staff"]:
            for c, (v, fmt) in enumerate([(shift, None), (time, None), (h, '0"시간"'), (n, '0"명"'),
                                           (h * n, '0"시간"'), (h * n * 30, '#,##0"시간"'),
                                           (lab["hourly"], WON), (h * n * 30 * lab["hourly"], WON)], 1):
                put(ws, r, c, v, fmt)
            r += 1
        put(ws, r, 1, "합계", font=B)
        put(ws, r, 4, lab["headcount"], '0"명"', font=B)
        put(ws, r, 5, lab["daily_hours"], '0"시간"', font=B)
        put(ws, r, 6, lab["month_hours"], '#,##0"시간"', font=B)
        put(ws, r, 8, lab["cost"], WON, font=B)
        r += 1
        put(ws, r, 1, "5인 이상 사업장 → 야간(22~06시) 50% 가산·4대보험 반영 평균 시급" if lab["big"]
            else "5인 미만 사업장 → 주휴수당·산재·고용보험만 반영")
        r += 2
    ws.column_dimensions["A"].width = 16
    ws.column_dimensions["B"].width = 16
    for col in "CDEFGH":
        ws.column_dimensions[col].width = 14


def sheet_fixed(wb):
    ws = wb.create_sheet("단계별_고정비")
    header(ws, 1, ["항목"] + [s["name"] for s in STAGES])
    for i, (k, vals) in enumerate(FIXED_STAGES.items(), 2):
        put(ws, i, 1, k)
        for j, v in enumerate(vals, 2):
            put(ws, i, j, v, WON)
    r = len(FIXED_STAGES) + 2
    put(ws, r, 1, "합계", font=B)
    for j in range(4):
        put(ws, r, j + 2, sum(v[j] for v in FIXED_STAGES.values()), WON, font=B)
    ws.column_dimensions["A"].width = 28
    for col in "BCDE":
        ws.column_dimensions[col].width = 22


def build_target_sheets(wb):
    bs = brands(plan_b=True)
    results = [stage_pnl(i, s, bs) for i, s in enumerate(STAGES)]
    sheet_targets(wb)
    sheet_roadmap(wb, results)
    sheet_staff(wb)
    sheet_fixed(wb)
    sheet_hourly(wb)
    for s, p in zip(STAGES, results):
        print(f"{s['name']}: 일 {p['total'] / 30:.0f}건, 공헌 {p['contrib']:,.0f}, 인건비 {p['labor']['cost']:,.0f} "
              f"({p['labor']['headcount']}명), 고정 {p['fixed']:,.0f}, 영업이익 {p['profit']:,.0f} "
              f"({p['profit'] / s['sales']:.1%})")


# ── 시간대별 처리량 ─────────────────────────────────────────────────────
HOURS = list(range(11, 24)) + [0]       # 11시 ~ 새벽 0시대 (01시 마감)

# 브랜드별 시간대 주문 비중 (합 = 1). 덮밥은 점심, 닭발은 야식, 찜·탕은 저녁 중심
PROFILES = {
    "김치찜": [.03, .09, .06, .03, .02, .03, .07, .16, .18, .12, .08, .06, .04, .03],
    "제육덮밥": [.08, .22, .14, .05, .03, .03, .07, .13, .12, .07, .03, .02, .01, .00],
    "닭발": [.00, .01, .01, .01, .01, .02, .04, .08, .11, .13, .15, .16, .14, .13],
    "곱도리탕": [.01, .03, .02, .01, .01, .03, .08, .16, .19, .16, .11, .08, .06, .05],
}
OWNER_HOURS = (11, 21)       # 사장 근무 11~21시
PER_PERSON = 8               # 1인당 시간당 처리 (사전 조리된 찜·탕 데우기·담기·포장 기준)
EQUIP_CAP = 40               # 15평 주방 설비 한계 (화구 6구 + 작업대 2, 시간당)


def _span(time):
    a, b = (int(t.split(":")[0]) for t in time.split("~"))
    return a, (b + 24 if b <= a else b)


def staff_on(stage, h):
    hh = h + 24 if h < 9 else h
    n = 1 if OWNER_HOURS[0] <= hh < OWNER_HOURS[1] else 0
    for _, time, _, cnt in stage["staff"]:
        a, b = _span(time)
        if a <= hh < b:
            n += cnt
    return n


def hourly(stage, bs):
    total, per = orders_for(stage["sales"], bs)
    rows = []
    for i, h in enumerate(HOURS):
        demand = [per[k] / 30 * PROFILES[b["name"].split(" ")[0]][i] for k, b in enumerate(bs)]
        staff = staff_on(stage, h)
        cap = min(staff * PER_PERSON, EQUIP_CAP)
        d = sum(demand)
        rows.append(dict(hour=h, demand=demand, total=d, staff=staff, cap_staff=staff * PER_PERSON,
                         cap=cap, util=d / cap if cap else float("inf")))
    return rows


def verdict(r):
    if r["total"] > r["cap"]:
        return f"부족 {r['total'] - r['cap']:.0f}건"
    if r["util"] >= 0.8:
        return "빠듯"
    return "여유"


def sheet_hourly(wb):
    from openpyxl.chart import BarChart, LineChart, Reference

    bs = brands(plan_b=True)
    ws = wb.create_sheet("시간대별_처리량")
    put(ws, 1, 1, f"시간대별 주문 수요 vs 처리 가능량 (1인당 시간당 {PER_PERSON}건, 주방 설비 한계 시간당 {EQUIP_CAP}건, 사장 11~21시 근무)",
        font=Font(bold=True, size=13))
    r = 3
    for s in STAGES:
        rows = hourly(s, bs)
        put(ws, r, 1, f"{s['name']} — 월매출 {money(s['sales'])}", font=B, fill=SUB)
        r += 1
        cols = ["시간"] + [b["name"].split(" ")[0] for b in bs] + ["총 주문", "근무 인원(사장 포함)",
                                                                   "처리 가능(인력)", "처리 가능(최종)", "가동률", "판정"]
        header(ws, r, cols)
        top = r + 1
        for row in rows:
            r += 1
            put(ws, r, 1, f"{row['hour']:02d}시")
            for k, v in enumerate(row["demand"]):
                put(ws, r, 2 + k, round(v, 1), '0.0"건"')
            put(ws, r, 6, round(row["total"], 1), '0.0"건"', font=B)
            put(ws, r, 7, row["staff"], '0"명"')
            put(ws, r, 8, row["cap_staff"], '0"건"')
            put(ws, r, 9, row["cap"], '0"건"')
            put(ws, r, 10, round(row["util"] * 100, 1), ps.PCT)
            v = verdict(row)
            put(ws, r, 11, v, font=Font(bold=True, color="C0392B" if v.startswith("부족") else
                                        ("B7791F" if v == "빠듯" else "0F8F8A")))
        bottom = r

        bar = BarChart()
        bar.type, bar.grouping, bar.overlap = "col", "stacked", 100
        bar.title = f"{s['name']} 시간대별 주문 vs 처리 가능량"
        bar.y_axis.title, bar.x_axis.title = "건/시간", "시간"
        bar.add_data(Reference(ws, min_col=2, max_col=5, min_row=top - 1, max_row=bottom), titles_from_data=True)
        bar.set_categories(Reference(ws, min_col=1, min_row=top, max_row=bottom))
        line = LineChart()
        line.add_data(Reference(ws, min_col=9, min_row=top - 1, max_row=bottom), titles_from_data=True)
        line.series[0].smooth = False
        line.series[0].graphicalProperties.line.solidFill = "0B0B0B"
        line.series[0].graphicalProperties.line.width = 28575   # 2.25pt
        bar += line
        bar.height, bar.width = 8, 18
        ws.add_chart(bar, f"M{top - 2}")
        r = max(r + 3, top + 16)
    ws.column_dimensions["A"].width = 10
    for col in "BCDEFGHIJK":
        ws.column_dimensions[col].width = 12


def draw_hourly_png(path, font_dir):
    import matplotlib
    matplotlib.use("Agg")
    from matplotlib import font_manager, pyplot as plt

    for w in (400, 700):
        font_manager.fontManager.addfont(f"{font_dir}/NotoSansKR-{w}.ttf")
    plt.rcParams["font.family"] = "Noto Sans KR"
    INK, INK2, GRID, SURF = "#0b0b0b", "#52514e", "#e6e5e1", "#fcfcfb"
    SERIES = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100"]      # 기준 팔레트 1~4번 고정 순서
    bs = brands(plan_b=True)
    fig, axes = plt.subplots(2, 2, figsize=(13, 8.2), sharey=True, facecolor=SURF)
    x = list(range(len(HOURS)))
    labels = [f"{h:02d}" for h in HOURS]
    ymax = max(max(max(r["total"], r["cap"]) for r in hourly(s, bs)) for s in STAGES) * 1.18
    for ax, s in zip(axes.flat, STAGES):
        rows = hourly(s, bs)
        ax.set_facecolor(SURF)
        bottom = [0] * len(x)
        for k, b in enumerate(bs):
            vals = [r["demand"][k] for r in rows]
            ax.bar(x, vals, bottom=bottom, width=0.72, color=SERIES[k], edgecolor=SURF, linewidth=1.2,
                   label=b["name"].split(" ")[0], zorder=2)
            bottom = [a + v for a, v in zip(bottom, vals)]
        caps = [r["cap"] for r in rows]
        ax.step([i - 0.5 for i in x] + [x[-1] + 0.5], caps + [caps[-1]], where="post", color=INK, linewidth=2,
                label="처리 가능량", zorder=3)
        for i, r in enumerate(rows):
            if r["total"] > r["cap"]:
                ax.annotate(f"▲부족 {r['total'] - r['cap']:.0f}", (i, r["total"]), xytext=(0, 4),
                            textcoords="offset points", ha="center", fontsize=8.5, color=INK, fontweight="bold")
        peak = max(rows, key=lambda r: r["total"])
        ax.set_title(f"{s['name']}  ·  월 {money(s['sales'])}  ·  하루 {sum(r['total'] for r in rows):.0f}건  "
                     f"(피크 {peak['hour']:02d}시 {peak['total']:.0f}건)", fontsize=10.5, color=INK, loc="left")
        ax.set_xticks(x, labels, fontsize=8.5, color=INK2)
        ax.tick_params(axis="y", labelsize=8.5, colors=INK2)
        ax.set_ylim(0, ymax)
        ax.grid(axis="y", color=GRID, linewidth=0.8, zorder=0)
        for side in ("top", "right", "left"):
            ax.spines[side].set_visible(False)
        ax.spines["bottom"].set_color(GRID)
    for ax in axes[:, 0]:
        ax.set_ylabel("시간당 주문 (건)", color=INK2, fontsize=9)
    for ax in axes[1]:
        ax.set_xlabel("시간대 (시)", color=INK2, fontsize=9)
    handles, labs = axes[0, 0].get_legend_handles_labels()
    fig.legend(handles, labs, loc="upper center", ncol=5, frameon=False, fontsize=9.5, bbox_to_anchor=(0.5, 0.965))
    fig.suptitle("시간대별 주문 수요(막대) vs 주방 처리 가능량(선)", fontsize=14, fontweight="bold", color=INK, y=0.995)
    fig.text(0.5, 0.005, f"처리 가능량 = min(근무 인원 × {PER_PERSON}건, 설비 한계 {EQUIP_CAP}건) · 사장 11~21시 근무 포함 · 플랜 B 메뉴 기준",
             ha="center", fontsize=8.5, color=INK2)
    fig.tight_layout(rect=(0, 0.02, 1, 0.93))
    fig.savefig(path, dpi=150, facecolor=SURF)
