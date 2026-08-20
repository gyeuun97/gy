"""쿠팡 상품 검색 (쿠팡 파트너스 Open API).

https://partners.coupang.com  →  로그인 후 [내 정보 > API 키 발급]
COUPANG_ACCESS_KEY / COUPANG_SECRET_KEY 환경변수가 필요하다.

쿠팡은 웹 검색 페이지를 크롤링하면 403으로 막는다. 파트너스 API가
공식적으로 열려 있는 유일한 경로라 그쪽만 사용한다.
"""

import hashlib
import hmac
import os
import time
import urllib.parse
from typing import List

from .http import FetchError, get_json
from .models import Offer

HOST = "https://api-gateway.coupang.com"
PATH = "/v2/providers/affiliate_open_api/apis/openapi/v1/products/search"
MAX_LIMIT = 100


def _authorization(method: str, path: str, query: str, access_key: str, secret_key: str) -> str:
    """쿠팡 파트너스의 HMAC(CEA) 서명 헤더를 만든다."""
    signed_date = time.strftime("%y%m%dT%H%M%SZ", time.gmtime())
    message = signed_date + method + path + query
    signature = hmac.new(
        secret_key.encode("utf-8"), message.encode("utf-8"), hashlib.sha256
    ).hexdigest()
    return (
        f"CEA algorithm=HmacSHA256, access-key={access_key}, "
        f"signed-date={signed_date}, signature={signature}"
    )


def search(query: str, limit: int = 30) -> List[Offer]:
    access_key = os.environ.get("COUPANG_ACCESS_KEY")
    secret_key = os.environ.get("COUPANG_SECRET_KEY")
    if not access_key or not secret_key:
        raise FetchError(
            "COUPANG_ACCESS_KEY / COUPANG_SECRET_KEY 가 설정되지 않았습니다. "
            "쿠팡 파트너스(https://partners.coupang.com)에서 API 키를 발급받으세요."
        )

    request_query = urllib.parse.urlencode(
        {"keyword": query, "limit": min(limit, MAX_LIMIT)}
    )
    payload = get_json(
        f"{HOST}{PATH}?{request_query}",
        headers={
            "Authorization": _authorization("GET", PATH, request_query, access_key, secret_key),
            "Content-Type": "application/json;charset=UTF-8",
        },
    )

    data = payload.get("data") or {}
    products = data.get("productData") or []

    offers = []
    for item in products:
        try:
            price = int(item.get("productPrice") or 0)
        except (TypeError, ValueError):
            continue
        if price <= 0:
            continue
        offers.append(
            Offer(
                source="coupang",
                title=(item.get("productName") or "").strip(),
                price=price,
                mall="쿠팡",
                url=item.get("productUrl", ""),
                product_id=str(item.get("productId", "")),
            )
        )
    return offers
