import is, { AssertionType } from "sarcastic";

const PerfDataShape = is.shape({
  count: is.number,
  next: is.maybe(is.string),
  previous: is.maybe(is.string),
  results: is.arrayOf(is.object),
});

export type PerfData = AssertionType<typeof PerfDataShape>;

export const assertPerfData = (data: unknown, context?: string): PerfData => 
  is(data, PerfDataShape, context || 'PerfData from server: ');
