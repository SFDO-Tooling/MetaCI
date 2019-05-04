/* eslint-disable react/display-name */
/* eslint-env jest */

// From: https://github.com/i18next/react-i18next/blob/master/example/v9.x.x/test-jest/__mocks__/react-i18next.js
// https://github.com/i18next/react-i18next/issues/465

'use strict';

const React = require('react');
const reactI18next = require('react-i18next');

const hasChildren = node =>
  node && (node.children || (node.props && node.props.children));

const getChildren = node =>
  node && node.children ? node.children : node.props && node.props.children;

const renderNodes = reactNodes => {
  if (typeof reactNodes === 'string') {
    return reactNodes;
  }

  return Object.keys(reactNodes).map((key, i) => {
    const child = reactNodes[key];
    const isElement = React.isValidElement(child);

    if (typeof child === 'string') {
      return child;
    }
    if (hasChildren(child)) {
      const inner = renderNodes(getChildren(child));
      return React.cloneElement(child, { ...child.props, key: i }, inner);
    } else if (typeof child === 'object' && !isElement) {
      return Object.keys(child).reduce(
        (str, childKey) => `${str}${child[childKey]}`,
        '',
      );
    }

    return child;
  });
};

const i18n = jest.genMockFromModule('react-i18next');

module.exports = {
  ...i18n,
  // this mock makes sure any components using the translate HoC receive the t function as a prop
  withNamespaces: jest.fn(() => Component => props => (
    <Component t={k => k} {...props} />
  )),
  Trans: jest.fn(({ children }) => renderNodes(children)),
  NamespacesConsumer: jest.fn(({ children }) => children(k => k, { i18n: {} })),

  // mock if needed
  Interpolate: reactI18next.Interpolate,
  I18nextProvider: reactI18next.I18nextProvider,
  loadNamespaces: reactI18next.loadNamespaces,
  initReactI18next: reactI18next.initReactI18next,
  setDefaults: reactI18next.setDefaults,
  getDefaults: reactI18next.getDefaults,
  setI18n: reactI18next.setI18n,
  getI18n: reactI18next.getI18n,
};
