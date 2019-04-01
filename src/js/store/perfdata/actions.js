// @flow

import queryString from 'query-string';

import type { ThunkAction } from 'redux-thunk';

import type { PerfData } from 'store/perfdata/reducer';

type PerfDataAvailable = { type: 'PERF_DATA_AVAILABLE', payload: PerfData };
type PerfDataLoading = { type: 'PERF_DATA_LOADING', payload: PerfData };
type PerfDataError = { type: 'PERF_DATA_ERROR', payload: string};
type UIDataAvailable = { type: 'UI_DATA_AVAILABLE', payload: PerfData };
type UIDataLoading = { type: 'UI_DATA_LOADING', payload: PerfData };
type UIDataError = { type: 'UI_DATA_ERROR', payload: string };

export type PerfDataAction = PerfDataAvailable | PerfDataLoading | PerfDataError;
export type UIDataAction = UIDataAvailable | UIDataLoading | UIDataError;

export const perfRESTFetch = (url : string, params?: {}):
        ThunkAction => (dispatch, getState, { apiFetch }) => {
  dispatch({ type: 'PERF_DATA_LOADING', payload: url });
  if(params){
    url = url + "&"+ queryString.stringify(params);
  }
  apiFetch(url, {
    method: 'GET',
  }).then((payload) => {
    if(payload){
      if(!payload.error){
        return dispatch({ type: 'PERF_DATA_AVAILABLE', payload });
      }else{
        // TODO: PERF_DATA_ERROR is not handled yet
        return dispatch({ type: 'PERF_DATA_ERROR', payload });
      }
    }else{
      alert("Missing payload from server");
    }
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
    if (payload) {
      if (!payload.error) {
        return dispatch({ type: 'UI_DATA_AVAILABLE', payload });
      } else {
        // TODO: UI_DATA_ERROR is not handled yet
        return dispatch({ type: 'UI_DATA_ERROR', payload });
      }
    } else {
      alert("Missing payload from server");
    }
  });
}
