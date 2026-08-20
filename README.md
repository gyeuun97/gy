# waterprice — 쿠팡 · 네이버 생수 최저가 비교

생수는 `2L × 6병`, `500ml × 40개`처럼 묶음으로 팔려서 **표시가격만으로는 비교가 안 된다.**
이 도구는 상품명에서 낱개 용량과 수량을 파싱해 총 리터를 구하고, **원/L 기준으로 줄세운다.**

## 설치

의존성 없음. Python 3.8+ 만 있으면 된다.

```bash
git clone https://github.com/gyeuun97/gy.git && cd gy
```

## API 키 설정 (필수)

두 사이트 모두 검색 페이지를 직접 크롤링하면 봇으로 차단된다
(쿠팡 `403`, 네이버쇼핑 `418`). 그래서 각자의 공식 API를 쓴다.

| 쇼핑몰 | 발급처 | 환경변수 |
| --- | --- | --- |
| 네이버 | [developers.naver.com](https://developers.naver.com) → 애플리케이션 등록 → **검색** API 추가 | `NAVER_CLIENT_ID`, `NAVER_CLIENT_SECRET` |
| 쿠팡 | [partners.coupang.com](https://partners.coupang.com) → 내 정보 → API 키 발급 | `COUPANG_ACCESS_KEY`, `COUPANG_SECRET_KEY` |

```bash
export NAVER_CLIENT_ID=...
export NAVER_CLIENT_SECRET=...
export COUPANG_ACCESS_KEY=...
export COUPANG_SECRET_KEY=...
```

한쪽 키만 있어도 동작한다. 없는 쪽은 경고를 찍고 건너뛴다.

> 쿠팡 파트너스 API는 제휴 회원 승인을 받아야 키가 발급된다. 승인 전이라면
> `--source naver` 로 네이버만 조회할 수 있다.

## 사용법

```bash
python3 -m waterprice                      # "생수" 기본 검색
python3 -m waterprice 삼다수 --top 20       # 검색어 지정
python3 -m waterprice --source naver       # 한쪽만 조회
python3 -m waterprice --sort price         # 원/L 대신 표시가 기준 정렬
python3 -m waterprice --json > result.json # JSON / CSV 출력
```

### 출력 예시

```
 #  몰                 원/L        가격      용량  상품명
------------------------------------------------------------------------------------------
 1  쿠팡                352      16,900       48L  탐사수 무라벨 2L 24병
 2  삼다수몰            579      13,900       24L  제주 삼다수 2L 12병
 3  이마트몰            662      15,900       24L  백산수 2L 12병
 4  쿠팡                945      18,900       20L  아이시스 8.0 500ml 40개

[요약] 쿠팡 최저 352원/L · 네이버 최저 579원/L
       → 쿠팡 승 (227원/L, 39.2% 저렴)
```

*(위 숫자는 형식을 보여주기 위한 예시이며 실제 시세가 아니다.)*

표시가 기준 2위인 삼다수(13,900원)가 원/L로는 쿠팡 탐사수보다 비싸다 —
이 도구가 필요한 이유가 그것이다.

## 주요 옵션

| 옵션 | 설명 |
| --- | --- |
| `--limit N` | 쇼핑몰당 조회 개수 (기본 50, 최대 100) |
| `--top N` | 출력할 상위 개수 (기본 15) |
| `--min-liters N` | 총 용량이 N L 미만이면 제외 (기본 1) |
| `--include-unknown` | 용량을 못 읽은 상품도 포함 (원/L은 빈칸) |
| `--exclude 키워드` | 제외 키워드 추가. 기본값은 정수기·필터·텀블러 등 |
| `--json` / `--csv` | 기계가 읽을 형식으로 출력 |

## 동작 방식

1. `naver.py` / `coupang.py` 가 각 공식 API에서 상품을 가져온다.
2. `volume.py` 가 상품명에서 총 용량을 뽑는다.
   `"2L 6개 x 2박스"` → `24L`, `"24개월"` 같은 숫자는 수량으로 세지 않는다.
   `"2L 24개입 x24"` 처럼 같은 수량이 중복 표기된 경우 한 번만 곱한다.
3. `compare.py` 가 물이 아닌 상품(정수기 필터 등)을 걸러내고 원/L로 정렬한다.
4. `cli.py` 가 표 / JSON / CSV로 출력한다.

한쪽 쇼핑몰이 실패해도 나머지 결과는 그대로 보여준다.

## 한계

- 배송비와 카드·쿠폰 할인은 반영하지 않는다. 표시가 기준이다.
- 상품명에 용량이 안 적힌 상품은 기본적으로 제외된다 (`--include-unknown` 으로 포함 가능).
- 네이버 검색 API는 최저가(`lprice`)를 주므로, 실제 구매 페이지 가격과 다를 수 있다.

## 테스트

```bash
python3 -m unittest discover -s tests -v
```
