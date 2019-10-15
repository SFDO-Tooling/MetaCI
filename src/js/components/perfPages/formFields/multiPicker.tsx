
import * as React from "react";
import Combobox from "@salesforce/design-system-react/components/combobox";

type Props = {
  onChange: (arg0: string[]) => void;
  choices: [string, string][];
  defaultValue?: string[] | null;
};

type SLDSChoiceOption = {
  id: string;
  label: string;
};

type Options = SLDSChoiceOption[];

const MultiPicker = ({
  onChange,
  choices,
  defaultValue
}: Props) => {
  console.assert(choices && choices.length, 'Choices is empty', choices); // eslint-disable-line no-console
  const options = choices.map(pair => ({ id: pair[0], label: pair[1] }));

  const onUpdate = (selections: Options) => {
    const include_fields = selections.map(selection => selection.id);
    onChange(include_fields);
  };

  return <Combobox id="combobox-readonly-multiple" events={{
    onRequestRemoveSelectedOption: (_event: unknown, data: {selection: Options;}) => onUpdate(data.selection),
    onSelect: (_event: unknown, data: {selection: Options;}) => onUpdate(data.selection)
  }} labels={{
    placeholder: 'Select Columns'
  }} multiple options={options} selection={getSelectionListFromDefaultValue(options, defaultValue)} // eslint-disable-line no-use-before-define
  value="" variant="readonly" />;
};

const getSelectionListFromDefaultValue = (options: any[], defaultValue) => {
  if (defaultValue !== null && defaultValue !== undefined) {
    const included_options = options.filter(option => defaultValue.indexOf(option.id) >= 0);
    return included_options;
  }
  return undefined;
};

export default MultiPicker;
