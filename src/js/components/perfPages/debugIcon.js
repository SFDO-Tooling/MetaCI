// @flow

import * as React from 'react';
import { connect } from 'react-redux';
import Icon from '@salesforce/design-system-react/components/icon';
import type { ComponentType } from 'react';
import { selectDebugStatus } from 'store/perfdata/selectors';
import type { AppState } from 'store';
import type { UIData } from 'api/testmethod_perf_UI_JSON_schema';
import get from 'lodash/get';

type ReduxProps = {
  debugStatus: boolean,
};

const UnwrappedDebugIcon = ({ debugStatus }: ReduxProps) =>
  debugStatus ? (
    <div style={{ textAlign: 'right' }}>
      <a href={get("foo", 'x')} target="_debugCodeWindow">
        <Icon
          assistiveText={{ label: 'debug' }}
          category="utility"
          name="cases"
        />
      </a>
    </div>
  ) : null;

const select = (appState: AppState) => ({
  debugStatus: selectDebugStatus(appState),
});

const DebugIcon: ComponentType<{}> = connect(
  select,
  null,
)(UnwrappedDebugIcon);

export default DebugIcon;
