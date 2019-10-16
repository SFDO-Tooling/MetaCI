// @flow

export const logError = (
  message: string | Error | Response,
  data: { [string]: mixed } = {},
) => {
  // Raven/Sentry is disabled for now. This is where it would go.
  window.console.error(message, data);
};

export const log = (...args: Array<mixed>) => {
  window.console.info(...args);
};
