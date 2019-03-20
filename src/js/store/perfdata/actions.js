// @flow

import type { ThunkAction } from 'redux-thunk';

import type { PerfData } from 'store/perfdata/reducer';

type PerfDataAvailable = { type: 'PERF_DATA_AVAILABLE', payload: PerfData };
type PerfDataLoading = { type: 'PERF_DATA_LOADING', payload: PerfData };

export type PerfDataAction = PerfDataAvailable | PerfDataLoading;

function encodeQueryString(params){
  var queryString = Object.keys(params).map((key) => {
    return encodeURIComponent(key) + '=' + encodeURIComponent(params[key])
  }).join('&');
  return queryString;
}

export const perfRESTFetch = (url?: string, options?: {}):
        ThunkAction => (dispatch, getState, { apiFetch }) => {
  dispatch({ type: 'PERF_DATA_LOADING', payload: url });
  url = url || "/api/testmethod_perf?include_fields=duration_average&group_by=repo&page_size=10"
  if(options){
    url = url + "&"+ encodeQueryString(options);
  }
  apiFetch(url, {
    method: 'GET',
  }).then((payload) => {
    return dispatch({ type: 'PERF_DATA_AVAILABLE', payload });
  });
}