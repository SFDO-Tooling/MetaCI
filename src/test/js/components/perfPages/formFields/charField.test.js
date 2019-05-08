import React from 'react';
import { render, fireEvent } from 'react-testing-library';
import { createField, AllFilters } from 'components/perfPages/formFields';

describe('Text Field', () => {
  test('renders CharField with value', () => {
    const filterDef = {
      name: 'MyCharFilter',
      label: 'MyLabel',
      field_type: 'CharField',
      field_module: '',
    };
    const field = createField(filterDef, 'abc');

    const filters = [field];
    const { getByLabelText } = render(<AllFilters filters={filters} />);

    expect(getByLabelText('MyLabel')).toBeVisible();
    expect(getByLabelText('MyLabel')).toHaveAttribute('value', 'abc');
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
  test('updates CharField (incomplete)', () => {
    const filterDef = {
      name: 'MyCharFilter',
      label: 'MyLabel',
      field_type: 'CharField',
      field_module: '',
    };
    const field = createField(filterDef);

    const filters = [field];
    const { getByLabelText, getByDisplayValue } = render(
      <AllFilters filters={filters} />,
    );
    const charField = getByLabelText('MyLabel');
    fireEvent.change(charField, { target: { value: 'abc' } });
    expect(getByDisplayValue('abc')).toBeVisible();
  });
});
