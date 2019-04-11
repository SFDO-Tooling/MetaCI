// @flow

import { combineReducers } from 'redux';
import type { CombinedReducer } from 'redux';
import userReducer from 'store/user/reducer';
import { perfDataReducer, perfDataUIReducer } from 'store/perfdata/reducer';
import type { User } from 'store/user/reducer';
import type { PerfDataState, PerfData_UI_State } from 'store/perfdata/reducer';

export type AppState = {
  +user: User,
  +perfData: PerfDataState,
  +perfDataUI: PerfData_UI_State,
};

type Action = { +type: string };

const reducer: CombinedReducer<AppState, Action> = combineReducers({
  user: userReducer,
  perfData: perfDataReducer,
  perfDataUI: perfDataUIReducer,
});

export default reducer;
