// @flow

import * as React from 'react';
import { useState } from 'react';
import * as ReactDOM from 'react-dom';

import { connect } from 'react-redux';

import { withRouter } from 'react-router';

import get from 'lodash/get';

import queryString from 'query-string';

// flowlint  untyped-import:off
import Combobox from '@salesforce/design-system-react/components/combobox';
import Icon from '@salesforce/design-system-react/components/icon';
import comboboxFilterAndLimit from '@salesforce/design-system-react/components/combobox/filter';
import IconSettings from '@salesforce/design-system-react/components/icon-settings';
// flowlint  untyped-import:error


import { perfRESTFetch, perfREST_UI_Fetch } from 'store/perfdata/actions';

import { selectPerfState, selectPerfUIStatus } from 'store/perfdata/selectors';

type Props = {
	choices : {id:string}[],
	field_name: string,
	value?: string|null,
	onSelect: (mixed) => void,
}

const FilterPicker = ({choices, field_name, value, onSelect}: Props) : React.Node =>  {
		let selected = value ? choices.filter((choice)=>choice.id===value) : [];
		let [inputValue, setInputValue] = useState("");
		let [selection, setSelection] = useState(selected);
		return (
			<Combobox
			id="combobox-inline-single"
			placeholder={field_name}
			events={{
				onChange: (event, { value }) => {
					setInputValue( value  );
				},
				onRequestRemoveSelectedOption: (event, data) => {
					setInputValue('');
					setSelection(data.selection);
					onSelect();
				},
				onSubmit: (event, { value }) => {
					setInputValue('');
					setSelection([
							...selection,
							{
								label: value,
								icon: (
									<Icon
										assistiveText={{ label: 'Account' }}
										category="standard"
										name="account"
									/>
								),
							},
					]);
				},
				onSelect: (event, data) => {
					if (onSelect && data) {
						onSelect(
							data.selection[0]["id"]
						);
					}
					setInputValue('');
					setSelection(data.selection);
				},
			}}
			labels={{
				placeholder: 'Select ' + field_name,
				placeholderReadOnly: 'Select ' + field_name,
			}}
			options={comboboxFilterAndLimit({
				inputValue: inputValue,
				options: choices,
				selection: selection,
				limit: 20,
			})}
			selection={selection}
			value={inputValue}
			variant="base"
		/>
		);
}

export default FilterPicker;