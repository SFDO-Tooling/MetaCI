// @flow

import * as React from 'react';
import Dropdown from '@salesforce/design-system-react/components/menu-dropdown';
import { t } from 'i18next';

import { addUrlParams } from 'utils/api';
import { logError } from 'utils/logging';
import CustomDomainModal from 'components/header/customDomainModal';

type Props = {
  id: string,
  label?: string | React.Node,
  buttonClassName: string,
  buttonVariant: string,
  triggerClassName?: string,
  disabled: boolean,
  menuPosition: string,
  nubbinPosition: string,
};
type MenuOption =
  | {|
      label: string,
      href?: string,
      disabled: boolean,
      modal?: boolean,
    |}
  | {| type: string |};

class Login extends React.Component<Props, { modalOpen: boolean }> {
  static defaultProps = {
    id: 'login',
    buttonClassName: 'slds-button_outline-brand',
    buttonVariant: 'base',
    disabled: false,
    menuPosition: 'overflowBoundaryElement',
    nubbinPosition: 'top right',
  };

  constructor(props: Props) {
    super(props);
    this.state = { modalOpen: false };
    if (!window.api_urls.salesforce_production_login) {
      logError('Login URL not found for salesforce_production provider.');
    }
    if (!window.api_urls.salesforce_test_login) {
      logError('Login URL not found for salesforce_test provider.');
    }
    if (!window.api_urls.salesforce_custom_login) {
      logError('Login URL not found for salesforce_custom provider.');
    }
  }

  toggleModal = (isOpen: boolean) => {
    this.setState({ modalOpen: isOpen });
  };

  handleSelect = (opt: MenuOption) => {
    if (opt.modal) {
      this.toggleModal(true);
      return;
    }
    if (opt.href) {
      window.location.assign(
        addUrlParams(opt.href, { next: window.location.pathname }),
      );
    }
  };

  static getMenuOpts(): Array<MenuOption> {
    return [
      {
        label: t('Production or Developer Org'),
        href:
          window.api_urls.salesforce_production_login &&
          window.api_urls.salesforce_production_login(),
        disabled: !window.api_urls.salesforce_production_login,
      },
      {
        label: t('Sandbox or Scratch Org'),
        href:
          window.api_urls.salesforce_test_login &&
          window.api_urls.salesforce_test_login(),
        disabled: !window.api_urls.salesforce_test_login,
      },
      {
        type: 'divider',
      },
      {
        label: t('Use Custom Domain'),
        modal: Boolean(window.api_urls.salesforce_custom_login),
        disabled: !window.api_urls.salesforce_custom_login,
      },
    ];
  }

  render(): React.Node {
    const menuOpts = Login.getMenuOpts();
    const {
      id,
      label,
      triggerClassName,
      buttonClassName,
      buttonVariant,
      disabled,
      menuPosition,
      nubbinPosition,
    } = this.props;
    const { modalOpen } = this.state;

    return (
      <>
        <Dropdown
          id={id}
          label={label === undefined ? t('Log In') : label}
          className="slds-dropdown_actions
            slds-dropdown_medium"
          triggerClassName={triggerClassName}
          buttonClassName={buttonClassName}
          buttonVariant={buttonVariant}
          disabled={disabled}
          menuPosition={menuPosition}
          nubbinPosition={nubbinPosition}
          iconCategory="utility"
          iconName="down"
          iconPosition="right"
          options={menuOpts}
          onSelect={this.handleSelect}
        />
        <CustomDomainModal isOpen={modalOpen} toggleModal={this.toggleModal} />
      </>
    );
  }
}

export default Login;
