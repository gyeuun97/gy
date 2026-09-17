#!/usr/bin/env node
// 마을 CLI.
//
//   node village/village.mjs init [--extended] [--seed N] [--name 이름]
//   node village/village.mjs status
//   node village/village.mjs tick [일수]
//   node village/village.mjs chronicle [--last N]
//   node village/village.mjs roster
//   node village/village.mjs welcome <주민id>
//
// 상태는 village/state.json 한 파일에 전부 들어간다.

import { readFileSync, writeFileSync, existsSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { dirname, join } from 'node:path';

import { createWorld, tick, assess, welcome, STATE_VERSION } from './world.mjs';
import { ROSTER, findResident } from './residents.mjs';
import { getBrain } from './brains/index.mjs';

const HERE = dirname(fileURLToPath(import.meta.url));
const STATE_PATH = join(HERE, 'state.json');
const CHRONICLE_PATH = join(HERE, 'chronicle.md');

function load() {
  if (!existsSync(STATE_PATH)) {
    throw new Error('아직 마을이 없습니다. 먼저 `node village/village.mjs init` 을 실행하세요.');
  }
  const world = JSON.parse(readFileSync(STATE_PATH, 'utf8'));
  if (world.version !== STATE_VERSION) {
    throw new Error(`state.json 버전이 ${world.version} 입니다 (기대: ${STATE_VERSION}). init 으로 다시 세우세요.`);
  }
  return world;
}

function save(world) {
  writeFileSync(STATE_PATH, JSON.stringify(world, null, 2) + '\n');
}

function bar(value, width = 20) {
  const filled = Math.round((value / 100) * width);
  return '█'.repeat(filled) + '·'.repeat(width - filled);
}

function flag(args, key, fallback) {
  const i = args.indexOf(`--${key}`);
  return i === -1 ? fallback : args[i + 1];
}

function cmdInit(args) {
  const world = createWorld({
    name: flag(args, 'name', '고요한 마을'),
    seed: Number(flag(args, 'seed', 20260917)),
    extended: args.includes('--extended'),
  });
  save(world);
  console.log(`${world.name}이(가) 세워졌습니다. 주민 ${world.residents.length}명.`);
  for (const r of world.residents) console.log(`  ${r.name.padEnd(5)} ${r.duty}  →  ${r.agent}`);
  console.log('\n`node village/village.mjs tick 3` 으로 사흘을 살아보세요.');
}

function cmdStatus() {
  const world = load();
  console.log(`\n【 ${world.name} 】 ${world.season} · ${world.day}일차`);
  console.log(`분위기  ${bar(world.mood)} ${world.mood}`);
  console.log('\n곳간');
  for (const [item, amount] of Object.entries(world.ledger)) {
    console.log(`  ${item.padEnd(4)} ${String(amount).padStart(4)}`);
  }
  console.log('\n주민');
  for (const r of world.residents) {
    const task = r.task ? `— ${r.task}` : '— 아직 일하지 않음';
    console.log(`  ${r.name.padEnd(5)} 활력 ${bar(r.vigor, 10)} ${String(r.vigor).padStart(3)}  ${task}`);
  }
  const warnings = assess(world);
  if (warnings.length) {
    console.log('\n⚠  ' + warnings.join('\n⚠  '));
  } else {
    console.log('\n별일 없는 하루입니다.');
  }
  console.log();
}

function cmdTick(args) {
  const world = load();
  const days = Number(args[0] ?? 1);
  if (!Number.isInteger(days) || days < 1) throw new Error(`일수는 1 이상의 정수여야 합니다: ${args[0]}`);
  const brain = getBrain();

  for (let i = 0; i < days; i++) {
    const entry = tick(world, { brain });
    console.log(`\n── ${entry.day}일차 (${entry.season}) ──`);
    for (const d of entry.decisions) {
      const earned = d.earned && Object.keys(d.earned).length
        ? '  +' + Object.entries(d.earned).map(([k, v]) => `${k}${v}`).join(' +')
        : '';
      console.log(`  ${d.resident.padEnd(5)} ${d.task.padEnd(10)}${earned}`);
      if (d.reason !== '평시 일과') console.log(`         └ ${d.reason}`);
    }
    for (const note of entry.notes) console.log(`  ! ${note}`);
  }
  save(world);
  appendChronicle(world, days);
  console.log(`\n${days}일이 지났습니다. 지금은 ${world.day}일차.`);
}

function appendChronicle(world, days) {
  const recent = world.chronicle.slice(-days);
  const lines = recent.map((e) => {
    const said = e.decisions.map((d) => `- **${d.resident}**: ${d.task} — "${d.say}"`).join('\n');
    const extras = [...(e.event ? [`> ${e.event}`] : []), ...e.notes.filter((n) => n !== e.event).map((n) => `> ${n}`)];
    return `### ${e.day}일차 (${e.season}) · 분위기 ${e.mood}\n\n${said}\n${extras.length ? '\n' + extras.join('\n') + '\n' : ''}`;
  });
  const header = existsSync(CHRONICLE_PATH) ? '' : `# ${world.name} 일지\n\n기록자가 남긴 마을의 나날.\n\n`;
  writeFileSync(CHRONICLE_PATH, header + lines.join('\n'), { flag: existsSync(CHRONICLE_PATH) ? 'a' : 'w' });
}

function cmdChronicle(args) {
  if (!existsSync(CHRONICLE_PATH)) throw new Error('아직 일지가 없습니다. 하루라도 살아야 기록이 남습니다.');
  const text = readFileSync(CHRONICLE_PATH, 'utf8');
  const last = Number(flag(args, 'last', 0));
  if (!last) return void console.log(text);
  const entries = text.split(/(?=^### )/m);
  console.log(entries.slice(-last).join(''));
}

function cmdRoster() {
  console.log('\n마을 명부 (각 주민 = .claude/agents/ 의 서브에이전트)\n');
  for (const r of ROSTER) {
    console.log(`  ${r.name.padEnd(5)} ${r.agent.padEnd(20)} ${r.duty}`);
    console.log(`        ${r.craft}`);
  }
  console.log();
}

function cmdWelcome(args) {
  const id = args[0];
  if (!id) throw new Error('누구를 들일까요? 예: welcome uisa');
  const def = findResident(id);
  if (!def) throw new Error(`명부에 '${id}' 이(가) 없습니다. \`roster\` 로 확인하세요.`);
  const world = load();
  welcome(world, def);
  save(world);
  console.log(`${def.name}이(가) 마을에 들어왔습니다. (${def.agent})`);
}

const COMMANDS = {
  init: cmdInit,
  status: cmdStatus,
  tick: cmdTick,
  chronicle: cmdChronicle,
  roster: cmdRoster,
  welcome: cmdWelcome,
};

function main() {
  const [cmd, ...args] = process.argv.slice(2);
  const handler = COMMANDS[cmd];
  if (!handler) {
    console.log(`쓸 수 있는 명령: ${Object.keys(COMMANDS).join(', ')}`);
    process.exit(cmd ? 1 : 0);
  }
  try {
    handler(args);
  } catch (err) {
    console.error(`✗ ${err.message}`);
    process.exit(1);
  }
}

main();
