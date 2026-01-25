/**
 * Navigation Utility
 * Provides safe navigation helpers to avoid navigation errors
 */

/**
 * Safely navigate to a screen with fallback options
 */
export const safeNavigate = (
  screen: string,
  navigateTo?: (screen: string, params?: any) => void,
  navigation?: any
): void => {
  if (navigateTo) {
    navigateTo(screen);
  } else if (navigation?.canGoBack?.()) {
    navigation.goBack();
  } else if (navigation?.navigate) {
    navigation.navigate(screen as never);
  }
};

/**
 * Navigate back safely
 */
export const safeGoBack = (
  navigateTo?: (screen: string, params?: any) => void,
  navigation?: any,
  fallbackScreen: string = 'home'
): void => {
  if (navigation?.canGoBack?.()) {
    navigation.goBack();
  } else if (navigateTo) {
    navigateTo(fallbackScreen);
  } else if (navigation?.navigate) {
    navigation.navigate(fallbackScreen as never);
  }
};

