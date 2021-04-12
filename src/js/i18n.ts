import i18next from 'i18next';
import i18nDetector from 'i18next-browser-languagedetector';
import i18nBackend from 'i18next-http-backend';
import { initReactI18next } from 'react-i18next';
import { logError } from 'utils/logging';

// Note: The `t` function should only be used inside Component lifecycle
// handlers, not in code executed immediately at runtime (before translations
// are loaded).

const init = (cb: (error?: string) => void): Promise<any> =>
  i18next
    .use(i18nDetector)
    .use(i18nBackend)
    .use(initReactI18next)
    .init(
      {
        fallbackLng: 'en',
        keySeparator: false,
        nsSeparator: false,
        returnNull: false,
        returnEmptyString: false,
        interpolation: {
          escapeValue: false,
        },
        saveMissing: true,
        missingKeyHandler(lng, ns, key, fallbackValue) {
          logError('missing translation', { lng, ns, key, fallbackValue });
        },
        backend: {
          loadPath: '/static/{{lng}}/{{ns}}.json',
        },
      },
      cb,
    );

export default init;
