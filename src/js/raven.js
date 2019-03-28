import raven from 'raven-js';

let config;
try {
  config = JSON.parse(document.getElementById('js-raven-setup').innerHTML);
} catch (err) {
  // Error-logging is not available, but it's not worth throwing an Error
  // and stopping execution. Intentionally swallow Error and continue.
}

if (config && config.dsn) {
  window.Raven = raven;

  // Recommended settings from: https://gist.github.com/impressiver/5092952
  // Ignore list based off: https://gist.github.com/1878283
  const ravenOptions = {
    ignoreErrors: [
      // Random plugins/extensions
      'top.GLOBALS',
      // http://blog.errorception.com/2012/03/tale-of-unfindable-js-error.html
      'originalCreateNotification',
      'canvas.contentDocument',
      'MyApp_RemoveAllHighlights',
      'http://tt.epicplay.com',
      "Can't find variable: ZiteReader",
      'jigsaw is not defined',
      'ComboSearch is not defined',
      'http://loading.retry.widdit.com/',
      'atomicFindClose',
      // Facebook borked
      'fb_xd_fragment',
      // ISP "optimizing" proxy; `Cache-Control: no-transform` seems to reduce
      // this. (thanks @acdha)
      // See http://stackoverflow.com/questions/4113268/
      'bmi_SafeAddOnload',
      'EBCallBackMessageReceived',
      'conduitPage',
    ],
    ignoreUrls: [
      // Facebook flakiness
      /graph\.facebook\.com/i,
      // Facebook blocked
      /connect\.facebook\.net\/en_US\/all\.js/i,
      // Woopra flakiness
      /eatdifferent\.com\.woopra-ns\.com/i,
      /static\.woopra\.com\/js\/woopra\.js/i,
      // Chrome extensions
      /extensions\//i,
      /^chrome:\/\//i,
      // Other plugins
      /127\.0\.0\.1:4001\/isrunning/i, // Cacaoweb
      /webappstoolbarba\.texthelp\.com\//i,
      /metrics\.itunes\.apple\.com\.edgesuite\.net\//i,
    ],
  };
  // Configure Raven; install default handler to capture uncaught exceptions
  raven.config(config.dsn, ravenOptions).install();
}
