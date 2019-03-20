// @flow

import type { ThunkAction } from 'redux-thunk';

import type { PerfData } from 'store/perfdata/reducer';

type PerfDataAvailable = { type: 'PERF_DATA_AVAILALBLE', payload: PerfData };
export type PerfDataAction = PerfDataAvailable;

export const PerfRESTFetch = (): ThunkAction => (dispatch, getState, { apiFetch }) =>
  apiFetch(window.api_urls.xyzzy(), {
    method: 'GET',
  }).then((payload) => {
    /* istanbul ignore else */
    return dispatch({ type: 'PERF_DATA_AVAILALBLE', payload });
  });
