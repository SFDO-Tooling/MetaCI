import {
  FilterDefinition,
  NumberFilterDefinitionShape,
} from 'api/testmethod_perf_UI_JSON_schema';
import React from 'react';
import is from 'sarcastic';

import FilterPicker from './filterPicker';
import TextInput from './textInput';

// interface representing fields that can be shown on the screen.
export interface Field {
  name: string;
  currentValue?: unknown;
  choices?: any[];
  render: () => any;
}

const ChoiceField = (
  filter: FilterDefinition,
  currentValue: string | null,
  fetchServerData,
): Field => {
  const choices: string[][] = is(
    filter.choices,
    is.arrayOf(is.arrayOf(is.string)),
  );
  const choicesAsObjs = choices.map((pair) => ({
    id: pair[0],
    label: pair[1],
  }));
  return {
    name: filter.name,
    choices: choicesAsObjs,
    currentValue,
    // eslint-disable-next-line react/display-name
    render: () => (
      <FilterPicker
        key={filter.name}
        field_name={filter.name}
        choices={choicesAsObjs}
        currentValue={currentValue}
        onSelect={fetchServerData}
      />
    ),
  };
};

const CharField = (
  filter: FilterDefinition,
  currentValue: string | null,
  fetchServerData,
): Field => ({
  name: filter.name,
  currentValue,
  // eslint-disable-next-line react/display-name
  render: () => (
    <TextInput
      defaultValue={currentValue}
      label={filter.label}
      tooltip={filter.description}
      onValueUpdate={fetchServerData}
    />
  ),
});

const DecimalField = (
  filter: FilterDefinition,
  currentValue: string | null,
  fetchServerData,
): Field => {
  filter = is(filter, NumberFilterDefinitionShape);
  // const minValue: number | null | typeof undefined = filter.min;
  // const maxValue: number | null | typeof undefined = filter.max;
  // linter bug?
  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  let step: number | null | typeof undefined = parseInt(filter.step, 10);
  if (isNaN(step)) {
    step = 1;
  }

  return {
    name: filter.name,
    currentValue,
    // eslint-disable-next-line react/display-name
    render: () => (
      <TextInput
        defaultValue={currentValue}
        label={filter.label}
        tooltip={filter.description}
        onValueUpdate={fetchServerData}
      />
    ),
  };
};

const FieldTypes = {
  ChoiceField,
  CharField,
  DecimalField,
};

export const createField = (
  filterDef: FilterDefinition,
  currentValue: string | null,
  onSubmit: (value) => void,
): Field => {
  const fieldType = FieldTypes[filterDef.field_type];
  if (fieldType) {
    return fieldType(filterDef, currentValue, onSubmit);
  }
  // eslint-disable-next-line no-console
  console.log('Unknown filterDef type', filterDef.field_type, filterDef);
  return null;
  // throw new Error(`Unknown field type: ${filterDef.field_type}`);
};

// This is a gross hack but its a legitimately hard problem: the server
// controls what fields it sends but the client needs to make it look nice.
// I need the fourth field (which I know is "Success Percentage") to wrap
// to the next line.
//
// There is no good place to put the responsibility for deciding how to lay
// things out. In the future we will use a filter UI more like Salesforce's
// and this hack can go away.
//
// Essentially random layout of server fields is why so many enterprise apps
// look horrible. This small hack is a compromise. It means that the client
// and server are more tightly bound then they otherwise would be. Adding
// or removing fields requires a change here.
const spacerField = {
  name: 'Blank "field" to space things out',
  currentValue: '',
  render: () => <span />, // eslint-disable-line react/display-name
};

export const AllFilters = ({ filters }: { filters: Field[] }) => {
  // Yes...this is gross. I'm sorry.
  filters.splice(2, 0, spacerField, spacerField);
  filters = filters.filter((x) => x); // get rid of nulls
  return (
    <div key="filterGrid" className="slds-grid slds-wrap slds-gutters">
      {filters.map((filter) => (
        <div key={filter.name} className="slds-col slds-size_3-of-12">
          {filter.render()}
        </div>
      ))}
    </div>
  );
};
