// @flow

import type { PerfDataAction, UIDataAction } from 'store/perfdata/actions';

export type PerfData = {
  count: Number,
  next: URL | null,
  previous: URL | null,
  results: [],
};

export type PerfDataLoading = {
  status: "PERF_DATA_LOADING", perfdata: (PerfData | null)
};

export type PerfDataAvailable = {
  status: "PERF_DATA_AVAILABLE", perfdata: PerfData
};

export type UIDataLoading = {
  status: "UI_DATA_LOADING", uidata: ({} | null)
};

export type UIDataAvailable = {
  status: "UI_DATA_AVAILABLE", uidata: {}
};

export type PerfDataState = PerfDataAvailable | PerfDataLoading | null;

export const perfDataReducer = (state: PerfDataState = null, action: PerfDataAction): PerfDataState => {
  switch (action.type) {
    case 'PERF_DATA_LOADING':
      return ({status: "PERF_DATA_LOADING", perfdata: state && state.perfdata} : PerfDataLoading);
    case 'PERF_DATA_AVAILABLE':
      return {status: "PERF_DATA_AVAILABLE", perfdata: action.payload};
  }
  return state;
};

export type PerfData_UI_State = UIDataLoading | UIDataAvailable | null;

export const perfDataUIReducer = (state: PerfData_UI_State = null, action: UIDataAction): PerfData_UI_State => {
  switch (action.type) {
    case 'UI_DATA_LOADING':
      return {status: "UI_DATA_LOADING", uidata: action.payload};
    case 'UI_DATA_AVAILABLE':
      return {status: "UI_DATA_AVAILABLE", uidata: action.payload};
  }
  return state;
};

