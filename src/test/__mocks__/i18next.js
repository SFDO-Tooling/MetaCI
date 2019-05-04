/* eslint-env jest */

'use strict';

const i18n = jest.genMockFromModule('i18next');

i18n.t = jest.fn((key, fallback) => {
  if (fallback && typeof fallback === 'string') {
    return fallback;
  }
  return key;
});

module.exports = i18n;
