// @flow

import type { AppState } from 'store';
import type { User } from 'store/user/reducer';

export const selectUserState = (appState: AppState): User => appState.user;
