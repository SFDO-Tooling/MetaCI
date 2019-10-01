// @flow

import React, { useEffect } from 'react';
import type { ComponentType } from 'react';
import get from 'lodash/get';
import { connect } from 'react-redux';
import { withRouter } from 'react-router-dom';
import BrandBand from '@salesforce/design-system-react/components/brand-band';
import BrandBannerBackground from '@salesforce-ux/design-system/assets/images/themes/oneSalesforce/banner-brand-default.png';
import type { Match, RouterHistory } from 'react-router-dom';

import DebugIcon from './debugIcon';
import PerfTableOptionsUI from './perfTableOptionsUI';
import PerfDataTable from './perfDataTable';
import { QueryParamHelpers, addIds } from './perfTableUtils';

import ErrorBoundary from 'components/error';
import type { AppState } from 'store';
import type {
  PerfDataState,
  PerfData_UI_State,
  LoadingStatus,
} from 'store/perfdata/reducer';
import { perfRESTFetch, perfREST_UI_Fetch } from 'store/perfdata/actions';
import type { TestMethodPerfUI } from 'api/testmethod_perf_UI_JSON_schema';
import {
  selectPerfState,
  selectPerfUIState,
  selectPerfUIStatus,
  selectTestMethodPerfUI,
} from 'store/perfdata/selectors';

export type ServerDataFetcher = (params?: {
  [string]: string | string[] | null | typeof undefined,
}) => void;

const gradient = 'linear-gradient(to top, rgba(221, 219, 218, 0) 0, #1B5F9E)';

// TODO: Stronger typing in these
type ReduxProps = {|
  perfState: PerfDataState,
  perfUIState: PerfData_UI_State,
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
  perfUIState,
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
    doPerfREST_UI_Fetch();
  }, []);

  // Fetch the real data
  useEffect(() => {
    if (uiAvailable) {
      doPerfRESTFetch({ ...queryparams.getAll() });
    }
  }, [uiAvailable]);

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
    const page = (params && params.page) || 1;
    queryparams.set({ ...queryparams.getAll(), ...params, page });
    doPerfRESTFetch(queryparams.getAll());
  };

  return (
    <div key="perfContainerDiv">
      <PerfTableOptionsUI
        fetchServerData={fetchServerData}
        uiAvailable={uiAvailable}
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

const AuthError = ({ message }: { message: string }) => (
  <BrandBand
    id="brand-band-lightning-blue"
    className="slds-p-around_small"
    theme="lightning-blue"
    style={{
      textAlign: 'center',
      backgroundImage: `url(${BrandBannerBackground}), ${gradient}`,
    }}
  >
    <div
      className="slds-box slds-theme_default"
      style={{ marginLeft: 'auto', marginRight: 'auto' }}
    >
      <h3 className="slds-text-heading_label slds-truncate">{message}</h3>
    </div>
    <div>
      <video
        onEnded={evt => {
          evt.target.load();
          evt.target.play();
        }}
        loop
        autoPlay
        muted
        playsInline
      >
        <source
          src="/static/images/NoNoNo.mp4"
          itemProp="contentUrl"
          type="video/mp4"
        />
      </video>
    </div>
  </BrandBand>
);

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
