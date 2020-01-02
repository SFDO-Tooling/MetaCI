import { render } from '@testing-library/react';
import React from 'react';

import { AllFilters, createField } from '@/components/perfPages/formFields';

describe('<AllFilters />', () => {
  test('returns null for missing field type', () => {
    const filterDef = {
      name: 'MyUnknownFilter',
      label: 'MyLabel',
      field_type: 'UnknownFieldType',
      field_module: '',
    };
    const field = createField(filterDef, 5);
    expect(field).toBeNull();

    const filters = [field];
    const { queryByLabelText } = render(<AllFilters filters={filters} />);

    expect(queryByLabelText('MyLabel')).toBeNull();
  });
});

// ChoiceField,
// CharField,
// DecimalField,
