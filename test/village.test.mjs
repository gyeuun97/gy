import { test } from 'node:test';
import assert from 'node:assert/strict';

import { createWorld, tick, assess, welcome } from '../village/world.mjs';
import { ROSTER, CORE, findResident } from '../village/residents.mjs';
import { getBrain } from '../village/brains/index.mjs';
import { nextRandom } from '../village/rng.mjs';

test('같은 씨앗은 같은 난수를 낸다', () => {
  const a = nextRandom(42);
  const b = nextRandom(42);
  assert.equal(a.value, b.value);
  assert.notEqual(nextRandom(a.cursor).value, a.value);
});

test('같은 씨앗의 두 마을은 똑같이 흘러간다', () => {
  const run = () => {
    const w = createWorld({ seed: 123, extended: true });
    for (let i = 0; i < 30; i++) tick(w);
    return w;
  };
  assert.deepEqual(run(), run());
});

test('마을을 세우면 1군 주민 넷이 있다', () => {
  const w = createWorld();
  assert.equal(w.residents.length, CORE.length);
  assert.deepEqual(w.residents.map((r) => r.name), ['촌장', '농부', '상인', '기록자']);
  assert.ok(w.residents.every((r) => r.vigor === 100));
});

test('하루가 지나면 날짜와 일지가 늘어난다', () => {
  const w = createWorld();
  const entry = tick(w);
  assert.equal(w.day, 2);
  assert.equal(entry.day, 1);
  assert.equal(w.chronicle.length, 1);
  assert.equal(entry.decisions.length, w.residents.length);
});

test('주민은 하루에 한 사람분 식량을 먹는다', () => {
  const w = createWorld();
  w.ledger.식량 = 100;
  // 아무도 식량을 만들지 않는 두뇌
  const idle = { decide: () => ({ task: '휴식', reason: '실험', say: '' }) };
  tick(w, { brain: idle });
  assert.equal(w.ledger.식량, 100 - w.residents.length);
});

test('곳간이 비면 마을 분위기가 상한다', () => {
  const w = createWorld();
  w.ledger.식량 = 0;
  const idle = { decide: () => ({ task: '휴식', reason: '실험', say: '' }) };
  const before = w.mood;
  const entry = tick(w, { brain: idle });
  assert.ok(w.mood < before, '굶었는데 분위기가 그대로다');
  assert.ok(entry.notes.some((n) => n.includes('모자랐다')));
  assert.equal(w.ledger.식량, 0, '식량이 음수로 내려갔다');
});

test('지친 주민은 스스로 쉰다', () => {
  const w = createWorld();
  const nongbu = w.residents.find((r) => r.name === '농부');
  nongbu.vigor = 10;
  const decision = getBrain('rule').decide(nongbu, w);
  assert.equal(decision.task, '휴식');
});

test('곳간이 비면 농부가 아니어도 밭으로 간다', () => {
  const w = createWorld();
  w.ledger.식량 = 0;
  const sangin = w.residents.find((r) => r.name === '상인');
  assert.equal(getBrain('rule').decide(sangin, w).task, '식량 확보');
});

test('60일을 살아도 마을이 무너지지 않는다', () => {
  for (const seed of [1, 777, 20260917, 31337]) {
    const w = createWorld({ seed, extended: true });
    let starvedDays = 0;
    for (let i = 0; i < 60; i++) {
      const entry = tick(w);
      if (entry.notes.some((n) => n.includes('굶은'))) starvedDays += 1;
    }
    assert.equal(starvedDays, 0, `seed ${seed}: ${starvedDays}일 굶었다`);
    assert.ok(w.mood > 20, `seed ${seed}: 분위기가 ${w.mood}까지 떨어졌다`);
  }
});

test('수치는 0~100을 벗어나지 않는다', () => {
  const w = createWorld({ seed: 5, extended: true });
  for (let i = 0; i < 120; i++) tick(w);
  assert.ok(w.mood >= 0 && w.mood <= 100);
  for (const r of w.residents) {
    assert.ok(r.vigor >= 0 && r.vigor <= 100, `${r.name} 활력 ${r.vigor}`);
    assert.ok(r.mood >= 0 && r.mood <= 100);
  }
  for (const [item, amount] of Object.entries(w.ledger)) {
    assert.ok(amount >= 0, `${item}이 ${amount}로 음수다`);
  }
});

test('새 주민을 들일 수 있고, 같은 사람을 두 번 들일 수는 없다', () => {
  const w = createWorld();
  const uisa = findResident('uisa');
  welcome(w, uisa);
  assert.equal(w.residents.length, CORE.length + 1);
  assert.throws(() => welcome(w, uisa), /이미 마을 주민/);
});

test('모든 주민은 서브에이전트와 짝이 있다', async () => {
  const { readdirSync } = await import('node:fs');
  const files = new Set(readdirSync(new URL('../.claude/agents', import.meta.url)));
  for (const r of ROSTER) {
    assert.ok(files.has(`${r.agent}.md`), `${r.name}의 에이전트 파일 ${r.agent}.md 가 없다`);
  }
});

test('모르는 두뇌를 부르면 이름을 알려주며 거절한다', () => {
  assert.throws(() => getBrain('점쟁이'), /쓸 수 있는 두뇌: rule/);
});

test('assess 는 위태로운 마을을 알아본다', () => {
  const w = createWorld();
  assert.deepEqual(assess(w), []);
  w.ledger.식량 = 0;
  w.mood = 10;
  w.residents[0].vigor = 5;
  const warnings = assess(w);
  assert.equal(warnings.length, 3);
  assert.ok(warnings.some((x) => x.includes('촌장')));
});
