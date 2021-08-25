export const logError = (
  message: string | Error | Response,
  data: { [key: string]: any } = {},
): void => {
  window.console.error(message, data);
};

export const log = (...args: unknown[]): void => {
  window.console.info(...args);
};
