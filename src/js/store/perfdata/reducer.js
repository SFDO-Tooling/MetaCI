// @flow

import type { PerfDataAction } from 'store/perfdata/actions';

export type PerfData = {
  count: Number,
  next: URL | null,
  previous: URL | null,
  results: [],
};

export type PerfDataAvailable = {
  status: "PERF_DATA_AVAILABLE", perfdata: PerfData
};

export type PerfDataLoading = {
  status: "PERF_DATA_LOADING", perfdata: (PerfData | null)
};

export type PerfDataState = PerfDataAvailable | PerfDataLoading | null;

const reducer = (state: PerfDataState = null, action: PerfDataAction): PerfDataState => {
  switch (action.type) {
    case 'PERF_DATA_AVAILABLE':
      return {status: "PERF_DATA_AVAILABLE", perfdata: action.payload};
      case 'PERF_DATA_LOADING':
      return ({status: "PERF_DATA_LOADING", perfdata: state && state.perfdata} : PerfDataLoading);
    }
  return state;
};

export default reducer;
