// 두뇌 교체 지점.
//
// 지금은 규칙 기반 하나뿐이다. 나중에 Claude API 두뇌를 붙일 때
// 여기에 등록만 하면 마을 코드는 한 줄도 건드릴 필요가 없다:
//
//   import * as claudeBrain from './claude-brain.mjs';
//   BRAINS.claude = claudeBrain;
//
// 두뇌가 지켜야 할 계약은 딱 하나 —
//   decide(resident, world) -> { task, reason, say }

import * as ruleBrain from './rule-brain.mjs';

export const BRAINS = {
  rule: ruleBrain,
};

export function getBrain(kind = process.env.VILLAGE_BRAIN || 'rule') {
  const brain = BRAINS[kind];
  if (!brain) {
    const known = Object.keys(BRAINS).join(', ');
    throw new Error(`'${kind}' 두뇌를 모릅니다. 쓸 수 있는 두뇌: ${known}`);
  }
  return brain;
}
