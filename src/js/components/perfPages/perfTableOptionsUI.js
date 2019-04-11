// @flow

import * as React from 'react';
import { useEffect, useState } from 'react';
import get from 'lodash/get';
import zip from 'lodash/zip';
import partition from 'lodash/partition';
import chunk from 'lodash/chunk';
import queryString from 'query-string';
import { connect } from 'react-redux';
import type { AppState } from 'store';
import is, { type AssertionType } from 'sarcastic';

// flowlint  untyped-import:off
import { t } from 'i18next';
import Accordion from '@salesforce/design-system-react/components/accordion';
import AccordionPanel from '@salesforce/design-system-react/components/accordion/panel';
// flowlint untyped-type-import:error

import { perfRESTFetch, perfREST_UI_Fetch } from 'store/perfdata/actions';
import {
  selectPerfUIStatus,
  selectBuildflowFiltersUI,
} from 'store/perfdata/selectors';
import type {
  FilterDefinition,
  TestMethodPerfUI,
} from 'api/testmethod_perf_UI_JSON_schema';
import { Trans } from 'react-i18next';

import FieldPicker from './formFields/fieldPicker';
import FilterPicker from './formFields/filterPicker';
import DateRangePicker from './formFields/dateRangePicker';
import TextInput from './formFields/textInput';

type Props = {
  fetchServerData: (params?: {
    [string]: ?(string | Array<string>),
  }) => void,
  queryparams: (name?: string) => string,
  testMethodPerfUI: TestMethodPerfUI,
};

type ReduxProps = {
  perfUIStatus: string,
  buildflow_filters: FilterDefinition[],
};

const PerfTableOptionsUI: React.ComponentType<Props & ReduxProps> = ({
  fetchServerData /* A function to trigger fetch */,
  queryparams /* A function to get queryparams or defaults */,
  perfUIStatus /* Has data been loaded yet? */,
  testMethodPerfUI /* UI Configuration data */,
  buildflow_filters /* List of filters from server */,
}: Props & ReduxProps) => {
  // is the UI data available? If so, populate the fields. If not,
  // just show the accordion.
  const uiAvailable = perfUIStatus == 'AVAILABLE';
  if (uiAvailable && !testMethodPerfUI) {
    throw new Error('Store error');
  }

  // state for managing the accordion. Maybe a single Map would be better.
  const [perfPanelColumnsExpanded, setPerfPanelColumnsExpanded] = useState(
    false,
  );
  const [perfPanelFiltersExpanded, setPerfPanelFiltersExpanded] = useState(
    false,
  );
  const [perfPanelOptionsExpanded, setPerfPanelOptionsExpanded] = useState(
    false,
  );
  const [perfPanelDatesExpanded, setPerfPanelDatesExpanded] = useState(false);

  // collect filters to display in filters accordion
  const gatherFilters = (perfdataUIstate: typeof testMethodPerfUI): Field[] => {
    console.log(perfdataUIstate);
    const filters: Field[] = [];
    if (!uiAvailable) {
      return filters;
    }

    const testmethod_perf_filters = perfdataUIstate.filters;
    console.log(buildflow_filters, testmethod_perf_filters);
    const all_filters = [...buildflow_filters, ...testmethod_perf_filters];
    if (all_filters.length) {
      all_filters.map(filterDef => {
        if (filterDef.field_type == 'ChoiceField') {
          filters.push(
            ChoiceField(
              filterDef,
              queryparams.get(filterDef.name),
              fetchServerData,
            ),
          );
        } else if (filterDef.field_type == 'DecimalField') {
          filters.push(
            DecimalField(
              filterDef,
              queryparams.get(filterDef.name),
              fetchServerData,
            ),
          );
        } else if (filterDef.field_type == 'CharField') {
          filters.push(
            CharField(
              filterDef,
              queryparams.get(filterDef.name),
              fetchServerData,
            ),
          );
        }
      });
    }
    return filters;
  };

  // get the filter configurations from the server if they have
  // arrived
  const filters = uiAvailable ? gatherFilters(testMethodPerfUI) : [];

  const exclude = ['o', 'include_fields', 'build_flows_limit'];
  const filterPanelFilters = filters.filter(
    filter => !exclude.includes(filter.name),
  );
  const filterPanelCount = filterPanelFilters.filter(f => f.currentValue)
    .length;
  const dateRangeCount: number = [
    queryparams.get('daterange_after'),
    queryparams.get('daterange_before'),
  ].filter(x => x).length;

  return (
    <Accordion key="perfUIMainAccordion">
      <AccordionPanel
        id="perfPanelColumns"
        key="perfPanelColumns"
        summary={t('Columns')}
        expanded={perfPanelColumnsExpanded}
        onTogglePanel={() =>
          setPerfPanelColumnsExpanded(!perfPanelColumnsExpanded)
        }
      >
        {uiAvailable && (
          <FieldPicker
            key="PerfDataTableFieldPicker"
            choices={get(testMethodPerfUI, 'includable_fields')}
            defaultValue={queryparams.getList('include_fields')}
            onChange={data => fetchServerData({ include_fields: data })}
          />
        )}
      </AccordionPanel>
      <AccordionPanel
        id="perfPanelFilters"
        key="perfPanelFilters"
        summary={
          t('Filters') + (filterPanelCount > 0 ? ` (${filterPanelCount})` : '')
        }
        expanded={perfPanelFiltersExpanded}
        onTogglePanel={() => {
          setPerfPanelFiltersExpanded(!perfPanelFiltersExpanded);
        }}
      >
        {uiAvailable && (
          <AllFilters
            filters={filterPanelFilters}
            fetchServerData={fetchServerData}
          />
        )}
      </AccordionPanel>
      <AccordionPanel
        id="perfPaneDates"
        key="perfPaneDates"
        summary={
          t('Date Range') +
          (dateRangeCount ? ` (${dateRangeCount.toString()})` : '')
        }
        expanded={perfPanelDatesExpanded}
        onTogglePanel={() => {
          setPerfPanelDatesExpanded(!perfPanelDatesExpanded);
        }}
      >
        {uiAvailable && (
          <DateRangePicker
            onChange={(name, data) => fetchServerData({ [name]: data })}
            startName="daterange_after"
            endName="daterange_before"
            startValue={queryparams.get('daterange_after')}
            endValue={queryparams.get('daterange_before')}
          />
        )}
      </AccordionPanel>
      <AccordionPanel
        id="perfPanelOptions"
        key="perfPanelOptions"
        summary={t('Options')}
        expanded={perfPanelOptionsExpanded}
        onTogglePanel={() => {
          setPerfPanelOptionsExpanded(!perfPanelOptionsExpanded);
        }}
      >
        {uiAvailable && (
          <React.Fragment>
            <TextInput
              defaultValue={queryparams.get('page_size')}
              label={t('Page Size')}
              tooltip="Number of rows to fetch per page"
              onValueUpdate={(value: string) =>
                fetchServerData({ page_size: value })
              }
            />
            <TextInput
              defaultValue={queryparams.get('build_flows_limit')}
              label={t('Build Flows Limit')}
              tooltip="Max number of build_flows to aggregate (performance optimization)"
              onValueUpdate={(value: string) =>
                fetchServerData({ build_flows_limit: value })
              }
            />
          </React.Fragment>
        )}
      </AccordionPanel>
    </Accordion>
  );
};

