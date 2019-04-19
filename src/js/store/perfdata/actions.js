// @flow

import queryString from 'query-string';
import type { ThunkAction } from 'redux-thunk';

import type { PerfData } from 'store/perfdata/reducer';
import type { UIData } from 'api/testmethod_perf_UI_JSON_schema';
import { assertUIData } from 'api/testmethod_perf_UI_JSON_schema';

type PerfDataAvailableAction = {
  type: 'PERF_DATA_AVAILABLE',
  payload: PerfData,
};
type PerfDataLoadingAction = {
  type: 'PERF_DATA_LOADING',
  payload: { url: string },
};
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

export const perfRESTFetch = (url: string, params?: {}): ThunkAction => (
  dispatch,
  _getState,
  { apiFetch },
) => {
  if (params) {
    url = `${url}&${queryString.stringify(params)}`;
  }
  dispatch({ type: 'PERF_DATA_LOADING', payload: { url } });
  apiFetch(url, {
    method: 'GET',
  }).then(payload => {
    if (payload) {
      if (!payload.error) {
        return dispatch({ type: 'PERF_DATA_AVAILABLE', payload });
      }
      return dispatch({ type: 'PERF_DATA_ERROR', payload });
    }
    return undefined;
  });
};

export const perfREST_UI_Fetch = (): ThunkAction => (
  dispatch,
  _getState,
  { apiFetch },
) => {
  const url = '/api/testmethod_perf_UI';
  dispatch({ type: 'UI_DATA_LOADING', payload: url });
  apiFetch(url, {
    method: 'GET',
  }).then(payload => {
    if (payload) {
      if (!payload.error) {
        const typedPayload: UIData = assertUIData(payload);
        return dispatch({ type: 'UI_DATA_AVAILABLE', payload: typedPayload });
      }
      return dispatch({ type: 'UI_DATA_ERROR', payload });
    }
    // eslint-disable-next-line no-console
    console.log('Missing payload from server');
    return undefined;
  });
};
