"""배민 캡처 데이터(stores_*.csv)로 상권·경쟁사 분석 PDF 보고서를 만든다.

HTML을 만든 뒤 headless Chromium의 --print-to-pdf로 변환한다.
사용법: python3 build_pdf.py [CSV] [OUT.pdf] [FONT_DIR]
FONT_DIR에는 NotoSansKR-400/700/900.ttf가 있어야 한다.
"""
import html
import os
import subprocess
import sys
import tempfile
from collections import defaultdict

from build_excel import dist_band, load

SRC = sys.argv[1] if len(sys.argv) > 1 else "stores_20261012.csv"
OUT = sys.argv[2] if len(sys.argv) > 2 else "배민_상권분석_충북대사창동_20261012.pdf"
FONT_DIR = sys.argv[3] if len(sys.argv) > 3 else "fonts"
CHROMIUM = os.environ.get("CHROMIUM", "/opt/pw-browsers/chromium")

e = html.escape


def fmt(n):
    return "-" if n is None else f"{n:,}"


def km(m):
    if m is None:
        return "-"
    return f"{m}m" if m < 1000 else f"{m / 1000:.1f}km"


def bar(value, max_value, color="var(--accent)"):
    pct = 0 if not max_value else value / max_value * 100
    return (f'<div class="bar"><span style="width:{pct:.1f}%;background:{color}"></span>'
            f'<em>{fmt(value)}</em></div>')


def store_table(rows, cols, max_reviews):
    head = "".join(f"<th>{c}</th>" for c in cols)
    body = []
    for r in rows:
        tags = []
        if r["프랜차이즈"] == "Y":
            tags.append('<i class="tag fr">프랜차이즈</i>')
        if r["광고"]:
            tags.append('<i class="tag ad">광고</i>')
        body.append(
            "<tr>"
            f'<td class="num">{r["주문순위"]}</td>'
            f'<td class="num">{r["리뷰순위"]}</td>'
            f'<td class="name">{e(r["가게명"])} {"".join(tags)}</td>'
            f"<td>{e(r['업종'])}</td>"
            f'<td class="num">{r["별점"]:.1f}</td>'
            f'<td class="barcell">{bar(r["리뷰수"], max_reviews)}</td>'
            f'<td class="num">{km(r["거리(m)"])}</td>'
            f'<td class="num">{fmt(r["배달시간(분)"])}</td>'
            f'<td class="num">{fmt(r["최소주문(원)"])}</td>'
            "</tr>")
    return f'<table class="stores"><thead><tr>{head}</tr></thead><tbody>{"".join(body)}</tbody></table>'


