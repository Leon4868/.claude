const catalog = {
  claude: {
    id: 'claude',
    aliases: ['anthropic'],
    preferredProtocol: 'claude-dynamic-workflow',
    sdkMethod: 'agent(prompt, options)',
  },
  gpt: {
    id: 'gpt',
    aliases: ['openai', 'chatgpt'],
    preferredProtocol: 'openai-responses',
    sdkMethod: 'client.responses.create(...)',
  },
  deepseek: {
    id: 'deepseek',
    aliases: ['deep-seek'],
    preferredProtocol: 'openai-chat-completions',
    sdkMethod: 'client.chat.completions.create(...)',
  },
  kimi: {
    id: 'kimi',
    aliases: ['moonshot'],
    preferredProtocol: 'kimi-or-openai-compatible',
    sdkMethod: 'client.chat.completions.create(...)',
  },
  glm: {
    id: 'glm',
    aliases: ['zhipu', 'bigmodel'],
    preferredProtocol: 'openai-compatible',
    sdkMethod: 'client.chat.completions.create(...)',
  },
  qwen: {
    id: 'qwen',
    aliases: ['dashscope', 'tongyi'],
    preferredProtocol: 'openai-responses',
    sdkMethod: 'client.responses.create(...)',
  },
  doubao: {
    id: 'doubao',
    aliases: ['ark', 'volcengine'],
    preferredProtocol: 'openai-responses',
    sdkMethod: 'client.responses.create(...)',
  },
};

export const PROVIDER_CATALOG = Object.freeze(catalog);

export function resolveProviderProfile(idOrAlias) {
  const normalized = String(idOrAlias || '').trim().toLowerCase();
  return Object.values(PROVIDER_CATALOG).find(
    (profile) => profile.id === normalized || profile.aliases.includes(normalized),
  );
}
