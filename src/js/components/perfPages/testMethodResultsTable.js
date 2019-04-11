// This file is not finished and is currently unused.

import * as React from 'react';
import { connect } from 'react-redux';
import { withRouter } from 'react-router-dom';
import type { AppState } from 'store';
import type { InitialProps } from 'components/utils';
import { perfRESTFetch, perfREST_UI_Fetch } from 'store/perfdata/actions';
import {
  selectPerfState,
  selectPerfUIStatus,
  selectTestMethodResultsUI,
} from 'store/perfdata/selectors';

import { UnwrappedPerfPage as PerfPage } from './perfPage';

const DEFAULT_COLUMNS = ['Date', 'Method Name', 'Duration'];

export const TestMethodResultsTable: typeof PerfPage = ({
  doPerfRESTFetch,
  doPerfREST_UI_Fetch,
  perfdatastate,
  perfdataUIstate,
  match,
  location,
  history,
}) =>
  PerfPage({
    doPerfRESTFetch,
    doPerfREST_UI_Fetch,
    perfdatastate,
    perfdataUIstate,
    match,
    location,
    history,
    default_columns: DEFAULT_COLUMNS,
  });

const select = (appState: AppState) => ({
  perfdatastate: selectPerfState(appState),
  perfdataUIstate: selectPerf_UI_State(appState),
});

const actions = {
  doPerfRESTFetch: (url, queryparts) =>
    perfRESTFetch(url || '/api/testmethod_results?', queryparts),
  doPerfREST_UI_Fetch: perfREST_UI_Fetch,
};

const WrappedTestMethodResultsTable: React.ComponentType<{}> = withRouter(
  connect(
    select,
    actions,
  )(TestMethodResultsTable),
);

export default WrappedTestMethodResultsTable;
