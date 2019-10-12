

import React, { useState, ReactNode } from "react";
import Combobox from "@salesforce/design-system-react/components/combobox";
import Icon from "@salesforce/design-system-react/components/icon";
import comboboxFilterAndLimit from "@salesforce/design-system-react/components/combobox/filter";

type Props = {
  choices: {id: string;}[];
  field_name: string;
  currentValue?: string | null;
  onSelect: (id: string) => void;
};

const FilterPicker = ({
  choices,
  field_name,
  currentValue,
  onSelect
}: Props): ReactNode => {
  const selected = currentValue ? choices.filter(choice => choice.id === currentValue) : [];
  const [inputValue, setInputValue] = useState('');
  const [selection, setSelection] = useState(selected);
  return <Combobox id="combobox-inline-single" events={{
    onChange: (_event, {
      value
    }) => {
      setInputValue(value);
    },
    onRequestRemoveSelectedOption: (_event, data) => {
      setInputValue('');
      setSelection(data.selection);
      onSelect('');
    },
    onSelect: (_event, data) => {
      if (onSelect && data) {
        onSelect(data.selection[0].id);
      }
      setInputValue('');
      setSelection(data.selection);
    }
  }} labels={{
    label: field_name[0].toUpperCase() + field_name.slice(1),
    placeholder: `Select ${field_name}`,
    placeholderReadOnly: `Select ${field_name}`
  }} options={comboboxFilterAndLimit({
    inputValue,
    options: choices,
    selection,
    limit: 20
  })} selection={selection} value={inputValue} variant="base" />;
};

export default FilterPicker;
