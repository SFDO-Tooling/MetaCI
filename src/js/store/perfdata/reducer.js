// @flow

import type { PerfDataAction, UIDataAction } from 'store/perfdata/actions';

export type PerfData = {
  count: Number,
  next: URL | null,
  previous: URL | null,
  results: {}[],
};

export type LoadingStatus = "LOADING" | "AVAILABLE" | "ERROR"

export type PerfDataLoading = {
  status: "LOADING", perfdata: (PerfData | null)
};

export type PerfDataAvailable = {
  status: "AVAILABLE", perfdata: PerfData
};

export type UIDataLoading = {
  status: "LOADING", uidata: ({} | null)
};

export type UIDataAvailable = {
  status: "AVAILABLE", uidata: {}
};

export type PerfDataState = PerfDataAvailable | PerfDataLoading;

export const perfDataReducer = (
            state : PerfDataState = {status: "LOADING", perfdata: null},
            action: PerfDataAction): PerfDataState => {
  switch (action.type) {
    case 'PERF_DATA_LOADING':
      return ({status: "LOADING", perfdata: state && state.perfdata} : PerfDataLoading);
    case 'PERF_DATA_AVAILABLE':
      return {status: "AVAILABLE", perfdata: action.payload};
  }
  return state;
};

export type PerfData_UI_State = UIDataLoading | UIDataAvailable | null;

export const perfDataUIReducer = (state: PerfData_UI_State = null, action: UIDataAction): PerfData_UI_State => {
  switch (action.type) {
    case 'UI_DATA_LOADING':
      return {status: "LOADING", uidata: action.payload};
    case 'UI_DATA_AVAILABLE':
      return {status: "AVAILABLE", uidata: action.payload};
  }
  return state;
};
