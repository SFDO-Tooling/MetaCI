// @flow

import type { PerfDataAction } from 'store/perfdata/actions';

export type PerfData = Object; // TODO: Make this more strongly typed!

const reducer = (state: PerfData = null, action: PerfDataAction): PerfData => {
  switch (action.type) {
    case 'PERF_DATA_AVAILALBLE':
      return null;
  }
  return state;
};

export default reducer;
