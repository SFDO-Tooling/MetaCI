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

import FieldPicker from './formFields/fieldPicker';
import FilterPicker from './formFields/filterPicker';
import DateRangePicker from './formFields/dateRangePicker';

import { perfRESTFetch, perfREST_UI_Fetch } from 'store/perfdata/actions';

import { selectPerfUIStatus, selectBuildflowFiltersUI } from 'store/perfdata/selectors';


type Props = {
    fetchServerData : (params?: {
        [string]: ?(string | Array<string>)
      }) => void,
      queryparams: (name?: string) => string,
      testmethodPerfUI: {},
}

type ReduxProps = {
    perfUIStatus : string,
    buildflow_filters: {}[],
}

let PerfTableOptionsUI: React.ComponentType<Props & ReduxProps> = (
            { fetchServerData, /* A function to trigger fetch */
                queryparams,    /* A function to get queryparams or defaults */
                perfUIStatus, /* Has data been loaded yet? */
                testmethodPerfUI, /* UI Configuration data */
                buildflow_filters, /* List of filters from server */
            } : Props & ReduxProps)  => {
    // is the UI data available? If so, populate the fields. If not,
    // just show the accordion.
    let uiAvailable = perfUIStatus == "AVAILABLE";
    console.log("ST", perfUIStatus);
    // state for managing the accordion. Maybe a single Map would be better.
    const [perfPanelColumnsExpanded, setPerfPanelColumnsExpanded] = useState(false);
    const [perfPanelFiltersExpanded, setPerfPanelFiltersExpanded] = useState(false);
    const [perfPanelOptionsExpanded, setPerfPanelOptionsExpanded] = useState(false);
    const [perfPanelDatesExpanded, setPerfPanelDatesExpanded] = useState(false);

    // Get the initial value for a form field either from the URL OR
    // from a default value specified on the server (if either is available)
    //
    // Possible that this duplicates work already being done in
    // queryparams.get.
    const getInitialValue = (filterOrString: {name:string} | string) :
                                                            string | string[] => {
        return queryparams.get(filterOrString);

        if( filterOrString.name === undefined){
            if( filterOrString.name=="method_name"){
                // I don't remember why this is special-cased
                // test removing the special case at some point
                return queryparams.get(filterOrString.name) || "";
            }else{
                return queryparams.get(filterOrString.name);
            }
        }else{
            return queryparams.get(filterOrString);
        }
    }

    const gatherFilters = (perfdataUIstate): Field[] => {
        let filters: Field[] = [];
        if(!uiAvailable) return filters;

        const testmethod_perf_filters = get(perfdataUIstate,
                            "filters");
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

    const filters = uiAvailable ? gatherFilters(testmethodPerfUI) : [];

    const exclude = ["o", "include_fields", "build_flows_limit"];
    let filterPanelFilters = filters.filter(
        (filter)=>!exclude.includes(filter.name))
    var filterPanelCount = filterPanelFilters.filter((f) =>
        f.currentValue).length;

    return (
        <Accordion key="perfUIMainAccordion">
            <AccordionPanel id="perfPanelColumns"
                key="perfPanelColumns"
                summary="Columns"
                expanded={perfPanelColumnsExpanded}
                onTogglePanel={() => setPerfPanelColumnsExpanded(!perfPanelColumnsExpanded)}>
                {uiAvailable &&
                <FieldPicker key="PerfDataTableFieldPicker"
                    choices={get(testmethodPerfUI, "includable_fields")}
                    defaultValue={getInitialValue("include_fields")}
                    onChange={fetchServerData} />}
            </AccordionPanel>
            <AccordionPanel id="perfPanelFilters"
                key="perfPanelFilters"
                summary={"Filters" + (filterPanelCount > 0 ? " (" + filterPanelCount + ")" : "")}
                expanded={perfPanelFiltersExpanded}
                onTogglePanel={() => { setPerfPanelFiltersExpanded(!perfPanelFiltersExpanded) }}>
                {uiAvailable &&
                    <AllFilters filters={filterPanelFilters} fetchServerData={fetchServerData}/>
                }
            </AccordionPanel>
            {/* TODO: highlight whether date has been set or not */ }
            <AccordionPanel id="perfPaneDates"
                key="perfPaneDates"
                summary={"Date Range"}
                expanded={perfPanelDatesExpanded}
                onTogglePanel={() => { setPerfPanelDatesExpanded(!perfPanelDatesExpanded) }}>
                {uiAvailable &&
                <DateRangePicker
                    onChange={(name, data) => fetchServerData({ [name]: data })}
                    startName="daterange_after"
                    endName="daterange_before"
                    startValue={new Date(getInitialValue("daterange_after"))}
                    endValue={new Date(getInitialValue("daterange_before"))} />
                }
            </AccordionPanel>
            <AccordionPanel id="perfPanelOptions"
                key="perfPanelOptions"
                summary="Options"
                expanded={perfPanelOptionsExpanded}
                onTogglePanel={() => { setPerfPanelOptionsExpanded(!perfPanelOptionsExpanded) }}>
                {uiAvailable &&
                <React.Fragment>
                    <QueryBoundTextInput defaultValue={getInitialValue("page_size")}
                        label="Page Size"
                        tooltip="Number of rows to fetch per page"
                        onValueUpdate={(value) => fetchServerData({ page_size: value })} />
                    <QueryBoundTextInput
                        defaultValue={getInitialValue("build_flows_limit")}
                        label="Build Flows Limit"
                        tooltip="Max number of build_flows to aggregate (performance optimization)"
                        onValueUpdate={(value) => fetchServerData({ build_flows_limit: value })} />
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
    console.log(defaultValue);

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
    currentValue?: mixed,
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
    currentValue?: string | string[], fetchServerData): Field => {
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
        perfUIStatus: selectPerfUIStatus(appState),
        buildflow_filters: selectBuildflowFiltersUI(appState),
    }
};

const actions = {
    doPerfREST_UI_Fetch: perfREST_UI_Fetch,
};


let PerfTableOptionsUIConnected: React.ComponentType<{}> =
    connect(select, actions)( PerfTableOptionsUI );

export default PerfTableOptionsUIConnected;
