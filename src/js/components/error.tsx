import BrandBand from '@salesforce/design-system-react/components/brand-band';
import BrandBannerBackground from '@salesforce-ux/design-system/assets/images/themes/oneSalesforce/banner-brand-default.png';
import get from 'lodash/get';
import React, { Component, ReactNode } from 'react';
import { Trans } from 'react-i18next';
import { logError } from 'utils/logging';

import brokenSvg from '!raw-loader!~img/broken.svg';

export const EmptyIllustration = ({ message }: { message: ReactNode }) => (
  <div className="slds-illustration slds-illustration_large">
    <div
      className="slds-m-vertical_xx-large"
      dangerouslySetInnerHTML={{ __html: brokenSvg }}
    />
    <h3 className="slds-illustration__header slds-text-heading_medium">
      ¯\_(ツ)_/¯
    </h3>
    <p className="slds-text-body_regular">{message}</p>
  </div>
);

interface Props {
  children: ReactNode;
}

class ErrorBoundary extends Component<
  Props,
  { hasError: boolean; error?: any; info?: any }
> {
  public constructor(props: Props) {
    super(props);
    this.state = { hasError: false };
  }

  /* istanbul ignore next */
  public componentDidCatch(error: Error, info: { [key: string]: any }) {
    this.setState({ hasError: true, error, info });
    logError(error, info);
  }

  public render() {
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
        onEnded={(evt) => {
          const medialement = evt.target as HTMLMediaElement;
          medialement.load();
          medialement.play();
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

export default ErrorBoundary;
