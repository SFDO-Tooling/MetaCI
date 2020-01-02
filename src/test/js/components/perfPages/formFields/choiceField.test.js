import { render } from '@testing-library/react';
import React from 'react';

import { AllFilters, createField } from '@/components/perfPages/formFields';

describe('Choice Field', () => {
  test('Renders Choice Fields with defauled value', () => {
    const filterDef = {
      name: 'MyChoiceFilter',
      field_type: 'ChoiceField',
      field_module: '',
      choices: [
        ['choice1', 'value1'],
        ['choicd2', 'value2'],
      ],
    };
    const field = createField(filterDef, 'value1');

    const filters = [field];
    const { getByPlaceholderText } = render(<AllFilters filters={filters} />);

    const input = getByPlaceholderText('Select MyChoiceFilter');
    expect(input).toBeVisible();
  });
  test('renders CharField with no value', () => {
    const filterDef = {
      name: 'MyCharFilter',
      label: 'MyLabel',
      field_type: 'CharField',
      field_module: '',
    };
    const field = createField(filterDef);

    const filters = [field];
    const { getByLabelText } = render(<AllFilters filters={filters} />);

    expect(getByLabelText('MyLabel')).toBeVisible();
    expect(getByLabelText('MyLabel').getAttribute('value')).toBeFalsy();
  });
});
