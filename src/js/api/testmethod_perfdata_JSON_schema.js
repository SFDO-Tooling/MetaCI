// @flow

import is, { type AssertionType } from 'sarcastic';

const PerfDataShape = is.shape({
    count: is.number,
    next: is.maybe(is.string),
    previous: is.maybe(is.string),
    results: is.arrayOf(is.object),
});


export type PerfData = AssertionType<typeof PerfDataShape>;

export function assertPerfData(data: mixed): PerfData {
    return is(data, PerfDataShape, 'UIData from server: ');
}
