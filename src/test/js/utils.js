import { render } from '@testing-library/react';
import React from 'react';
import { Provider } from 'react-redux';
import configureStore from 'redux-mock-store';
import thunk from 'redux-thunk';

import getApiFetch from '@/api/api_fetch';

const mockStore = configureStore([]);

export const renderWithRedux = (
  ui,
  initialState = {},
  customStore = mockStore,
  rerender = false,
) => {
  const store = customStore(initialState);
  const renderFn = rerender ? rerender : render;
  return {
    ...renderFn(<Provider store={store}>{ui}</Provider>),
    // adding `store` to the returned utilities to allow us
    // to reference it in our tests (just try to avoid using
    // this to test implementation details).
    store,
  };
};

export const storeWithApi = configureStore([
  thunk.withExtraArgument({
    apiFetch: getApiFetch(),
  }),
]);
