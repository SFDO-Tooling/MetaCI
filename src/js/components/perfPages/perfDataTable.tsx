import DataTable from '@salesforce/design-system-react/components/data-table';
import DataTableColumn from '@salesforce/design-system-react/components/data-table/column';
import Spinner from '@salesforce/design-system-react/components/spinner';
import i18next from 'i18next';
import get from 'lodash/get';
import zip from 'lodash/zip';
import PropTypes from 'prop-types';
import { parse } from 'query-string';
import * as React from 'react';
import { LoadingStatus, PerfDataState } from 'store/perfdata/reducer';

import { ServerDataFetcher } from './perfPage';
import { QueryParamHelpers } from './perfTableUtils';

interface SpinnerProps {
  status: LoadingStatus;
}

const PerfDataTableSpinner = ({ status }: SpinnerProps) => {
  if (status === 'LOADING') {
    return (
      <Spinner
        size="small"
        variant="base"
        assistiveText={{ label: 'Small spinner' }}
      />
    );
  }
  return null;
};
PerfDataTableSpinner.propTypes = {
  status: PropTypes.string.isRequired,
};

interface Props {
  fetchServerData: ServerDataFetcher;
  queryparams: QueryParamHelpers;
  perfState: PerfDataState;
  items: Record<string, unknown>[];
}

const PerfDataTable = ({
  fetchServerData,
  items,
  perfState,
  queryparams,
}: Props) => {
  if (perfState && perfState.status === 'ERROR') {
    const message =
      get(perfState, 'reason.reason.detail') ||
      get(perfState, 'reason.error') ||
      '';
    throw new Error(message);
  }
  /*
   * Extract the page from the server-generated URL and ensure it is
   * browser URL before fetching it.
   */
  const goPageFromUrl = (url: string) => {
    const qs = url.split('?', 2)[1];
    const qParts = parse(qs);
    const page = qParts.page;
    if (Array.isArray(page)) {
      fetchServerData({ page: page[1] });
    } else if (typeof page === 'string') {
      fetchServerData({ page });
    } else {
      fetchServerData({ page: undefined });
    }
  };

  const page = parseInt(String(queryparams.get('page') || '1'), 10) - 1;
  const custom_page_size = queryparams.get('page_size');
  const count = get(perfState, 'perfdata.count') || -1;
  const page_size = custom_page_size // flowlint-line sketchy-null-number:off
    ? parseInt(String(custom_page_size), 10)
    : get(perfState, 'perfdata.results.length') || null;
  const previousPage: string = get(perfState, 'perfdata.previous') || '';
  const nextPage: string = get(perfState, 'perfdata.next') || '';

  /* https://appexchange.salesforce.com/listingDetail?listingId=a0N3A00000E9TBZUA3 */
  const PerfDataTableFooter = () => (
    <div className="slds-card__footer slds-grid">
      {
        /* eslint-disable-next-line react/prop-types */
        items.length > 0 && perfState && Boolean(perfState.perfdata) && (
          <>
            <div
              className="slds-col slds-size--1-of-2"
              style={{ textAlign: 'left' }}
            >
              {i18next.t('Showing {{fromnum}} to {{tonum}} of {{totalnum}}', {
                fromnum: (page * page_size).toString(),
                tonum: Math.min((page + 1) * page_size, count),
                totalnum: count.toString(),
              })}
            </div>
            <div className="slds-col slds-size--1-of-2">
              <button
                onClick={() => goPageFromUrl(previousPage)}
                className="slds-button slds-button--brand"
                disabled={!previousPage}
              >
                Previous
              </button>
              <button
                onClick={() => goPageFromUrl(nextPage)}
                className="slds-button slds-button--brand"
                disabled={!nextPage}
              >
                Next
              </button>
            </div>
          </>
        )
      }
    </div>
  );

  const columns = (): [string, string][] => {
    if (items.length > 0) {
      const columnIds = Object.keys(items[0]).filter((item) => item !== 'id');
      const columnPairs: [string, string][] = columnIds.map((id) => [id, id]);
      return columnPairs;
    }
    // these are really just for looks. If there are no items, they
    // don't matter.
    const default_columns = queryparams.getList('include_fields') || [
      'Method Name',
      'Duration',
    ];
    return zip(default_columns, default_columns);
  };

  const perfDataColumns = () =>
    columns().map(([name, label]: [string, string]) => {
      let isSorted = false;
      let sortDirection: 'desc' | 'asc' | null = null;

      if (queryparams.get('o') === name) {
        isSorted = true;
        sortDirection = 'asc';
      } else if (queryparams.get('o') === `-${name}`) {
        isSorted = true;
        sortDirection = 'desc';
      }

      return (
        <DataTableColumn
          key={name}
          label={label}
          property={name}
          sortable
          isSorted={isSorted}
          sortDirection={sortDirection}
        />
      );
    });

  const doSort = (sortColumn) => {
    let sortProperty = sortColumn.property;
    const sortDirection = sortColumn.sortDirection;

    if (sortDirection === 'desc') {
      sortProperty = `-${sortProperty}`;
    }
    fetchServerData({ o: sortProperty, page: '1' });
  };
  const perfStatus = perfState ? perfState.status : 'LOADING';
  return (
    <div key="perfContainerDiv">
      <div style={{ position: 'relative' }}>
        <PerfDataTableSpinner status={perfStatus} />
        <DataTable
          items={items}
          fixedLayout={true}
          onSort={doSort}
          id="perfDataTable"
        >
          {perfDataColumns()}
        </DataTable>
        <PerfDataTableFooter />
      </div>
    </div>
  );
};

export default PerfDataTable;
