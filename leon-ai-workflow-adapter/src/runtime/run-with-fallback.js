import { isPreflightFallbackError } from './errors.js';

async function prepare(adapter, args, hooks) {
  await adapter.probe({ args });
  return adapter.createRuntime({ args, ...hooks });
}

export async function runWithRuntimeFallback({
  workflow,
  args = {},
  primary,
  fallback,
  onPhase,
  onLog,
  onFallback = () => {},
}) {
  if (typeof workflow !== 'function') throw new TypeError('workflow 必须是函数');
  if (!primary) throw new TypeError('primary Provider Adapter 不能为空');

  let preparedPrimary;
  try {
    preparedPrimary = await prepare(primary, args, { onPhase, onLog });
    const result = await workflow(preparedPrimary.runtime);
    return { provider: primary.id, fallbackUsed: false, result };
  } catch (error) {
    const agentCalls = preparedPrimary && preparedPrimary.state
      ? preparedPrimary.state.agentCalls
      : 0;

    const canFallback = fallback && agentCalls === 0 && isPreflightFallbackError(error);
    if (!canFallback) throw error;

    onFallback({ from: primary.id, to: fallback.id, error });
    if (typeof fallback.runWorkflow === 'function') {
      await fallback.probe({ args });
      const result = await fallback.runWorkflow({ args });
      return { provider: fallback.id, fallbackUsed: true, result };
    }

    const preparedFallback = await prepare(fallback, args, { onPhase, onLog });
    const result = await workflow(preparedFallback.runtime);
    return { provider: fallback.id, fallbackUsed: true, result };
  }
}
