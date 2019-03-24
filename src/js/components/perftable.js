// @flow
 /* flowlint
  *   untyped-import:off
  */

import * as React from 'react';
import * as ReactDOM from 'react-dom';
import { useEffect, useState } from 'react';
import get from 'lodash/get';
import zip from 'lodash/zip';
import debounce from 'lodash/debounce';

import queryString from 'query-string';

import { connect } from 'react-redux';
import { withRouter } from 'react-router-dom';
import type { AppState } from 'store';
import type { InitialProps } from 'components/utils';
import { t } from 'i18next';
import Spinner from '@salesforce/design-system-react/components/spinner';
import DataTable from '@salesforce/design-system-react/components/data-table';
import DataTableColumn from '@salesforce/design-system-react/components/data-table/column';
import DataTableCell from '@salesforce/design-system-react/components/data-table/cell';
import Accordion from '@salesforce/design-system-react/components/accordion'; 
import AccordionPanel from '@salesforce/design-system-react/components/accordion/panel'; 
import Input from '@salesforce/design-system-react/components/input'; 
import Tooltip from '@salesforce/design-system-react/components/tooltip'; 

import FieldPicker from './fieldPicker';
import FilterPicker from './filterPicker';
import DateRangePicker from './dateRangePicker';
import PerfTableOptionsUI from './perfTableOptionsUI';

import { perfRESTFetch, perfREST_UI_Fetch } from 'store/perfdata/actions';

import { selectPerfState, selectPerf_UI_State } from 'store/perfdata/selectors';

const default_columns = ["Method Name", "Duration"];


export const ShowRenderTime = () =>
 <p>{(new Date()).toString()}</p>

export const default_query_params = {page_size: 10, include_fields : ["repo", "duration_average"]};

export const queryParts = (name?:string) => {
  let parts = { ...default_query_params, ...queryString.parse(window.location.search)};
  if(name){
    return parts[name];
  }else{
    return parts;
  }
}


/**
 * Add iDs to table values for consumption by the SLDS DataTable
 * @param {*} rows hashes from database
 */
const addIds = (rows : [{[string]: mixed}]) => {
  return rows.map((row, index)=>{return {...row, id: index.toString()}})
}

const PerfDataTableSpinner = ({status}) => {
  useEffect(() => {
    return(()=>{console.log("UNMOUNTING Spinner")});
  });
  if(status === "PERF_DATA_LOADING"){
    return <Spinner
      size="small"
      variant="base"
      assistiveText={{ label: 'Small spinner' }}
    />
  }
  return null;
}

const PerfTable = ({doPerfRESTFetch, doPerfREST_UI_Fetch, 
                          perfdatastate, perfdataUIstate,
                          match, location, history }) => {
    console.log("Here we go");
    useEffect(() => {
        doPerfRESTFetch(null, queryParts());
        return(()=>{console.log("UNMOUNTING PerfTable 1")});
      }, []);
    useEffect(()=>{
      doPerfREST_UI_Fetch();
      return(()=>{console.log("UNMOUNTING PerfTable 2")});
    }, []);


    var items;
    if(perfdatastate && perfdatastate.perfdata){
      items = addIds(perfdatastate.perfdata.results);
    }else{
      items = [];
    }

    const getDataFromQueryParams = (params?: {[string]: string | string[]}) => {
      changeUrl({...queryParts(), ...params});
      doPerfRESTFetch(null, queryParts());
    }
  
    const changeUrl = (newQueryParts: {[string] : string | string[] | null | typeof undefined}) => {
      history.push({
         pathname: window.location.pathname,
        search: queryString.stringify({...queryParts(), ...newQueryParts})
      })
    };
  

    const goPageFromUrl = (url: string) => {
      var qs = url.split("?", 2)[1];
      var qParts = queryString.parse(qs);
      var page = qParts["page"];
      if(Array.isArray(page) ){
        getDataFromQueryParams({page: page[1]});
      }else if(typeof page === 'string' ){
        getDataFromQueryParams({page});
      }
    };  

    var page = parseInt(queryParts()["page"]||"1") - 1;
    var custom_page_size = queryParts("page_size");
    var page_size = custom_page_size ? parseInt(custom_page_size) : 
                        get(perfdatastate, "perfdata.results.length") || -1;

    /* https://appexchange.salesforce.com/listingDetail?listingId=a0N3A00000E9TBZUA3 */
    const PerfDataTableFooter = () => {
      useEffect(() => {
        return ()=>{console.log("Unmounting footer");}
      });
      return (
      <div className="slds-card__footer slds-grid" >
        { items.length>0 &&
          <React.Fragment>
            <div className="slds-col slds-size--1-of-2"
                  style={{ textAlign: "left" }}>
                          Showing {page * page_size} to {' '}
                                {Math.min((page + 1) * page_size, )} {' '}
                          of  {perfdatastate.perfdata.count} records
            </div>
            <div className="slds-col slds-size--1-of-2">
                      <button onClick={()=>goPageFromUrl(perfdatastate.perfdata.previous)}
                        className="slds-button slds-button--brand"
                        disabled={!get(perfdatastate, "perfdata.previous")}>Previous</button>
                      <button onClick={()=>goPageFromUrl(perfdatastate.perfdata.next)}
                        className="slds-button slds-button--brand"
                        disabled={!get(perfdatastate, "perfdata.next")}>Next</button>
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
      getDataFromQueryParams({o: sortProperty, page: '1'});
    };
  
  
    console.log("RE-RENDERING");
    useEffect(()=>{return ()=>{console.log("unmounting whole")}});
    return <div key="perfContainerDiv">
      <ShowRenderTime/>
      <PerfTableOptionsUI getDataFromQueryParams={getDataFromQueryParams} key="thePerfAccordian"/>
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
  
const select2 = (appState: AppState) => {
  console.log("Selecting", selectPerfState(appState));
  return {
    perfdatastate: selectPerfState(appState),
    perfdataUIstate: selectPerf_UI_State(appState),
  }};

const actions2 = {
  doPerfRESTFetch: perfRESTFetch,
  doPerfREST_UI_Fetch: perfREST_UI_Fetch,
};

const WrappedPerfTable: React.ComponentType<{}> = withRouter(connect(select2, actions2)(
  PerfTable,
));

export default WrappedPerfTable;