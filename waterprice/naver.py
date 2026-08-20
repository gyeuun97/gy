"""네이버 쇼핑 검색 (네이버 개발자센터 검색 API).

https://developers.naver.com/docs/serviceapi/search/shopping/shopping.md
NAVER_CLIENT_ID / NAVER_CLIENT_SECRET 환경변수가 필요하다.
"""

import os
import re
import urllib.parse
from typing import List

from .http import FetchError, get_json
from .models import Offer

ENDPOINT = "https://openapi.naver.com/v1/search/shop.json"
MAX_DISPLAY = 100

_TAG_RE = re.compile(r"</?b>")


def _clean(title: str) -> str:
    return urllib.parse.unquote(_TAG_RE.sub("", title)).strip()


def search(query: str, limit: int = 30) -> List[Offer]:
    client_id = os.environ.get("NAVER_CLIENT_ID")
    client_secret = os.environ.get("NAVER_CLIENT_SECRET")
    if not client_id or not client_secret:
        raise FetchError(
            "NAVER_CLIENT_ID / NAVER_CLIENT_SECRET 가 설정되지 않았습니다. "
            "https://developers.naver.com 에서 애플리케이션을 등록하고 '검색' API를 추가하세요."
        )

    params = urllib.parse.urlencode(
        {"query": query, "display": min(limit, MAX_DISPLAY), "sort": "asc"}
    )
    payload = get_json(
        f"{ENDPOINT}?{params}",
        headers={
            "X-Naver-Client-Id": client_id,
            "X-Naver-Client-Secret": client_secret,
        },
    )

    offers = []
    for item in payload.get("items", []):
        try:
            price = int(item.get("lprice") or 0)
        except (TypeError, ValueError):
            continue
        if price <= 0:
            continue
        offers.append(
            Offer(
                source="naver",
                title=_clean(item.get("title", "")),
                price=price,
                mall=item.get("mallName", "") or "네이버쇼핑",
                url=item.get("link", ""),
                product_id=str(item.get("productId", "")),
            )
        )
    return offers
