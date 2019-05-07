// @flow

import cookies from 'js-cookie';

import { logError } from 'utils/logging';

export type UrlParams = { [string]: string | number | boolean };

// these HTTP methods do not require CSRF protection
const csrfSafeMethod = method => /^(GET|HEAD|OPTIONS|TRACE)$/.test(method);

const getResponse = (resp, errorStatus) =>
  resp
    .text()
    .then(text => {
      try {
        text = JSON.parse(text);
      } catch (err) {
        // swallow error
      }
      // flowlint-next-line sketchy-null-number:off
      if (errorStatus) {
        return { error: errorStatus, reason: text };
      }
      return text;
    })
    .catch(
      /* istanbul ignore next */
      err => {
        logError(err);
        throw err;
      },
    );

const getApiFetch = () => (url: string, opts: { [string]: mixed } = {}) => {
  const options = Object.assign({}, { headers: {} }, opts);
  const method = options.method || 'GET';
  if (!csrfSafeMethod(method)) {
    options.headers['X-CSRFToken'] = cookies.get('csrftoken') || '';
  }

  return fetch(url, options)
    .then(
      response => {
        if (response.ok) {
          return getResponse(response);
        }
        if (response.status >= 400 && response.status) {
          logError(response);
          return getResponse(response, response.status);
        }
        const error = (new Error(response.statusText): { [string]: mixed });
        error.response = response;
        throw error;
      },
      err => {
        logError(err);
        throw err;
      },
    )
    .catch(err => {
      logError(err);
      throw err;
    });
};

export default getApiFetch;
