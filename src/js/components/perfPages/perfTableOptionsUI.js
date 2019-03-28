// @flow

import * as React from 'react';
import * as ReactDOM from 'react-dom';
import { useEffect, useState } from 'react';
import get from 'lodash/get';
import zip from 'lodash/zip';
import partition from 'lodash/partition';
import debounce from 'lodash/debounce';
import chunk from 'lodash/chunk';

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

import { queryparams, ShowRenderTime } from './perfTable';

import { perfRESTFetch, perfREST_UI_Fetch } from 'store/perfdata/actions';

import { selectPerfState, selectPerf_UI_State } from 'store/perfdata/selectors';

type Props = {
    fetchServerData : (string) => number,
    perfdataUIstate? : {[string]: mixed}
}

const getInitialValue = (filter) : string => {
    let defaultVal:string;
    // don't remember why this is special-cased
    // test removing the special case
    if(filter.name=="method_name"){
        defaultVal = "";
    }else{
        defaultVal = filter.default;
    }
    return queryparams.get(filter.name) || defaultVal;
}

let PerfTableOptionsUI: React.ComponentType<Props> = (
            { fetchServerData, perfdataUIstate })  => {
    let queryParts = queryparams.get;
    let uiAvailable = get( perfdataUIstate,  "status") === "UI_DATA_AVAILABLE";

    const [perfPanelColumnsExpanded, setPerfPanelColumnsExpanded] = useState(false);
    const [perfPanelFiltersExpanded, setPerfPanelFiltersExpanded] = useState(false);
    const [perfPanelOptionsExpanded, setPerfPanelOptionsExpanded] = useState(false);
    const [perfPanelDatesExpanded, setPerfPanelDatesExpanded] = useState(false);

    // TODO: unify this with getInitialValue when all components are
    //       constructed from Filter objects
    const getDefaultValue = (field_name:string) : string =>  {
        let defaultVal:string;
        if(field_name=="method_name"){
            defaultVal = ""
        }else{
            defaultVal = get(perfdataUIstate, "uidata.defaults." + field_name)
        }
        return queryParts(field_name) || defaultVal;
    }

    const gatherFilters = (perfdataUIstate): Field[] => {
        let filters: Field[] = [];
        if(!uiAvailable) return filters;

        const buildflow_filters = get(perfdataUIstate,
                                    "uidata.buildflow_filters");
        const testmethod_perf_filters = get(perfdataUIstate,
                            "uidata.testmethod_perf.filters");
        const all_filters = [...buildflow_filters, ...testmethod_perf_filters];
        if(all_filters.length){
            all_filters.map((filterDef)=>{
                if(get(filterDef, "choices")){
                    filters.push(
                        ChoiceField(filterDef,
                            getInitialValue(filterDef),
                            fetchServerData));
                } else if (filterDef.field_type == "DecimalField") {
                    filters.push(
                        DecimalField(filterDef,
                            getInitialValue(filterDef),
                            fetchServerData));
                } else if (filterDef.field_type == "CharField") {
                    filters.push(
                        CharField(filterDef,
                            getInitialValue(filterDef),
                            fetchServerData));
                }
            });
        }
        return filters;
    }

    var filters = gatherFilters(perfdataUIstate);

    const exclude = ["o", "include_fields", "build_flows_limit"];
    let filterPanelFilters = filters.filter(
        (filter)=>!exclude.includes(filter.name))
    var filterPanelCount = filterPanelFilters.filter((f) =>
        f.currentValue).length;

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
                summary={"Filters" + (filterPanelCount > 0 ? " (" + filterPanelCount + ")" : "")}
                expanded={perfPanelFiltersExpanded}
                onTogglePanel={() => { setPerfPanelFiltersExpanded(!perfPanelFiltersExpanded) }}>
                <AllFilters filters={filterPanelFilters} fetchServerData={fetchServerData}/>
            </AccordionPanel>
            {/* TODO: highlight whether date has been set or not */ }
            <AccordionPanel id="perfPaneDates"
                key="perfPaneDates"
                summary={"Date Range"}
                expanded={perfPanelDatesExpanded}
                onTogglePanel={() => { setPerfPanelDatesExpanded(!perfPanelDatesExpanded) }}>
                <DateRangePicker
                    onChange={(name, data) => fetchServerData({ [name]: data })}
                    startName="daterange_after"
                    endName="daterange_before"
                    startValue={new Date(getDefaultValue("daterange_after"))}
                    endValue={new Date (getDefaultValue("daterange_before"))} />
            </AccordionPanel>
            <AccordionPanel id="perfPanelOptions"
                key="perfPanelOptions"
                summary="Options"
                expanded={perfPanelOptionsExpanded}
                onTogglePanel={() => { setPerfPanelOptionsExpanded(!perfPanelOptionsExpanded) }}>
                {uiAvailable &&
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
            tooltip &&
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



const TEMPORARILY_UNUSED_DateRangeRenderer = ({ filter, fetchServerData }) => {
    let startName = filter.name + "_after";
    let endName = filter.name + "_before"
    return <DateRangePicker
                onChange={(name, data) => fetchServerData({ [name]: data })}
                startName={startName}
                endName={endName}
                startValue={new Date()} // new Date(getDefaultValue(startName))}
                endValue={new Date()} // new Date (getDefaultValue(endName))}
                />
}


const AllFilters = ({ filters, fetchServerData }) => {
    return <div key="filterGrid" className="slds-grid slds-wrap slds-gutters">
            {filters.map((filter)=>
                <div key={filter.name} className="slds-col slds-size_3-of-12">
                    {filter.render()}
                </div>
            )}
        </div>
}

type FieldOption = {
    id: string,
    label: string
}

type Field = {
    name: string,
    currentValue?: string,
    render: () => React$Element<any>
};

const ChoiceField = (filter: {name:string, choices:[]},
                                currentValue, fetchServerData) : Field => {

    let choices_as_objs = filter.choices.map((pair) => (
            { id: pair[0], label: pair[1] }));
    return {
        name: filter.name,
        choices: choices_as_objs,
        currentValue,
        render: () =>
            <FilterPicker
                key={filter.name}
                field_name={filter.name}
                choices={choices_as_objs}
                value={currentValue}
                onSelect={(value) => {
                    fetchServerData({ [filter.name]: value }) }} />

    };
}

const CharField = (filter: { name: string,
                description?: string,
                label?: string,
                choices: [] },
    currentValue?: string, fetchServerData): Field => {
    return {
        name: filter.name,
        currentValue,
        render: () =>
            <QueryBoundTextInput defaultValue={currentValue}
                label={filter.label}
                tooltip={filter.description}
                onValueUpdate={(value) =>
                    fetchServerData({ [filter.name]: value })}/>
    };
}

const DecimalField = CharField;

const select = (appState: AppState) => {
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
