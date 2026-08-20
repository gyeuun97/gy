"""양쪽에서 모은 상품을 걸러내고 원/L 기준으로 줄세운다."""

from typing import Iterable, List, Optional, Sequence

from .models import Offer

# "생수"로 검색해도 딸려오는 물이 아닌 상품들
DEFAULT_EXCLUDE = (
    "정수기", "필터", "텀블러", "물통", "보온병", "케이스", "거치대",
    "받침대", "카트", "펌프", "디스펜서", "수건", "티슈", "사료",
)


def _is_noise(title: str, exclude: Sequence[str]) -> bool:
    lowered = title.lower()
    return any(word.lower() in lowered for word in exclude)


def prepare(
    offers: Iterable[Offer],
    exclude: Sequence[str] = DEFAULT_EXCLUDE,
    min_liters: float = 1.0,
    include_unknown: bool = False,
) -> List[Offer]:
    """원/L을 계산하고, 물이 아닌 상품과 용량 미상 상품을 걸러낸다."""
    prepared = []
    for offer in offers:
        if _is_noise(offer.title, exclude):
            continue
        priced = offer.with_unit_price()
        if priced.unit_price is None:
            if include_unknown:
                prepared.append(priced)
            continue
        if priced.liters is not None and priced.liters < min_liters:
            continue
        prepared.append(priced)
    return prepared


def rank(offers: Iterable[Offer], by: str = "unit") -> List[Offer]:
    """원/L(기본) 또는 표시가 기준 오름차순 정렬. 값이 없는 항목은 뒤로."""
    if by == "price":
        return sorted(offers, key=lambda o: o.price)

    def key(offer: Offer):
        return (offer.unit_price is None, offer.unit_price or 0, offer.price)

    return sorted(offers, key=key)


def cheapest(offers: Sequence[Offer], source: str) -> Optional[Offer]:
    """특정 쇼핑몰의 최저 원/L 상품."""
    candidates = [o for o in offers if o.source == source and o.unit_price is not None]
    return min(candidates, key=lambda o: o.unit_price) if candidates else None
