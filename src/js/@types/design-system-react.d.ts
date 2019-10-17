/* eslint-disable one-var */

declare module '@salesforce/design-system-react/components/*' {
  import { ComponentType } from 'react';

  const value: ComponentType<any>;
  export default value;
}

declare module '@salesforce/design-system-react/components/combobox/filter' {
  const filter: ({
    inputValue,
    limit,
    options,
    selection,
  }: {
    inputValue: string;
    limit?: number;
    options?: any;
    selection?: any;
  }) => any;

  export default filter;
}

declare module '@salesforce/design-system-react/components/settings' {
  const settings: {
    setAssetsPaths: (path: string) => void;
    getAssetsPaths: () => string;
    setAppElement: (el: Element) => void;
    getAppElement: () => Element | undefined;
  };
  export default settings;
}
