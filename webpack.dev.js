/* eslint-disable no-process-env */

'use strict';

process.env.NODE_ENV = 'development';

const fs = require('fs');
const path = require('path');

const { CleanWebpackPlugin } = require('clean-webpack-plugin');
const I18nextWebpackPlugin = require('i18next-scanner-webpack');
const MiniCssExtractPlugin = require('mini-css-extract-plugin');
const merge = require('webpack-merge');

const common = require('./webpack.common.js');

const babel = require('@babel/core');

module.exports = merge(common, {
  mode: 'development',
  output: {
    filename: '[name].js',
    path: path.join(__dirname, 'dist'),
  },
  resolve: {
    extensions: ['.tsx', '.ts', '.js'],
  },
  devtool: 'cheap-module-inline-source-map',
  devServer: {
    index: '',
    proxy: {
      '**': 'http://localhost:8000',
      '/ws': {
        target: 'http://localhost:8000',
        ws: true,
      },
    },
    hot: false,
    writeToDisk: true,
    port: 4088,
  },
  plugins: [
    new CleanWebpackPlugin(),
    new MiniCssExtractPlugin({
      filename: '[name].css',
    }),
    // Parse for translatable text strings
    new I18nextWebpackPlugin({
      src: ['./src/js/'],
      options: {
        sort: true,
        attr: false,
        func: {
          list: ['t', 'i18next.t', 'i18n.t', 'translate'],
          extensions: ['.js'],
        },
        nsSeparator: false,
        keySeparator: false,
        lngs: ['en'],
        // See custom transform below for <Trans> components
        trans: {
          extensions: [],
        },
        resource: {
          savePath: '../locales_dev/{{lng}}/{{ns}}.json',
        },
        defaultValue(lng, ns, key) {
          if (lng === 'en') {
            // Return key as the default value for English language
            return key;
          }
          // Return the string '__NOT_TRANSLATED__' for other languages
          return '__NOT_TRANSLATED__';
        },
      },
      // Custom transform to allow parsing Js with Flow types
      // https://github.com/i18next/i18next-scanner/issues/88
      transform(file, enc, done) {
        const extname = path.extname(file.path);
        if (['.js', '.jsx', '.ts', '.tsx'].includes(extname)) {
          const parser = this.parser;
          fs.readFile(file.path, enc, (err, data) => {
            if (err) {
              done(err);
            } else {
              const options = {
                filename: file.path,
                presets: ['@babel/preset-typescript'],
                plugins: [
                  '@babel/plugin-syntax-jsx',
                  '@babel/plugin-proposal-class-properties',
                  '@babel/plugin-proposal-object-rest-spread',
                ],
                configFile: false,
              };

              const code = babel.transform(data, options).code;

              parser.parseTransFromString(code);
              done();
            }
          });
        } else {
          done();
        }
      },
    }),
  ],
});
