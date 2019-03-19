// @flow

import * as React from 'react';
import Alert from '@salesforce/design-system-react/components/alert';
import AlertContainer from '@salesforce/design-system-react/components/alert/container';
import { t } from 'i18next';

const reloadPage = (): void => {
  window.location.reload();
};

const OfflineAlert = () => (
  <AlertContainer className="offline-alert">
    <Alert
      labels={{
        heading: t(
          'You are in offline mode. We are trying to reconnect, but you may need to',
        ),
        headingLink: t('reload the page.'),
      }}
      onClickHeadingLink={reloadPage}
      variant="offline"
    />
  </AlertContainer>
);

export default OfflineAlert;