const AllFilters = ({ filters, fetchServerData }) => (
  <div key="filterGrid" className="slds-grid slds-wrap slds-gutters">
    {filters.map(filter => (
      <div key={filter.name} className="slds-col slds-size_3-of-12">
        {filter.render()}
      </div>
    ))}
  </div>
);

// interface representing fields that can be shown on the screen.
type Field = {
  name: string,
  currentValue?: mixed,
  render: () => React.Node,
};

const ChoiceField = (
  filter: FilterDefinition,
  currentValue?: string | null,
  fetchServerData,
): Field => {
  const choices: string[][] = is(
    filter.choices,
    is.arrayOf(is.arrayOf(is.string)),
  );
  const choices_as_objs = choices.map(pair => ({
    id: pair[0],
    label: pair[1],
  }));
  return {
    name: filter.name,
    choices: choices_as_objs,
    currentValue,
    render: () => (
      <FilterPicker
        key={filter.name}
        field_name={filter.name}
        choices={choices_as_objs}
        value={currentValue}
        onSelect={value => {
          fetchServerData({ [filter.name]: value });
        }}
      />
    ),
  };
};

const CharField = (
  filter: FilterDefinition,
  currentValue?: string | null,
  fetchServerData,
): Field => ({
  name: filter.name,
  currentValue,
  render: () => (
    <TextInput
      defaultValue={currentValue}
      label={filter.label}
      tooltip={filter.description}
      onValueUpdate={value => fetchServerData({ [filter.name]: value })}
    />
  ),
});

const DecimalField = CharField;

const select = (appState: AppState) => ({
  perfUIStatus: selectPerfUIStatus(appState),
  buildflow_filters: selectBuildflowFiltersUI(appState),
});

const actions = {
  doPerfREST_UI_Fetch: perfREST_UI_Fetch,
};

const PerfTableOptionsUIConnected: React.ComponentType<{}> = connect(
  select,
  actions,
)(PerfTableOptionsUI);

export default PerfTableOptionsUIConnected;
