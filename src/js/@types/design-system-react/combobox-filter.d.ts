export type Option = {
  id: string;
  icon?: JSX.Element;
  label?: string;
  subTitle?: string;
  type?: string;
  disabled?: boolean;
  tooltipContent?: JSX.Element;
};
export type Selection = {
  id: string;
  icon?: JSX.Element;
  label?: string;
  subTitle?: string;
  type?: string;
};

export let filter: (opts: {
  inputValue: string;
  limit?: number;
  options: Option[];
  selection: Selection[];
}) => Option[];

export default filter;
