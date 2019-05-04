import React from 'react';
import { MemoryRouter } from 'react-router-dom';
import fetchMock from 'fetch-mock';

import { renderWithRedux, storeWithApi } from '../../utils';
import testmethod_perf_UI_data from '../../api/testmethod_perf_UI.json';
import testmethod_perf_data from '../../api/testmethod_perf.json';

import PerfPage from 'components/perfPages/perfPage';

const initialStoreState = {
  user: {},
  perfData: { status: 'LOADING', perfdata: null, url: '' },
  perfDataUI: { status: 'LOADING', uidata: null },
};

const mockHTTP = () => {
  fetchMock.getOnce('begin:/api/testmethod_perf', 200);
  fetchMock.getOnce('begin:/api/testmethod_perf_UI', 200);
};

describe('Perf Page', () => {
  test('Initial Render', () => {
    mockHTTP();
    const { getByText, queryByText } = renderWithRedux(
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
    expect(queryByText('Success percentage above')).toBeNull();
  });
  test('Render UI from store without method data', () => {
    const store = {
      ...initialStoreState,
      perfDataUI: { status: 'AVAILABLE', uidata: testmethod_perf_UI_data },
    };
    fetchMock.mock('*', 200);
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
    expect(getByText('Success percentage above')).toBeVisible();
  });
  test('Render data from store without UI', () => {
    const store = {
      ...initialStoreState,
      perfData: { status: 'AVAILABLE', perfdata: testmethod_perf_data },
    };

    fetchMock.mock('*', 200);
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
    expect(getByText('accFinderBuildsCorrectSearchQuery')).toBeVisible();
  });
  test('Render data and UI both from store', () => {
    fetchMock.mock('*', 200);
    const store = {
      ...initialStoreState,
      perfData: { status: 'AVAILABLE', perfdata: testmethod_perf_data },
      perfDataUI: { status: 'AVAILABLE', uidata: testmethod_perf_UI_data },
    };
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
    expect(getByText('accFinderBuildsCorrectSearchQuery')).toBeVisible();
  });
  test('Render data and UI from server', () => {

  });
});
