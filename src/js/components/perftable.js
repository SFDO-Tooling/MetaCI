// @flow
 /* flowlint
  *   untyped-import:off
  */

import * as React from 'react';
import * as ReactDOM from 'react-dom';

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
	/>,

	<DataTableColumn
		key="duration_average"
		label="Average Duration"
		property="duration_average"
	/>,

	<DataTableColumn
		key="repo"
		label="Repository"
		property="repo"
	/>,
];

const addIds = (rows : []) => {
    return rows.map((row)=>{return {...row, id: Object.values(row).toString()}})
}

const UnwrappedPerfTable = ({doPerfRESTFetch, perfdatastate}) => (
    <div>
        <button onClick={()=>doPerfRESTFetch()}>Call Server</button>
        <p>{ perfdatastate ? JSON.stringify(perfdatastate.status) : "No perf data yet"}</p>
        {perfdatastate && perfdatastate.status == "PERF_DATA_AVAILABLE"? 
        <DataTable items={addIds(perfdatastate.perfdata.results)}
            id="perfDataTable">
            {columns}
        </DataTable>
        : "" }

    </div>
  );
  
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