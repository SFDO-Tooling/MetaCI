// @flow

import i18n_backend from 'i18next-xhr-backend';
import i18n_detector from 'i18next-browser-languagedetector';
import { initReactI18next } from 'react-i18next';
import { use } from 'i18next';

import { logError } from 'utils/logging';

// Note: The `t` function should only be used inside Component lifecycle
// handlers, not in code executed immediately at runtime (before translations
// are loaded).

const init = (cb: () => void): void =>
  use(i18n_detector)
    .use(i18n_backend)
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
