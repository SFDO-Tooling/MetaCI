// @flow
import get from 'lodash/get';
import * as React from 'react';
import { Trans } from 'react-i18next';
import Illustration from '@salesforce/design-system-react/components/illustration';

import svgPath from 'images/broken.svg';
import { logError } from 'utils/logging';

type Props = { children: React.Node };

class ErrorBoundary extends React.Component<
  Props,
  { hasError: boolean, error?: any, info?: any },
> {
  constructor(props: Props) {
    super(props);
    this.state = { hasError: false };
  }

  /* istanbul ignore next */
  componentDidCatch(error: Error, info: {}) {
    this.setState({ hasError: true, error, info });
    logError(error, info);
  }

  render(): React.Node {
    if (this.state.hasError) {
      return (
        <EmptyIllustration
          message={
            <>
              <Trans i18nKey="anErrorOccurred">
                Unless you pasted a URL incorrectly, it is probably a bug in the
                code or a networking problem.
                <br />
                Our top minds have been alerted.
                <br />
                You may need to <a href="./perf">rebuild your query</a> from
                scratch. Sorry about that.
                <br />
              </Trans>
              <p>
                {get(this.state, 'error.message') && (
                  <>
                    The error was &ldquo;{get(this.state, 'error.message')}
                    &rdquo;
                  </>
                )}
              </p>
            </>
          }
        />
      );
    }
    return this.props.children;
  }
}

export const EmptyIllustration = ({ message }: { message: React.Node }) => (
  <Illustration
    heading="Yikes! An error occurred!  :("
    messageBody={message}
    name="Broken"
    path={`${svgPath}#broken`}
    size="large"
  />
);

export default ErrorBoundary;
