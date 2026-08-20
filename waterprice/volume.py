"""상품명에서 총 용량(L)을 뽑아낸다.

생수는 "삼다수 2L 12병", "500ml 40페트" 처럼 낱개 용량과 수량이 따로 적힌다.
표시가격만 보면 2L 6개와 500ml 40개를 비교할 수 없으므로,
낱개 용량 × 수량(들)을 곱해 총 리터를 구하고 원/L로 환산한다.
"""

import re
from typing import List, Optional

# 낱개 용량: "2L", "1.5리터", "500ml", "500 mL"
_VOLUME_RE = re.compile(
    r"(?<![\d.])(\d+(?:[.,]\d+)?)\s*(ml|mL|ML|밀리리터|미리|l|L|ℓ|리터|리뜰)(?![a-zA-Z가-힣])"
)

# 수량: "12병", "24개입", "x24", "*6", "40펫", "2박스"
_COUNT_UNIT = r"개입|개|입|병|팩|펫|페트|pet|PET|ea|EA|캔|박스|BOX|box|묶음|줄"
_COUNT_RE = re.compile(rf"(?<![\d.])(\d+)\s*(?:{_COUNT_UNIT})(?![a-zA-Z])")
_MULT_RE = re.compile(r"[xX×*]\s*(\d+)(?![\d.])")

# "24개월", "1+1" 같은 오인식 방지용
_MONTH_RE = re.compile(r"\d+\s*개월")

_ML_UNITS = {"ml", "mL", "ML", "밀리리터", "미리"}

# 낱개 용량으로 인정할 범위 (L). 생수 한 병은 0.1L~20L 사이로 본다.
_MIN_UNIT_L = 0.1
_MAX_UNIT_L = 20.0
# 한 상품의 수량 상한. 이보다 크면 수량이 아니라 다른 숫자로 본다.
_MAX_COUNT = 200


def _to_liters(number: str, unit: str) -> Optional[float]:
    value = float(number.replace(",", "."))
    if unit in _ML_UNITS:
        value /= 1000.0
    if not (_MIN_UNIT_L <= value <= _MAX_UNIT_L):
        return None
    return value


def parse_unit_liters(title: str) -> Optional[float]:
    """낱개 용량(L)만 파싱한다. 첫 번째로 나오는 유효한 용량을 쓴다."""
    for number, unit in _VOLUME_RE.findall(title):
        liters = _to_liters(number, unit)
        if liters is not None:
            return liters
    return None


def parse_counts(title: str) -> List[int]:
    """수량으로 볼 수 있는 숫자들을 모두 뽑는다. ("2L 6개 x 2박스" -> [6, 2])"""
    cleaned = _MONTH_RE.sub(" ", title)
    counts = [int(n) for n in _COUNT_RE.findall(cleaned)]
    counts += [int(n) for n in _MULT_RE.findall(cleaned)]
    return [c for c in counts if 1 < c <= _MAX_COUNT]


def parse_liters(title: str) -> Optional[float]:
    """총 용량(L)을 돌려준다. 용량을 못 찾으면 None."""
    if not title:
        return None
    unit_liters = parse_unit_liters(title)
    if unit_liters is None:
        return None

    total = unit_liters
    for count in _dedupe(parse_counts(title)):
        total *= count
    return round(total, 4)


def _dedupe(counts: List[int]) -> List[int]:
    """'2L 24개입 x24' 처럼 같은 수량이 두 번 표기된 경우 한 번만 곱한다."""
    seen = set()
    result = []
    for c in counts:
        if c not in seen:
            seen.add(c)
            result.append(c)
    return result
