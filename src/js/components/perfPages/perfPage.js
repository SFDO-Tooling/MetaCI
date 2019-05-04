// @flow

import React, { useEffect } from 'react';
import type { ComponentType } from 'react';
import get from 'lodash/get';
import { connect } from 'react-redux';
import { withRouter } from 'react-router-dom';
import type { Match, RouterHistory } from 'react-router-dom';

import DebugIcon from './debugIcon';
import PerfTableOptionsUI from './perfTableOptionsUI';
import PerfDataTable from './perfDataTable';
import { QueryParamHelpers, addIds } from './perfTableUtils';

import type { AppState } from 'store';
import type { PerfDataState, LoadingStatus } from 'store/perfdata/reducer';
import { perfRESTFetch, perfREST_UI_Fetch } from 'store/perfdata/actions';
import type { TestMethodPerfUI } from 'api/testmethod_perf_UI_JSON_schema';
import {
  selectPerfState,
  selectPerfUIStatus,
  selectTestMethodPerfUI,
} from 'store/perfdata/selectors';

export type ServerDataFetcher = (params?: {
  [string]: string | string[] | null | typeof undefined,
}) => void;

// TODO: Stronger typing in these
type ReduxProps = {|
  perfState: PerfDataState,
  perfUIStatus: LoadingStatus,
  testMethodPerfUI: TestMethodPerfUI,
  doPerfRESTFetch: ({}) => null,
  doPerfREST_UI_Fetch: typeof perfREST_UI_Fetch,
  // eslint-disable-next-line no-use-before-define
|} & typeof actions;

export type RouterProps = {| match: Match, history: RouterHistory |};

type SelfProps = { default_columns: string[] };

export const UnwrappedPerfPage = ({
  doPerfRESTFetch,
  doPerfREST_UI_Fetch,
  perfState,
  testMethodPerfUI,
  perfUIStatus,
}: ReduxProps & RouterProps & SelfProps) => {
  const uiAvailable = perfUIStatus === 'AVAILABLE';
  const queryparams = new QueryParamHelpers(
    get(testMethodPerfUI, 'defaults', {}),
  );
  if (uiAvailable && !testMethodPerfUI) {
    throw new Error('Store error');
  }

  if (perfUIStatus === 'ERROR' || (perfState && perfState.status === 'ERROR')) {
    const message =
      get(perfState, 'reason.reason') || get(perfState, 'reason.error') || '';
    throw new Error(message);
  }

  // Fetch the data: both UI configuration and also actual data results
  useEffect(() => {
    /* Special case for getting repo name from URL
     * path into query params with other filters
     */
    const pathParts = window.location.pathname.split('/');
    const repo = pathParts[pathParts.length - 2];
    queryparams.set({ repo });
    doPerfRESTFetch({ ...queryparams.getAll(), repo });
    doPerfREST_UI_Fetch();
  }, []);

  let results;
  if (
    perfState &&
    perfState.perfdata &&
    Array.isArray(perfState.perfdata.results)
  ) {
    results = addIds(perfState.perfdata.results);
  } else {
    results = [];
  }

  const fetchServerData: ServerDataFetcher = params => {
    // its okay to pass null or undefined because query-string has reasonable
    // and useful interpretations of both of them.
    queryparams.set({ ...queryparams.getAll(), ...params });
    doPerfRESTFetch(queryparams.getAll());
  };

  return (
    <div key="perfContainerDiv">
      <PerfTableOptionsUI
        fetchServerData={fetchServerData}
        testMethodPerfUI={testMethodPerfUI}
        queryparams={queryparams}
        key="thePerfAccordian"
      />
      <div style={{ position: 'relative' }}>
        <PerfDataTable
          fetchServerData={fetchServerData}
          perfState={perfState}
          queryparams={queryparams}
          items={results}
        />
      </div>{' '}
      <DebugIcon />
    </div>
  );
};


const select = (appState: AppState) => ({
  perfState: selectPerfState(appState),
  testMethodPerfUI: selectTestMethodPerfUI(appState),
  perfUIStatus: selectPerfUIStatus(appState),
});

const actions = {
  doPerfRESTFetch: (queryparts: {}) =>
    perfRESTFetch('/api/testmethod_perf?', queryparts),
  doPerfREST_UI_Fetch: perfREST_UI_Fetch,
};

const WrappedPerfPage: ComponentType<{}> = withRouter(
  connect(
    select,
    actions,
  )(UnwrappedPerfPage),
);

export default WrappedPerfPage;
