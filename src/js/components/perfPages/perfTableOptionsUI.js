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
// flowlint  untyped-import:off
import { t } from 'i18next';
import Accordion from '@salesforce/design-system-react/components/accordion';
import AccordionPanel from '@salesforce/design-system-react/components/accordion/panel';
// flowlint untyped-type-import:error

import FieldPicker from './formFields/fieldPicker';
import FilterPicker from './formFields/filterPicker';
import DateRangePicker from './formFields/dateRangePicker';
import TextInput from './formFields/textInput';

import { perfRESTFetch, perfREST_UI_Fetch } from 'store/perfdata/actions';

import { selectPerfUIStatus, selectBuildflowFiltersUI } from 'store/perfdata/selectors';
import type { FilterDefinition } from '../../api/testmethod_perf_UI';

type Props = {
    fetchServerData : (params?: {
        [string]: ?(string | Array<string>)
      }) => void,
      queryparams: (name?: string) => string,
      testmethodPerfUI: {},
}

type ReduxProps = {
    perfUIStatus : string,
    buildflow_filters: FilterDefinition[],
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
    const getInitialValue = (param: string) :
                                            string | null => {
        var stringOrList: string | string[] = queryparams.get(param);
        if(Array.isArray(stringOrList)) return stringOrList[0];
        else return stringOrList;

        // There was more complicated code here for special-casing
        // method_name. If you need to revive it, its in commit
        // ca3d2b8a9
    }

    const getInitialValueList = (param: string):
        string[] | null => {

        var stringOrList: string | string[] = queryparams.get(param);
        if (Array.isArray(stringOrList)) return stringOrList;
        else return [stringOrList];
    }

    const gatherFilters = (perfdataUIstate): Field[] => {
        let filters: Field[] = [];
        if(!uiAvailable) return filters;

        const testmethod_perf_filters = get(perfdataUIstate,
                            "filters");
        const all_filters = [...buildflow_filters, ...testmethod_perf_filters];
        if(all_filters.length){
            all_filters.map((filterDef)=>{
                console.log(filterDef.name, getInitialValue(filterDef));
                if(get(filterDef, "choices")){
                    filters.push(
                        ChoiceField(filterDef,
                            getInitialValue(filterDef.name),
                            fetchServerData));
                } else if (filterDef.field_type == "DecimalField") {
                    filters.push(
                        DecimalField(filterDef,
                            getInitialValue(filterDef.name),
                            fetchServerData));
                } else if (filterDef.field_type == "CharField") {
                    filters.push(
                        CharField(filterDef,
                            getInitialValue(filterDef.name),
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
                    defaultValue={getInitialValueList("include_fields")}
                    onChange={(data) => fetchServerData({include_fields:data})} />}
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
                    startValue={getInitialValue("daterange_after")}
                    endValue={getInitialValue("daterange_before")} />
                }
            </AccordionPanel>
            <AccordionPanel id="perfPanelOptions"
                key="perfPanelOptions"
                summary="Options"
                expanded={perfPanelOptionsExpanded}
                onTogglePanel={() => { setPerfPanelOptionsExpanded(!perfPanelOptionsExpanded) }}>
                {uiAvailable &&
                <React.Fragment>
                    <TextInput defaultValue={getInitialValue("page_size")}
                        label="Page Size"
                        tooltip="Number of rows to fetch per page"
                        onValueUpdate={(value: string) => fetchServerData({ page_size: value })} />
                    <TextInput
                        defaultValue={getInitialValue("build_flows_limit")}
                        label="Build Flows Limit"
                        tooltip="Max number of build_flows to aggregate (performance optimization)"
                        onValueUpdate={(value: string) => fetchServerData({ build_flows_limit: value })} />
                </React.Fragment>
                }
            </AccordionPanel>
        </Accordion>
    )
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
    render: () => React.Node
};

const ChoiceField = (filter: FilterDefinition,
                    currentValue?: string | null,
                    fetchServerData) : Field => {
    // TODO: switch to Sarcastic for this
    console.assert(Array.isArray(filter.choices) && filter.choices.length>1);
    const choices:string[] = (filter.choices:any);
    let choices_as_objs = choices.map((pair) => (
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

const CharField = (filter: FilterDefinition,
    currentValue?: string | null,
    fetchServerData): Field => {
    return {
        name: filter.name,
        currentValue,
        render: () =>
            <TextInput defaultValue={currentValue}
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
