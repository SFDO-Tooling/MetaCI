'use strict';

const presets = ['@babel/preset-react', '@babel/preset-flow'];

module.exports = {
  presets: [
    ...presets,
    [
      '@babel/preset-env',
      {
        modules: false,
        useBuiltIns: 'usage',
        exclude: ['transform-regenerator'],
      },
    ],
  ],
  plugins: [
    '@babel/plugin-proposal-class-properties',
    '@babel/plugin-proposal-object-rest-spread',
  ],
  env: {
    test: {
      presets: [...presets, '@babel/preset-env'],
    },
  },
};
