// 세계 — 시계, 자원 원장, 사건.
//
// 주민은 결정을 내리고, 세계는 그 결정의 결과를 계산한다.
// 이 파일에는 LLM 호출이 없다. 전부 규칙이다.

import { roll, rollInt, pick } from './rng.mjs';
import { CORE, EXTENDED, spawn } from './residents.mjs';
import { getBrain } from './brains/index.mjs';

export const STATE_VERSION = 1;
const SEASONS = ['봄', '여름', '가을', '겨울'];
const DAYS_PER_SEASON = 10;

/** 일의 종류에 따라 무엇이 얼마나 나오는가 */
const YIELD = {
  밭갈이: { 식량: 5 },
  수확: { 식량: 9 },
  씨뿌리기: { 식량: 3 },
  '식량 확보': { 식량: 5 },
  '교역로 점검': { 금화: 2 },
  '장터 개설': { 금화: 4, 식량: 3 },
  '재고 정리': { 금화: 1 },
  '일지 정리': { 기록: 2 },
  '족보 갱신': { 기록: 1 },
  '공고문 작성': { 기록: 1 },
  '연장 수리': { 목재: 1 },
  '쟁기 제작': { 목재: 3 },
  '화덕 정비': { 목재: 2 },
  왕진: { 약초: 1 },
  '약초 조제': { 약초: 3 },
  '역병 감시': { 약초: 1 },
  휴식: {},
};

/** 계절이 수확에 미치는 영향 */
const SEASON_FOOD_MULTIPLIER = { 봄: 1.0, 여름: 1.2, 가을: 1.5, 겨울: 0.5 };

export function createWorld({ name = '고요한 마을', seed = 20260917, extended = false } = {}) {
  const defs = extended ? [...CORE, ...EXTENDED] : CORE;
  return {
    version: STATE_VERSION,
    name,
    seed,
    rng: seed,
    day: 1,
    season: SEASONS[0],
    mood: 70,
    ledger: { 식량: 20, 목재: 10, 약초: 5, 금화: 12, 기록: 0 },
    residents: defs.map(spawn),
    chronicle: [],
  };
}

/** 마을에 주민 한 명을 들인다. */
export function welcome(world, def) {
  if (world.residents.some((r) => r.id === def.id)) {
    throw new Error(`${def.name}은(는) 이미 마을 주민입니다.`);
  }
  world.residents.push(spawn(def));
  return world;
}

const EVENTS = [
  {
    id: 'poongnyeon',
    text: '풍년이 들었다. 밭마다 곡식이 넘친다.',
    apply: (w) => { w.ledger.식량 += 8; w.mood += 8; },
  },
  {
    id: 'gamul',
    text: '가뭄이 들었다. 우물이 마른다.',
    apply: (w) => { w.ledger.식량 = Math.max(0, w.ledger.식량 - 6); w.mood -= 10; },
  },
  {
    id: 'yeokbyeong',
    text: '역병이 돌았다. 앓아누운 주민이 나왔다.',
    apply: (w) => {
      for (const r of w.residents) r.vigor = Math.max(0, r.vigor - 15);
      w.ledger.약초 = Math.max(0, w.ledger.약초 - 2);
      w.mood -= 8;
    },
  },
  {
    id: 'ibangin',
    text: '이방인이 마을 문을 두드렸다. 낯선 물건을 내밀었다.',
    apply: (w) => { w.ledger.금화 += 5; w.mood += 3; },
  },
  {
    id: 'chukje',
    text: '광장에서 축제가 열렸다. 효율은 없었지만 다들 웃었다.',
    apply: (w) => {
      w.ledger.식량 = Math.max(0, w.ledger.식량 - 3);
      w.mood += 15;
      for (const r of w.residents) r.mood = clamp(r.mood + 10);
    },
  },
];

function clamp(n, min = 0, max = 100) {
  return Math.max(min, Math.min(max, n));
}

/**
 * 하루를 진행한다.
 * @returns {{day:number, season:string, decisions:Array, event:object|null, notes:string[]}}
 */
export function tick(world, { brain = getBrain() } = {}) {
  const notes = [];
  const decisions = [];

  // 1. 주민마다 오늘 할 일을 정하고, 그 결과를 원장에 반영한다.
  for (const resident of world.residents) {
    const decision = brain.decide(resident, world);
    resident.task = decision.task;

    if (decision.task === '휴식') {
      resident.vigor = clamp(resident.vigor + 45);
      resident.mood = clamp(resident.mood + 5);
    } else {
      // 분위기가 좋으면 더 많이 거둔다. 40점이 기준선.
      const moodFactor = 0.7 + (world.mood / 100) * 0.6;
      const gains = YIELD[decision.task] ?? {};
      const earned = {};
      for (const [item, base] of Object.entries(gains)) {
        const seasonFactor = item === '식량' ? SEASON_FOOD_MULTIPLIER[world.season] : 1;
        const amount = Math.max(0, Math.round(base * moodFactor * seasonFactor));
        world.ledger[item] = (world.ledger[item] ?? 0) + amount;
        earned[item] = amount;
      }
      resident.vigor = clamp(resident.vigor - rollInt(world, 8, 15));
      resident.daysWorked += 1;
      decision.earned = earned;
    }
    decisions.push({ resident: resident.name, agent: resident.agent, ...decision });
  }

  // 2. 먹는다. 못 먹으면 마을이 상한다.
  const need = world.residents.length;
  if (world.ledger.식량 >= need) {
    world.ledger.식량 -= need;
  } else {
    const short = need - world.ledger.식량;
    world.ledger.식량 = 0;
    world.mood = clamp(world.mood - short * 6);
    for (const r of world.residents) r.vigor = clamp(r.vigor - short * 4);
    notes.push(`식량이 ${short} 모자랐다. 굶은 주민이 있다.`);
  }

  // 3. 사건. 10% 확률로 하루가 흔들린다.
  let event = null;
  if (roll(world) < 0.1) {
    event = pick(world, EVENTS);
    event.apply(world);
    notes.push(event.text);
  }

  // 4. 분위기는 평상시로 조금씩 되돌아간다.
  world.mood = clamp(world.mood + (world.mood < 60 ? 2 : -1));

  // 5. 날이 밝는다.
  world.day += 1;
  world.season = SEASONS[Math.floor((world.day - 1) / DAYS_PER_SEASON) % SEASONS.length];

  const entry = {
    day: world.day - 1,
    season: world.season,
    mood: world.mood,
    decisions,
    event: event ? event.text : null,
    notes,
  };
  world.chronicle.push(entry);
  return entry;
}

/** 마을이 위태로운가 */
export function assess(world) {
  const warnings = [];
  if (world.ledger.식량 < world.residents.length) warnings.push('곳간이 비었다');
  if (world.mood < 35) warnings.push('마을 분위기가 무너지고 있다');
  const exhausted = world.residents.filter((r) => r.vigor < 30).map((r) => r.name);
  if (exhausted.length) warnings.push(`지친 주민: ${exhausted.join(', ')}`);
  return warnings;
}
