// 마을 주민 명부.
//
// 각 주민은 .claude/agents/ 의 서브에이전트와 1:1로 대응한다.
// agent 필드가 그 연결고리다 — 규칙 엔진에서 "농부가 오늘 밭일을 했다"는
// 실제로 farmer-nongbu 서브에이전트에게 구현 작업을 맡겼다는 뜻이다.

/** 1군: 없으면 마을이 돌아가지 않는 주민 */
export const CORE = [
  {
    id: 'chonjang',
    name: '촌장',
    agent: 'mayor-chonjang',
    duty: '계획 수립과 작업 분배',
    craft: '요구사항을 쪼개 누구에게 맡길지 정한다',
    produces: null, // 촌장은 직접 생산하지 않고 남의 생산성을 올린다
    upkeep: 1,
    traits: { 결단: 8, 체력: 5, 참을성: 7 },
  },
  {
    id: 'nongbu',
    name: '농부',
    agent: 'farmer-nongbu',
    duty: '기능 구현',
    craft: '밭을 갈듯 코드를 기른다',
    produces: { 식량: 4 },
    upkeep: 1,
    traits: { 결단: 5, 체력: 9, 참을성: 8 },
  },
  {
    id: 'sangin',
    name: '상인',
    agent: 'merchant-sangin',
    duty: '의존성과 외부 리소스 교역',
    craft: '바깥에서 가져올 것과 직접 만들 것을 저울질한다',
    produces: { 금화: 3 },
    upkeep: 1,
    traits: { 결단: 7, 체력: 5, 참을성: 4 },
  },
  {
    id: 'girokja',
    name: '기록자',
    agent: 'scribe-girokja',
    duty: '마을 일지와 문서',
    craft: '오늘 무슨 일이 있었는지 남긴다. 마을의 기억 그 자체',
    produces: { 기록: 2 },
    upkeep: 1,
    traits: { 결단: 4, 체력: 6, 참을성: 10 },
  },
];

/** 2군: 마을을 풍성하게 하는 주민 */
export const EXTENDED = [
  {
    id: 'daejangjang',
    name: '대장장이',
    agent: 'smith-daejangjang',
    duty: '리팩터링과 도구 정비',
    craft: '무뎌진 코드를 벼린다. 농부의 생산성이 대장장이 손에 달렸다',
    produces: { 목재: 3 },
    upkeep: 1,
    traits: { 결단: 6, 체력: 8, 참을성: 6 },
  },
  {
    id: 'uisa',
    name: '의사',
    agent: 'doctor-uisa',
    duty: '버그 진단과 치료',
    craft: '증상이 아니라 병인을 찾는다',
    produces: { 약초: 2 },
    upkeep: 1,
    traits: { 결단: 6, 체력: 5, 참을성: 9 },
  },
  {
    id: 'gyeongbi',
    name: '경비',
    agent: 'guard-gyeongbi',
    duty: '보안과 코드 리뷰',
    craft: '마을 문으로 뭐가 들어오는지 본다',
    produces: null,
    upkeep: 1,
    traits: { 결단: 9, 체력: 7, 참을성: 5 },
  },
];

export const ROSTER = [...CORE, ...EXTENDED];

export function findResident(id) {
  return ROSTER.find((r) => r.id === id || r.name === id || r.agent === id);
}

/** 명부 정의를 살아있는 주민 상태로 만든다. */
export function spawn(def) {
  return {
    id: def.id,
    name: def.name,
    agent: def.agent,
    duty: def.duty,
    vigor: 100, // 활력. 0이 되면 쓰러진다
    mood: 70, // 개인 기분
    task: null, // 배정된 일
    daysWorked: 0,
  };
}
