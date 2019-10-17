import Input from '@salesforce/design-system-react/components/input';
import Tooltip from '@salesforce/design-system-react/components/tooltip';
import debounce from 'lodash/debounce';
import React, { useState } from 'react';

interface Props {
  label?: string | null;
  defaultValue?: string | null;
  onValueUpdate: (value: string) => void;
  tooltip?: string | null;
}

const TextInput = ({ label, defaultValue, onValueUpdate, tooltip }: Props) => {
  // debounce to reduce redraws while typing
  let debouncedCallback = debounce(
    (value: string) => onValueUpdate(value),
    1000,
  );

  // store in state so debouncer can have internal history
  const [debouncedChangeUrl] = useState(
    // wrap in obj to prevent magic useState behaviour
    { debouncedCallback },
  );
  // unwrap
  debouncedCallback = debouncedChangeUrl.debouncedCallback;

  return (
    <Input
      label={label}
      fieldLevelHelpTooltip={
        tooltip && <Tooltip align="top left" content={tooltip} />
      }
      defaultValue={defaultValue}
      onChange={(_event: null, { value }: { value: string }) =>
        debouncedCallback(value)
      }
    />
  );
};

export default TextInput;
