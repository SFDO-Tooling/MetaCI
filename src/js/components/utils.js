// @flow

import * as React from 'react';
import type { Match, RouterHistory } from 'react-router-dom';

export type InitialProps = {| match: Match, history: RouterHistory |};

type TransientMessageState = {
  transientMessageVisible: boolean,
};
export type TransientMessageProps = {|
  transientMessageVisible?: boolean,
  showTransientMessage?: () => void,
  hideTransientMessage?: () => void,
|};

export const withTransientMessage = function<
  Props: {},
  Component: React.ComponentType<Props>,
>(
  WrappedComponent: Component,
  options?: {| duration?: number |},
): Class<
  React.Component<$Diff<Props, TransientMessageProps>, TransientMessageState>,
> {
  const defaults = {
    duration: 5 * 1000,
  };
  const opts = { ...defaults, ...options };

  return class WithTransientMessage extends React.Component<
    Props,
    TransientMessageState,
  > {
    timeout: ?TimeoutID;

    constructor(props: Props) {
      super(props);
      this.state = { transientMessageVisible: false };
      this.timeout = null;
    }

    componentWillUnmount() {
      this.clearTimeout();
    }

    clearTimeout() {
      if (this.timeout !== undefined && this.timeout !== null) {
        clearTimeout(this.timeout);
        this.timeout = null;
      }
    }

    showTransientMessage = () => {
      this.setState({ transientMessageVisible: true });
      this.clearTimeout();
      this.timeout = setTimeout(() => {
        this.hideTransientMessage();
      }, opts.duration);
    };

    hideTransientMessage = () => {
      this.setState({ transientMessageVisible: false });
      this.clearTimeout();
    };

    render(): React.Node {
      return (
        <WrappedComponent
          {...this.props}
          transientMessageVisible={this.state.transientMessageVisible}
          showTransientMessage={this.showTransientMessage}
          hideTransientMessage={this.hideTransientMessage}
        />
      );
    }
  };
};
