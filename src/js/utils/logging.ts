export const logError = (
  message: string | Error | Response,
  data: { [key: string]: any } = {},
): void => {
  // Raven/sentry is not configured for this project yet.
  window.console.error(message, data);
};

export const log = (...args: unknown[]): void => {
  window.console.info(...args);
};
