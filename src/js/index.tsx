import IconSettings from '@salesforce/design-system-react/components/icon-settings';
import settings from '@salesforce/design-system-react/components/settings';
import actionSprite from '@salesforce-ux/design-system/assets/icons/action-sprite/svg/symbols.svg';
import customSprite from '@salesforce-ux/design-system/assets/icons/custom-sprite/svg/symbols.svg';
import doctypeSprite from '@salesforce-ux/design-system/assets/icons/doctype-sprite/svg/symbols.svg';
import standardSprite from '@salesforce-ux/design-system/assets/icons/standard-sprite/svg/symbols.svg';
import utilitySprite from '@salesforce-ux/design-system/assets/icons/utility-sprite/svg/symbols.svg';
// import TestMethodsResultsTable from 'components/perfPages/testMethodResultsTable';
import getApiFetch from 'api/api_fetch';
import ErrorBoundary from 'components/error';
import PerfPage from 'components/perfPages/perfPage';
import i18next from 'i18next';
import * as React from 'react';
import DocumentTitle from 'react-document-title';
import * as ReactDOM from 'react-dom';
import { Provider } from 'react-redux';
import { BrowserRouter, Route, Switch } from 'react-router-dom';
import { applyMiddleware, createStore } from 'redux';
import { composeWithDevTools } from 'redux-devtools-extension';
import { logger } from 'redux-logger';
import thunk from 'redux-thunk';
import reducer from 'store';
import { logError } from 'utils/logging';

import init_i18n from './i18n';

const App = () => (
  <DocumentTitle title={i18next.t('Meta CI')}>
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
