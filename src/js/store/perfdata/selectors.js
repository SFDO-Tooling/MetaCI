// @flow

import type { AppState } from 'store';
import type { PerfData } from 'store/perfdata/reducer';

export const selectUserState = (appState: AppState): PerfData => appState.perfData;
