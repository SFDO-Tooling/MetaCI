// @flow

import { combineReducers } from 'redux';
import type { CombinedReducer } from 'redux';

import userReducer from 'store/user/reducer';
import perfDataReducer from 'store/perfdata/reducer'
import type { User } from 'store/user/reducer';
import type { PerfDataState } from 'store/perfdata/reducer';

export type AppState = {
  +user: User,
  +perfData: PerfDataState,
};

type Action = { +type: string };

const reducer: CombinedReducer<AppState, Action> = combineReducers({
  user: userReducer,
  perfData: perfDataReducer,
});

export default reducer;
