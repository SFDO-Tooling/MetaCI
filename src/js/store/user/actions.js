// @flow
import type { ThunkAction } from 'redux-thunk';

import type { User } from 'store/user/reducer';

type LoginAction = { type: 'USER_LOGGED_IN', payload: User };
type LogoutAction = { type: 'USER_LOGGED_OUT' };
export type UserAction = LoginAction | LogoutAction;

export const login = (payload: User): LoginAction =>
  // Raven/Sentry is not yet enabled for this project.
  ({
    type: 'USER_LOGGED_IN',
    payload,
  });

export const logout = (): ThunkAction => (dispatch, _getState, { apiFetch }) =>
  apiFetch(window.api_urls.account_logout(), {
    method: 'POST',
  }).then(() =>
    // Raven/Sentry is not yet enabled for this project.
    dispatch({ type: 'USER_LOGGED_OUT' }),
  );
