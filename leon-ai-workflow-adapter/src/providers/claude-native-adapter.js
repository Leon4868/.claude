import { createPortableAgentRuntime } from '../runtime/agent-runtime.js';
import { RuntimeCapabilityError } from '../runtime/errors.js';

const REQUIRED_GLOBALS = ['agent'];

export function createClaudeNativeAdapter(globals) {
  return {
    id: 'claude',
    aliases: ['anthropic', 'claude-native'],
    async probe() {
      for (const name of REQUIRED_GLOBALS) {
        if (!globals || typeof globals[name] !== 'function') {
          throw new RuntimeCapabilityError(`Claude Dynamic Workflow 未注入 ${name}()`);
        }
      }
    },
    async createRuntime({ args, onPhase, onLog }) {
      const prepared = createPortableAgentRuntime({
        providerId: 'claude',
        args,
        executeAgent: (prompt, options) => globals.agent(prompt, options),
        onPhase: onPhase || globals.phase,
        onLog: onLog || globals.log,
      });

      if (typeof globals.parallel === 'function') prepared.runtime.parallel = globals.parallel;
      if (typeof globals.pipeline === 'function') prepared.runtime.pipeline = globals.pipeline;
      return prepared;
    },
  };
}
