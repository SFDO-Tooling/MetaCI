// @flow
import * as React from 'react';
import Combobox from '@salesforce/design-system-react/components/combobox';

type Props = {
  onChange: (string[]) => void,
  choices: [string, string][],
  defaultValue?: string[] | null,
};

type SLDSChoiceOption = {
  id: string,
  label: string,
};

type Options = SLDSChoiceOption[];

const FieldPicker = ({ onChange, choices, defaultValue }: Props) => {
  console.assert(choices && choices.length, 'Choices is empty', choices); // eslint-disable-line no-console
  const options = choices.map(pair => ({ id: pair[0], label: pair[1] }));

  const onUpdate = (selections: Options) => {
    const include_fields = selections.map(selection => selection.id);
    onChange(include_fields);
  };

  return (
    <Combobox
      id="combobox-readonly-multiple"
      events={{
        onRequestRemoveSelectedOption: (
          _event: mixed,
          data: { selection: Options },
        ) => onUpdate(data.selection),
        onSelect: (_event: mixed, data: { selection: Options }) =>
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

const getSelectionListFromDefaultValue = (options, defaultValue) => {
  if (defaultValue !== null && defaultValue !== undefined) {
    // this is for flow's benefit
    const indexOf = defaultValue.indexOf.bind(defaultValue);

    const included_options = options.filter(option => indexOf(option.id) >= 0);
    return included_options;
  }
  return undefined;
};

export default FieldPicker;
