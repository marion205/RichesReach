// Import Reanimated first (required for worklets)
import 'react-native-reanimated';

// Import gesture handler (required for react-native-tab-view)
import 'react-native-gesture-handler';

// Import URL polyfill first to fix React Native URL.protocol issues
import 'react-native-url-polyfill/auto';

import { AppRegistry } from 'react-native';
import App from './src/App';

// Register the main component
AppRegistry.registerComponent('main', () => App);
