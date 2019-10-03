import React from 'react';

import { renderWithRedux, storeWithApi } from '../../utils';

import testmethod_perf_UI_data from '../../api/testmethod_perf_UI.json';

import { QueryParamHelpers } from 'components/perfPages/perfTableUtils';
import PerfTableOptionsUI from 'components/perfPages/perfTableOptionsUI';

describe('Perf Table Options', () => {
  test('Initial Render', () => {
    const queryparams = new QueryParamHelpers({});

    const { getByText } = renderWithRedux(
      <PerfTableOptionsUI
        fetchServerData={() => {}}
        queryparams={queryparams}
        key="thePerfAccordian"
      />,
      { perfDataUI: {} },
      storeWithApi,
    );

    expect(getByText('Columns')).toBeVisible();
    expect(getByText('Filters')).toBeVisible();
    expect(getByText('Date Range')).toBeVisible();
    expect(getByText('Options')).toBeVisible();
  });
  test('Throws if store state is inconsistent', () => {
    const queryparams = new QueryParamHelpers({});

    const shouldThrow = () => {
      renderWithRedux(
        <PerfTableOptionsUI
          fetchServerData={() => {}}
          queryparams={queryparams}
          key="thePerfAccordian"
        />,
        {
          perfDataUI: {
            status: 'AVAILABLE',
            uidata: {},
          },
        },
        storeWithApi,
      );
    };
    expect(shouldThrow).toThrow();
  });
  test('Renders simple UI properly', () => {
    const queryparams = new QueryParamHelpers({});

    const { getByPlaceholderText } = renderWithRedux(
      <PerfTableOptionsUI
        fetchServerData={() => {}}
        testMethodPerfUI={testmethod_perf_UI_data.testmethod_perf}
        queryparams={queryparams}
        key="thePerfAccordian"
      />,
      {
        perfDataUI: {
          status: 'AVAILABLE',
          uidata: testmethod_perf_UI_data,
        },
      },
      storeWithApi,
    );
    expect(getByPlaceholderText('Select an Option')).toBeVisible();
  });
});
