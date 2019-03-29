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

import PerfDataTableOptionsUI from './perfTableOptionsUI';

import { perfRESTFetch, perfREST_UI_Fetch } from 'store/perfdata/actions';

import { selectPerfState,
         selectPerfUIStatus,
         selectTestmethodPerfUI,
       } from 'store/perfdata/selectors';

import { QueryParamHelpers, addIds } from './perfTableUtils';

const DEFAULT_COLUMNS = ["Method Name", "Duration"];

type SpinnerProps = {
  status: LoadingStatus;
}

const PerfDataTableSpinner = ({status}) => {
  console.log("STATUS", status);
  if(status === "LOADING"){
    return <Spinner
      size="small"
      variant="base"
      assistiveText={{ label: 'Small spinner' }}
    />
  }
  return null;
}

// TODO: Stronger typing in these
type ReduxProps = {|
    perfState: PerfDataState | {},
    perfUIStatus: LoadingStatus ,
    testmethodPerfUI: {}
  |} & typeof actions;


type SelfProps = {default_columns: string[]};

export const UnwrappedPerfDataTable = ({doPerfRESTFetch, doPerfREST_UI_Fetch,
                          perfState, testmethodPerfUI,
                           perfUIStatus,
                          match, location, history }:
                              ReduxProps & InitialProps & SelfProps) => {
    let uiAvailable = perfUIStatus=== "AVAILABLE";
    console.log("ST3", perfUIStatus);
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


    /*
     * Extract the page from the server-generated URL and ensure it is
     * browser URL before fetching it.
     */
    const goPageFromUrl = (url: string) => {
      var qs = url.split("?", 2)[1];
      var qParts = queryString.parse(qs);
      var page = qParts["page"];
      if(Array.isArray(page) ){
        fetchServerData({page: page[1]});
      }else if(typeof page === 'string' ){
        fetchServerData({page});
      }else{
        fetchServerData({page: undefined});
      }
    };

    var page = parseInt(queryParts()["page"]||"1") - 1;
    var custom_page_size = queryParts("page_size");
    var page_size = custom_page_size ? parseInt(custom_page_size) :
                        get(perfState, "perfdata.results.length") || -1;
    var previousPage:string|null = get(perfState, "perfdata.previous");
    var nextPage:string|null = get(perfState, "perfdata.next")

    /* https://appexchange.salesforce.com/listingDetail?listingId=a0N3A00000E9TBZUA3 */
    const PerfDataTableFooter = () => {
      return (
      <div className="slds-card__footer slds-grid" >
        { items.length>0 && perfState && !!(perfState.perfdata) &&
          <React.Fragment>
            <div className="slds-col slds-size--1-of-2"
                  style={{ textAlign: "left" }}>
                          Showing {(page * page_size).toString()} to {' '}
                                {((page + 1) * page_size).toString()} {' '}
                          of  {get(perfState, "perfdata.count").toString()} records
            </div>
            <div className="slds-col slds-size--1-of-2">
                      <button onClick={()=>goPageFromUrl(previousPage)}
                        className="slds-button slds-button--brand"
                        disabled={!previousPage}>Previous</button>
                      <button onClick={()=>goPageFromUrl(nextPage)}
                        className="slds-button slds-button--brand"
                        disabled={!nextPage}>Next</button>
            </div>
          </React.Fragment>
        }
      </div>
    )}

    const columns = () => {
      let columns;
      if(items.length>0){
        let columnNames = Object.keys(items[0]).filter((item)=>item!="id");
        return zip(columnNames, columnNames);
      }else{
        // these are really just for looks. If there are no items, they
        // don't matter. TODO: use included_columns for this instead.
        let default_columns = queryParts("include_fields") ||
                              ["Method Name", "Duration"];
        return zip(default_columns, default_columns)
      }
    }

    const PerfDataColumns = () => {
      return (
          columns().map(([name, label])=>
          {

            let isSorted:bool = false, sortDirection:string|null = null;

            if(queryParts()["o"]===name){
              isSorted = true;
              sortDirection = "asc";
            }else if(queryParts()["o"]==="-"+name){
              isSorted = true;
              sortDirection = "desc";
            }

            return  <DataTableColumn
                          key={name}
                          label={label}
                          property={name}
                          sortable
                          isSorted={isSorted}
                          sortDirection={sortDirection}
                        ></DataTableColumn>
          }
      ))
    }

    const doSort = (sortColumn, ...rest) => {
      var sortProperty = sortColumn.property;
      const sortDirection = sortColumn.sortDirection;

      if (sortDirection === 'desc') {
        sortProperty = "-" + sortProperty
      }
      fetchServerData({o: sortProperty, page: '1'});
    };
    return <div key="perfContainerDiv">
			<div style={{ position: 'relative'}}>
            <PerfDataTableSpinner status={perfState.status}/>
            <DataTable items={items}
                fixedLayout={true}
                onSort={doSort}
              id="perfDataTable">
            {PerfDataColumns()}
            </DataTable>
            <PerfDataTableFooter/>
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

const WrappedPerfDataTable: React.ComponentType<{}> = withRouter(connect(select, actions)(
  UnwrappedPerfDataTable,
));

export default WrappedPerfDataTable;