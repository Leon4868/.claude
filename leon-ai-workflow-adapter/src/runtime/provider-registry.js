import { RuntimeCapabilityError } from './errors.js';

function normalizeId(value) {
  return String(value || '').trim().toLowerCase();
}

function assertAdapter(adapter) {
  if (!adapter || !normalizeId(adapter.id)) {
    throw new RuntimeCapabilityError('Provider Adapter 缺少 id');
  }
  const canCreateRuntime = typeof adapter.createRuntime === 'function';
  const canRunWorkflow = typeof adapter.runWorkflow === 'function';
  if (typeof adapter.probe !== 'function' || (!canCreateRuntime && !canRunWorkflow)) {
    throw new RuntimeCapabilityError(`${adapter.id} 必须实现 probe()，并实现 createRuntime() 或 runWorkflow()`);
  }
}

export function createProviderRegistry(initialAdapters = []) {
  const adapters = new Map();
  const aliases = new Map();

  function register(adapter) {
    assertAdapter(adapter);
    const id = normalizeId(adapter.id);
    adapters.set(id, adapter);
    aliases.set(id, id);
    for (const alias of adapter.aliases || []) aliases.set(normalizeId(alias), id);
    return adapter;
  }

  function resolve(idOrAlias) {
    const normalized = normalizeId(idOrAlias);
    const id = aliases.get(normalized);
    return id ? adapters.get(id) : undefined;
  }

  for (const adapter of initialAdapters) register(adapter);

  return {
    register,
    resolve,
    list: () => [...adapters.values()],
  };
}
