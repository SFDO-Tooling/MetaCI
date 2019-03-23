// @flow

import queryString from 'query-string';

import type { ThunkAction } from 'redux-thunk';

import type { PerfData } from 'store/perfdata/reducer';

type PerfDataAvailable = { type: 'PERF_DATA_AVAILABLE', payload: PerfData };
type PerfDataLoading = { type: 'PERF_DATA_LOADING', payload: PerfData };
type UIDataAvailable = { type: 'UI_DATA_AVAILABLE', payload: PerfData };
type UIDataLoading = { type: 'UI_DATA_LOADING', payload: PerfData };

export type PerfDataAction = PerfDataAvailable | PerfDataLoading;
export type UIDataAction = UIDataAvailable | UIDataLoading;



export const perfRESTFetch = (url?: string, params?: {}):
        ThunkAction => (dispatch, getState, { apiFetch }) => {
  dispatch({ type: 'PERF_DATA_LOADING', payload: url });
  // todo use reverse
  url = url || "/api/testmethod_perf?group_by=repo"
  if(params){
    url = url + "&"+ queryString.stringify(params);
  }
  apiFetch(url, {
    method: 'GET',
  }).then((payload) => {
    return dispatch({ type: 'PERF_DATA_AVAILABLE', payload });
  });
}

export const perfREST_UI_Fetch = ():
        ThunkAction => (dispatch, getState, { apiFetch }) => {
  // todo use reverse
  let url = "/api/testmethod_perf_UI";
  dispatch({ type: 'UI_DATA_LOADING', payload: url });
  apiFetch(url, {
    method: 'GET',
  }).then((payload) => {
    return dispatch({ type: 'UI_DATA_AVAILABLE', payload });
  });
}

