

import { UIData } from "../../api/testmethod_perf_UI_JSON_schema";
import { PerfData as P } from "../../api/testmethod_perfdata_JSON_schema";

import { PerfDataAction, UIDataAction } from "store/perfdata/actions";

export type PerfData = P;

export type LoadingStatus = "LOADING" | "AVAILABLE" | "ERROR";

export type PerfDataLoading = {
  status: "LOADING";
  perfdata: PerfData | null;
  url: string;
};

export type PerfDataAvailable = {
  status: "AVAILABLE";
  perfdata: PerfData;
  url: string;
};

export type PerfDataError = {
  status: "ERROR";
  perfdata: PerfData | null;
  reason: string;
  url: string;
};

export type UIDataLoading = {
  status: "LOADING";
  url: string;
  uidata?: UIData;
};

export type UIDataAvailable = {
  status: "AVAILABLE";
  uidata: UIData;
  url: string;
};

export type UIDataError = {
  status: "ERROR";
  reason: string;
  uidata?: UIData;
  url: string;
};

export type PerfDataState = PerfDataAvailable | PerfDataLoading | PerfDataError;

export const perfDataReducer = (state: PerfDataState = { status: 'LOADING', perfdata: null, url: '' }, action: PerfDataAction): PerfDataState => {
  switch (action.type) {
    case 'PERF_DATA_LOADING':
      return {
        status: 'LOADING',
        perfdata: state && state.perfdata,
        url: action.payload.url
      };
    case 'PERF_DATA_AVAILABLE':
      return { status: 'AVAILABLE', perfdata: action.payload, url: state.url };
    case 'PERF_DATA_ERROR':
      return {
        status: 'ERROR',
        reason: action.payload,
        url: state.url,
        perfdata: state ? state.perfdata : null
      };

  }
  return state;
};

export type PerfData_UI_State = UIDataLoading | UIDataAvailable | UIDataError;
export const perfDataUIReducer = (state: PerfData_UI_State = { status: 'LOADING', uidata: null, url: '' }, action: UIDataAction): PerfData_UI_State => {
  switch (action.type) {
    case 'UI_DATA_LOADING':
      return {
        status: 'LOADING',
        url: action.payload.url,
        uidata: state ? state.uidata : null
      };
    case 'UI_DATA_AVAILABLE':
      return { status: 'AVAILABLE', uidata: action.payload, url: state.url };
    case 'UI_DATA_ERROR':
      return {
        status: 'ERROR',
        reason: action.payload,
        url: state.url,
        uidata: state ? state.uidata : null
      };

  }
  return state;
};
