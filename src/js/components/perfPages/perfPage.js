// @flow

import React, { useEffect } from 'react';
import type { ComponentType } from 'react';
import get from 'lodash/get';
import { connect } from 'react-redux';
import { withRouter } from 'react-router-dom';
import { t } from 'i18next';
import BrandBand from '@salesforce/design-system-react/components/brand-band';
import BrandBannerBackground from '@salesforce-ux/design-system/assets/images/themes/oneSalesforce/banner-brand-default.png';
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

const gradient = 'linear-gradient(to top, rgba(221, 219, 218, 0) 0, #1B5F9E)';

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
        uiAvailable={uiAvailable}
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
});

const actions = {
  doPerfRESTFetch: (queryparts: {}) =>
    perfRESTFetch('/api/fast_testmethod_perf?', queryparts),
  doPerfREST_UI_Fetch: perfREST_UI_Fetch,
};

const WrappedPerfPage: ComponentType<{}> = withRouter(
  connect(
    select,
    actions,
  )(UnwrappedPerfPage),
);

export default WrappedPerfPage;
