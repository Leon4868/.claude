#!/usr/bin/env node
// 由 /leon:ai 各节点调用，把当前执行状态写入 state.json 供可视化界面轮询。
// 用法: node update-state.mjs --node N3 --status running --feature "1.登录" --featureIndex 1 --featureTotal 5 --task "T-002 实现登录接口" --taskIndex 2 --taskTotal 6 --message "正在调用 leon-backend-engineer"

import { readFileSync, writeFileSync, existsSync, mkdirSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';

const __dirname = dirname(fileURLToPath(import.meta.url));
const STATE_PATH = join(__dirname, '..', 'state.json');

const NODE_LABELS = {
  N1: '初始化', N2: '进入 Feature', N3: '执行 Task',
  N4: '审查收尾', N5: '完成',
};

function parseArgs(argv) {
  const out = {};
  for (let i = 0; i < argv.length; i++) {
    const a = argv[i];
    if (a.startsWith('--')) {
      const key = a.slice(2);
      const next = argv[i + 1];
      if (next === undefined || next.startsWith('--')) {
        out[key] = true;
      } else {
        out[key] = next;
        i++;
      }
    }
  }
  return out;
}

function loadState() {
  if (existsSync(STATE_PATH)) {
    try {
      return JSON.parse(readFileSync(STATE_PATH, 'utf8'));
    } catch {
      // 损坏则重建
    }
  }
  return {
    node: '', nodeLabel: '', status: 'idle',
    feature: '', featureIndex: 0, featureTotal: 0,
    task: '', taskIndex: 0, taskTotal: 0,
    message: '', updatedAt: new Date().toISOString(), history: [],
  };
}

const args = parseArgs(process.argv.slice(2));
if (!args.node) {
  console.error('用法: update-state.mjs --node N1..N5 [--status running|paused|done|idle] [--feature ..] [--task ..] [--message ..]');
  process.exit(1);
}

const state = loadState();
const now = new Date().toISOString();

state.node = args.node;
state.nodeLabel = NODE_LABELS[args.node] || args.node;
state.status = args.status || 'running';
if (args.feature !== undefined) state.feature = String(args.feature);
if (args.featureIndex !== undefined) state.featureIndex = Number(args.featureIndex) || 0;
if (args.featureTotal !== undefined) state.featureTotal = Number(args.featureTotal) || 0;
if (args.task !== undefined) state.task = String(args.task);
if (args.taskIndex !== undefined) state.taskIndex = Number(args.taskIndex) || 0;
if (args.taskTotal !== undefined) state.taskTotal = Number(args.taskTotal) || 0;
state.message = args.message !== undefined ? String(args.message) : '';
state.updatedAt = now;

state.history = state.history || [];
state.history.push({
  node: state.node, status: state.status, feature: state.feature,
  task: state.task, message: state.message, at: now,
});
if (state.history.length > 60) state.history = state.history.slice(-60);

mkdirSync(dirname(STATE_PATH), { recursive: true });
writeFileSync(STATE_PATH, JSON.stringify(state, null, 2));
console.log(`[leon-flow] ${state.node} ${state.nodeLabel} -> ${state.status}`);
