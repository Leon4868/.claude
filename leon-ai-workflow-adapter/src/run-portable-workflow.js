import { runLeonAiWorkflow } from './leon-ai-workflow.core.js';
import { RuntimeUnavailableError } from './runtime/errors.js';
import { runWithRuntimeFallback } from './runtime/run-with-fallback.js';

export async function runPortableLeonWorkflow({
  registry,
  provider,
  fallbackProvider = 'claude',
  args = {},
  onPhase,
  onLog,
  onFallback,
}) {
  if (!registry || typeof registry.resolve !== 'function') {
    throw new TypeError('registry 必须是 Provider Registry');
  }

  const primary = registry.resolve(provider);
  if (!primary) throw new RuntimeUnavailableError(`未注册 Provider: ${provider}`);

  const fallback = fallbackProvider ? registry.resolve(fallbackProvider) : undefined;
  return runWithRuntimeFallback({
    workflow: runLeonAiWorkflow,
    args,
    primary,
    fallback,
    onPhase,
    onLog,
    onFallback,
  });
}
