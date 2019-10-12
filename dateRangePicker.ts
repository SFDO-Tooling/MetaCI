"use strict";

var __importStar = this && this.__importStar || function (mod) {
  if (mod && mod.__esModule) return mod;
  var result = {};
  if (mod != null) for (var k in mod) if (Object.hasOwnProperty.call(mod, k)) result[k] = mod[k];
  result["default"] = mod;
  return result;
};
var __importDefault = this && this.__importDefault || function (mod) {
  return mod && mod.__esModule ? mod : { "default": mod };
};
exports.__esModule = true;
var react_1 = __importStar(require("react"));
var date_picker_1 = __importDefault(require("@salesforce/design-system-react/components/date-picker"));
var button_1 = __importDefault(require("@salesforce/design-system-react/components/button"));
var DateRangePicker = function (_a) {
  var onChange = _a.onChange,
      startName = _a.startName,
      endName = _a.endName,
      startValue = _a.startValue,
      endValue = _a.endValue;
  var localOnChange = function (name, data) {
    if (data.formattedDate === '') {
      onChange(name, undefined);
    } else if (data.date.getFullYear() > 2015) {
      var YYYY = data.date.getFullYear().toString();
      var MM = (data.date.getMonth() + 1).toString();
      var DD = data.date.getDate().toString();
      onChange(name, YYYY + "-" + MM + "-" + DD);
    }
  };
  // changing the key reliably clears the input,
  // so these variables are part of an input clearing hack
  // https://github.com/salesforce/design-system-react/issues/1868#issue-425218055
  var _b = react_1.useState(1),
      startDateKey = _b[0],
      setStartDateKey = _b[1];
  var _c = react_1.useState(1),
      endDateKey = _c[0],
      setEndDateKey = _c[1];
  // check for bad or missing dates
  var startValueOrNull = null;
  var endValueOrNull = null;
  if (startValue) {
    startValueOrNull = new Date(startValue);
  }
  if (endValue) {
    endValueOrNull = new Date(endValue);
  }
  return react_1["default"].createElement(react_1["default"].Fragment, null, react_1["default"].createElement(date_picker_1["default"], { key: "start" + startDateKey, value: startValueOrNull, onChange: function (_event, data) {
      localOnChange(startName, data);
    } }), react_1["default"].createElement(button_1["default"], { iconCategory: "action", variant: "icon", iconName: "remove", onClick: function () {
      setStartDateKey(startDateKey + 1);
      onChange(startName, undefined);
    } }), "\u00A0 - \u00A0", react_1["default"].createElement(date_picker_1["default"], { key: "end" + endDateKey, value: endValueOrNull, onChange: function (_event, data) {
      localOnChange(endName, data);
    } }), react_1["default"].createElement(button_1["default"], { iconCategory: "action", variant: "icon", iconName: "remove", onClick: function () {
      onChange(endName, undefined);
      setEndDateKey(endDateKey + 1);
    } }));
};
exports["default"] = DateRangePicker;
