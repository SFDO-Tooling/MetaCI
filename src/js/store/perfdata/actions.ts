

import queryString from "query-string";

import { PerfData } from "store/perfdata/reducer";
import { UIData } from "api/testmethod_perf_UI_JSON_schema";
import { assertPerfData } from "api/testmethod_perfdata_JSON_schema";
import { assertUIData } from "api/testmethod_perf_UI_JSON_schema";
import { ThunkDispatch } from 'redux-thunk'
import { AnyAction } from 'redux';

export const testmethod_perfdata_url = '/api/testmethod_perf';
export const testmethod_perf_UI_url = '/api/testmethod_perf_UI';

type PerfDataAvailableAction = {
  type: "PERF_DATA_AVAILABLE";
  payload: PerfData;
};
type PerfDataLoadingAction = {
  type: "PERF_DATA_LOADING";
  payload: {url: string;};
};
type PerfDataError = {type: "PERF_DATA_ERROR";payload: string;};

type UIDataAvailableAction = {type: "UI_DATA_AVAILABLE";payload: UIData;};
type UIDataLoadingAction = {
  type: "UI_DATA_LOADING";
  payload: {url: string;};
};
type UIDataError = {type: "UI_DATA_ERROR";payload: string;};

export type PerfDataAction = PerfDataAvailableAction | PerfDataLoadingAction | PerfDataError;
export type UIDataAction = UIDataAvailableAction | UIDataLoadingAction | UIDataError;

type ReduxDispatch = ThunkDispatch<{}, {}, AnyAction>;

/* eslint-disable no-use-before-define */

export const perfRESTFetch = (url: string, params?: {}) => (dispatch : ReduxDispatch, _getState : any, {
  apiFetch
}) => {
  if (params) {
    url = `${url}&${queryString.stringify(params)}`;
  }
  return perfREST_API({
    dispatch,
    apiFetch,
    prefix: 'PERF',
    url,
    checkValid: assertPerfData
  });
};

export const perfREST_UI_Fetch = (params?: {}) => (dispatch : ReduxDispatch, _getState: any, {
  apiFetch
} : {apiFetch : any}) => {
  let url = testmethod_perf_UI_url;
  if (params) {
    url = `${url}?${queryString.stringify(params)}`;
  }
  return perfREST_API({
    dispatch,
    apiFetch,
    prefix: 'UI',
    url,
    checkValid: assertUIData
  });
};

// flowlint-next-line unclear-type:off
type UntypedFunc = Function; // the types would be quite complex.

export const perfREST_API = ({
  dispatch,
  apiFetch,
  prefix,
  url,
  checkValid
}: {
  dispatch: ReduxDispatch;
  apiFetch: UntypedFunc;
  prefix: string;
  url: string;
  checkValid: UntypedFunc;
}) => {
  dispatch({ type: `${prefix}_DATA_LOADING`, payload: { url } });
  return apiFetch(url, { method: 'GET' }).then((payload:any) => {
    try {
      if (!payload) {
        throw new Error('No payload');
      }
      if (payload.error) {
        throw new Error(`Server error: ${payload.error}`);
      }
      const checkedPayload = checkValid(payload);
      return dispatch({
        type: `${prefix}_DATA_AVAILABLE`,
        payload: checkedPayload
      });
    } catch (e) {
      dispatch({ type: `${prefix}_DATA_ERROR`, e });
      throw e;
    }
  });
};
