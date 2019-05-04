// @flow
/* eslint-disable react/display-name */

import is from 'sarcastic';
import React from 'react';
import type { Node } from 'react';

import FilterPicker from './filterPicker';
import TextInput from './textInput';

import type { FilterDefinition } from 'api/testmethod_perf_UI_JSON_schema';
import { NumberFilterDefinitionShape } from 'api/testmethod_perf_UI_JSON_schema';

// interface representing fields that can be shown on the screen.
export type Field = {
  name: string,
  currentValue?: mixed,
  render: () => Node,
};

const ChoiceField = (
  filter: FilterDefinition,
  currentValue?: string | null,
  fetchServerData,
): Field => {
  const choices: string[][] = is(
    filter.choices,
    is.arrayOf(is.arrayOf(is.string)),
  );
  const choices_as_objs = choices.map(pair => ({
    id: pair[0],
    label: pair[1],
  }));
  return {
    name: filter.name,
    choices: choices_as_objs,
    currentValue,
    render: () => (
      <FilterPicker
        key={filter.name}
        field_name={filter.name}
        choices={choices_as_objs}
        currentValue={currentValue}
        onSelect={fetchServerData}
      />
    ),
  };
};

const CharField = (
  filter: FilterDefinition,
  currentValue?: string | null,
  fetchServerData,
): Field => ({
  name: filter.name,
  currentValue,
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
  currentValue?: string | null,
  fetchServerData,
): Field => {
  filter = is(filter, NumberFilterDefinitionShape);
  const minValue: number | null | typeof undefined = filter.min;
  const maxValue: number | null | typeof undefined = filter.max;
  let step: number | null | typeof undefined = parseInt(filter.step, 10);
  step = isNaN(step) ? 1 : step;

  return {
    name: filter.name,
    currentValue,
    render: () => (
      <TextInput
        defaultValue={currentValue}
        label={filter.label}
        tooltip={filter.description}
        minValue={minValue === null ? undefined : minValue}
        maxValue={maxValue === null ? undefined : maxValue}
        variant="counter"
        step={step}
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
  currentValue?: string | null,
  onSubmit: () => typeof undefined,
) => {
  const fieldType = FieldTypes[filterDef.field_type];
  if (fieldType) {
    return fieldType(filterDef, currentValue, onSubmit);
  }
  // eslint-disable-next-line no-console
  console.log('Unknown filterDef type', filterDef.field_type, filterDef);
  return null;
  // throw new Error(`Unknown field type: ${filterDef.field_type}`);
};

export const AllFilters = ({ filters }: { filters: Field[] }) => (
  <div key="filterGrid" className="slds-grid slds-wrap slds-gutters">
    {filters
      .filter(x => x) // filter out nulls from unknown filter types
      .map(filter => (
        <div key={filter.name} className="slds-col slds-size_3-of-12">
          {filter.render()}
        </div>
      ))}
  </div>
);
