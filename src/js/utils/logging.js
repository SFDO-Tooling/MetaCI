// @flow

export const logError = (
  message: string | Error,
  data: { [string]: mixed } = {},
) => {
  if (window.Raven && window.Raven.isSetup()) {
    if (message instanceof Error) {
      window.Raven.captureException(message, data);
    } else {
      window.Raven.captureMessage(message, data);
    }
  }
  window.console.error(message, data);
};

export const log = (...args: Array<mixed>) => {
  window.console.info(...args);
};
