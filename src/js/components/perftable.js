// @flow
 /* flowlint
  *   untyped-import:off
  */

import * as React from 'react';
import * as ReactDOM from 'react-dom';
import { useEffect } from 'react';
import { withRouter } from 'react-router';
import get from 'lodash/get';

import queryString from 'query-string';

import { connect } from 'react-redux';
import type { AppState } from 'store';
import type { InitialProps } from 'components/utils';
import { t } from 'i18next';
import Spinner from '@salesforce/design-system-react/components/spinner';
import DataTable from '@salesforce/design-system-react/components/data-table';
import DataTableColumn from '@salesforce/design-system-react/components/data-table/column';
import DataTableCell from '@salesforce/design-system-react/components/data-table/cell';

import { perfRESTFetch } from 'store/perfdata/actions';

import { selectPerfState } from 'store/perfdata/selectors';

const columns = [
	<DataTableColumn
		key="method_name"
		label="Method Name"
		property="method_name"
		sortable
	/>,

	<DataTableColumn
		key="duration_average"
		label="Average Duration"
		property="duration_average"
		sortable
	/>,

	<DataTableColumn
		key="repo"
		label="Repository"
		property="repo"
		sortable
	/>,
];

const addIds = (rows : [{[string]: mixed}]) => {
    return rows.map((row)=>{return {...row, id: Object.values(row).toString()}})
}

const UnwrappedPerfTable = ({doPerfRESTFetch, perfdatastate, match, location, history }) => {
  var queryParts = queryString.parse(window.location.search);
  useEffect(() => {
      doPerfRESTFetch(null, queryParts);
    }, []);

    const changeUrl = (queryParts: {[string] : string}) => {
      history.push({
        pathname: window.location.pathname,
        search: queryString.stringify(queryParts)
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

    const getDataFromQueryParams = (params: {[string]: string}) => {
      changeUrl({...queryParts, ...params});
      doPerfRESTFetch(null, {...queryParts, ...params});
    }

    const doSort = (sortColumn, ...rest) => {
      var sortProperty = sortColumn.property;
      const sortDirection = sortColumn.sortDirection;

      if (sortDirection === 'desc') {
        sortProperty = "-" + sortProperty
      }
      getDataFromQueryParams({o: sortProperty, page: '1'});
    };

    var items;
    if(perfdatastate && perfdatastate.perfdata){
      items = addIds(perfdatastate.perfdata.results);
    }else{
      items = [];
    }

    const PerfDataTableSpinner = () => {
      if(get(perfdatastate, "status") === "PERF_DATA_LOADING"){
        return <Spinner
          size="small"
          variant="base"
          assistiveText={{ label: 'Small spinner' }}
        />
      }
      return null;
    }

    var page = parseInt(queryParts["page"]||"1") - 1;
    var custom_page_size = queryParts["page_size"];
    var page_size = custom_page_size ? parseInt(custom_page_size) : 
                        get(perfdatastate, "perfdata.results.length") || -1;

    /* https://appexchange.salesforce.com/listingDetail?listingId=a0N3A00000E9TBZUA3 */
    const PerfDataTableFooter = () => (
      <div className="slds-card__footer slds-grid" >
        { items.length>0 &&
          <React.Fragment>
            <div className="slds-col slds-size--1-of-2"
                  style={{ textAlign: "left" }}>
                          Showing {page * page_size} to {' '}
                                {(page + 1) * page_size} {' '}
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
    )
  
    return <div>
			<div style={{ position: 'relative'}}>
            <PerfDataTableSpinner/>
            <DataTable items={items}
                fixedLayout={true}
                onSort={doSort}
              id="perfDataTable">
              {columns}
            </DataTable>
            <PerfDataTableFooter/>
        </div>
    </div>
  };
  
  const select = (appState: AppState) => ({
    perfdatastate: selectPerfState(appState),
  });
  
  const actions = {
    doPerfRESTFetch: perfRESTFetch,
  };
  
  const PerfTable: React.ComponentType<{}> = connect(select, actions)(
    withRouter(UnwrappedPerfTable),
  );

  export default PerfTable;