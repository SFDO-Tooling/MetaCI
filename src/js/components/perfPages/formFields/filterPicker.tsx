// @flow

import React, { useState } from 'react';
import type { Node } from 'react';
import Combobox from '@salesforce/design-system-react/components/combobox';
import Icon from '@salesforce/design-system-react/components/icon';
import comboboxFilterAndLimit from '@salesforce/design-system-react/components/combobox/filter';

type Props = {
  choices: { id: string }[],
  field_name: string,
  currentValue?: string | null,
  onSelect: mixed => void,
};

const FilterPicker = ({
  choices,
  field_name,
  currentValue,
  onSelect,
}: Props): Node => {
  const selected = currentValue
    ? choices.filter(choice => choice.id === currentValue)
    : [];
  const [inputValue, setInputValue] = useState('');
  const [selection, setSelection] = useState(selected);
  return (
    <Combobox
      id="combobox-inline-single"
      events={{
        onChange: (_event, { value }) => {
          setInputValue(value);
        },
        onRequestRemoveSelectedOption: (_event, data) => {
          setInputValue('');
          setSelection(data.selection);
          onSelect();
        },
        onSubmit: (_event, { value }) => {
          setInputValue('');
          setSelection([
            ...selection,
            {
              label: value,
              icon: (
                <Icon
                  assistiveText={{ label: 'Account' }}
                  category="standard"
                  name="account"
                />
              ),
            },
          ]);
        },
        onSelect: (_event, data) => {
          if (onSelect && data) {
            onSelect(data.selection[0].id);
          }
          setInputValue('');
          setSelection(data.selection);
        },
      }}
      labels={{
        label: field_name[0].toUpperCase() + field_name.slice(1),
        placeholder: `Select ${field_name}`,
        placeholderReadOnly: `Select ${field_name}`,
      }}
      options={comboboxFilterAndLimit({
        inputValue,
        options: choices,
        selection,
        limit: 20,
      })}
      selection={selection}
      value={inputValue}
      variant="base"
    />
  );
};

export default FilterPicker;
