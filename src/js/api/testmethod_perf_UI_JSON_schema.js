// @flow

import is, { type AssertionType } from 'sarcastic';

const FilterDefinitionShape = is.shape({
  name: is.string,
  label: is.maybe(is.string),
  description: is.maybe(is.string),
  choices: is.maybe(is.arrayOf(is.arrayOf(is.string))),
  currentValue: is.maybe(is.string),
  field_type: is.string,
  field_module: is.string,
  lookup_expr: is.maybe(is.string),
});

const TestMethodPerfUIShape = is.shape({
  defaults: is.object,
  filters: is.arrayOf(FilterDefinitionShape),
  includable_fields: is.arrayOf(is.arrayOf(is.string)),
});

const UIDataShape = is.shape({
  buildflow_filters: is.arrayOf(FilterDefinitionShape),
  testmethod_perf: TestMethodPerfUIShape,
  testmethod_results: TestMethodPerfUIShape,
});

export type UIData = AssertionType<typeof UIDataShape>;
export type FilterDefinition = AssertionType<typeof FilterDefinitionShape>;
export type TestMethodPerfUI = AssertionType<typeof TestMethodPerfUIShape>;

export const assertUIData = (data: mixed): UIData =>
  is(data, UIDataShape, 'UIData from server: ');
