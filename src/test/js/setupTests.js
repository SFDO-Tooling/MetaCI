import 'isomorphic-fetch';
import '@testing-library/jest-dom/extend-expect';

import fetchMock from 'fetch-mock';

beforeAll(() => {
  window.api_urls = {
    account_logout: () => '/accounts/logout/',
    salesforce_production_login: () => '/accounts/salesforce-production/login/',
    salesforce_test_login: () => '/accounts/salesforce-test/login/',
    salesforce_custom_login: () => '/accounts/salesforce-custom/login/',
    product_list: () => '/api/products/',
    version_list: () => '/api/versions/',
    plan_preflight: (id) => `/api/plans/${id}/preflight/`,
    job_list: () => '/api/jobs/',
    job_detail: (id) => `/api/jobs/${id}/`,
    org_list: () => '/api/org/',
    user: () => '/api/user/',
  };
  window.GLOBALS = {};
  window.SITE_NAME = 'MetaDeploy';
  window.console.error = jest.fn();
  window.console.warn = jest.fn();
  window.console.info = jest.fn();
});

afterEach(() => fetchMock.reset());
