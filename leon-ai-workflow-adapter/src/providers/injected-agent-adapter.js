import { createPortableAgentRuntime } from '../runtime/agent-runtime.js';
import { RuntimeUnavailableError } from '../runtime/errors.js';

export function createInjectedAgentAdapter({
  id,
  aliases = [],
  executeAgent,
  isAvailable = () => true,
}) {
  return {
    id,
    aliases,
    async probe(context) {
      if (!(await isAvailable(context))) {
        throw new RuntimeUnavailableError(`${id} Agent 执行器不可用`);
      }
    },
    async createRuntime({ args, onPhase, onLog }) {
      return createPortableAgentRuntime({
        providerId: id,
        args,
        executeAgent,
        onPhase,
        onLog,
      });
    },
  };
}
