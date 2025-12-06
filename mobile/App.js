// This file re-exports the main App component from src/App.tsx
// This ensures Expo's AppEntry.js can find the App component when it imports ../../App
// Metro bundler should resolve .tsx files, but this .js file provides a fallback

import App from './src/App';
export default App;

