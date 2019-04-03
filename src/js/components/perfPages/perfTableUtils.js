// @flow

import queryString from 'query-string';
import is, { type AssertionType } from 'sarcastic';

// This differs from the normal query paramemter helper classes in that
// it is designed to have default parameters as state
export class QueryParamHelpers {
    default_params: { [string]: mixed };

    constructor(default_params: { [string]: mixed }) {
        this.default_params = default_params;
        this.get = this.get.bind(this); // Javascript grossness!
    }

    get = (name: string) : string | number | null => {
        let rc = this.getAll()[name];
        console.log(rc)
        return is(rc, is.maybe(is.either(is.string, is.number)));
    }

    getList = (name: string): string[] | typeof undefined => {
        var rc = this.getAll()[name];
        if(Array.isArray(rc)){
            return rc;
        }else if(typeof rc==='string' || typeof rc==='number'){
            return [rc];
        }else{
            return rc;
        }
    }

    getAll = () : {[string]: string | string[]} => {
        return { ...this.default_params, ...queryString.parse(window.location.search) };
    }


    set = (newQueryParts: { [string]: string | string[] | null | typeof undefined }) => {
        let qs = queryString.stringify({ ...this.getAll(), ...newQueryParts });
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
