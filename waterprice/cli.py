"""쿠팡 / 네이버 생수 최저가 비교 CLI."""

import argparse
import csv
import json
import sys
import unicodedata
from typing import List, Tuple

from . import coupang, naver
from .compare import DEFAULT_EXCLUDE, cheapest, prepare, rank
from .http import FetchError
from .models import Offer

SOURCES = {"coupang": coupang.search, "naver": naver.search}


def collect(query: str, limit: int, sources: List[str]) -> Tuple[List[Offer], List[str]]:
    """각 쇼핑몰에서 상품을 모은다. 한쪽이 실패해도 나머지는 살린다."""
    offers: List[Offer] = []
    errors: List[str] = []
    for name in sources:
        try:
            found = SOURCES[name](query, limit=limit)
        except FetchError as exc:
            errors.append(f"{name}: {exc}")
            continue
        if not found:
            errors.append(f"{name}: 검색 결과가 없습니다.")
        offers.extend(found)
    return offers, errors


def _display_width(text: str) -> int:
    """한글·한자처럼 두 칸을 차지하는 문자를 감안한 출력 폭."""
    return sum(2 if unicodedata.east_asian_width(ch) in "WF" else 1 for ch in text)


def _truncate(text: str, width: int) -> str:
    """출력 폭 기준으로 자른다."""
    if _display_width(text) <= width:
        return text
    out = ""
    used = 0
    for ch in text:
        step = 2 if unicodedata.east_asian_width(ch) in "WF" else 1
        if used + step > width - 1:
            break
        out += ch
        used += step
    return out + "…"


def _ljust(text: str, width: int) -> str:
    return text + " " * max(0, width - _display_width(text))


def _rjust(text: str, width: int) -> str:
    return " " * max(0, width - _display_width(text)) + text


def format_table(offers: List[Offer], top: int) -> str:
    rows = offers[:top]
    if not rows:
        return "표시할 상품이 없습니다."

    header = (
        f"{'#':>2}  {_ljust('몰', 14)} {_rjust('원/L', 8)}  "
        f"{_rjust('가격', 10)}  {_rjust('용량', 8)}  상품명"
    )
    lines = [header, "-" * 90]
    for index, offer in enumerate(rows, start=1):
        unit = f"{offer.unit_price:,.0f}" if offer.unit_price is not None else "-"
        liters = f"{offer.liters:g}L" if offer.liters is not None else "-"
        lines.append(
            f"{index:>2}  {_ljust(_truncate(offer.mall, 14), 14)} {unit:>8}  "
            f"{offer.price:>10,}  {liters:>8}  {_truncate(offer.title, 50)}"
        )
    return "\n".join(lines)


def format_summary(offers: List[Offer]) -> str:
    best_coupang = cheapest(offers, "coupang")
    best_naver = cheapest(offers, "naver")
    if not best_coupang or not best_naver:
        only = best_coupang or best_naver
        if not only:
            return ""
        return f"\n[요약] {only.mall} 만 조회됨 — 최저 {only.unit_price:,.0f}원/L"

    winner, loser = (
        (best_coupang, best_naver)
        if best_coupang.unit_price <= best_naver.unit_price
        else (best_naver, best_coupang)
    )
    gap = loser.unit_price - winner.unit_price
    percent = gap / loser.unit_price * 100
    return (
        f"\n[요약] 쿠팡 최저 {best_coupang.unit_price:,.0f}원/L · "
        f"네이버 최저 {best_naver.unit_price:,.0f}원/L\n"
        f"       → {winner.mall} 승 ({gap:,.0f}원/L, {percent:.1f}% 저렴)\n"
        f"       {_truncate(winner.title, 60)}\n"
        f"       {winner.url}"
    )


def write_csv(offers: List[Offer], stream) -> None:
    writer = csv.writer(stream)
    writer.writerow(["source", "mall", "unit_price_per_l", "price", "liters", "title", "url"])
    for offer in offers:
        writer.writerow(
            [offer.source, offer.mall, offer.unit_price, offer.price,
             offer.liters, offer.title, offer.url]
        )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="waterprice",
        description="쿠팡과 네이버쇼핑에서 생수를 검색해 원/L 기준 최저가로 정렬합니다.",
    )
    parser.add_argument("query", nargs="?", default="생수", help="검색어 (기본: 생수)")
    parser.add_argument("--limit", type=int, default=50, help="쇼핑몰당 조회 개수 (기본: 50)")
    parser.add_argument("--top", type=int, default=15, help="출력할 상위 개수 (기본: 15)")
    parser.add_argument(
        "--source", action="append", choices=sorted(SOURCES),
        help="조회할 쇼핑몰. 여러 번 지정 가능 (기본: 둘 다)",
    )
    parser.add_argument(
        "--sort", choices=("unit", "price"), default="unit",
        help="정렬 기준: unit=원/L(기본), price=표시가",
    )
    parser.add_argument("--min-liters", type=float, default=1.0, help="최소 총 용량 L (기본: 1)")
    parser.add_argument(
        "--include-unknown", action="store_true", help="용량을 못 읽은 상품도 포함",
    )
    parser.add_argument(
        "--exclude", action="append", default=None,
        help=f"제외 키워드. 기본값: {', '.join(DEFAULT_EXCLUDE)}",
    )
    parser.add_argument("--json", action="store_true", help="JSON으로 출력")
    parser.add_argument("--csv", action="store_true", help="CSV로 출력")
    return parser


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)
    sources = args.source or sorted(SOURCES)
    exclude = args.exclude if args.exclude is not None else list(DEFAULT_EXCLUDE)

    raw, errors = collect(args.query, args.limit, sources)
    for error in errors:
        print(f"[경고] {error}", file=sys.stderr)

    if not raw:
        print("조회된 상품이 없습니다.", file=sys.stderr)
        return 1

    ranked = rank(
        prepare(raw, exclude=exclude, min_liters=args.min_liters,
                include_unknown=args.include_unknown),
        by=args.sort,
    )

    if args.json:
        print(json.dumps([o.to_dict() for o in ranked[: args.top]],
                         ensure_ascii=False, indent=2))
        return 0
    if args.csv:
        write_csv(ranked[: args.top], sys.stdout)
        return 0

    print(f"검색어: {args.query}  ·  수집 {len(raw)}건 → 비교 대상 {len(ranked)}건")
    print(format_table(ranked, args.top))
    summary = format_summary(ranked)
    if summary:
        print(summary)
    return 0
