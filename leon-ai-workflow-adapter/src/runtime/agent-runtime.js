import { RuntimeCapabilityError } from './errors.js';

const REQUIRED_FUNCTIONS = ['agent', 'parallel', 'pipeline', 'phase', 'log'];

export function assertAgentRuntime(runtime) {
  if (!runtime || typeof runtime !== 'object') {
    throw new RuntimeCapabilityError('AgentRuntime 必须是对象');
  }

  for (const name of REQUIRED_FUNCTIONS) {
    if (typeof runtime[name] !== 'function') {
      throw new RuntimeCapabilityError(`AgentRuntime 缺少函数: ${name}`);
    }
  }

  return runtime;
}

export function createPortableAgentRuntime({
  providerId,
  args = {},
  executeAgent,
  onPhase = () => {},
  onLog = () => {},
}) {
  if (typeof executeAgent !== 'function') {
    throw new RuntimeCapabilityError(`${providerId || 'unknown'} 缺少 executeAgent`);
  }

  const state = {
    agentCalls: 0,
    currentPhase: null,
  };

  const runtime = {
    args,
    async agent(prompt, options = {}) {
      state.agentCalls += 1;
      return executeAgent(prompt, options, { args, providerId });
    },
    async parallel(tasks) {
      if (!Array.isArray(tasks)) {
        throw new TypeError('parallel(tasks) 要求 tasks 为数组');
      }
      return Promise.all(tasks.map((task) => task()));
    },
    async pipeline(items, ...stages) {
      if (!Array.isArray(items)) {
        throw new TypeError('pipeline(items, ...stages) 要求 items 为数组');
      }
      return Promise.all(items.map(async (original, index) => {
        let value = original;
        for (const stage of stages) {
          value = await stage(value, original, index);
        }
        return value;
      }));
    },
    phase(name) {
      state.currentPhase = name;
      onPhase(name);
    },
    log(message) {
      onLog(message);
    },
  };

  assertAgentRuntime(runtime);
  return { runtime, state };
}
