
//  TODO: Add Flow Checking to this

import * as React from 'react';
import * as ReactDOM from 'react-dom';

import { connect } from 'react-redux';

import { withRouter } from 'react-router';

import get from 'lodash/get';

import queryString from 'query-string';

import Combobox from '@salesforce/design-system-react/components/combobox';
import Icon from '@salesforce/design-system-react/components/icon';

import { perfRESTFetch, perfREST_UI_Fetch } from 'store/perfdata/actions';

import { selectPerfState, selectPerf_UI_State } from 'store/perfdata/selectors';


class FieldPicker extends React.Component<{}> {
	constructor(props) {
		super(props);
    }

    getSelectionFromUrl(options){
        let oldQueryParams = queryString.parse(window.location.search);
        let included_field_names = oldQueryParams["include_fields"];
        if(!Array.isArray(included_field_names)){
            included_field_names = [included_field_names];
        }
        let included_options = options.filter((option)=>included_field_names.indexOf( option.id )>=0);
        console.log("Included options", included_options);
        return included_options;
    }

    queryStringFromSelection(selection){
        let include_fields = selection.map((selection) => selection.id );
        let newQueryParams = {include_fields};
        let oldQueryParams = queryString.parse(window.location.search);
        let qs = queryString.stringify({...oldQueryParams, ...newQueryParams});
        return qs;
    }

    changeURL = (history, data) => {
        this.props.history.push({pathname: window.location.pathname, 
            search: this.queryStringFromSelection(data.selection)});
        if(this.props.onChange) this.props.onChange();
        };

	render() {      
          const columnOptions = () => {
            let columns: [string, string][] = [["Loading", "Loading"]];
            let server_column_options: [string, string][] = get(this.props.perfdataUIstate, "uidata.includable_fields");
            if(server_column_options){
              columns = server_column_options;
            }
            return columns.map((pair)=>({id: pair[0], label: pair[1]}));
          }
      
          let options = columnOptions();
      
		return (
				<Combobox
					id="combobox-readonly-multiple"
					events={{
						onRequestRemoveSelectedOption: this.changeURL,
						onSelect: this.changeURL,
					}}
					labels={{
						label: 'Column',
						placeholder: 'Select Columns',
					}}
					multiple
					options={options}
					selection={this.getSelectionFromUrl(options)}
					value=""
					variant="readonly"
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
  
 const ConnectedFieldPicker : React.ComponentType<{}> = withRouter(connect(select, actions)(
    FieldPicker,
));

export default ConnectedFieldPicker;