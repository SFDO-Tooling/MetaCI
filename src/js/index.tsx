// @flow

import * as React from 'react';
import * as ReactDOM from 'react-dom';
import DocumentTitle from 'react-document-title';
import IconSettings from '@salesforce/design-system-react/components/icon-settings';
import logger from 'redux-logger';
import settings from '@salesforce/design-system-react/components/settings';
import thunk from 'redux-thunk';
import { BrowserRouter, Route, Switch } from 'react-router-dom';
import { Provider } from 'react-redux';
import { applyMiddleware, createStore } from 'redux';
import { composeWithDevTools } from 'redux-devtools-extension';
import i18n from 'i18next';
import actionSprite from '@salesforce-ux/design-system/assets/icons/action-sprite/svg/symbols.svg';
import customSprite from '@salesforce-ux/design-system/assets/icons/custom-sprite/svg/symbols.svg';
import doctypeSprite from '@salesforce-ux/design-system/assets/icons/doctype-sprite/svg/symbols.svg';
import standardSprite from '@salesforce-ux/design-system/assets/icons/standard-sprite/svg/symbols.svg';
import utilitySprite from '@salesforce-ux/design-system/assets/icons/utility-sprite/svg/symbols.svg';

import init_i18n from './i18n';

import ErrorBoundary from 'components/error';
import PerfPage from 'components/perfPages/perfPage';
// import TestMethodsResultsTable from 'components/perfPages/testMethodResultsTable';
import getApiFetch from 'api/api_fetch';
import reducer from 'store';
import { logError } from 'utils/logging';

const App = () => (
  <DocumentTitle title={i18n.t('Meta CI')}>
    <div
      className="slds-grid
        slds-grid_vertical"
    >
      <ErrorBoundary>
        <div
          className="slds-p-around_x-large slds-grow
            slds-shrink-none"
        >
          <ErrorBoundary>
            <Switch>
              <Route path="/repos/:owner/:repo/perf" component={PerfPage} />
              {/* <Route
                path="/repos/:owner/:repo/tests"
                component={TestMethodsResultsTable}
              /> */}
            </Switch>
          </ErrorBoundary>
        </div>
      </ErrorBoundary>
    </div>
  </DocumentTitle>
);

init_i18n(() => {
  const el = document.getElementById('app');
  if (el) {
    // Create store
    const appStore = createStore(
      reducer,
      {},
      composeWithDevTools(
        applyMiddleware(
          thunk.withExtraArgument({
            apiFetch: getApiFetch(),
          }),
          logger,
        ),
      ),
    );

    // Get JS globals
    let GLOBALS = {};
    try {
      const globalsEl = document.getElementById('js-globals');
      if (globalsEl) {
        GLOBALS = JSON.parse(globalsEl.textContent);
      }
    } catch (err) {
      logError(err);
    }
    window.GLOBALS = GLOBALS;

    // Set App element (used for react-SLDS modals)
    settings.setAppElement(el);

    ReactDOM.render(
      <Provider store={appStore}>
        <BrowserRouter>
          <IconSettings
            actionSprite={actionSprite}
            customSprite={customSprite}
            doctypeSprite={doctypeSprite}
            standardSprite={standardSprite}
            utilitySprite={utilitySprite}
          >
            <App />
          </IconSettings>
        </BrowserRouter>
      </Provider>,
      el,
    );
  }
});
