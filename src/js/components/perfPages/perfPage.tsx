import { TestMethodPerfUI } from 'api/testmethod_perf_UI_JSON_schema';
import ErrorBoundary from 'components/error';
import get from 'lodash/get';
import React, { useEffect } from 'react';
import { ComponentType } from 'react';
import { connect } from 'react-redux';
import { withRouter } from 'react-router-dom';
import { RouteComponentProps } from 'react-router-dom';
import { AppState } from 'store';
import { perfREST_UI_Fetch,perfRESTFetch } from 'store/perfdata/actions';
import {
  LoadingStatus,
  PerfData_UI_State,
  PerfDataState,
} from 'store/perfdata/reducer';
import {
  selectPerfState,
  selectPerfUIState,
  selectPerfUIStatus,
  selectTestMethodPerfUI,
} from 'store/perfdata/selectors';

import DebugIcon from './debugIcon';
import PerfDataTable from './perfDataTable';
import PerfTableOptionsUI from './perfTableOptionsUI';
import { addIds,QueryParamHelpers } from './perfTableUtils';

export type ServerDataFetcher = (params?: {
  [Key: string]: string | string[] | null | typeof undefined;
}) => void;

type ReduxProps = {
  perfState: PerfDataState;
  perfUIState: PerfData_UI_State;
  perfUIStatus: LoadingStatus;
  testMethodPerfUI: TestMethodPerfUI;
  doPerfRESTFetch: (arg0: {}) => null;
  doPerfREST_UI_Fetch: typeof perfREST_UI_Fetch;
  // eslint-disable-next-line no-use-before-define
} & typeof actions;

interface SelfProps { default_columns: string[] }

export const UnwrappedPerfPage = ({
  doPerfRESTFetch,
  doPerfREST_UI_Fetch,
  perfState,
  perfUIState,
  testMethodPerfUI,
  perfUIStatus,
}: ReduxProps & RouteComponentProps & SelfProps) => {
  const uiAvailable = perfUIStatus === 'AVAILABLE';
  const queryparams = new QueryParamHelpers(
    get(testMethodPerfUI, 'defaults', {}),
  );
  if (uiAvailable && !testMethodPerfUI) {
    throw new Error('Store error');
  }

  if (perfUIStatus === 'ERROR') {
    const message =
      get(perfUIState, 'reason.reason') ||
      get(perfUIState, 'reason.error') ||
      '';
    throw new Error(message);
  }

  // Fetch the UI data
  useEffect(() => {
    /* Special case for getting repo name from URL
     * path into query params with other filters
     */
    const pathParts = window.location.pathname.split('/');
    const repo = pathParts[pathParts.length - 2];
    queryparams.set({ repo });
    doPerfREST_UI_Fetch({ repo });
  }, []);

  // Fetch the real data
  useEffect(() => {
    if (uiAvailable) {
      doPerfRESTFetch({ ...queryparams.getAll() });
    }
  }, [uiAvailable]);

  let results: {}[];
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
    const page = (params && params.page) || 1;
    queryparams.set({
      ...queryparams.getAll(),
      ...params,
      page: page.toString(),
    });
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
      <ErrorBoundary>
        <div style={{ position: 'relative' }}>
          <PerfDataTable
            fetchServerData={fetchServerData}
            perfState={perfState}
            queryparams={queryparams}
            items={results}
          />
        </div>{' '}
      </ErrorBoundary>
      <DebugIcon />
    </div>
  );
};

const select = (appState: AppState) => ({
  perfState: selectPerfState(appState),
  testMethodPerfUI: selectTestMethodPerfUI(appState),
  perfUIStatus: selectPerfUIStatus(appState),
  perfUIState: selectPerfUIState(appState),
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
