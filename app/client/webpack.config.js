var path = require('path')
var webpack = require('webpack')
const CopyWebpackPlugin = require('copy-webpack-plugin')
const BundleAnalyzerPlugin = require('webpack-bundle-analyzer').BundleAnalyzerPlugin;
const UglifyJsPlugin = require('uglifyjs-webpack-plugin');

module.exports = {
  mode: 'development',
  entry: {
    document: './src/document.js',
    documentIndex: './src/documentIndex.js'
  },
  output: {
    path: path.resolve(__dirname, '../static/js'),
    publicPath: '/lettres/static/js/',
    filename: '[name].build.js'
  },
  module: {
    rules: [
      {
        test: /\.css$/,
        use: [
          'vue-style-loader',
          'css-loader'
        ],
      },
      {
        test: /\.scss$/,
        loaders: ['style-loader', 'css-loader', 'sass-loader']
      },
      {
        test: /\.vue$/,
        loader: 'vue-loader',
        options: {
          loaders: {
          }
          // other vue-loader options go here
        }
      },
      {
        test: /\.js$/,
        loader: 'babel-loader'
      },
      {
        test: /\.ts$/,
        loader: 'ts-loader',
        options: {
          compilerOptions: {
            //declaration: false,
            target: 'es5',
            module: 'commonjs'
          },
          transpileOnly: true
        }
      },
      {
        test: /\.(png|jpg|gif)$/,
        loader: 'file-loader',
        options: {
          name: '[name].[ext]?[hash]'
        }
      },
      {
        test: /\.svg$/,
        loader: 'svg-inline-loader'
      }
    ]
  },
  resolve: {
    alias: {
      'vue$': 'vue/dist/vue.esm.js',
      'parchment': path.resolve(__dirname, 'node_modules/parchment/src/parchment.ts'),
      'quill$': path.resolve(__dirname, 'node_modules/quill/quill.js'),
    },
    extensions: ['*', '.js', '.vue', '.json', '.ts']
  },
  devServer: {
    index: './index.htm',
    contentBase: path.join(__dirname, '..'),
    historyApiFallback: true,
    noInfo: true,
    overlay: true,
    proxy: {
      '/lettres': {
        target: 'http://localhost:5004',
        publicPath: '/lettres/static/js/',
        changeOrigin: true
  }
}
  },
  performance: {
    hints: false
  },
  devtool: '#eval-source-map',
    optimization: {
    minimizer: [
      // we specify a custom UglifyJsPlugin here to get source maps in production
      new UglifyJsPlugin({
        cache: true,
        parallel: true,
        uglifyOptions: {
          compress: false,
          ecma: 6,
          mangle: true
        },
        sourceMap: true
      })
    ]
  }
}

if (process.env.NODE_ENV === 'production') {
  module.exports.mode = 'production';
  module.exports.devtool = '#source-map';
  // http://vue-loader.vuejs.org/en/workflow/production.html
  module.exports.plugins = (module.exports.plugins || []).concat([
    new webpack.DefinePlugin({
      'process.env': {
        NODE_ENV: '"production"'
      }
    }),
    new webpack.LoaderOptionsPlugin({
      minimize: true
    }),
    new BundleAnalyzerPlugin({
      analyzerMode: 'static',
      openAnalyzer: false
    })
  ])
}