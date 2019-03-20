// @flow

import type { AppState } from 'store';
import type { PerfDataState } from 'store/perfdata/reducer';

export const selectPerfState = (appState: AppState): PerfDataState => appState.perfData;
