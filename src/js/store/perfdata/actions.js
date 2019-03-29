// @flow

import queryString from 'query-string';

import type { ThunkAction } from 'redux-thunk';

import type { PerfData } from 'store/perfdata/reducer';

type PerfDataAvailableAction = { type: 'PERF_DATA_AVAILABLE', payload: PerfData };
type PerfDataLoadingAction = { type: 'PERF_DATA_LOADING', payload: PerfData };
type UIDataAvailableAction = { type: 'UI_DATA_AVAILABLE', payload: PerfData };
type UIDataLoadingAction = { type: 'UI_DATA_LOADING', payload: PerfData };

export type PerfDataAction = PerfDataAvailableAction | PerfDataLoadingAction;
export type UIDataAction = UIDataAvailableAction | UIDataLoadingAction;



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
        alert(JSON.stringify(payload.reason));
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
    // TODO: Error handling
    return dispatch({ type: 'UI_DATA_AVAILABLE', payload });
  });
}
