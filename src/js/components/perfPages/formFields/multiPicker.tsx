import Combobox from '@salesforce/design-system-react/components/combobox';
import * as React from 'react';

interface Props {
  onChange: (data: string[]) => void;
  choices: [string, string][];
  defaultValue?: string[] | null;
}

interface SLDSChoiceOption {
  id: string;
  label: string;
}

type Options = SLDSChoiceOption[];

const getSelectionListFromDefaultValue = (options: any[], defaultValue) => {
  if (defaultValue !== null && defaultValue !== undefined) {
    const included_options = options.filter(
      (option) => defaultValue.indexOf(option.id) >= 0,
    );
    return included_options;
  }
  return undefined;
};

const MultiPicker = ({ onChange, choices, defaultValue }: Props) => {
  console.assert(choices && choices.length, 'Choices is empty', choices); // eslint-disable-line no-console
  const options = choices.map((pair) => ({ id: pair[0], label: pair[1] }));

  const onUpdate = (selections: Options) => {
    const include_fields = selections.map((selection) => selection.id);
    onChange(include_fields);
  };

  return (
    <Combobox
      id="combobox-readonly-multiple"
      events={{
        onRequestRemoveSelectedOption: (
          _event: unknown,
          data: { selection: Options },
        ) => onUpdate(data.selection),
        onSelect: (_event: unknown, data: { selection: Options }) =>
          onUpdate(data.selection),
      }}
      labels={{
        placeholder: 'Select Columns',
      }}
      multiple
      options={options}
      selection={getSelectionListFromDefaultValue(options, defaultValue)} // eslint-disable-line no-use-before-define
      value=""
      variant="readonly"
    />
  );
};

export default MultiPicker;
