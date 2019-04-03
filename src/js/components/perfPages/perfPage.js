// @flow

import * as React from 'react';
import { useEffect, useState } from 'react';
import get from 'lodash/get';
import zip from 'lodash/zip';

import queryString from 'query-string';

import { connect } from 'react-redux';
import { withRouter } from 'react-router-dom';
import type { AppState } from 'store';
import type { PerfDataState, LoadingStatus } from 'store/perfdata/reducer';
import type { InitialProps } from 'components/utils';
import { t } from 'i18next';

// flowlint  untyped-import:off
import Spinner from '@salesforce/design-system-react/components/spinner';
import DataTable from '@salesforce/design-system-react/components/data-table';
import DataTableColumn from '@salesforce/design-system-react/components/data-table/column';
import DataTableCell from '@salesforce/design-system-react/components/data-table/cell';
import BrandBand from '@salesforce/design-system-react/components/brand-band';
import BrandBannerBackground from '@salesforce-ux/design-system/assets/images/themes/oneSalesforce/banner-brand-default.png';
// flowlint  untyped-import:error

import PerfTableOptionsUI from './perfTableOptionsUI';

import { perfRESTFetch, perfREST_UI_Fetch } from 'store/perfdata/actions';

import { selectPerfState,
         selectPerfUIStatus,
         selectTestmethodPerfUI,
       } from 'store/perfdata/selectors';

import { QueryParamHelpers, addIds } from './perfTableUtils';

import PerfDataTable from './perfDataTable';

const DEFAULT_COLUMNS = ["Method Name", "Duration"];

export type ServerDataFetcher =
      (params?: { [string]: string | string[] | null | typeof undefined })
        => void

// TODO: Stronger typing in these
type ReduxProps = {|
    perfState: PerfDataState,
    perfUIStatus: LoadingStatus,
    testmethodPerfUI: {},
    doPerfRESTFetch: ({})=>null,
    doPerfREST_UI_Fetch: typeof perfREST_UI_Fetch,


  |} & typeof actions;


type SelfProps = {default_columns: string[]};

export const UnwrappedPerfPage = ({doPerfRESTFetch, doPerfREST_UI_Fetch,
                          perfState, testmethodPerfUI,
                           perfUIStatus,
                          match, location, history }:
                              ReduxProps & InitialProps & SelfProps) => {
    let uiAvailable = perfUIStatus=== "AVAILABLE";
    let queryparams = new QueryParamHelpers(get(testmethodPerfUI, "defaults", {}));

    // These shortcuts are not very helpful. Replace them.
    let queryParts = queryparams.getAll;
    let changeUrl = queryparams.set;

    if ((perfUIStatus === "ERROR") ||
        (perfState && perfState.status === "ERROR")) {
        return <AuthError
          message="Top Secret! Please ensure you are on the VPN and logged in to MetaCI."
          />
    }

    useEffect(() => {
      doPerfRESTFetch(queryParts());
      doPerfREST_UI_Fetch();
      let pathParts = window.location.pathname.split("/");

      /* Special case for getting repo name from URL
        * path into query params with other filters
        */
      changeUrl({repo: pathParts[pathParts.length-2]})
    }, []);

    var items;
    if(perfState && perfState.perfdata
        && Array.isArray(perfState.perfdata.results)){
      items = addIds(perfState.perfdata.results);
    }else{
      items = [];
    }

    // its okay to pass null or undefined because query-string has reasonable
    // and useful interpretations of both of them.
    const fetchServerData: ServerDataFetcher = (params) => {
      changeUrl({...queryParts(), ...params});
      doPerfRESTFetch(queryParts());
    }

    return <div key="perfContainerDiv">
      <PerfTableOptionsUI
          fetchServerData={fetchServerData}
          uiAvailable={uiAvailable}
          testmethodPerfUI={testmethodPerfUI}
          queryparams={queryparams}
          key="thePerfAccordian"/>
			<div style={{ position: 'relative'}}>
        <PerfDataTable
          fetchServerData={fetchServerData}
          perfState={perfState}
          queryparams={queryparams}
          items={items}/>
      </div>
    </div>
};

const AuthError = ({ message }: { message: string }) => {
  return <BrandBand
    id="brand-band-lightning-blue"
    className="slds-p-around_small"
    theme="lightning-blue"
    style={{
      textAlign: "center",
      backgroundImage: "url(" + BrandBannerBackground + "), linear-gradient(to top, rgba(221, 219, 218, 0) 0, #1B5F9E)"
    }}
  >
    <div className="slds-box slds-theme_default"
      style={{ marginLeft: "auto", marginRight: "auto" }}>
      <h3 className="slds-text-heading_label slds-truncate">{message}</h3>
    </div>
    <div>
      <img src="https://i.gifer.com/G36W.gif" />
    </div>
  </BrandBand>
}

const select = (appState: AppState) => {
  return {
    perfState: selectPerfState(appState),
    testmethodPerfUI: selectTestmethodPerfUI(appState),
    perfUIStatus: selectPerfUIStatus(appState)
  }};


const actions = {
  doPerfRESTFetch: (queryparts:{}) => perfRESTFetch("/api/testmethod_perf?", queryparts),
  doPerfREST_UI_Fetch: perfREST_UI_Fetch,
};

const WrappedPerfPage: React.ComponentType<{}> = withRouter(connect(select, actions)(
  UnwrappedPerfPage,
));

export default WrappedPerfPage;