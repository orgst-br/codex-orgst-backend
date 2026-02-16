const { merge } = require('webpack-merge')
const singleSpaDefaults = require('webpack-config-single-spa')
const HtmlWebpackPlugin = require('html-webpack-plugin')
const path = require('path')

module.exports = (webpackConfigEnv, argv) => {
  const defaultConfig = singleSpaDefaults({
    orgName: 'orgst',
    projectName: 'root-config',
    webpackConfigEnv,
    argv,
    disableHtmlGeneration: true,
  })

  return merge(defaultConfig, {
    resolve: {
      extensions: ['.ts', '.tsx', '.js', '.jsx', '.mjs', '.json'],
    },
    module: {
      rules: [
        {
          test: /\.[jt]sx?$/,
          exclude: /node_modules/,
          use: {
            loader: 'babel-loader',
            options: {
              presets: [
                ['@babel/preset-env', { targets: { esmodules: true } }],
                '@babel/preset-typescript',
              ],
            },
          },
        },
      ],
    },
    plugins: [
      new HtmlWebpackPlugin({
        inject: false,
        template: path.resolve(__dirname, 'src/index.ejs'),
        templateParameters: {
          isLocal: webpackConfigEnv && webpackConfigEnv.isLocal,
          orgName: 'orgst',
        },
      }),
    ],
  })
}
