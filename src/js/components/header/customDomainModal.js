// @flow

import * as React from 'react';
import Button from '@salesforce/design-system-react/components/button';
import Input from '@salesforce/design-system-react/components/input';
import Modal from '@salesforce/design-system-react/components/modal';
import { t } from 'i18next';

import { addUrlParams } from 'utils/api';

type Props = {
  isOpen: boolean,
  toggleModal: boolean => void,
};

class CustomDomainModal extends React.Component<Props, { url: string }> {
  constructor(props: Props) {
    super(props);
    this.state = { url: '' };
  }

  handleClose = () => {
    this.props.toggleModal(false);
    this.setState({ url: '' });
  };

  handleSubmit = (event: SyntheticEvent<HTMLFormElement>) => {
    event.preventDefault();
    const val = this.state.url.trim();
    if (!val) {
      return;
    }
    const baseUrl = window.api_urls.salesforce_custom_login();
    window.location.assign(
      addUrlParams(baseUrl, {
        custom_domain: val,
        next: window.location.pathname,
      }),
    );
  };

  handleChange = (event: SyntheticInputEvent<HTMLInputElement>) => {
    this.setState({ url: event.target.value });
  };

  render(): React.Node {
    const footer = [
      <Button key="cancel" label={t('Cancel')} onClick={this.handleClose} />,
      <Button
        key="submit"
        label={t('Continue')}
        variant="brand"
        onClick={this.handleSubmit}
      />,
    ];
    return (
      <Modal
        isOpen={this.props.isOpen}
        title={t('Use Custom Domain')}
        onRequestClose={this.handleClose}
        footer={footer}
      >
        <form className="slds-p-around_large" onSubmit={this.handleSubmit}>
          <div
            className="slds-form-element__help
              slds-p-bottom_small"
          >
            {t(
              'To go to your company’s login page, enter the custom domain name.',
            )}
          </div>
          <Input
            id="login-custom-domain"
            label={t('Custom Domain')}
            value={this.state.url}
            onChange={this.handleChange}
            aria-describedby="login-custom-domain-help"
          >
            <div
              id="login-custom-domain-help"
              className="slds-form-element__help
                slds-truncate
                slds-p-top_small"
              data-testid="custom-domain"
            >
              https://
              {this.state.url.trim() ? this.state.url.trim() : <em>domain</em>}
              .my.salesforce.com
            </div>
          </Input>
        </form>
      </Modal>
    );
  }
}

export default CustomDomainModal;
