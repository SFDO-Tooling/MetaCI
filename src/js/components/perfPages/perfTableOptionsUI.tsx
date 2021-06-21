/* eslint-disable no-use-before-define */

import Accordion from '@salesforce/design-system-react/components/accordion';
import AccordionPanel from '@salesforce/design-system-react/components/accordion/panel';
import {
  FilterDefinition,
  TestMethodPerfUI,
} from 'api/testmethod_perf_UI_JSON_schema';
import i18next from 'i18next';
import get from 'lodash/get';
import React, { ComponentType, useState } from 'react';
import { connect } from 'react-redux';
import { AppState } from 'store';
import { perfREST_UI_Fetch } from 'store/perfdata/actions';
import {
  selectBuildflowFiltersUI,
  selectPerfUIStatus,
} from 'store/perfdata/selectors';

import { AllFilters, createField, Field } from './formFields';
import DateRangePicker from './formFields/dateRangePicker';
import MultiPicker from './formFields/multiPicker';
import TextInput from './formFields/textInput';
import { QueryParamHelpers } from './perfTableUtils';

interface Props {
  fetchServerData: (params?: {
    [Key: string]: (string | string[]) | null;
  }) => void;
  queryparams: QueryParamHelpers;
  testMethodPerfUI: TestMethodPerfUI;
}

interface ReduxProps {
  perfUIStatus: string;
  buildflow_filters: FilterDefinition[];
}

const PerfTableOptionsUI: ComponentType<Props & ReduxProps> = ({
  fetchServerData,
  /* A function to trigger fetch */
  queryparams,
  /* A function to get queryparams or defaults */
  perfUIStatus,
  /* Has data been loaded yet? */
  testMethodPerfUI,
  /* UI Configuration data */
  buildflow_filters,
}: /* List of filters from server */

Props & ReduxProps) => {
  // is the UI data available? If so, populate the fields. If not,
  // just show the accordion.
  const uiAvailable = perfUIStatus === 'AVAILABLE';
  if (uiAvailable && !testMethodPerfUI) {
    throw new Error('Store error');
  }

  // state for managing the accordion. Maybe a single Map would be better.
  const [perfPanelColumnsExpanded, setPerfPanelColumnsExpanded] =
    useState(false);
  const [perfPanelFiltersExpanded, setPerfPanelFiltersExpanded] =
    useState(false);
  const [perfPanelOptionsExpanded, setPerfPanelOptionsExpanded] =
    useState(false);
  const [perfPanelDatesExpanded, setPerfPanelDatesExpanded] = useState(false);

  // collect filters to display in filters accordion
  const gatherFilters = (perfdataUIstate: typeof testMethodPerfUI): Field[] => {
    const testmethod_perf_filters = perfdataUIstate.filters;
    const all_filters = [...buildflow_filters, ...testmethod_perf_filters];
    const relevant_filters = all_filters.filter((filter) =>
      ['ChoiceField', 'CharField', 'DecimalField'].includes(filter.field_type),
    );
    return relevant_filters
      .map((filterDef) =>
        createField(
          filterDef,
          queryparams.get(filterDef.name) &&
            String(queryparams.get(filterDef.name)),
          (value) => fetchServerData({ [filterDef.name]: value }),
        ),
      )
      .filter(Boolean); // filter out nulls
  };

  // get the filter configurations from the server if they have
  // arrived
  const filters = uiAvailable ? gatherFilters(testMethodPerfUI) : [];

  const exclude = ['o', 'include_fields'];
  const filterPanelFilters = filters.filter(
    (filter) => !exclude.includes(filter.name),
  );
  const filterPanelCount = filterPanelFilters.filter(
    (f) => f.currentValue,
  ).length;
  const dateRangeCount: number = [
    queryparams.get('daterange_after'),
    queryparams.get('daterange_before'),
  ].filter((x) => x).length;

  return (
    <Accordion key="perfUIMainAccordion">
      <AccordionPanel
        id="perfPanelColumns"
        key="perfPanelColumns"
        summary={i18next.t('Columns')}
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
            onChange={(data) => fetchServerData({ include_fields: data })}
          />
        )}
      </AccordionPanel>
      <AccordionPanel
        id="perfPanelFilters"
        key="perfPanelFilters"
        summary={
          i18next.t('Filters') +
          (filterPanelCount > 0 ? ` (${filterPanelCount})` : '')
        }
        expanded={perfPanelFiltersExpanded}
        onTogglePanel={() => {
          setPerfPanelFiltersExpanded(!perfPanelFiltersExpanded);
        }}
      >
        {uiAvailable && <AllFilters filters={filterPanelFilters} />}
      </AccordionPanel>
      <AccordionPanel
        id="perfPaneDates"
        key="perfPaneDates"
        summary={
          i18next.t('Date Range') +
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
        summary={i18next.t('Options')}
        expanded={perfPanelOptionsExpanded}
        onTogglePanel={() => {
          setPerfPanelOptionsExpanded(!perfPanelOptionsExpanded);
        }}
      >
        {uiAvailable && (
          <React.Fragment>
            <TextInput
              defaultValue={queryparams.get('page_size')}
              label={i18next.t('Page Size')}
              tooltip="Number of rows to fetch per page"
              onValueUpdate={(value: string) =>
                fetchServerData({ page_size: value })
              }
            />
            {/* Build flow limit input removed in commit 0bd356e22 */}
          </React.Fragment>
        )}
      </AccordionPanel>
    </Accordion>
  );
};

const select = (appState: AppState) => ({
  perfUIStatus: selectPerfUIStatus(appState),
  buildflow_filters: selectBuildflowFiltersUI(appState),
});

const actions = {
  doPerfREST_UI_Fetch: perfREST_UI_Fetch,
};

const PerfTableOptionsUIConnected: any = connect(
  select,
  actions,
)(PerfTableOptionsUI);

export default PerfTableOptionsUIConnected;
