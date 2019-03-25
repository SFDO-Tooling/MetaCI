// @flow

import * as React from 'react';
import * as ReactDOM from 'react-dom';

import { connect } from 'react-redux';

import { withRouter } from 'react-router';
import type { RouterHistory } from 'react-router';

import get from 'lodash/get';

import queryString from 'query-string';

// flowlint  untyped-import:off
import Combobox from '@salesforce/design-system-react/components/combobox';
import Icon from '@salesforce/design-system-react/components/icon';
// flowlint  untyped-import:error

import { perfRESTFetch, perfREST_UI_Fetch } from 'store/perfdata/actions';

import { selectPerfState, selectPerf_UI_State } from 'store/perfdata/selectors';
import type { AppState } from 'store';
import type { InitialProps } from 'components/utils';

type Props = {
  onChange: () => null,
  perfdataUIstate?: { [string]: mixed }, 
}

type ReduxProps = {
  perfdataUIstate?: { [string]: mixed }, 
}

const FieldPicker = ({ history, onChange, perfdataUIstate }: Props & ReduxProps & InitialProps)  =>  {
  const columnOptions = () => {
    let columns: [string, string][] = [["Loading", "Loading"]];
    let server_column_options: [string, string][] = get(perfdataUIstate, "uidata.includable_fields");
    if (server_column_options) {
      columns = server_column_options;
    }
    return columns.map((pair) => ({ id: pair[0], label: pair[1] }));
  }

  let options = columnOptions();

  const changeURL = (data) => {
    history.push({
      pathname: window.location.pathname,
      search: queryStringFromSelection(data.selection)
    });
    if (onChange) onChange();
  };
  

  return (
    <Combobox
      id="combobox-readonly-multiple"
      events={{
        onRequestRemoveSelectedOption: (event, data) => changeURL(data),
        onSelect:  (event, data) => changeURL(data),
      }}
      labels={{
        label: 'Column',
        placeholder: 'Select Columns',
      }}
      multiple
      options={options}
      selection={getSelectionFromUrl(options)}
      value=""
      variant="readonly"
    />
  );
}

const getSelectionFromUrl = (options) => {
  let oldQueryParams = queryString.parse(window.location.search);
  let included_field_names = oldQueryParams["include_fields"];
  if (included_field_names != null) {
    if (!Array.isArray(included_field_names)) {
      included_field_names = [included_field_names];
    }
    // this is for flow's benefit
    let indexOf = included_field_names.indexOf.bind(included_field_names);

    let included_options = options.filter((option) => indexOf(option.id) >= 0);
    return included_options;
  }
}

const queryStringFromSelection = (selection: Array<{id: string}>) => {
  let include_fields = selection.map((selection) => selection.id);
  let newQueryParams = { include_fields };
  let oldQueryParams = queryString.parse(window.location.search);
  let qs = queryString.stringify({ ...oldQueryParams, ...newQueryParams });
  return qs;
}

const select = (appState: AppState) => {
  return {
    perfdataUIstate: selectPerf_UI_State(appState),
  }
};

const actions = {
  doPerfREST_UI_Fetch: perfREST_UI_Fetch,
};

const ConnectedFieldPicker: React.ComponentType<Props> = connect(select, actions)(
  withRouter(FieldPicker),
);

export default ConnectedFieldPicker;