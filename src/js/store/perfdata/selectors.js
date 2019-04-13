// @flow

import type { AppState } from 'store';
import type { PerfDataState, LoadingStatus } from 'store/perfdata/reducer';
import type {
  TestMethodPerfUI,
  FilterDefinition,
} from 'api/testmethod_perf_UI_JSON_schema';

export const selectPerfState = (appState: AppState): PerfDataState =>
  appState.perfData;

export const selectPerfUIStatus = (appState: AppState): LoadingStatus =>
  appState.perfDataUI ? appState.perfDataUI.status : 'LOADING';

export const selectPerfDataAPIUrl = (appState: AppState): string =>
  appState.perfData.status === 'AVAILABLE' ? appState.perfData.url : '';

// TODO: Improve strong typing on these:
export const selectTestMethodPerfUI = (
  appState: AppState,
): TestMethodPerfUI | null =>
  appState.perfDataUI.status === 'AVAILABLE'
    ? appState.perfDataUI.uidata.testmethod_perf
    : null;

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

export const selectDebugStatus = (appState: AppState): boolean =>
  appState.perfDataUI.status === 'AVAILABLE'
    ? appState.perfDataUI.uidata.debug
    : false;
