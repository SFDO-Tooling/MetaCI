// @flow
 /* flowlint
  *   untyped-import:off
  */

import * as React from 'react';
import Datepicker from '@salesforce/design-system-react/components/date-picker';
import Button from '@salesforce/design-system-react/components/button';
import { useState } from 'react';

const dateRangePicker = ({onChange, startName, endName, startValue, endValue} :
                    {startName: string, endName: string,
                     startValue: Date, endValue: Date,
                        onChange : (string, string | typeof undefined) => void}) => {
    let localOnChange = (name, data) => {
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
    let [startDateKey, setStartDateKey] = useState(1);
    let [endDateKey, setEndDateKey] = useState(-1);

    // check for bad or missing dates
    let startValueOrNull = isNaN(startValue.getDate()) ? null : startValue;
    let endValueOrNull = isNaN(endValue.getDate()) ? null : endValue;
    return (
        <React.Fragment>
            <Datepicker
            key={startDateKey}
            value={startValueOrNull}
            onChange={(event, data) => {localOnChange(startName, data)}}
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
            onChange={(event, data) => {localOnChange(endName, data)}}
        />
        <Button iconCategory="action" variant="icon" iconName="remove"
            onClick={()=>{onChange(endName, undefined); setEndDateKey(endDateKey-1)} }>
            </Button>

        </React.Fragment>

    )
}

export default dateRangePicker;
