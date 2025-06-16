/**
 * @format
 */

// Import URL polyfill for React Native/Hermes compatibility
import 'react-native-url-polyfill/auto';

// Initialize deep link handler
import './src/utils/initializeApp';

import {AppRegistry} from 'react-native';
import App from './App';
import {name as appName} from './app.json';

AppRegistry.registerComponent(appName, () => App);
