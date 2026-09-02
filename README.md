# 청주 공유창고 단가 조사

청주시 소재 공유창고(셀프스토리지·무인창고·컨테이너 보관창고) 업체 리스트업 및 단가 조사 자료입니다.

| 문서 | 내용 |
|------|------|
| [research/cheongju-shared-warehouse-vendors.md](research/cheongju-shared-warehouse-vendors.md) | 업체 16곳 · 규격별 단가 · 용도별 추천 · 손익분기 · 전화조사 스크립트 |
| [research/web-research-method.md](research/web-research-method.md) | 국내 로컬 업체를 Claude Code로 조사하는 방법론 (검증된 수집 경로/차단 경로) |
| [data/cheongju_storage_vendors.csv](data/cheongju_storage_vendors.csv) | 업체·주소·연락처·요금공개여부 |
| [data/cheongju_storage_prices.csv](data/cheongju_storage_prices.csv) | 규격별 단가 (치수·부피·㎥당 단가 포함) |
| [tools/](tools/) | 네이버 플레이스 수집 · 브랜드 요금표 크롤러 · 블로그 요금 추출 |

## 요약 (2026-09-02 기준)

- 청주 소재 **16곳** (흥덕구 8 · 청원구 4 · 서원구 4)
- 요금 공개는 **4곳**(알파박스 2, 아이엠박스 1, 옐로박스 1), 나머지 12곳은 전화 확인 필요
- 가격 밴드: **57,000원**(옐로박스 S, 1㎥) ~ **410,000원**(아이엠박스 OS 정상가)
- 최저 실질단가: 옐로박스 S 12개월 일시불 **월 36,000원**
- 부피당 단가: **10,397원/㎥**(알파박스 A01) ~ **57,000원/㎥**(옐로박스 S) — 최대 5.5배 차이
- 대전 동일 브랜드 대비 **평균 약 15% 저렴**
- 일반 상온 물류창고(평당 월 3.2~3.3만원)의 2.5~6배 → **10평 이상이면 일반 창고 임대가 유리**

## 조사 도구

```bash
python3 tools/naver_place_search.py --csv data/places.csv "청주 공유창고" "청주 셀프스토리지"
python3 tools/storage_price_crawl.py alphabox --max 40 --filter 청주
python3 tools/naver_blog_price.py --posts 6 --must 옐로박스,청주 "옐로박스 청주 이용요금"
```

> Claude Code 기본 WebSearch는 구글/US 기반이라 네이버 플레이스 전용 등록 업체를 놓칩니다.
> 이 조사에서도 기본 검색으로는 16곳 중 3곳만 나왔습니다. 자세한 내용은 [방법론 문서](research/web-research-method.md) 참조.
