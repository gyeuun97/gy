// 규칙 기반 두뇌 — API 키 없이 즉시 돌아간다.
//
// 주민이 오늘 무엇을 할지 성격 수치와 마을 상태만 보고 결정한다.
// 결과는 아래 형태로 고정 (Claude 두뇌도 똑같은 모양을 돌려줘야 한다):
//   { task: string, reason: string, say: string }

import { pick } from '../rng.mjs';

const TASKS = {
  chonjang: ['마을 회의', '일감 배분', '분쟁 조정'],
  nongbu: ['밭갈이', '수확', '씨뿌리기'],
  sangin: ['교역로 점검', '장터 개설', '재고 정리'],
  girokja: ['일지 정리', '족보 갱신', '공고문 작성'],
  daejangjang: ['연장 수리', '쟁기 제작', '화덕 정비'],
  uisa: ['왕진', '약초 조제', '역병 감시'],
  gyeongbi: ['성문 경계', '순찰', '무기 점검'],
};

const REST = '휴식';

export const name = 'rule';

/**
 * @param {object} resident 살아있는 주민 상태
 * @param {object} world    마을 상태 (읽기 전용으로 다루되 rng 커서는 전진한다)
 * @returns {{task: string, reason: string, say: string}}
 */
export function decide(resident, world) {
  // 1. 지쳤으면 무조건 쉰다. 활력이 바닥난 주민은 사고를 낸다.
  if (resident.vigor < 30) {
    return {
      task: REST,
      reason: `활력 ${resident.vigor} — 한계`,
      say: '오늘은 도저히 못 하겠소.',
    };
  }

  // 2. 식량이 바닥나면 농부가 아니어도 다들 밭으로 간다.
  if (world.ledger.식량 < world.residents.length && resident.id !== 'chonjang') {
    return {
      task: '식량 확보',
      reason: `창고에 식량 ${world.ledger.식량} — 마을 인원보다 적다`,
      say: '곳간이 비었소. 다들 밭으로 갑시다.',
    };
  }

  // 3. 마을 분위기가 무너지면 촌장이 회의를 연다.
  if (resident.id === 'chonjang' && world.mood < 40) {
    return {
      task: '마을 회의',
      reason: `분위기 ${world.mood} — 수습이 필요하다`,
      say: '광장으로 모이시오. 이대로는 안 됩니다.',
    };
  }

  // 4. 평소에는 제 일을 한다.
  const options = TASKS[resident.id] ?? [REST];
  const task = pick(world, options);
  return {
    task,
    reason: '평시 일과',
    say: `오늘은 ${task}이오.`,
  };
}
