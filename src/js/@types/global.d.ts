import * as Sentry from '@sentry/browser';

declare global {
  interface Window {
    GLOBALS: { [key: string]: any };
    Sentry?: typeof Sentry;
    api_urls: { [key: string]: (...args: any[]) => string };
  }
}
