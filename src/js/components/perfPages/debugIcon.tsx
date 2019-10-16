// @flow

import * as React from 'react';
import { connect } from 'react-redux';
import Icon from '@salesforce/design-system-react/components/icon';
import type { ComponentType } from 'react';

import {
  selectDebugStatus,
  selectPerfDataAPIUrl,
} from 'store/perfdata/selectors';
import type { AppState } from 'store';

type ReduxProps = {
  debugStatus: boolean,
  apiURL: string,
};

const UnwrappedDebugIcon = ({ debugStatus, apiURL }: ReduxProps) =>
  debugStatus ? (
    <div style={{ textAlign: 'right' }}>
      <a href={apiURL} target="_debugCodeWindow">
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
  apiURL: selectPerfDataAPIUrl(appState),
});

const DebugIcon: ComponentType<{}> = connect(
  select,
  null,
)(UnwrappedDebugIcon);

export default DebugIcon;
