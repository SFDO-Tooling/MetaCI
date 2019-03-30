// @flow
 /* flowlint
  *   untyped-import:off
  */

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
import Spinner from '@salesforce/design-system-react/components/spinner';
import DataTable from '@salesforce/design-system-react/components/data-table';
import DataTableColumn from '@salesforce/design-system-react/components/data-table/column';
import DataTableCell from '@salesforce/design-system-react/components/data-table/cell';

import PerfTableOptionsUI from './perfTableOptionsUI';

import { perfRESTFetch, perfREST_UI_Fetch } from 'store/perfdata/actions';

import { selectPerfState,
         selectPerfUIStatus,
         selectTestmethodPerfUI,
       } from 'store/perfdata/selectors';

import { QueryParamHelpers, addIds } from './perfTableUtils';

import PerfDataTable from './perfDataTable';

const DEFAULT_COLUMNS = ["Method Name", "Duration"];

// TODO: Stronger typing in these
type ReduxProps = {|
    perfState: PerfDataState,
    perfUIStatus: LoadingStatus ,
    testmethodPerfUI: {}
  |} & typeof actions;


type SelfProps = {default_columns: string[]};

export const UnwrappedPerfPage = ({doPerfRESTFetch, doPerfREST_UI_Fetch,
                          perfState, testmethodPerfUI,
                           perfUIStatus,
                          match, location, history }:
                              ReduxProps & InitialProps & SelfProps) => {
    let uiAvailable = perfUIStatus=== "AVAILABLE";
    let queryparams = new QueryParamHelpers(get(testmethodPerfUI, "defaults", {}));

    let queryParts = queryparams.get;
    let changeUrl = queryparams.set;

    useEffect(() => {
      doPerfRESTFetch(null, queryParts());
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
    const fetchServerData = (params?: {[string]: string | string[] | null | typeof undefined}) => {
      changeUrl({...queryParts(), ...params});
      doPerfRESTFetch(null, queryParts());
    }

    return <div key="perfContainerDiv">
      <PerfTableOptionsUI
          fetchServerData={fetchServerData}
          uiAvailable={uiAvailable}
          testmethodPerfUI={testmethodPerfUI}
          queryparams={queryparams}
          key="thePerfAccordian"/>
			<div style={{ position: 'relative'}}>
        <PerfDataTable/>
      </div>
    </div>
  };

const select = (appState: AppState) => {
  return {
    perfState: selectPerfState(appState),
    testmethodPerfUI: selectTestmethodPerfUI(appState),
    perfUIStatus: selectPerfUIStatus(appState)
  }};


const actions = {
  doPerfRESTFetch: (url, queryparts) => perfRESTFetch(url || "/api/testmethod_perf?", queryparts),
  doPerfREST_UI_Fetch: perfREST_UI_Fetch,
};

const WrappedPerfPage: React.ComponentType<{}> = withRouter(connect(select, actions)(
  UnwrappedPerfPage,
));

export default WrappedPerfPage;