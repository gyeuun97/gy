#!/usr/bin/env python3
"""네이버 블로그를 검색해 업체 요금 언급을 추출한다.

요금을 홈페이지에 공개하지 않는 로컬 업체는 공식 블로그나 이용 후기에
가격이 적혀 있는 경우가 많다. 네이버 블로그 검색 → 본문 수집 →
"N만원 / N,NNN원 / N평" 패턴 주변 문장을 뽑아 사람이 검토할 근거를 만든다.

주의: 블로그는 1차 출처가 아니다. 여기서 나온 숫자는 '확인 대상'일 뿐이며,
확정 단가는 업체 전화 확인이 필요하다.

사용법:
    python3 tools/naver_blog_price.py "박스호텔 공유창고 청주 요금"
    python3 tools/naver_blog_price.py --posts 8 --must 옐로박스,청주 "옐로박스 청주 공유창고 가격"
"""
import argparse
import re
import subprocess
import sys
import urllib.parse

UA = ("Mozilla/5.0 (Linux; Android 13) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/120 Mobile Safari/537.36")

# "10만원", "120,000원", "월 15만", "0.8평" 같은 표현 주변을 문맥째로 집는다
PRICE_RE = re.compile(
    r"[^。.\n]{0,60}?(?:[0-9]{1,3}(?:,[0-9]{3})+\s*원|[0-9]{1,4}\s*만\s*원?|"
    r"[0-9]+(?:\.[0-9]+)?\s*평)[^。.\n]{0,60}")
NOISE = re.compile(r"이웃추가|공감|댓글|블로그|카테고리|폰트|신고하기|URL복사")


def get(url: str) -> str:
    out = subprocess.run(["curl", "-sS", "-m", "25", "-A", UA, url],
                         capture_output=True, text=True, errors="replace")
    return out.stdout if out.returncode == 0 else ""


def search_posts(query: str, limit: int) -> list:
    url = ("https://m.search.naver.com/search.naver?ssc=tab.m_blog.all&query="
           + urllib.parse.quote(query))
    page = get(url)
    urls = re.findall(r"https://(?:m\.)?blog\.naver\.com/[A-Za-z0-9_-]+/\d{9,}", page)
    normalized = ["https://m." + u.split("://", 1)[1].removeprefix("m.")
                  for u in dict.fromkeys(urls)]
    return normalized[:limit]


def post_text(url: str) -> str:
    body = get(url)
    if not body:
        return ""
    body = re.sub(r"<script.*?</script>", " ", body, flags=re.S)
    body = re.sub(r"<style.*?</style>", " ", body, flags=re.S)
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", body))


def main():
    ap = argparse.ArgumentParser(description="네이버 블로그 요금 언급 추출")
    ap.add_argument("query")
    ap.add_argument("--posts", type=int, default=6, help="확인할 포스트 수")
    ap.add_argument("--must", default="",
                    help="본문에 반드시 포함되어야 할 문자열(쉼표 구분). 무관한 포스트를 걸러낸다")
    args = ap.parse_args()

    posts = search_posts(args.query, args.posts)
    print(f"[검색] '{args.query}' → 포스트 {len(posts)}건\n", file=sys.stderr)
    if not posts:
        print("검색 결과 없음", file=sys.stderr)
        return

    for url in posts:
        text = post_text(url)
        if not text:
            continue
        musts = [t.strip() for t in args.must.split(",") if t.strip()]
        if musts and not all(t in text for t in musts):
            continue
        title = text[:90].strip()
        hits = []
        for m in PRICE_RE.findall(text):
            snippet = m.strip()
            if NOISE.search(snippet) or snippet in hits:
                continue
            hits.append(snippet)
        if not hits:
            continue
        print(f"── {url}\n   {title}")
        for h in hits[:8]:
            print(f"   · {h}")
        print()


if __name__ == "__main__":
    main()
