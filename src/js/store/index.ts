import { combineReducers } from "redux";

import { perfDataReducer, perfDataUIReducer } from "store/perfdata/reducer";
import { PerfDataState, PerfData_UI_State } from "store/perfdata/reducer";

export type AppState = {
  readonly perfData: PerfDataState;
  readonly perfDataUI: PerfData_UI_State;
};


const reducer = combineReducers({
  perfData: perfDataReducer,
  perfDataUI: perfDataUIReducer
});

export default reducer;
