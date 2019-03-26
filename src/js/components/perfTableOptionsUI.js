// @flow

import * as React from 'react';
import * as ReactDOM from 'react-dom';
import { useEffect, useState } from 'react';
import get from 'lodash/get';
import zip from 'lodash/zip';
import debounce from 'lodash/debounce';

import queryString from 'query-string';

import { connect } from 'react-redux';
import type { AppState } from 'store';
// flowlint  untyped-import:off
import { t } from 'i18next';
import Accordion from '@salesforce/design-system-react/components/accordion';
import AccordionPanel from '@salesforce/design-system-react/components/accordion/panel';
import Input from '@salesforce/design-system-react/components/input';
import Tooltip from '@salesforce/design-system-react/components/tooltip';
// flowlint untyped-type-import:error

import FieldPicker from './fieldPicker';
import FilterPicker from './filterPicker';
import DateRangePicker from './dateRangePicker';

import { queryParts, ShowRenderTime } from './perftable';

import { perfRESTFetch, perfREST_UI_Fetch } from 'store/perfdata/actions';

import { selectPerfState, selectPerf_UI_State } from 'store/perfdata/selectors';

type Props = {
    fetchServerData : (string) => number,
    perfdataUIstate? : {[string]: mixed}
}

let PerfTableOptionsUI: React.ComponentType<Props> = ({ fetchServerData, perfdataUIstate })  => {

    // useful for debugging for now
    useEffect(() => {
        return (() => { console.log("UNMOUNTING ACCORDIAN") });
    });

    const [perfPanelColumnsExpanded, setPerfPanelColumnsExpanded] = useState(false);
    const [perfPanelFiltersExpanded, setPerfPanelFiltersExpanded] = useState(false);
    const [perfPanelOptionsExpanded, setPerfPanelOptionsExpanded] = useState(false);

    var filters = gatherFilters(perfdataUIstate);
    var filtersWithValues = filters.filter((f) => f.currentValue).length;

    console.log(filters);

    const getDefaultValue = (field_name:string) : string =>  {
        let defaultVal:string;
        if(field_name=="method_name"){
            defaultVal = ""
        }else{
            defaultVal = get(perfdataUIstate, "uidata.defaults." + field_name)
                ||"MISSING_DEFAULT"
        }
        return queryParts(field_name) || defaultVal;
    }

    return (
        <Accordion key="perfUIMainAccordion">
            <ShowRenderTime />
            <AccordionPanel id="perfPanelColumns"
                key="perfPanelColumns"
                summary="Columns"
                expanded={perfPanelColumnsExpanded}
                onTogglePanel={() => setPerfPanelColumnsExpanded(!perfPanelColumnsExpanded)}>
                <FieldPicker key="PerfDataTableFieldPicker"
                    onChange={fetchServerData} />
            </AccordionPanel>
            <AccordionPanel id="perfPanelFilters"
                key="perfPanelFilters"
                summary={"Filters" + (filtersWithValues > 0 ? " (" + filtersWithValues + ")" : "")}
                expanded={perfPanelFiltersExpanded}
                onTogglePanel={() => { setPerfPanelFiltersExpanded(!perfPanelFiltersExpanded) }}>
                <BuildFilterPickers filters={filters} fetchServerData={fetchServerData} />
                <DateRangePicker
                    onChange={(name, data) => fetchServerData({ [name]: data })}
                    startName="daterange_after"
                    endName="daterange_before"
                    startValue={new Date(getDefaultValue("daterange_after"))}
                    endValue={new Date (getDefaultValue("daterange_before"))} />
                <QueryBoundTextInput defaultValue={getDefaultValue("method_name")}
                        label="Method Name"
                        tooltip="Method to query"
                        onValueUpdate={(value) => fetchServerData({ method_name: value })} />
            </AccordionPanel>
            <AccordionPanel id="perfPanelOptions"
                key="perfPanelOptions"
                summary="Options"
                expanded={perfPanelOptionsExpanded}
                onTogglePanel={() => { setPerfPanelOptionsExpanded(!perfPanelOptionsExpanded) }}>
                {get( perfdataUIstate,  "status") === "UI_DATA_AVAILABLE" && 
                <React.Fragment>
                    <QueryBoundTextInput defaultValue={getDefaultValue("page_size")}
                        label="Page Size"
                        tooltip="Number of rows to fetch per page"
                        onValueUpdate={(value) => fetchServerData({ page_size: value })} />
                    <QueryBoundTextInput 
                        defaultValue={getDefaultValue("build_flows_limit")}
                        label="Build Flows Limit"
                        tooltip="Max number of build_flows to aggregate (performance optimization)"
                        onValueUpdate={(value) => fetchServerData({ build_flows_limit: value })} />
                <ShowRenderTime />
                </React.Fragment>
                }
            </AccordionPanel>
        </Accordion>
    )
}

