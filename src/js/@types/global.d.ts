declare global {
  interface Window {
    GLOBALS: { [key: string]: any };
    api_urls: { [key: string]: (...args: any[]) => string };
  }
}
