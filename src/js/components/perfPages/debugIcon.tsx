import Icon from '@salesforce/design-system-react/components/icon';
import React from 'react';
import { connect } from 'react-redux';
import { AppState } from 'store';
import {
  selectDebugStatus,
  selectPerfDataAPIUrl,
} from 'store/perfdata/selectors';

interface ReduxProps {
  debugStatus: boolean;
  apiURL: string;
}

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

const DebugIcon: React.ComponentType<{}> = connect(
  select,
  null,
)(UnwrappedDebugIcon);

export default DebugIcon;
