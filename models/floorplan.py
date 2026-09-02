#!/usr/bin/env python3
"""2층 70평 셀프스토리지 평면 배치 — 소형·중형 위주.

평면은 장변 19.3m(X) × 단변 12.0m(Y)의 직사각형으로 두고,
좌하단에 계단+화장실 코어(3.5×4.0m)를 고정한다.

배치 원칙:
  깊은 유닛 밴드(2.3m 이상)를 쓰면 유닛 하나가 6㎥를 넘어 소형·중형이 나오지 않는다.
  통로를 하나 더 내주는 대신 밴드를 1.3~1.5m로 얕게 가져가, 통로 3열이
  각각 양옆 밴드 2개를 담당하는 구성으로 소형 위주 구성을 만든다.

단가: 청주 경쟁사 실단가를 부피로 회귀 → 37,500 × 부피^0.70 (5천원 반올림)
"""
import json

PY_M2 = 3.305785
LEN, WID = 19.3, 12.0            # X(장변), Y(단변)
CORE = (0.0, 8.0, 3.5, 4.0)      # 계단+화장실 x,y,w,h (좌하단)
LINK = (3.5, 1.3, 1.5, 9.2)      # 코어~각 통로를 잇는 세로 연결통로
H_WALK, H_LOCKER = 2.4, 1.15

# 밴드: 이름, y시작, 깊이, x구간들, 유닛폭, 단수, 구분
BANDS = [
    ("A",  0.0, 1.3, [(0.0, 19.3)],               1.0, 2, "로커"),
    ("B",  2.5, 1.4, [(0.0, 3.5), (5.0, 19.3)],   1.0, 1, "소형"),
    ("C",  3.9, 1.4, [(0.0, 3.5), (5.0, 19.3)],   1.0, 1, "소형"),
    ("D",  6.5, 1.4, [(0.0, 3.5), (5.0, 19.3)],   1.0, 1, "소형"),
    ("E",  7.9, 1.4, [(5.0, 19.3)],               1.2, 1, "중형"),
    ("F", 10.5, 1.5, [(3.5, 19.3)],               1.5, 1, "중형+"),
]
# 통로: y시작, 폭, x구간
CORRIDORS = [(1.3, 1.2, 0.0, 19.3), (5.3, 1.2, 0.0, 19.3), (9.3, 1.2, 3.5, 19.3)]


def price_of(v):
    return round(37_500 * v ** 0.70 / 5_000) * 5_000


def build():
    units = []
    for name, y, depth, spans, uw, tiers, kind in BANDS:
        h = H_WALK if tiers == 1 else H_LOCKER
        vol = round(uw * depth * h, 2)
        p = price_of(vol)
        for x0, x1 in spans:
            n = int((x1 - x0) / uw + 1e-9)
            for i in range(n):
                for t in range(tiers):
                    units.append({
                        "band": name, "kind": kind, "x": round(x0 + i * uw, 2), "y": y,
                        "w": uw, "d": depth, "h": h, "tier": t + 1, "tiers": tiers,
                        "vol": vol, "price": p,
                    })
    return units


def areas():
    corr = sum(w * (x1 - x0) for _, w, x0, x1 in CORRIDORS)
    link = LINK[2] * LINK[3] - sum(LINK[2] * w for _, w, _, _ in CORRIDORS)
    return corr + link, CORE[2] * CORE[3]


def report(units):
    from collections import defaultdict
    g = defaultdict(lambda: {"n": 0, "rev": 0, "u": None})
    for u in units:
        g[u["band"]]["n"] += 1
        g[u["band"]]["rev"] += u["price"]
        g[u["band"]]["u"] = u
    total = LEN * WID
    print("=" * 88)
    print(f"■ 유닛 스케줄 — {LEN}m × {WID}m = {total:.1f}㎡ ({total/PY_M2:.1f}평)")
    print("=" * 88)
    print(f"  {'밴드':<5}{'구분':<8}{'치수 W×D×H(m)':<22}{'부피':>8}{'개수':>6}{'단가':>10}{'소계':>12}")
    print("  " + "─" * 73)
    tn = tr = ta = 0
    for k in sorted(g, key=lambda k: g[k]["u"]["y"]):
        u, n, rev = g[k]["u"], g[k]["n"], g[k]["rev"]
        dim = f'{u["w"]} × {u["d"]} × {u["h"]}' + ("  (2단 적층)" if u["tiers"] == 2 else "")
        print(f'  {k:<5}{u["kind"]:<8}{dim:<22}{u["vol"]:>7.2f}㎥{n:>6}{u["price"]:>10,}{rev:>12,}')
        tn += n
        tr += rev
        ta += u["w"] * u["d"] * (n / u["tiers"])
    corr, core = areas()
    print("  " + "─" * 73)
    print(f'  {"합계":<5}{"":<8}{"":<22}{"":>8}{tn:>6}{"":>10}{tr:>12,}')
    print(f"\n  유닛 {ta:.1f}㎡ ({ta/PY_M2:.1f}평)  통로 {corr:.1f}㎡  코어 {core:.1f}㎡"
          f"  검산 {ta+corr+core:.1f} / {total:.1f}㎡")
    print(f"  임대효율 {ta/total:.1%}  |  평당 만실매출 {tr/(total/PY_M2):,.0f}원")
    return tn, tr


def pnl(full, n_units, rent=3_000_000, gp=70):
    fixed = rent + gp * 5_000 + 250_000 + 150_000 + 200_000 + 400_000 + 150_000
    print("\n" + "=" * 88)
    print(f"■ 손익 — 월세 {rent:,}원 (고정비 {fixed:,}원 + 카드수수료 2%)")
    print("=" * 88)
    print(f"  {'점유율':>7}{'계약':>7}{'월매출':>12}{'월순익':>12}")
    print("  " + "─" * 38)
    for occ in (0.5, 0.6, 0.7, 0.8, 0.9, 1.0):
        rev = full * occ
        print(f"  {occ:>6.0%}{occ*n_units:>7.0f}{rev:>12,.0f}{rev-(fixed+rev*0.02):>12,.0f}")
    lo, hi = 0.0, 1.0
    for _ in range(60):
        m = (lo + hi) / 2
        rev = full * m
        if rev - (fixed + rev * 0.02) < 0:
            lo = m
        else:
            hi = m
    print(f"\n  손익분기 점유율 {hi:.1%}  ({n_units}개 중 {n_units*hi:.0f}개 계약)")


if __name__ == "__main__":
    u = build()
    n, r = report(u)
    pnl(r, n)
    json.dump({"units": u, "bands": BANDS, "corridors": CORRIDORS,
               "core": CORE, "link": LINK, "len": LEN, "wid": WID},
              open("models/floorplan_units.json", "w"), ensure_ascii=False)
