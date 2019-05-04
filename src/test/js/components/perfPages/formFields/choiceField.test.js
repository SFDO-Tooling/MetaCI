import React from 'react';
import { render } from 'react-testing-library';
import { fireEvent } from 'dom-testing-library';

import { createField, AllFilters } from 'components/perfPages/formFields';

const delay = ms => new Promise(res => setTimeout(res, ms));

describe('Choice Field', () => {
  test('Renders Choice Fields with defauled value', () => {
    const filterDef = {
      name: 'MyChoiceFilter',
      field_type: 'ChoiceField',
      field_module: '',
      choices: [['choice1', 'value1'], ['choicd2', 'value2']],
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

// ChoiceField,
// CharField,
// DecimalField,
