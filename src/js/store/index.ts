import { combineReducers } from 'redux';
import {
  PerfData_UI_State,
  perfDataReducer,
  PerfDataState,
  perfDataUIReducer,
} from 'store/perfdata/reducer';

export interface AppState {
  readonly perfData: PerfDataState;
  readonly perfDataUI: PerfData_UI_State;
}

const reducer = combineReducers({
  perfData: perfDataReducer,
  perfDataUI: perfDataUIReducer,
});

export default reducer;
