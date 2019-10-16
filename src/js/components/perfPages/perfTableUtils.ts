// @flow

import queryString from 'query-string';
import is from 'sarcastic';

// This differs from the normal query paramemter helper classes in that
// it is designed to have default parameters as state. Also, its fairly
// strongly typed.
export class QueryParamHelpers {
  default_params: { [string]: mixed };

  constructor(default_params: { [string]: mixed }) {
    this.default_params = default_params;
    this.get = this.get.bind(this); // Javascript grossness!
  }

  // get a single value
  get = (name: string): string | number | null => {
    const rc = this.getAll()[name];
    try {
      return is(rc, is.maybe(is.either(is.string, is.number)));
    } catch (exception) {
      // eslint-disable-next-line no-console
      console.log('UNKNOWN TYPE', name, rc, exception);
      throw exception;
    }
  };

  // get a list of strings
  getList = (name: string): string[] | typeof undefined => {
    const rc = this.getAll()[name];
    if (Array.isArray(rc)) {
      return rc;
    } else if (typeof rc === 'string' || typeof rc === 'number') {
      return [rc];
    }
    return rc;
  };

  // get everything includigng default values in one object
  getAll = (): { [string]: string | string[] } => ({
    ...this.default_params,
    ...queryString.parse(window.location.search),
  });

  // set a value. Does not merge list-like values. It overwrites them.
  set = (newQueryParts: {
    [string]: string | string[] | null | typeof undefined,
  }) => {
    const qs = queryString.stringify({ ...this.getAll(), ...newQueryParts });
    window.history.pushState(null, '', `${window.location.pathname}?${qs}`);
  };
}

/**
 * Add iDs to table values for consumption by the SLDS DataTable
 * @param {*} rows hashes from database
 */
export const addIds = (rows: Array<{ [key: string]: mixed }>): {}[] =>
  rows.map((row, index) => ({ ...row, id: index.toString() }));