def build_html(stores):
    by_review = sorted(stores, key=lambda r: -(r["리뷰수"] or 0))
    for i, r in enumerate(by_review, 1):
        r["리뷰순위"] = i
    n = len(stores)
    total_reviews = sum(r["리뷰수"] for r in stores)
    avg_rating = sum(r["별점"] for r in stores) / n
    fr = sum(1 for r in stores if r["프랜차이즈"] == "Y")
    near = sum(1 for r in stores if r["거리(m)"] is not None and r["거리(m)"] <= 500)
    max_reviews = by_review[0]["리뷰수"]

    groups = defaultdict(list)
    for r in stores:
        groups[r["업종"]].append(r)
    cats = []
    for cat, rs in groups.items():
        known = [r for r in rs if r["최소주문(원)"] is not None]
        cats.append(dict(
            name=cat, n=len(rs), reviews=sum(r["리뷰수"] for r in rs),
            avg=round(sum(r["리뷰수"] for r in rs) / len(rs)),
            rating=sum(r["별점"] for r in rs) / len(rs),
            min_order=round(sum(r["최소주문(원)"] for r in known) / len(known)) if known else None,
            near=sum(1 for r in rs if r["거리(m)"] is not None and r["거리(m)"] <= 500),
            fr=sum(1 for r in rs if r["프랜차이즈"] == "Y"),
            best=min(rs, key=lambda r: r["주문순위"])["가게명"]))
    cats.sort(key=lambda c: -c["reviews"])
    max_cat = cats[0]["reviews"]
    max_avg = max(c["avg"] for c in cats)

    cat_rows = "".join(
        "<tr>"
        f"<td class='name'>{e(c['name'])}</td>"
        f"<td class='num'>{c['n']}</td>"
        f"<td class='barcell'>{bar(c['reviews'], max_cat)}</td>"
        f"<td class='barcell'>{bar(c['avg'], max_avg, 'var(--accent2)')}</td>"
        f"<td class='num'>{c['rating']:.2f}</td>"
        f"<td class='num'>{fmt(c['min_order'])}</td>"
        f"<td class='num'>{c['near']}</td>"
        f"<td class='num'>{c['fr']}/{c['n']}</td>"
        f"<td class='small'>{e(c['best'])}</td>"
        "</tr>" for c in cats)

    bands = defaultdict(list)
    for r in stores:
        bands[dist_band(r["거리(m)"])].append(r)
    band_rows = "".join(
        "<tr>"
        f"<td class='name'>{e(b)}</td><td class='num'>{len(rs)}</td>"
        f"<td class='num'>{fmt(sum(r['리뷰수'] for r in rs))}</td>"
        f"<td class='small'>{e(', '.join(r['가게명'] for r in sorted(rs, key=lambda r: r['주문순위'])[:8]))}"
        f"{' 외' if len(rs) > 8 else ''}</td></tr>"
        for b, rs in sorted(bands.items()))

    cols = ["주문", "리뷰", "가게명", "업종", "별점", "리뷰수", "거리", "배달(분)", "최소주문"]
    top20 = store_table(by_review[:20], cols, max_reviews)
    all1 = store_table(stores[:32], cols, max_reviews)
    all2 = store_table(stores[32:], cols, max_reviews)

    return f"""<!doctype html><html lang="ko"><head><meta charset="utf-8">
<style>
@font-face {{ font-family: NKR; src: url('{FONT_DIR}/NotoSansKR-400.ttf'); font-weight: 400; }}
@font-face {{ font-family: NKR; src: url('{FONT_DIR}/NotoSansKR-700.ttf'); font-weight: 700; }}
@font-face {{ font-family: NKR; src: url('{FONT_DIR}/NotoSansKR-900.ttf'); font-weight: 900; }}
:root {{ --accent:#2AC1BC; --accent2:#7C8CF8; --ink:#1d2433; --muted:#6b7280; --line:#e5e7eb; --soft:#f3fbfb; }}
@page {{ size: A4; margin: 14mm 12mm 14mm 12mm; }}
* {{ box-sizing: border-box; }}
body {{ font-family: NKR, sans-serif; color: var(--ink); font-size: 9.5pt; line-height: 1.5; margin: 0; }}
h1 {{ font-size: 22pt; font-weight: 900; margin: 0 0 2mm; letter-spacing: -0.5px; }}
h2 {{ font-size: 13pt; font-weight: 900; margin: 0 0 3mm; padding-bottom: 1.5mm; border-bottom: 2px solid var(--accent); }}
h3 {{ font-size: 10.5pt; margin: 4mm 0 1.5mm; }}
.page {{ page-break-after: always; }}
.page:last-child {{ page-break-after: auto; }}
.sub {{ color: var(--muted); margin-bottom: 6mm; }}
.kpis {{ display: grid; grid-template-columns: repeat(5, 1fr); gap: 3mm; margin: 4mm 0 6mm; }}
.kpi {{ background: var(--soft); border-radius: 3mm; padding: 3mm 3.5mm; }}
.kpi b {{ display: block; font-size: 16pt; font-weight: 900; color: #0f8f8a; }}
.kpi span {{ color: var(--muted); font-size: 8.5pt; }}
.meta {{ width: 100%; border-collapse: collapse; margin-bottom: 5mm; }}
.meta td {{ padding: 1.5mm 2mm; border-bottom: 1px solid var(--line); vertical-align: top; }}
.meta td:first-child {{ width: 26mm; color: var(--muted); }}
ul.ins {{ margin: 0; padding-left: 5mm; }}
ul.ins li {{ margin-bottom: 2mm; }}
ul.ins b {{ color: #0f8f8a; }}
.note {{ background: #fff8e6; border-left: 3px solid #f2b705; padding: 2.5mm 3.5mm; font-size: 8.5pt; margin-top: 5mm; }}
.note p {{ margin: 0 0 1mm; }}
table {{ width: 100%; border-collapse: collapse; }}
th {{ background: var(--accent); color: #fff; font-weight: 700; font-size: 8.3pt; padding: 1.6mm 1.5mm; text-align: center; }}
td {{ padding: 1.2mm 1.5mm; border-bottom: 1px solid var(--line); font-size: 8.3pt; }}
tbody tr:nth-child(even) td {{ background: #fafafa; }}
tr {{ page-break-inside: avoid; }}
td.num {{ text-align: right; white-space: nowrap; font-variant-numeric: tabular-nums; }}
td.name {{ font-weight: 700; }}
td.small {{ font-size: 7.6pt; color: #374151; }}
td.barcell {{ width: 30mm; }}
.bar {{ position: relative; height: 4mm; background: #eef2f3; border-radius: 1mm; }}
.bar span {{ position: absolute; left: 0; top: 0; bottom: 0; border-radius: 1mm; }}
.bar em {{ position: absolute; right: 1mm; top: -0.3mm; font-style: normal; font-size: 7.6pt; font-weight: 700; }}
.tag {{ font-style: normal; font-size: 6.5pt; font-weight: 400; padding: 0 1.2mm; border-radius: 1mm; margin-left: 0.8mm; vertical-align: 1px; }}
.tag.fr {{ background: #eceffd; color: #4253c9; }}
.tag.ad {{ background: #fdecec; color: #c0392b; }}
.foot {{ color: var(--muted); font-size: 7.5pt; margin-top: 3mm; }}
</style></head><body>

<section class="page">
  <h1>배달 상권·경쟁사 분석</h1>
  <div class="sub">청주 서원구 사창동 · 충북대 정문 인근 | 배달의민족 '주문 많은 순' 상위 {n}개 가게 | 2026-10-12 수집</div>
  <div class="kpis">
    <div class="kpi"><b>{n}</b><span>분석 가게 수</span></div>
    <div class="kpi"><b>{fmt(total_reviews)}</b><span>리뷰 합계</span></div>
    <div class="kpi"><b>{avg_rating:.2f}</b><span>평균 별점</span></div>
    <div class="kpi"><b>{fr / n:.0%}</b><span>프랜차이즈 비중 ({fr}곳)</span></div>
    <div class="kpi"><b>{near}</b><span>500m 이내 가게</span></div>
  </div>
  <table class="meta">
    <tr><td>기준 위치</td><td>청주시 서원구 사창동 · 충북대 정문 / 사창사거리 일대 (배민 배달주소 기준)</td></tr>
    <tr><td>수집 방법</td><td>배민 앱 음식배달 › 홈(전체 업종)을 '주문 많은 순'으로 정렬해 스크롤 캡처 6장 판독</td></tr>
    <tr><td>수집 항목</td><td>가게명, 별점, 리뷰 수, 예상 배달시간, 거리, 최소주문금액, 배달팁, 광고 여부</td></tr>
  </table>
  <h2>핵심 인사이트</h2>
  <ul class="ins">
    <li><b>마라탕·중식이 가장 큰 수요.</b> 7곳 리뷰 합계 {fmt(next(c['reviews'] for c in cats if c['name'] == '마라탕·중식'))}개로 1위이며,
      리뷰 1위 가게(하이 탠탠마라탕 충북대점, 6,699개)도 이 업종입니다. 다만 충북대 앞 500m 안에 3곳이 몰려 있어 경쟁이 가장 치열합니다.</li>
    <li><b>찜·탕(김치찜·감자탕·곱도리탕)은 '적은 가게, 높은 실적'.</b> 5곳뿐이지만 가게당 평균 리뷰 약 2,800개, 평균 별점 4.98로
      가게당 실적이 상위권입니다. 1인분 메뉴 + 최소주문 1만 원 안팎 구성이 주력입니다.</li>
    <li><b>분식·떡볶이는 11곳으로 많지만 가게당 리뷰는 평균 1,200개 수준.</b> 엽기떡볶이 등 프랜차이즈가 절반 이상이며,
      개인 매장(오떡상회 3,398 · 타코찡 3,521)이 오히려 리뷰가 많습니다.</li>
    <li><b>버거·패스트푸드와 치킨은 프랜차이즈 독점 구조.</b> 버거 12곳 중 11곳, 치킨 5곳 중 4곳이 프랜차이즈이고 가게당 리뷰도 낮아
      개인 창업 진입 매력은 낮습니다.</li>
    <li><b>별점은 변별력이 없음.</b> 거의 모든 가게가 4.8~5.0입니다. 경쟁력 비교는 <b>리뷰 수와 주문순위</b>로 보는 것이 맞습니다.</li>
    <li><b>배달팁 0원이 기본값.</b> 가게배달 일부를 제외하면 사실상 전부 배민클럽 배달팁 0원이며, 상위 가게 대부분이 1,000~6,000원 즉시할인을 함께 걸고 있습니다.</li>
  </ul>
  <div class="note">
    <p>※ 배민 목록에는 '최근 주문 수'가 표시되지 않습니다. <b>주문순위</b>는 배민 '주문 많은 순' 정렬 순서로, 주문량의 상대 지표입니다.</p>
    <p>※ 정렬에는 거리·광고가 함께 반영되어 실제 주문수와 완전히 일치하지 않으며, 리뷰 수는 누적값이라 업력이 긴 가게에 유리합니다.</p>
    <p>※ 캡처 경계에서 가게 1~2곳이 누락되었을 수 있습니다 (22위 가게명 일부 잘림, 54~55위 사이 치킨집 1곳 확인 불가).</p>
  </div>
</section>

<section class="page">
  <h2>업종별 경쟁 현황</h2>
  <table>
    <thead><tr><th>업종</th><th>가게</th><th>리뷰 합계</th><th>가게당 평균 리뷰</th><th>평균 별점</th><th>평균 최소주문</th><th>500m 내</th><th>프랜차이즈</th><th>주문순위 1위 가게</th></tr></thead>
    <tbody>{cat_rows}</tbody>
  </table>
  <h3>거리 구간별 분포</h3>
  <table>
    <thead><tr><th>거리</th><th>가게</th><th>리뷰 합계</th><th>가게 (주문순)</th></tr></thead>
    <tbody>{band_rows}</tbody>
  </table>
  <h3>창업 관점 시사점</h3>
  <ul class="ins">
    <li><b>수요 검증된 블루오션 후보: 찜·탕 / 족발·닭발 / 덮밥.</b> 가게 수 대비 가게당 리뷰가 높고 프랜차이즈 비중이 0%입니다.</li>
    <li><b>마라탕은 수요는 최대지만 레드오션.</b> 진입한다면 가격·용량(1인 세트) 또는 배달시간으로 차별화가 필요합니다.</li>
    <li><b>근거리 경쟁:</b> 500m 안에 {near}곳이 있으며 배달시간이 대부분 20~30분대입니다. 같은 입지에서는 '빠른 도착'이 기본 조건입니다.</li>
    <li><b>가격 기준선:</b> 1인 메뉴 1만~1.2만 원, 최소주문 5,000~14,000원, 배달팁 0원 + 즉시할인이 상위권 가게의 공통 패턴입니다.</li>
  </ul>
</section>

<section class="page">
  <h2>리뷰 수 TOP 20</h2>
  {top20}
  <div class="foot">주문 = 배민 '주문 많은 순' 순위, 리뷰 = 리뷰 수 순위. 막대는 최다 리뷰(6,699개) 대비 비율.</div>
</section>

<section class="page">
  <h2>전체 가게 목록 (주문 많은 순 1~32위)</h2>
  {all1}
</section>
<section class="page">
  <h2>전체 가게 목록 (주문 많은 순 33~{n}위)</h2>
  {all2}
  <div class="foot">데이터: 배달의민족 앱 화면 캡처(2026-10-12 18:54~18:55) 수기 판독. 22위는 가게명 일부가 잘려 추정값이며 상세정보 미확인.</div>
</section>
</body></html>"""


def main():
    stores = load(SRC)
    with tempfile.NamedTemporaryFile("w", suffix=".html", delete=False, encoding="utf-8") as f:
        f.write(build_html(stores))
        html_path = f.name
    subprocess.run([CHROMIUM, "--headless", "--no-sandbox", "--disable-gpu",
                    "--allow-file-access-from-files", "--no-pdf-header-footer",
                    f"--print-to-pdf={os.path.abspath(OUT)}", f"file://{html_path}"],
                   check=True, capture_output=True)
    print("saved", OUT)


if __name__ == "__main__":
    main()
