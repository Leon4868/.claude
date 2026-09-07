import { createInjectedAgentAdapter } from './injected-agent-adapter.js';
import { createClaudeNativeAdapter } from './claude-native-adapter.js';
import { PROVIDER_CATALOG } from '../runtime/provider-catalog.js';
import { createProviderRegistry } from '../runtime/provider-registry.js';

export function createLeonProviderRegistry({ executors = {}, claudeGlobals } = {}) {
  const adapters = [];

  for (const profile of Object.values(PROVIDER_CATALOG)) {
    if (profile.id === 'claude' && claudeGlobals) {
      adapters.push(createClaudeNativeAdapter(claudeGlobals));
      continue;
    }

    const executeAgent = executors[profile.id];
    adapters.push(createInjectedAgentAdapter({
      id: profile.id,
      aliases: profile.aliases,
      isAvailable: () => typeof executeAgent === 'function',
      executeAgent: (...args) => executeAgent(...args),
    }));
  }

  return createProviderRegistry(adapters);
}
