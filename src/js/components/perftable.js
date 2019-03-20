// @flow
 /* flowlint
  *   untyped-import:off
  */

import * as React from 'react';
import * as ReactDOM from 'react-dom';
import { useEffect } from 'react';

import { connect } from 'react-redux';
import type { AppState } from 'store';
import type { InitialProps } from 'components/utils';
import { t } from 'i18next';
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

const addIds = (rows : []) => {
    return rows.map((row)=>{return {...row, id: Object.values(row).toString()}})
}

const UnwrappedPerfTable = ({doPerfRESTFetch, perfdatastate}) => {
    useEffect(() => {
      doPerfRESTFetch();
    }, []);

    const canGoPrev = perfdatastate
                      && perfdatastate.status == "PERF_DATA_AVAILABLE"
                      && perfdatastate.perfdata.previous;

    const doPrev = () => {
      if(canGoPrev){
          doPerfRESTFetch(perfdatastate.perfdata.previous); // TODO: previous
        }
    };

    const canGoNext = perfdatastate
                      && perfdatastate.status == "PERF_DATA_AVAILABLE"
                      && perfdatastate.perfdata.next;

    const doNext = () => {
      if(canGoNext){
          doPerfRESTFetch(perfdatastate.perfdata.next); // TODO: next
        }
    };

    const doSort = (sortColumn, ...rest) => {
      var sortProperty = sortColumn.property;
      const sortDirection = sortColumn.sortDirection;

      if (sortDirection === 'desc') {
        sortProperty = "-" + sortProperty
      }
      doPerfRESTFetch(null, {o: sortProperty});
    };

    var items;
    if(perfdatastate && perfdatastate.status == "PERF_DATA_AVAILABLE"){
      items = addIds(perfdatastate.perfdata.results);
    }else{
      items = {}
    }

    return <div>
            <DataTable items={items}
                fixedLayout={true}
                onSort={doSort}
              id="perfDataTable">
              {columns}
            </DataTable>
  {/* https://appexchange.salesforce.com/listingDetail?listingId=a0N3A00000E9TBZUA3*/}
            <div className="slds-card__footer slds-grid" >
            { items.length>0 &&
          <React.Fragment>
              <div className="slds-col slds-size--1-of-2"
                  style={{ textAlign: "left" }}>
                          Showing {perfdatastate.perfdata.results.length} of {perfdatastate.perfdata["count"]} records
              </div>
              <div className="slds-col slds-size--1-of-2">
                      <button onClick={()=>doPrev()}
                        className="slds-button slds-button--brand"
                        disabled={!canGoPrev}>Previous</button>
                      <button onClick={()=>doNext()}
                        className="slds-button slds-button--brand"
                        disabled={!canGoNext}>Next</button>
              </div>
            </React.Fragment>
            }
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
    UnwrappedPerfTable,
  );

  export default PerfTable;