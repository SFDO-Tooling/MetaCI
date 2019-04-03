// @flow

import * as React from 'react';
import { useState } from 'react';

// flowlint  untyped-import:off
import Datepicker from '@salesforce/design-system-react/components/date-picker';
import Button from '@salesforce/design-system-react/components/button';
// flowlint  untyped-import:error

type SLDSDateOption = {
    formattedDate : string,
    date: Date,
};

const dateRangePicker = ({onChange, startName, endName, startValue, endValue} :
                    {startName: string, endName: string,
                     startValue?: string | null, endValue?: string | null,
                        onChange : (string, string | typeof undefined) => void}) => {
    let localOnChange = (name, data:SLDSDateOption) => {
        if(data.formattedDate===""){
            onChange(name, undefined);
        }else if(data.date.getFullYear()>2015){
                onChange(name, data.date.getFullYear().toString() + "-"
                                + (data.date.getMonth() +1).toString()+ "-"
                                + data.date.getDate().toString() );
        }
    };

    // changing the key reliably clears the input,
    // so these variables are part of an input clearing hack
    // https://github.com/salesforce/design-system-react/issues/1868#issue-425218055
    let [startDateKey, setStartDateKey] = useState(1);
    let [endDateKey, setEndDateKey] = useState(-1);

    // check for bad or missing dates
    let startValueOrNull = null;
    let endValueOrNull = null;
    if(startValue) startValueOrNull = new Date(startValue);
    if(endValue) startValueOrNull = new Date(endValue);
    console.log(startDateKey);
    return (
        <React.Fragment>
            <Datepicker
            key={startDateKey}
            value={startValueOrNull}
            onChange={(event:mixed, data) => {localOnChange(startName, data)}}
        />
        <Button iconCategory="action" variant="icon" iconName="remove"
            onClick={()=>{
                setStartDateKey(startDateKey+1);
                onChange(startName, undefined)}}>
                </Button>
        &nbsp; - &nbsp;
        <Datepicker
            key={endDateKey}
            value={endValueOrNull}
            onChange={(event:mixed, data) => {localOnChange(endName, data)}}
        />
        <Button iconCategory="action" variant="icon" iconName="remove"
            onClick={()=>{onChange(endName, undefined); setEndDateKey(endDateKey-1)} }>
            </Button>

        </React.Fragment>

    )
}

export default dateRangePicker;
