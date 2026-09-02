#!/usr/bin/env python3
"""셀프스토리지 브랜드 공식 사이트에서 지점별 요금표를 수집한다.

브랜드 사이트는 지점 페이지가 연속된 정수 ID로 노출되는 경우가 많아
(alphabox.co.kr/store_N, iambox.co.kr/...?office_idx=N) ID를 훑으면
검색엔진에 안 걸리는 지점까지 전수 수집할 수 있다.

사용법:
    python3 tools/storage_price_crawl.py alphabox --max 40 --filter 청주
    python3 tools/storage_price_crawl.py iambox --max 260 --filter 청주 --csv out.csv
"""
import argparse
import csv
import re
import subprocess
import sys

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/120 Safari/537.36")

SITES = {
    "alphabox": "https://alphabox.co.kr/store_{}",
    "iambox": "https://www.iambox.co.kr/sub/selfStorage/storage_view.php?office_idx={}",
}

FIELDS = ["brand", "page_id", "branch", "address", "size_code",
          "dimensions", "area", "monthly_fee", "deposit", "url"]


def get(url: str) -> str:
    out = subprocess.run(["curl", "-sS", "-m", "20", "-A", UA, url],
                         capture_output=True, text=True, errors="replace")
    return out.stdout if out.returncode == 0 else ""


def strip_tags(fragment: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", fragment)).strip()


def parse_alphabox(page: str) -> tuple:
    """알파박스: <table>에 구분/사이즈/면적/표준가격/보증금 컬럼이 있다."""
    branch = ""
    m = re.search(r"(알파박스\s*[가-힣]+점)", page)
    if m:
        branch = m.group(1).replace(" ", "")
    address = ""
    # 메타 설명문에 걸리지 않도록 "시/군 + 도로명·지번"이 이어지는 형태만 주소로 본다
    m = re.search(r"((?:충북|충남|경북|경남|전북|전남|강원|제주|서울|경기|부산|대구|"
                  r"인천|광주|대전|울산|세종)\s*[가-힣]+[시군][^<>\n]{5,45})", page)
    if m:
        address = re.sub(r"\s+", " ", m.group(1)).strip()

    rows = []
    for tr in re.findall(r"<tr[^>]*>(.*?)</tr>", page, re.S):
        cells = [strip_tags(td) for td in re.findall(r"<td[^>]*>(.*?)</td>", tr, re.S)]
        # 구분 / 사이즈 / 면적 / 표준가격 / 보증금 / (우체국 박스 환산)
        if len(cells) >= 5 and re.match(r"^[A-Z]\d+$", cells[0]) and "평" in cells[2]:
            rows.append({
                "size_code": cells[0],
                "dimensions": cells[1],
                "area": cells[2],
                "monthly_fee": cells[3].replace(",", ""),
                "deposit": cells[4].replace(",", ""),
            })
    return branch, address, rows


def parse_iambox(page: str) -> tuple:
    """아이엠박스: 사이즈 라벨과 정상가/할인가가 쌍으로 나열된다."""
    branch = ""
    m = re.search(r"([가-힣]+(?:점|호점))", page)
    if m:
        branch = m.group(1)
    address = ""
    m = re.search(r"(충[북청][^<>\n]{5,50})", page)
    if m:
        address = m.group(1).strip()

    prices = re.findall(r"([0-9]{1,3}(?:,[0-9]{3})+)\s*원", page)
    sizes = re.findall(r">\s*(XS|S|M\+|M|L|XL|XXL|OS)\s*<", page)
    rows = []
    # 정상가/할인가가 번갈아 나오는 구조 → 2개씩 묶어 사이즈에 대응시킨다
    for idx, size in enumerate(dict.fromkeys(sizes)):
        pair = prices[idx * 2:idx * 2 + 2]
        if not pair:
            break
        rows.append({
            "size_code": size,
            "dimensions": "",
            "area": "",
            "monthly_fee": pair[0].replace(",", ""),
            "deposit": pair[1].replace(",", "") if len(pair) > 1 else "",
        })
    return branch, address, rows


PARSERS = {"alphabox": parse_alphabox, "iambox": parse_iambox}


def main():
    ap = argparse.ArgumentParser(description="셀프스토리지 지점 요금표 수집")
    ap.add_argument("brand", choices=sorted(SITES))
    ap.add_argument("--max", type=int, default=40, help="훑을 지점 ID 상한")
    ap.add_argument("--filter", default="", help="주소/지점명에 포함되어야 할 문자열")
    ap.add_argument("--csv", help="결과 CSV 경로")
    args = ap.parse_args()

    template, parse = SITES[args.brand], PARSERS[args.brand]
    out = []
    for page_id in range(1, args.max + 1):
        url = template.format(page_id)
        page = get(url)
        if not page:
            continue
        branch, address, rows = parse(page)
        if not rows:
            continue
        if args.filter and args.filter not in (branch + address + page[:6000]):
            continue
        print(f"[{args.brand} #{page_id}] {branch} / {address} / {len(rows)}개 규격",
              file=sys.stderr)
        for row in rows:
            out.append({"brand": args.brand, "page_id": page_id, "branch": branch,
                        "address": address, "url": url, **row})

    if args.csv:
        with open(args.csv, "w", newline="", encoding="utf-8-sig") as fh:
            w = csv.DictWriter(fh, fieldnames=FIELDS)
            w.writeheader()
            w.writerows(out)
        print(f"\n총 {len(out)}행 → {args.csv}", file=sys.stderr)
    else:
        for r in out:
            print(f"{r['branch']:<16} {r['size_code']:<5} {r['area']:<7} "
                  f"{r['monthly_fee']:>8} / 보증금 {r['deposit']:>8}")


if __name__ == "__main__":
    main()
