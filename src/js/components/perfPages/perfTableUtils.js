// @flow

import queryString from 'query-string';

export class QueryParamHelpers {
    default_params: { [string]: mixed };

    constructor(default_params: { [string]: mixed }) {
        this.default_params = default_params;
        this.get = this.get.bind(this); // Javascript grossness!
    }

    get = (name?: string) => {
        let parts = { ...this.default_params, ...queryString.parse(window.location.search) };
        if (name) {
            return parts[name];
        } else {
            return parts;
        }
    }

    set = (newQueryParts: { [string]: string | string[] | null | typeof undefined }) => {
        let qs = queryString.stringify({ ...this.get(), ...newQueryParts });
        window.history.pushState(null, "", window.location.pathname + "?" + qs);
    };
}


/**
 * Add iDs to table values for consumption by the SLDS DataTable
 * @param {*} rows hashes from database
 */
export const addIds = (rows: {}[]) : {}[] => {
    return rows.map((row, index) => { return { ...row, id: index.toString() } })
}
