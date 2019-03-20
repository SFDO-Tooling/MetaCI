// @flow

import type { ThunkAction } from 'redux-thunk';

import type { PerfData } from 'store/perfdata/reducer';

type PerfDataAvailable = { type: 'PERF_DATA_AVAILABLE', payload: PerfData };
type PerfDataLoading = { type: 'PERF_DATA_LOADING', payload: PerfData };

export type PerfDataAction = PerfDataAvailable | PerfDataLoading;

export const perfRESTFetch = (): ThunkAction => (dispatch, getState, { apiFetch }) => {
  dispatch({ type: 'PERF_DATA_LOADING' })
  apiFetch("/api/testmethod_perf?include_fields=duration_average&group_by=repo", {
    method: 'GET',
  }).then((payload) => {
    /* istanbul ignore else */
    return dispatch({ type: 'PERF_DATA_AVAILABLE', payload });
  });
}