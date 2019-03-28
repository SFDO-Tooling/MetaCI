// @flow

import * as React from 'react';
import { Trans } from 'react-i18next';

import routes from 'utils/routes';
import { logError } from 'utils/logging';
import { EmptyIllustration } from 'components/404';

type Props = { children: React.Node };

class ErrorBoundary extends React.Component<Props, { hasError: boolean }> {
  constructor(props: Props) {
    super(props);
    this.state = { hasError: false };
  }

  /* istanbul ignore next */
  componentDidCatch(error: Error, info: {}) {
    this.setState({ hasError: true });
    logError(error, info);
  }

  render(): React.Node {
    if (this.state.hasError) {
      return (
        <EmptyIllustration
          message={
            <Trans i18nKey="anErrorOccurred">
              An error occurred. Try the <a href={routes.home()}>home page</a>?
            </Trans>
          }
        />
      );
    }
    return this.props.children;
  }
}

export default ErrorBoundary;
