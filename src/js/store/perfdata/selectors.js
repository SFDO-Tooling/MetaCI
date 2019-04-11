// @flow

import type { AppState } from 'store';
import type {
  PerfDataState,
  PerfData_UI_State,
  LoadingStatus,
} from 'store/perfdata/reducer';
import type {
  TestMethodPerfUI,
  FilterDefinition,
} from 'api/testmethod_perf_UI_JSON_schema';
import get from 'lodash/get';

export const selectPerfState = (appState: AppState): PerfDataState =>
  appState.perfData;
export const selectPerfUIStatus = (appState: AppState): LoadingStatus =>
  appState.perfDataUI ? appState.perfDataUI.status : 'LOADING';

// TODO: Improve strong typing on these:
export const selectTestMethodPerfUI = (
  appState: AppState,
): TestMethodPerfUI | null => {
  console.log(
    appState.perfDataUI.status,
    appState.perfDataUI.status === 'AVAILABLE'
      ? appState.perfDataUI.uidata.testmethod_perf
      : null,
  );
  return appState.perfDataUI.status === 'AVAILABLE'
    ? appState.perfDataUI.uidata.testmethod_perf
    : null;
};

export const selectTestMethodResultsUI = (
  appState: AppState,
): TestMethodPerfUI | null =>
  appState.perfDataUI.status === 'AVAILABLE'
    ? appState.perfDataUI.uidata.testmethod_results
    : null;

export const selectBuildflowFiltersUI = (
  appState: AppState,
): FilterDefinition[] | null =>
  appState.perfDataUI.status === 'AVAILABLE'
    ? appState.perfDataUI.uidata.buildflow_filters
    : null;
