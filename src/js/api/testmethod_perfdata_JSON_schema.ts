// @flow

import is, { type AssertionType } from 'sarcastic';

const PerfDataShape = is.shape({
  count: is.number,
  next: is.maybe(is.string),
  previous: is.maybe(is.string),
  results: is.arrayOf(is.object),
});

export type PerfData = AssertionType<typeof PerfDataShape>;

export const assertPerfData = (data: mixed, context?: string): PerfData =>
  is(data, PerfDataShape, context || 'PerfData from server: ');
