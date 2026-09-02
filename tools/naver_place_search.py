#!/usr/bin/env python3
"""네이버 모바일 검색에서 로컬 업체(플레이스) 정보를 수집한다.

Claude Code의 WebSearch는 구글/미국 기반이라 네이버 플레이스에만 등록된
국내 로컬 업체를 대부분 놓친다. 이 스크립트는 m.search.naver.com이 페이지에
심어두는 __APOLLO_STATE__ JSON에서 업체 목록을 직접 파싱한다.

사용법:
    python3 tools/naver_place_search.py "청주 공유창고" "청주 셀프스토리지"
    python3 tools/naver_place_search.py --csv out.csv "청주 공유창고"
"""
import argparse
import csv
import json
import re
import subprocess
import sys
import urllib.parse

UA = ("Mozilla/5.0 (Linux; Android 13) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/120 Mobile Safari/537.36")

FIELDS = ["query", "name", "category", "fullAddress", "roadAddress",
          "phone", "businessHours", "x", "y", "id"]


def fetch(query: str) -> str:
    url = ("https://m.search.naver.com/search.naver?query="
           + urllib.parse.quote(query))
    out = subprocess.run(
        ["curl", "-sS", "-m", "40", "-A", UA, url],
        capture_output=True, text=True, errors="replace",
    )
    if out.returncode != 0:
        raise RuntimeError(f"curl 실패({out.returncode}): {out.stderr[:200]}")
    return out.stdout


def extract_apollo(page: str) -> dict:
    """__APOLLO_STATE__ = {...}; 에서 JSON 객체만 중괄호 균형으로 잘라낸다."""
    marker = "__APOLLO_STATE__ = "
    start = page.find(marker)
    if start == -1:
        return {}
    start += len(marker)
    depth, in_str, esc = 0, False, False
    for i, ch in enumerate(page[start:], start):
        if in_str:
            if esc:
                esc = False
            elif ch == "\\":
                esc = True
            elif ch == '"':
                in_str = False
            continue
        if ch == '"':
            in_str = True
        elif ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                try:
                    return json.loads(page[start:i + 1])
                except json.JSONDecodeError as e:
                    print(f"  [warn] JSON 파싱 실패: {e}", file=sys.stderr)
                    return {}
    return {}


def clean(value):
    """네이버가 검색어 강조로 넣는 <mark> 태그와 이스케이프를 제거한다."""
    if not isinstance(value, str):
        return "" if value is None else value
    value = value.replace("\\u002F", "/").replace("\\u003C", "<").replace("\\u003E", ">")
    return re.sub(r"</?mark>", "", value).strip()


def collect(query: str) -> list:
    state = extract_apollo(fetch(query))
    rows = []
    for key, item in state.items():
        if not key.startswith("PlaceListBusinessesItem"):
            continue
        rows.append({
            "query": query,
            "name": clean(item.get("normalizedName") or item.get("name")),
            "category": clean(item.get("category")),
            "fullAddress": clean(item.get("fullAddress")),
            "roadAddress": clean(item.get("roadAddress")),
            "phone": clean(item.get("phone") or item.get("virtualPhone")),
            "businessHours": clean(item.get("businessHours")),
            "x": clean(item.get("x")),
            "y": clean(item.get("y")),
            "id": clean(item.get("id")),
        })
    return rows


def main():
    ap = argparse.ArgumentParser(description="네이버 플레이스 로컬 업체 수집")
    ap.add_argument("queries", nargs="+", help="검색어 (여러 개 가능)")
    ap.add_argument("--csv", help="결과를 저장할 CSV 경로")
    args = ap.parse_args()

    seen, rows = set(), []
    for query in args.queries:
        found = collect(query)
        new = 0
        for row in found:
            key = row["id"] or (row["name"], row["fullAddress"])
            if key in seen:
                continue
            seen.add(key)
            rows.append(row)
            new += 1
        print(f"[{query}] {len(found)}건 수집, 신규 {new}건", file=sys.stderr)

    if args.csv:
        with open(args.csv, "w", newline="", encoding="utf-8-sig") as fh:
            writer = csv.DictWriter(fh, fieldnames=FIELDS)
            writer.writeheader()
            writer.writerows(rows)
        print(f"\n총 {len(rows)}건 → {args.csv}", file=sys.stderr)
    else:
        for row in rows:
            print(f"{row['name']} | {row['category']} | {row['fullAddress']} | {row['phone']}")


if __name__ == "__main__":
    main()
