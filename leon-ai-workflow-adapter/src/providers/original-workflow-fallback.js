import { RuntimeCapabilityError } from '../runtime/errors.js';

export function createOriginalWorkflowFallback({
  invokeWorkflow,
  workflowName = 'leon-ai-workflow',
} = {}) {
  return {
    id: 'claude-original',
    aliases: ['original', 'legacy'],
    async probe() {
      if (typeof invokeWorkflow !== 'function') {
        throw new RuntimeCapabilityError('宿主未提供原 Claude Workflow 调用函数');
      }
    },
    async runWorkflow({ args }) {
      return invokeWorkflow({ name: workflowName, args });
    },
  };
}
