// 결정적 난수 생성기 (mulberry32).
// 같은 seed + 같은 호출 횟수 = 항상 같은 결과.
// 마을이 재현 가능해야 버그를 "어제 무슨 일이 있었나"로 추적할 수 있다.

export function nextRandom(cursor) {
  let t = (cursor + 0x6d2b79f5) >>> 0;
  let x = Math.imul(t ^ (t >>> 15), 1 | t);
  x = (x + Math.imul(x ^ (x >>> 7), 61 | x)) ^ x;
  const value = ((x ^ (x >>> 14)) >>> 0) / 4294967296;
  return { value, cursor: t };
}

/** 세계 상태의 rng 커서를 전진시키며 0~1 난수를 뽑는다. */
export function roll(world) {
  const { value, cursor } = nextRandom(world.rng);
  world.rng = cursor;
  return value;
}

/** min~max 사이 정수 */
export function rollInt(world, min, max) {
  return min + Math.floor(roll(world) * (max - min + 1));
}

/** 배열에서 하나 고르기 */
export function pick(world, items) {
  return items[Math.floor(roll(world) * items.length)];
}
