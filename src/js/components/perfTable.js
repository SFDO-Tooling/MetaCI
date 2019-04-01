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
import type { PerfDataState } from 'store/perfdata/reducer';
import type { InitialProps } from 'components/utils';
import { t } from 'i18next';
import Spinner from '@salesforce/design-system-react/components/spinner';
import DataTable from '@salesforce/design-system-react/components/data-table';
import DataTableColumn from '@salesforce/design-system-react/components/data-table/column';
import DataTableCell from '@salesforce/design-system-react/components/data-table/cell';
import BrandBand from '@salesforce/design-system-react/components/brand-band';
import BrandBannerBackground from '@salesforce-ux/design-system/assets/images/themes/oneSalesforce/banner-brand-default.png';

import FieldPicker from './fieldPicker';
import FilterPicker from './filterPicker';
import PerfTableOptionsUI from './perfTableOptionsUI';

import { perfRESTFetch, perfREST_UI_Fetch } from 'store/perfdata/actions';

import { selectPerfState, selectPerf_UI_State } from 'store/perfdata/selectors';

const DEFAULT_COLUMNS = ["Method Name", "Duration"];


export const ShowRenderTime = () => null
// <p>{(new Date()).toString()}</p>


export class QueryParamHelpers{
  default_params: { [string]: mixed };

  constructor(default_params:{[string]: mixed}) {
    this.default_params = default_params;
  }

   get = (name?:string) => {
    let parts = { ...this.default_params, ...queryString.parse(window.location.search)};

    if(name){
      return parts[name];
    }else{
      return parts;
    }
  }

  set = (newQueryParts: {[string] : string | string[] | null | typeof undefined}) => {
    let qs = queryString.stringify({...this.get(), ...newQueryParts});
    window.history.pushState(null, "", window.location.pathname+"?"+qs);
  };
}


/**
 * Add iDs to table values for consumption by the SLDS DataTable
 * @param {*} rows hashes from database
 */
const addIds = (rows : {}[]) => {
  return rows.map((row, index)=>{return {...row, id: index.toString()}})
}

const PerfDataTableSpinner = ({status}) => {
  if(status === "PERF_DATA_LOADING"){
    return <Spinner
      size="small"
      variant="base"
      assistiveText={{ label: 'Small spinner' }}
    />
  }
  return null;
}

let default_query_params = {page_size: 10, include_fields : ["repo", "duration_average"]};
export const queryparams = new QueryParamHelpers(default_query_params);


type ReduxProps = {doPerfRESTFetch: Function,
                  doPerfREST_UI_Fetch: Function,
                  perfdatastate: PerfDataState,
                  perfdataUIstate:{}};
type SelfProps = {default_columns: string[]};

export const UnwrappedPerfTable = ({doPerfRESTFetch, doPerfREST_UI_Fetch,
                          perfdatastate, perfdataUIstate,
                          match, location, history, default_columns }:
                              ReduxProps & InitialProps & SelfProps) => {
    default_columns = default_columns || DEFAULT_COLUMNS;
  if ((perfdataUIstate && perfdataUIstate.status === "UI_DATA_ERROR") ||
    (perfdatastate && perfdatastate.status === "PERF_DATA_ERROR")){
    return <AuthError
        message= "Top Secret! Please ensure you are on the VPN and logged in to MetaCI."/>
    }

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
    if(perfdatastate && perfdatastate.perfdata){
      items = addIds(perfdatastate.perfdata.results);
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
     * Extract the page from the server-generated URL
     *
     * TODO: this code may be obsolete as of March 27
     *
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
                        get(perfdatastate, "perfdata.results.length") || -1;
    var previousPage:number|null = get(perfdatastate, "perfdata.previous");
    var nextPage:number|null = get(perfdatastate, "perfdata.next")

    /* https://appexchange.salesforce.com/listingDetail?listingId=a0N3A00000E9TBZUA3 */
    const PerfDataTableFooter = () => {
      return (
      <div className="slds-card__footer slds-grid" >
        { items.length>0 && perfdatastate && perfdatastate.perfdata &&
          <React.Fragment>
            <div className="slds-col slds-size--1-of-2"
                  style={{ textAlign: "left" }}>
                          Showing {(page * page_size).toString()} to {' '}
                                {Math.min((page + 1) * page_size, 1).toString()} {' '}
                          of  {get(perfdatastate, "perfdata.count").toString()} records
            </div>
            <div className="slds-col slds-size--1-of-2">
                      <button onClick={()=>doPerfRESTFetch(previousPage)}
                        className="slds-button slds-button--brand"
                        disabled={!previousPage}>Previous</button>
                      <button onClick={()=>doPerfRESTFetch(nextPage)}
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
      <ShowRenderTime/>
      <PerfTableOptionsUI
          fetchServerData={fetchServerData}
          key="thePerfAccordian"/>
			<div style={{ position: 'relative'}}>
            <ShowRenderTime/>
            <PerfDataTableSpinner status={get(perfdatastate, "status")}/>
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

const AuthError = ({message}:{message:string}) => {
  return <BrandBand
      id="brand-band-lightning-blue"
      className="slds-p-around_small"
      theme="lightning-blue"
      style={{textAlign:"center",
            backgroundImage: "url("+ BrandBannerBackground + "), linear- gradient(to top, rgba(221, 219, 218, 0) 0, #e8e8e8)"}}
    >
      <div className="slds-box slds-theme_default"
        style={{marginLeft:"auto", marginRight:"auto"}}>
        <h3 className="slds-text-heading_label slds-truncate">{message}</h3>
      </div>
      <div>
        <img src="https://i.gifer.com/G36W.gif" />
      </div>
    </BrandBand>
}

const select = (appState: AppState) => {
  return {
    perfdatastate: selectPerfState(appState),
    perfdataUIstate: selectPerf_UI_State(appState),
  }};

const actions = {
  doPerfRESTFetch: (url, queryparts) => perfRESTFetch(url || "/api/testmethod_perf?", queryparts),
  doPerfREST_UI_Fetch: perfREST_UI_Fetch,
};

const WrappedPerfTable: React.ComponentType<{}> = withRouter(connect(select, actions)(
  UnwrappedPerfTable,
));

export default WrappedPerfTable;