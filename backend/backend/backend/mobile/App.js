// Import URL polyfill first to fix React Native URL.protocol issues
import 'react-native-url-polyfill/auto';

import { AppRegistry } from 'react-native';
import App from './src/App';

// Register the main component with the correct app name
AppRegistry.registerComponent('richesreach-ai', () => App);
