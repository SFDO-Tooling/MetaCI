// @flow

import queryString from 'query-string';
import type { ThunkAction } from 'redux-thunk';
import type { PerfData } from 'store/perfdata/reducer';

type PerfDataAvailableAction = {
  type: 'PERF_DATA_AVAILABLE',
  payload: PerfData,
};
type PerfDataLoadingAction = { type: 'PERF_DATA_LOADING', payload: PerfData };
type PerfDataError = { type: 'PERF_DATA_ERROR', payload: string };

type UIDataAvailableAction = { type: 'UI_DATA_AVAILABLE', payload: UIData };
type UIDataLoadingAction = { type: 'UI_DATA_LOADING', payload: PerfData };
type UIDataError = { type: 'UI_DATA_ERROR', payload: string };

export type PerfDataAction =
  | PerfDataAvailableAction
  | PerfDataLoadingAction
  | PerfDataError;
export type UIDataAction =
  | UIDataAvailableAction
  | UIDataLoadingAction
  | UIDataError;

import type { UIData } from '../../api/testmethod_perf_UI_JSON_schema';
import { assertUIData } from '../../api/testmethod_perf_UI_JSON_schema';

export const perfRESTFetch = (url: string, params?: {}): ThunkAction => (
  dispatch,
  getState,
  { apiFetch },
) => {
  dispatch({ type: 'PERF_DATA_LOADING', payload: url });
  if (params) {
    url = `${url}&${queryString.stringify(params)}`;
  }
  apiFetch(url, {
    method: 'GET',
  }).then(payload => {
    if (payload) {
      if (!payload.error) {
        return dispatch({ type: 'PERF_DATA_AVAILABLE', payload });
      }
      // TODO: PERF_DATA_ERROR is not handled yet
      return dispatch({ type: 'PERF_DATA_ERROR', payload });
    }
    alert('Missing payload from server');
  });
};

export const perfREST_UI_Fetch = (): ThunkAction => (
  dispatch,
  getState,
  { apiFetch },
) => {
  // todo use reverse
  const url = '/api/testmethod_perf_UI';
  dispatch({ type: 'UI_DATA_LOADING', payload: url });
  apiFetch(url, {
    method: 'GET',
  }).then(payload => {
    if (payload) {
      if (!payload.error) {
        const typedPayload: UIData = assertUIData(payload);
        return dispatch({ type: 'UI_DATA_AVAILABLE', payload });
      }
      return dispatch({ type: 'UI_DATA_ERROR', payload });
    }
    alert('Missing payload from server');
  });
};
