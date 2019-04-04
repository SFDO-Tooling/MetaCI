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
import { t } from 'i18next';
// flowlint  untyped-import:off
import Spinner from '@salesforce/design-system-react/components/spinner';
import DataTable from '@salesforce/design-system-react/components/data-table';
import DataTableColumn from '@salesforce/design-system-react/components/data-table/column';
import DataTableCell from '@salesforce/design-system-react/components/data-table/cell';
// flowlint  untyped-import:error

import PerfDataTableOptionsUI from './perfTableOptionsUI';

import { perfRESTFetch, perfREST_UI_Fetch } from 'store/perfdata/actions';

import { selectPerfState,
       } from 'store/perfdata/selectors';

import { QueryParamHelpers } from './perfTableUtils';
import { Trans } from 'react-i18next';
import type { ServerDataFetcher } from './perfPage';
type Props = {|
  fetchServerData: ServerDataFetcher,
  queryparams: QueryParamHelpers,
  perfState: PerfDataState,
  items: {}[],
  |};

export const PerfDataTable = ({ fetchServerData,
                              defaults,
                              items,
                              perfState,
                              queryparams} :
                  Props) => {
    let changeUrl = queryparams.set;

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

    var page = parseInt(queryparams.get("page")||"1") - 1;
    var custom_page_size = queryparams.get("page_size");
    var count = get(perfState, "perfdata.count") || -1;
    var page_size = custom_page_size ? parseInt(custom_page_size) :
              get(perfState, "perfdata.results.length") || null;
    var previousPage:string = get(perfState, "perfdata.previous") || "";
    var nextPage:string = get(perfState, "perfdata.next") || "";

    /* https://appexchange.salesforce.com/listingDetail?listingId=a0N3A00000E9TBZUA3 */
    const PerfDataTableFooter = () => {
      return (
      <div className="slds-card__footer slds-grid" >
        { items.length>0 && perfState && !!(perfState.perfdata) &&
          <>
            <div className="slds-col slds-size--1-of-2"
                  style={{ textAlign: "left" }}>
                    {t("Showing")} {(page * page_size).toString()}{t(' to ')}
                                {Math.min((page + 1) * page_size, count)}
                    {t(' of ')}{count.toString()} {t('records')}
            </div>
            <div className="slds-col slds-size--1-of-2">
                      <button onClick={()=>goPageFromUrl(previousPage)}
                        className="slds-button slds-button--brand"
                        disabled={!previousPage}>Previous</button>
                      <button onClick={()=>goPageFromUrl(nextPage)}
                        className="slds-button slds-button--brand"
                        disabled={!nextPage}>Next</button>
            </div>
          </>
        }
      </div>
    )}

    const columns = () => {
      let columns;
      if(items.length>0){
        let columnIds = Object.keys(items[0]).filter((item)=>item!="id");
        let columnPairs = columnIds.map((id)=>[
          id, id
        ]);
        return columnPairs;
      }else{
        // these are really just for looks. If there are no items, they
        // don't matter.
        let default_columns = queryparams.getList("include_fields") ||
                              ["Method Name", "Duration"];
        return zip(default_columns, default_columns)
      }
    }

    const PerfDataColumns = () => {
      return (
          columns().map(([name, label])=>
          {
            let isSorted:bool = false, sortDirection:string|null = null;

            if (queryparams.get("o")===name){
              isSorted = true;
              sortDirection = "asc";
            } else if (queryparams.get("o")==="-"+name){
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
            <PerfDataTableSpinner status={perfState && perfState.status}/>
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

type SpinnerProps = {
  status: LoadingStatus;
}

const PerfDataTableSpinner = ({ status }) => {
  if (status === "LOADING") {
    return <Spinner
      size="small"
      variant="base"
      assistiveText={{ label: 'Small spinner' }}
    />
  }
  return null;
}

export default PerfDataTable;