"""비교 결과를 담는 자료구조."""

from dataclasses import dataclass, asdict
from typing import Optional


@dataclass
class Offer:
    """검색된 상품 하나."""

    source: str          # "coupang" | "naver"
    title: str
    price: int           # 표시가 (원)
    mall: str = ""       # 판매처 (네이버는 몰 이름, 쿠팡은 "쿠팡")
    url: str = ""
    product_id: str = ""
    liters: Optional[float] = None       # 파싱된 총 용량 (L)
    unit_price: Optional[float] = None   # 원/L

    def with_unit_price(self) -> "Offer":
        """총 용량을 파싱해 원/L을 채운 새 Offer를 돌려준다."""
        from .volume import parse_liters

        liters = parse_liters(self.title)
        unit = round(self.price / liters, 1) if liters else None
        return Offer(
            source=self.source,
            title=self.title,
            price=self.price,
            mall=self.mall,
            url=self.url,
            product_id=self.product_id,
            liters=liters,
            unit_price=unit,
        )

    def to_dict(self) -> dict:
        return asdict(self)
