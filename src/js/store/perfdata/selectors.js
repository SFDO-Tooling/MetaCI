// @flow

import type { AppState } from 'store';
import type { PerfDataState, PerfData_UI_State } from 'store/perfdata/reducer';

export const selectPerfState = (appState: AppState): PerfDataState => appState.perfData;
export const selectPerf_UI_State = (appState: AppState): PerfData_UI_State => appState.perfDataUI;