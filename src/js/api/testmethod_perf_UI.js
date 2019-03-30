// @flow

import is, { type AssertionType } from 'sarcastic';

const FilterDefinition = is.shape({
    name: is.string,
    label: is.maybe(is.string),
    description: is.maybe(is.string),
    choices: is.arrayOf(is.arrayOf(is.string)),
    currentValue: is.maybe(is.string),
});

const TestMethodPerfData =is.shape({
    defaults: is.object,
    filters: is.arrayOf(FilterDefinition),
    includable_fields: is.arrayOf(is.arrayOf(is.string))
});

const UIDataShape = is.shape({
    buildflow_filters: is.arrayOf(FilterDefinition),
    testmethod_perf: TestMethodPerfData,
    testmethod_results: TestMethodPerfData,
});



type UIData = AssertionType<typeof UIDataShape>;

function assertPkg(data: mixed): UIData {
    return is(data, UIDataShape, 'UIData from server');
}
