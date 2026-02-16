const { merge } = require('webpack-merge')
const singleSpaDefaults = require('webpack-config-single-spa-react-ts')
const path = require('path')

module.exports = (webpackConfigEnv, argv) => {
  const defaultConfig = singleSpaDefaults({
    orgName: 'orgst',
    projectName: 'member-card',
    webpackConfigEnv,
    argv,
  })

  return merge(defaultConfig, {
    resolve: {
      alias: {
        '@': path.resolve(__dirname, 'src'),
      },
    },
  })
}
