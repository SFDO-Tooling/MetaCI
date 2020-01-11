import { render } from '@testing-library/react';
import React from 'react';

import { AllFilters, createField } from '@/components/perfPages/formFields';

describe('Decimal Field', () => {
  test('renders DecimalField with value', () => {
    const filterDef = {
      name: 'MyDecimalFilter',
      label: 'MyLabel',
      field_type: 'DecimalField',
      field_module: '',
    };
    const field = createField(filterDef, 5);

    const filters = [field];
    const { getByLabelText } = render(<AllFilters filters={filters} />);

    expect(getByLabelText('MyLabel')).toBeVisible();
    expect(getByLabelText('MyLabel')).toHaveAttribute('value', '5');
  });
  test('renders DecimalField with no value', () => {
    const filterDef = {
      name: 'MyDecimalFilter',
      label: 'MyLabel',
      field_type: 'DecimalField',
      field_module: '',
    };
    const field = createField(filterDef);

    const filters = [field];
    const { getByLabelText } = render(<AllFilters filters={filters} />);

    expect(getByLabelText('MyLabel')).toBeVisible();
    expect(getByLabelText('MyLabel').getAttribute('value')).toBeFalsy();
  });
  test('renders DecimalField with minimum, maximum and step values', () => {
    const filterDef = {
      name: 'MyDecimalFilter',
      label: 'MyLabel',
      field_type: 'DecimalField',
      min: 0,
      max: 0,
      step: 0,
      field_module: '',
    };
    const field = createField(filterDef);

    const filters = [field];
    const { getByLabelText } = render(<AllFilters filters={filters} />);

    expect(getByLabelText('MyLabel')).toBeVisible();
    expect(getByLabelText('MyLabel')).not.toHaveAttribute('value', '5');
  });
});

// ChoiceField,
// CharField,
// DecimalField,
