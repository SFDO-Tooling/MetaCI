import { render } from '@testing-library/react';
import React from 'react';

import DateRangePicker from '../../../../../js/components/perfPages/formFields/dateRangePicker';

describe('Choice Field', () => {
  test('Renders simple DateRangePicker', () => {
    const { getAllByPlaceholderText } = render(<DateRangePicker />);
    expect(getAllByPlaceholderText('Pick a Date')).toHaveLength(2);
  });

  test('Renders DateRangePicker with defaults', () => {
    const { getAllByPlaceholderText, getByDisplayValue } = render(
      <div>
        1. <DateRangePicker startValue="2019-01-20T02:00" />
        2. <DateRangePicker endValue="2019-01-31T00:01" />
        3.
        <DateRangePicker
          startValue="2019-05-20T00:00"
          endValue="2019-09-31T23:30+0000"
        />
      </div>,
    );
    expect(getAllByPlaceholderText('Pick a Date')).toHaveLength(6);
    expect(getByDisplayValue('1/20/2019')).toBeVisible();
    expect(getByDisplayValue('1/31/2019')).toBeVisible();
    expect(getByDisplayValue('5/20/2019')).toBeVisible();
    // the following shows some time zone issues to work through!
    expect(getByDisplayValue('10/1/2019')).toBeVisible();
  });
});
