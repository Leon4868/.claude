export class RuntimeUnavailableError extends Error {
  constructor(message, options = {}) {
    super(message, options);
    this.name = 'RuntimeUnavailableError';
    this.code = 'RUNTIME_UNAVAILABLE';
  }
}

export class RuntimeCapabilityError extends Error {
  constructor(message, options = {}) {
    super(message, options);
    this.name = 'RuntimeCapabilityError';
    this.code = 'RUNTIME_CAPABILITY_MISSING';
  }
}

export function isPreflightFallbackError(error) {
  return error instanceof RuntimeUnavailableError || error instanceof RuntimeCapabilityError;
}
