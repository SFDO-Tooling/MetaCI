// @flow

import * as React from 'react';
import PageHeader from '@salesforce/design-system-react/components/page-header';
import { Link } from 'react-router-dom';
import { connect } from 'react-redux';
import { t } from 'i18next';

import routes from 'utils/routes';
import { logout } from 'store/user/actions';
import { selectUserState } from 'store/user/selectors';
import type { AppState } from 'store';
import type { User } from 'store/user/reducer';

type Props = {
  user: User,
  doLogout: typeof logout,
};

const Header = ({ user, doLogout }: Props) => (
  <>
    <PageHeader
      className="global-header
        slds-p-horizontal_x-large
        slds-p-vertical_medium"
      title={
        <Link
          to={routes.home()}
          className="slds-page-header__title
            slds-text-heading_large
            slds-text-link_reset"
        >
          <span>{t('Meta CI')}</span>
        </Link>
      }

      variant="objectHome"
    />
  </>
);

const select = (appState: AppState) => ({
  user: selectUserState(appState),
});

const actions = {
  doLogout: logout,
};

const WrappedHeader: React.ComponentType<{}> = connect(
  select,
  actions,
)(Header);

export default WrappedHeader;
