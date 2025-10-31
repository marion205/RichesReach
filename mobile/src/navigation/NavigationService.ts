let navigator: any = null;

export function setNavigator(ref: any) {
  navigator = ref;
}

export function navigate(name: string, params?: any) {
  if (navigator && navigator.navigate) {
    navigator.navigate(name as never, params as never);
  }
}

/**
 * Global navigate function that handles nested navigation
 * Supports patterns like 'Learn', { screen: 'tutor-module' }
 */
export function globalNavigate(name: string | any, params?: any) {
  if (!navigator) {
    console.warn('NavigationService: Navigator not set. Name:', name);
    return;
  }

  if (!navigator.navigate) {
    console.warn('NavigationService: navigator.navigate not available. Name:', name);
    return;
  }

  try {
    console.log('NavigationService: Navigating to', name, 'with params:', params);
    
    // Handle nested navigation pattern: globalNavigate('Learn', { screen: 'tutor-module' })
    if (typeof name === 'string' && params && typeof params === 'object' && params.screen) {
      // Navigate to tab first, then to screen within that stack
      navigator.navigate(name as never, {
        screen: params.screen,
        params: params.params,
      } as never);
      console.log('NavigationService: Nested navigation successful');
    } 
    // Handle object-based navigation: globalNavigate({ screen: 'tutor-module', tab: 'Learn' })
    else if (typeof name === 'object' && name.screen) {
      const tabName = name.tab || name.name;
      const screenName = name.screen;
      
      if (tabName) {
        navigator.navigate(tabName as never, {
          screen: screenName,
          params: params || name.params,
        } as never);
      } else {
        // Direct screen navigation
        navigator.navigate(screenName as never, params || name.params as never);
      }
      console.log('NavigationService: Object navigation successful');
    } else if (typeof name === 'string') {
      // Simple string navigation - try direct navigation first
      navigator.navigate(name as never, params as never);
      console.log('NavigationService: Direct navigation successful to', name);
    }
  } catch (error) {
    console.error('NavigationService: Navigation error', error, { name, params });
    // Try alternative navigation method if available
    if (navigator.navigate) {
      try {
        // Fallback: try just the screen name
        if (typeof name === 'string') {
          navigator.navigate(name as never, params as never);
        }
      } catch (fallbackError) {
        console.error('NavigationService: Fallback navigation also failed', fallbackError);
      }
    }
  }
}


