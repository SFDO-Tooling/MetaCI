// @flow

import * as React from 'react';
import Avatar from '@salesforce/design-system-react/components/avatar';
import Button from '@salesforce/design-system-react/components/button';
import Dropdown from '@salesforce/design-system-react/components/menu-dropdown';
import DropdownTrigger from '@salesforce/design-system-react/components/menu-dropdown/button-trigger';
import { t } from 'i18next';

import type { User } from 'store/user/reducer';
import typeof { logout as LogoutType } from 'store/user/actions';

const Logout = ({
  user,
  doLogout,
}: {
  user: User,
  doLogout: LogoutType,
}): React.Node => (
  <Dropdown
    id="logout"
    options={[
      {
        label: user && user.username,
        type: 'header',
      },
      { type: 'divider' },
      {
        label: t('Log Out'),
        leftIcon: {
          name: 'logout',
          category: 'utility',
        },
      },
    ]}
    onSelect={doLogout}
    menuPosition="relative"
    nubbinPosition="top right"
  >
    <DropdownTrigger>
      <Button variant="icon">
        <Avatar />
      </Button>
    </DropdownTrigger>
  </Dropdown>
);

export default Logout;
