// @flow

import type { AppState } from 'store';
import type { PerfDataState, PerfData_UI_State, LoadingStatus } from 'store/perfdata/reducer';
import get from 'lodash/get';


export const selectPerfState = (appState: AppState): PerfDataState => appState.perfData;
export const selectPerfUIStatus = (appState: AppState): LoadingStatus =>
        appState.perfDataUI ? appState.perfDataUI.status : "LOADING";

// TODO: Improve strong typing on these:
export const selectTestmethodPerfUI =
            (appState: AppState): {} =>
        get(appState, "perfDataUI.uidata.testmethod_perf");
export const selectTestmethodResultsUI =
            (appState: AppState): {} =>
        get(appState, "perfDataUI.uidata.testmethod_results");

export const selectBuildflowFiltersUI =
        (appState: AppState): {} =>
    get(appState, "perfDataUI.uidata.buildflow_filters");
