// @flow

import type { PerfDataAction, UIDataAction } from 'store/perfdata/actions';
import type { UIData } from '../../api/testmethod_perf_UI_JSON_schema';

import type { PerfData as P } from '../../api/testmethod_perfdata_JSON_schema';

export type PerfData = P;

export type LoadingStatus = "LOADING" | "AVAILABLE" | "ERROR"

export type PerfDataLoading = {
  status: "LOADING", perfdata: (PerfData | null)
};

export type PerfDataAvailable = {
  status: "AVAILABLE", perfdata: PerfData
};

export type PerfDataError = {
  status: "ERROR",
  perfdata: (PerfData | null),
  reason: string
};

export type UIDataLoading = {
  status: "LOADING", uidata: ({} | null)
};

export type UIDataAvailable = {
  status: "AVAILABLE", uidata: UIData
};

export type PerfDataState = PerfDataAvailable | PerfDataLoading | PerfDataError;

export const perfDataReducer = (
            state : PerfDataState = {status: "LOADING", perfdata: null},
            action: PerfDataAction): PerfDataState => {
  switch (action.type) {
    case 'PERF_DATA_LOADING':
      return ({status: "LOADING", perfdata: state && state.perfdata} : PerfDataLoading);
    case 'PERF_DATA_AVAILABLE':
      return {status: "AVAILABLE", perfdata: action.payload};
    case 'PERF_DATA_ERROR':
      return { status: "ERROR", reason: action.payload,
            perfdata:state ? state.perfdata : null };
  }
  return state;
};

export type PerfData_UI_State = UIDataLoading | UIDataAvailable;

export const perfDataUIReducer = (state: PerfData_UI_State =
      { status: "LOADING", uidata: null }, action: UIDataAction): PerfData_UI_State => {
  switch (action.type) {
    case 'UI_DATA_LOADING':
      return {status: "LOADING", uidata: action.payload};
    case 'UI_DATA_AVAILABLE':
      return {status: "AVAILABLE", uidata: action.payload};
  }
  return state;
};
