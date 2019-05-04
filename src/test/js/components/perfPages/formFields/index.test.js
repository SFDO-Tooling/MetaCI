import React from 'react';
import { render } from 'react-testing-library';

import { createField, AllFilters } from 'components/perfPages/formFields';

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
