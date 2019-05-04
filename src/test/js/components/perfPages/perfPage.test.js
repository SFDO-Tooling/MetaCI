import React from 'react';
import { MemoryRouter } from 'react-router-dom';

import { renderWithRedux, storeWithApi } from '../../utils';

import testmethod_perf_UI_data from '../../api/testmethod_perf_UI.json';
import testmethod_perf_data from '../../api/testmethod_perf.json';

import PerfPage from 'components/perfPages/perfPage';


const initialStoreState = {
  user: {},
  perfData: { status: 'LOADING', perfdata: null, url: '' },
  perfDataUI: { status: 'LOADING', uidata: null },
};

describe('Perf Page', () => {
  test('Initial Render', () => {
    const { getByText } = renderWithRedux(
      <MemoryRouter>
        <PerfPage />
      </MemoryRouter>,
      initialStoreState,
      storeWithApi,
    );

    expect(getByText('Columns')).toBeVisible();
    expect(getByText('Filters')).toBeVisible();
    expect(getByText('Date Range')).toBeVisible();
    expect(getByText('Options')).toBeVisible();
  });
  test('Render UI without data', () => {
    const store = { ...initialStoreState, perfDataUI: testmethod_perf_UI_data };
    const { getByText } = renderWithRedux(
      <MemoryRouter>
        <PerfPage />
      </MemoryRouter>,
      store,
      storeWithApi,
    );

    expect(getByText('Columns')).toBeVisible();
    expect(getByText('Filters')).toBeVisible();
    expect(getByText('Date Range')).toBeVisible();
    expect(getByText('Options')).toBeVisible();
  });
  test('TODO: Render data without UI', () => {
    const store = { ...initialStoreState, perfData: testmethod_perf_data };

    const { getByText } = renderWithRedux(
      <MemoryRouter>
        <PerfPage />
      </MemoryRouter>,
      store,
      storeWithApi,
    );

    expect(getByText('Columns')).toBeVisible();
    expect(getByText('Filters')).toBeVisible();
    expect(getByText('Date Range')).toBeVisible();
    expect(getByText('Options')).toBeVisible();
  });
  test('TODO: Render data and UI', () => {
    const { getByText } = renderWithRedux(
      <MemoryRouter>
        <PerfPage />
      </MemoryRouter>,
      initialStoreState,
      storeWithApi,
    );

    expect(getByText('Columns')).toBeVisible();
    expect(getByText('Filters')).toBeVisible();
    expect(getByText('Date Range')).toBeVisible();
    expect(getByText('Options')).toBeVisible();
  });
});
