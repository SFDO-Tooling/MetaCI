import React from 'react';
import { render } from 'react-testing-library';

import DateRangePicker from '../../../../../js/components/perfPages/formFields/dateRangePicker';

describe('Choice Field', () => {
  test('Renders simple DateRangePicker', () => {
    const { getByPlaceholderText } = render(<DateRangePicker />);
    expect(getByPlaceholderText('Pick a Date')).toBeVisible();
  });

  test('Renders DateRangePicker with defaults', () => {
    const { getByPlaceholderText, getByValue } = render(
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
    expect(getByPlaceholderText('Pick a Date')).toBeVisible();
    expect(getByValue('1/20/2019')).toBeVisible();
    expect(getByValue('1/31/2019')).toBeVisible();
    expect(getByValue('5/20/2019')).toBeVisible();
    // the following shows some time zone issues to work through!
    expect(getByValue('10/1/2019')).toBeVisible();
  });
});
