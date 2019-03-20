// @flow

import { combineReducers } from 'redux';
import type { CombinedReducer } from 'redux';

import userReducer from 'store/user/reducer';
import type { User } from 'store/user/reducer';

export type AppState = {
  +user: User,
};

type Action = { +type: string };

const reducer: CombinedReducer<AppState, Action> = combineReducers({
  user: userReducer,
});

export default reducer;
