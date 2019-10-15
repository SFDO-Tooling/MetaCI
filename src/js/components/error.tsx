// @flow
import get from 'lodash/get';
import * as React from 'react';
import { Trans } from 'react-i18next';
import Illustration from '@salesforce/design-system-react/components/illustration';
import BrandBand from '@salesforce/design-system-react/components/brand-band';
import BrandBannerBackground from '@salesforce-ux/design-system/assets/images/themes/oneSalesforce/banner-brand-default.png';

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

const gradient = 'linear-gradient(to top, rgba(221, 219, 218, 0) 0, #1B5F9E)';

export const AuthError = ({ message }: { message: string }) => (
  <BrandBand
    id="brand-band-lightning-blue"
    className="slds-p-around_small"
    theme="lightning-blue"
    style={{
      textAlign: 'center',
      backgroundImage: `url(${BrandBannerBackground}), ${gradient}`,
    }}
  >
    <div
      className="slds-box slds-theme_default"
      style={{ marginLeft: 'auto', marginRight: 'auto' }}
    >
      <h3 className="slds-text-heading_label slds-truncate">{message}</h3>
    </div>
    <div>
      <video
        onEnded={evt => {
          evt.target.load();
          evt.target.play();
        }}
        loop
        autoPlay
        muted
        playsInline
      >
        <source
          src="/static/images/NoNoNo.mp4"
          itemProp="contentUrl"
          type="video/mp4"
        />
      </video>
    </div>
  </BrandBand>
);

const EmptyIllustration = ({ message }: { message: React.Node }) => (
  <Illustration
    heading="Yikes! An error occurred!  :("
    messageBody={message}
    name="Broken"
    path={`${svgPath}#broken`}
    size="large"
  />
);

export default ErrorBoundary;
