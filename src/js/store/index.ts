// @flow

import { combineReducers } from 'redux';
import type { CombinedReducer } from 'redux';

import { perfDataReducer, perfDataUIReducer } from 'store/perfdata/reducer';
import type { PerfDataState, PerfData_UI_State } from 'store/perfdata/reducer';

export type AppState = {
  +perfData: PerfDataState,
  +perfDataUI: PerfData_UI_State,
};

type Action = { +type: string };

const reducer: CombinedReducer<AppState, Action> = combineReducers({
  perfData: perfDataReducer,
  perfDataUI: perfDataUIReducer,
});

export default reducer;
