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

import { selectPerfState, selectPerfUIStatus } from 'store/perfdata/selectors';
import type { AppState } from 'store';
import type { InitialProps } from 'components/utils';

type Props = {
  onChange: (string[]) => void,
  choices: [string, string][],
  defaultValue?: string[] | null,
};

type SLDSChoiceOption = {
  id: string,
  label: string,
};

type Options = SLDSChoiceOption[]

const FieldPicker = ({ onChange, choices, defaultValue }: Props)  =>  {
  console.assert(choices && choices.length, "Choices is empty", choices);
  let options = choices.map((pair) => ({ id: pair[0], label: pair[1] }));;

  const onUpdate = (selections : Options) => {
    let include_fields = selections.map((selection) => selection.id);
    onChange(include_fields)
  };

  return (
    <Combobox
      id="combobox-readonly-multiple"
      events={{
        onRequestRemoveSelectedOption: (event: mixed,
            data: {selection: Options}) => onUpdate(data.selection),
        onSelect:  (event: mixed,
            data: {selection: Options}) => onUpdate(data.selection),
      }}
      labels={{
        placeholder: 'Select Columns',
      }}
      multiple
      options={options}
      selection={getSelectionListFromDefaultValue(options, defaultValue)}
      value=""
      variant="readonly"
    />
  );
}

const getSelectionListFromDefaultValue = (options, defaultValue) => {
  if (defaultValue != null) {
    // this is for flow's benefit
    let indexOf = defaultValue.indexOf.bind(defaultValue);

    let included_options = options.filter((option) => indexOf(option.id) >= 0);
    return included_options;
  }
}

export default FieldPicker;