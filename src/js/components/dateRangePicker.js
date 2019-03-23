// @flow
 /* flowlint
  *   untyped-import:off
  */

import * as React from 'react';
import Datepicker from '@salesforce/design-system-react/components/date-picker';

const dateRangePicker = ({onChange, startName, endName} : 
                    {startName: string, endName: string, 
                        onChange : (string, string) => void}) => {
    var rc = {};
    let localOnChange = (name, data) => {
        onChange(name, data.date.getFullYear().toString() + "-"
                        + (data.date.getMonth() +1).toString()+ "-"
                        + data.date.getDate().toString() );
    };

    return (
        <React.Fragment>
            <Datepicker
            onChange={(event, data) => {localOnChange(startName, data)}}
        /> &nbsp; - &nbsp;
            <Datepicker
            onChange={(event, data) => {localOnChange(endName, data)}}
        />

</React.Fragment>
    
    )
}

export default dateRangePicker;
