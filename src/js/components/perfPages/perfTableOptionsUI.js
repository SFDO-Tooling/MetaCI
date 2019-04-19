/* eslint-disable react/display-name */
/* eslint-disable no-use-before-define */
// @flow
import React, { useState } from 'react';
import type { ComponentType } from 'react';
import get from 'lodash/get';
import { connect } from 'react-redux';
import { t } from 'i18next';
import Accordion from '@salesforce/design-system-react/components/accordion';
import AccordionPanel from '@salesforce/design-system-react/components/accordion/panel';

import { createField } from './formFields';
import type { Field } from './formFields';
import TextInput from './formFields/textInput';
import MultiPicker from './formFields/multiPicker';
import DateRangePicker from './formFields/dateRangePicker';

import { perfREST_UI_Fetch } from 'store/perfdata/actions';
import type {
  FilterDefinition,
  TestMethodPerfUI,
} from 'api/testmethod_perf_UI_JSON_schema';
import type { AppState } from 'store';
import {
  selectPerfUIStatus,
  selectBuildflowFiltersUI,
} from 'store/perfdata/selectors';

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

const PerfTableOptionsUI: ComponentType<Props & ReduxProps> = ({
  fetchServerData /* A function to trigger fetch */,
  queryparams /* A function to get queryparams or defaults */,
  perfUIStatus /* Has data been loaded yet? */,
  testMethodPerfUI /* UI Configuration data */,
  buildflow_filters /* List of filters from server */,
}: Props & ReduxProps) => {
  // is the UI data available? If so, populate the fields. If not,
  // just show the accordion.
  const uiAvailable = perfUIStatus === 'AVAILABLE';
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
    const filters: Field[] = [];
    if (!uiAvailable) {
      return filters;
    }

    const testmethod_perf_filters = perfdataUIstate.filters;
    const all_filters = [...buildflow_filters, ...testmethod_perf_filters];
    const relevant_filters = all_filters.filter(filter =>
      ['ChoiceField', 'CharField', 'DecimalField'].includes(filter.field_type),
    );
    if (relevant_filters.length) {
      relevant_filters.forEach(filterDef => {
        const onSubmit = value => fetchServerData({ [filterDef.name]: value });
        const newField = createField(
          filterDef,
          queryparams.get(filterDef.name),
          onSubmit,
        );

        if (newField) {
          filters.push(newField);
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
          <MultiPicker
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

const AllFilters = ({ filters }: { filters: Field[] }) => (
  <div key="filterGrid" className="slds-grid slds-wrap slds-gutters">
    {filters.map(filter => (
      <div key={filter.name} className="slds-col slds-size_3-of-12">
        {filter.render()}
      </div>
    ))}
  </div>
);

const select = (appState: AppState) => ({
  perfUIStatus: selectPerfUIStatus(appState),
  buildflow_filters: selectBuildflowFiltersUI(appState),
});

const actions = {
  doPerfREST_UI_Fetch: perfREST_UI_Fetch,
};

const PerfTableOptionsUIConnected: ComponentType<{}> = connect(
  select,
  actions,
)(PerfTableOptionsUI);

export default PerfTableOptionsUIConnected;
