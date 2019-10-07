import React from 'react';
import { render } from 'react-testing-library';

import MultiPicker from '../../../../../js/components/perfPages/formFields/multiPicker';

describe('Choice Field', () => {
  test('Renders simple multipicker', () => {
    const choices = [['a', 'AXYZZY'], ['b', 'BXYZZY']];
    const { getByPlaceholderText } = render(<MultiPicker choices={choices} />);
    expect(getByPlaceholderText('Select an Option')).toBeVisible();
  });

  test('Renders multipicker with default', () => {
    const choices = [['a', 'AXYZZY'], ['b', 'BXYZZY']];
    const { getByPlaceholderText } = render(
      <MultiPicker choices={choices} defaultValue="b" />,
    );
    expect(getByPlaceholderText('Select an Option')).toBeVisible();
  });
});
