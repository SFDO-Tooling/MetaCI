import { assertUIData, UIData } from 'api/testmethod_perf_UI_JSON_schema';
import { assertPerfData } from 'api/testmethod_perfdata_JSON_schema';
import { stringify } from 'query-string';
import { Dispatch } from 'redux';
import { AppState } from 'store';
import { PerfData } from 'store/perfdata/reducer';

export const testmethod_perfdata_url = '/api/testmethod_perf';
export const testmethod_perf_UI_url = '/api/testmethod_perf_UI';

interface PerfDataAvailableAction {
  type: 'PERF_DATA_AVAILABLE';
  payload: PerfData;
}
interface PerfDataLoadingAction {
  type: 'PERF_DATA_LOADING';
  payload: { url: string };
}
interface PerfDataError {
  type: 'PERF_DATA_ERROR';
  payload: string;
}

interface UIDataAvailableAction {
  type: 'UI_DATA_AVAILABLE';
  payload: UIData;
}
interface UIDataLoadingAction {
  type: 'UI_DATA_LOADING';
  payload: { url: string };
}
interface UIDataError {
  type: 'UI_DATA_ERROR';
  payload: string;
}

export type PerfDataAction =
  | PerfDataAvailableAction
  | PerfDataLoadingAction
  | PerfDataError;
export type UIDataAction =
  | UIDataAvailableAction
  | UIDataLoadingAction
  | UIDataError;

// eslint-disable-next-line @typescript-eslint/ban-types
type UntypedFunc = Function; // the types would be quite complex.

export const perfREST_API = ({
  dispatch,
  apiFetch,
  prefix,
  url,
  checkValid,
}: {
  dispatch: Dispatch;
  apiFetch: UntypedFunc;
  prefix: string;
  url: string;
  checkValid: UntypedFunc;
}) => {
  dispatch({ type: `${prefix}_DATA_LOADING`, payload: { url } });
  return apiFetch(url, { method: 'GET' }).then((payload: any) => {
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
        payload: checkedPayload,
      });
    } catch (e) {
      dispatch({ type: `${prefix}_DATA_ERROR`, e });
      throw e;
    }
  });
};

/* eslint-disable no-use-before-define */

export const perfRESTFetch = (
  url: string,
  params?: Record<string, unknown>,
) => (
  dispatch: Dispatch,
  _getState: AppState,
  { apiFetch }: { apiFetch: UntypedFunc },
) => {
  if (params) {
    url = `${url}&${stringify(params)}`;
  }
  return perfREST_API({
    dispatch,
    apiFetch,
    prefix: 'PERF',
    url,
    checkValid: assertPerfData,
  });
};

export const perfREST_UI_Fetch = (params?: Record<string, unknown>) => (
  dispatch: Dispatch,
  _getState: AppState,
  { apiFetch }: { apiFetch: any },
) => {
  let url = testmethod_perf_UI_url;
  if (params) {
    url = `${url}?${stringify(params)}`;
  }
  return perfREST_API({
    dispatch,
    apiFetch,
    prefix: 'UI',
    url,
    checkValid: assertUIData,
  });
};
