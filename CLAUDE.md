# AI 마을

이 저장소는 두 층으로 되어 있습니다. 섞지 마십시오.

- `.claude/agents/` — **주민**. 실제 Claude 서브에이전트이고, 실제 개발 업무를 합니다.
- `village/` — **세계**. 규칙 기반 시뮬레이션 엔진입니다. LLM 호출이 없고, 앞으로도 없어야 합니다.

## 주민에게 일을 맡길 때

| 일의 성격 | 주민 |
|---|---|
| 계획 수립, 작업 분배 | `mayor-chonjang` (촌장) |
| 새 기능 구현 | `farmer-nongbu` (농부) |
| 버그 진단과 수정 | `doctor-uisa` (의사) |
| 리팩터링, 빌드·도구 정비 | `smith-daejangjang` (대장장이) |
| 보안·코드 리뷰 | `guard-gyeongbi` (경비) |
| 의존성 판단 | `merchant-sangin` (상인) |
| 문서와 일지 | `scribe-girokja` (기록자) |

한 파일 고치면 끝나는 일에 촌장을 부르지 마십시오. 바로 농부나 의사에게 맡기는 편이 낫습니다.

## village/ 를 고칠 때 지킬 것

1. **LLM 호출을 넣지 마십시오.** 세계는 결정적이어야 합니다. 판단이 필요하면 `village/brains/` 에 두뇌를 추가하고 `BRAINS` 에 등록하십시오.
2. **`Math.random()` 을 쓰지 마십시오.** 난수는 전부 `village/rng.mjs` 의 `roll`/`rollInt`/`pick` 을 통해 세계의 `rng` 커서에서 나옵니다. 같은 씨앗이 같은 마을을 만드는 것이 이 엔진의 핵심이고, 테스트가 그것을 검사합니다.
3. **밸런스를 건드렸으면 60일을 돌려보십시오.** 수확량·활력·소비량 중 하나라도 바꿨다면 `npm test` 의 "60일을 살아도 마을이 무너지지 않는다" 테스트가 여러 씨앗으로 검증합니다. 이 테스트를 지우지 말고 통과시키십시오.
4. **수치는 0~100 안에 머물러야 합니다.** 활력·기분·분위기 모두. 자원은 음수가 되면 안 됩니다.
5. **주민을 추가하면 서브에이전트도 같이 만드십시오.** `village/residents.mjs` 의 `agent` 필드와 `.claude/agents/<agent>.md` 파일이 1:1로 맞아야 하고, 테스트가 이를 검사합니다.

## 명령

```bash
npm test                                   # 테스트 (의존성 없음)
node village/village.mjs init --extended   # 마을 다시 세우기
node village/village.mjs tick 7            # 일주일 진행
node village/village.mjs status            # 현재 상태
```

`village/state.json` 과 `village/chronicle.md` 는 `.gitignore` 대상입니다. 실행하면 생기는 파일이니 커밋하지 마십시오.

## 말투

이 저장소의 문서·주석·CLI 출력은 모두 한국어이고, 마을 은유를 일관되게 씁니다. 새로 쓰는 것도 그에 맞추십시오.
