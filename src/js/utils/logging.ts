export const logError = (
  message: string | Error | Response,
  data: {
    [Key: string]: unknown;
  } = {},
): void => {
  // Raven/sentry is not configured for this project yet.
  window.console.error(message, data);
};

export const log = (...args: unknown[]): void => {
  window.console.info(...args);
};
