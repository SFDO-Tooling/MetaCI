// @flow
import React, { useState } from 'react';
import Datepicker from '@salesforce/design-system-react/components/date-picker';
import Button from '@salesforce/design-system-react/components/button';

type SLDSDateOption = {
  formattedDate: string,
  date: Date,
};

const dateRangePicker = ({
  onChange,
  startName,
  endName,
  startValue,
  endValue,
}: {
  startName: string,
  endName: string,
  startValue?: string | null,
  endValue?: string | null,
  onChange: (string, string | typeof undefined) => void,
}) => {
  const localOnChange = (name, data: SLDSDateOption) => {
    if (data.formattedDate === '') {
      onChange(name, undefined);
    } else if (data.date.getFullYear() > 2015) {
      const YYYY = data.date.getFullYear().toString();
      const MM = (data.date.getMonth() + 1).toString();
      const DD = data.date.getDate().toString();
      onChange(name, `${YYYY}-${MM}-${DD}`);
    }
  };

  // changing the key reliably clears the input,
  // so these variables are part of an input clearing hack
  // https://github.com/salesforce/design-system-react/issues/1868#issue-425218055
  const [startDateKey, setStartDateKey] = useState(1);
  const [endDateKey, setEndDateKey] = useState(1);

  // check for bad or missing dates
  let startValueOrNull = null;
  let endValueOrNull = null;
  if (startValue) {
    startValueOrNull = new Date(startValue);
  }
  if (endValue) {
    endValueOrNull = new Date(endValue);
  }
  return (
    <React.Fragment>
      <Datepicker
        key={`start${startDateKey}`}
        value={startValueOrNull}
        onChange={(_event: mixed, data) => {
          localOnChange(startName, data);
        }}
      />
      <Button
        iconCategory="action"
        variant="icon"
        iconName="remove"
        onClick={() => {
          setStartDateKey(startDateKey + 1);
          onChange(startName, undefined);
        }}
      />
      &nbsp; - &nbsp;
      <Datepicker
        key={`end${endDateKey}`}
        value={endValueOrNull}
        onChange={(_event: mixed, data) => {
          localOnChange(endName, data);
        }}
      />
      <Button
        iconCategory="action"
        variant="icon"
        iconName="remove"
        onClick={() => {
          onChange(endName, undefined);
          setEndDateKey(endDateKey + 1);
        }}
      />
    </React.Fragment>
  );
};

export default dateRangePicker;
