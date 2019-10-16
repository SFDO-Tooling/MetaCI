
export const logError = (message: string | Error | Response, data: {
  [Key: string]: unknown;
} = {}) => {
  // Raven/sentry is not configured for this project yet.
  window.console.error(message, data);
};

export const log = (...args: Array<unknown>) => {
  window.console.info(...args);
};
