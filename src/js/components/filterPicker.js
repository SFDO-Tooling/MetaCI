
//  TODO: Add Flow Checking to this

import * as React from 'react';
import * as ReactDOM from 'react-dom';

import { connect } from 'react-redux';

import { withRouter } from 'react-router';

import get from 'lodash/get';

import queryString from 'query-string';

import Combobox from '@salesforce/design-system-react/components/combobox';
import Icon from '@salesforce/design-system-react/components/icon';
import comboboxFilterAndLimit from '@salesforce/design-system-react/components/combobox/filter';
import IconSettings from '@salesforce/design-system-react/components/icon-settings';


import { perfRESTFetch, perfREST_UI_Fetch } from 'store/perfdata/actions';

import { selectPerfState, selectPerf_UI_State } from 'store/perfdata/selectors';

class FilterPicker extends React.Component<{}> {
	constructor(props) {
		super(props);

		let selected = this.props.choices.filter((value)=>value.id===this.props.value);
		this.state = {
			inputValue: "",
			selection: selected,
		};
	}

	render() {
		return (
			<Combobox
			id="combobox-inline-single"
			placeholder={this.props.field_name}
			events={{
				onChange: (event, { value }) => {
					this.setState({ inputValue: value });
				},
				onRequestRemoveSelectedOption: (event, data) => {
					this.setState({
						inputValue: '',
						selection: data.selection,
					});
					this.props.onSelect(undefined);
				},
				onSubmit: (event, { value }) => {
					this.setState({
						inputValue: '',
						selection: [
							...this.state.selection,
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
						],
					});
				},
				onSelect: (event, data) => {
					if (this.props.onSelect && data) {
						this.props.onSelect(
							data.selection[0]["id"]
						);
					}
					this.setState({
						inputValue: '',
						selection: data.selection,
					});
				},
			}}
			labels={{
				placeholder: 'Select ' + this.props.field_name,
				placeholderReadOnly: 'Select ' + this.props.field_name,
			}}
			options={comboboxFilterAndLimit({
				inputValue: this.state.inputValue,
				options: this.props.choices,
				selection: this.state.selection,
				limit: 20,
			})}
			selection={this.state.selection}
			value={
				this.state.selectedOption
					? this.state.selectedOption.label
					: this.state.inputValue
			}
			variant="base"
		/>
		);
	}
}


const select = (appState: AppState) => {
    return {
    perfdataUIstate: selectPerf_UI_State(appState),
  }};
  
  const actions = {
    doPerfREST_UI_Fetch: perfREST_UI_Fetch,
  };
  
 const ConnectedFilterPicker : React.ComponentType<{}> = withRouter(connect(select, actions)(
	FilterPicker,
));

export default ConnectedFilterPicker;