const QueryBoundTextInput = ({ label, defaultValue, onValueUpdate,
    tooltip }) => {
    // debounce to reduce redraws while typing
    let debouncedCallback = debounce((value) => onValueUpdate(value), 1000)

    // store in state so debouncer can have internal history
    let [debouncedChangeUrl, setDebouncer] = useState(
        // wrap in obj to prevent magic useState behaviour
        { debouncedCallback }
    );
    // unwrap
    debouncedCallback = debouncedChangeUrl.debouncedCallback;

    return <Input
        label={label}
        fieldLevelHelpTooltip={
            <Tooltip
                align="top left"
                content={tooltip}
            />
        }
        defaultValue={defaultValue}
        onChange={(event, { value }) => debouncedCallback(value)}
    />
}

const BuildFilterPicker = ({ filter, fetchServerData }) => {
    return <FilterPicker
                key={filter.name}
                field_name={filter.name}
                choices={filter.choices}
                value={filter.currentValue}
                onSelect={(value) => { fetchServerData({ [filter.name]: value }) }} />
}


const BuildFilterPickers = ({ filters, fetchServerData }) => {
    let choice_filters = filters.filter((filter) => filter.choices);
    let first4 = choice_filters.slice(0,4);
    let rest = choice_filters.slice(4);
    let first_row= <div class="slds-grid slds-gutters">
        {
            first4.map((filter) => 
                <div class="slds-col "
                         key={filter.name}>
                         <BuildFilterPicker filter={filter} fetchServerData={fetchServerData}/>
                        </div>
            )
        }                         
        </div>
    let other_html = rest.map((filter) => 
             <BuildFilterPicker filter={filter} 
                fetchServerData={fetchServerData}/>);

    return <React.Fragment>
        {first_row}
        {other_html}
    </React.Fragment>
}

type FilterOption = {
    id: string,
    label: string
}

type Filter = {
    name: string,
    choices?: FilterOption,
    currentValue?: string,
};

const gatherFilters = (perfdataUIstate): Filter[] => {
    // TODO: handle all filters here
    let filters: Filter[] = [];
    const choiceFilters = get(perfdataUIstate, "uidata.buildflow_filters.choice_filters", {});
    Object.keys(choiceFilters).map((fieldname) => {
        let filterDef = choiceFilters[fieldname];
        let choices = filterDef["choices"].map((pair) => ({ id: pair[0], label: pair[1] }));
        let currentValue = queryParts()[fieldname];
        filters.push({ name: fieldname, choices, currentValue });
    });

    return filters;
}


const select = (appState: AppState) => {
    console.log("Selecting", selectPerfState(appState));
    return {
        perfdataUIstate: selectPerf_UI_State(appState),
    }
};

const actions = {
    doPerfREST_UI_Fetch: perfREST_UI_Fetch,
};


let PerfTableOptionsUIConnected: React.ComponentType<{}> = 
    connect(select, actions)( PerfTableOptionsUI );

export default PerfTableOptionsUIConnected;
