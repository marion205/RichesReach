import logger from '../utils/logger';

let navigator: any = null;
let navigatorReadyCallbacks: Array<() => void> = [];

export function setNavigator(ref: any) {
  navigator = ref;
  logger.log('✅ NavigationService: Navigator set, executing', navigatorReadyCallbacks.length, 'pending callbacks');
  // Execute any pending callbacks
  navigatorReadyCallbacks.forEach(callback => {
    try {
      callback();
    } catch (error) {
      logger.error('NavigationService: Error in ready callback', error);
    }
  });
  navigatorReadyCallbacks = [];
}

export function onNavigatorReady(callback: () => void) {
  if (navigator) {
    callback();
  } else {
    navigatorReadyCallbacks.push(callback);
  }
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
  // Wait a bit if navigator isn't ready yet (it might still be initializing)
  if (!navigator) {
    logger.warn('NavigationService: Navigator not set yet. Name:', name, '- Will queue and retry');
    // Queue the navigation to execute when navigator is ready
    onNavigatorReady(() => {
      logger.log('NavigationService: Executing queued navigation to', name);
      globalNavigate(name, params);
    });
    // Also retry after delays as fallback
    setTimeout(() => {
      if (navigator) {
        globalNavigate(name, params);
      } else {
        logger.warn('NavigationService: Navigator still not available after 100ms, will keep retrying');
        // Keep retrying with exponential backoff
        setTimeout(() => {
          if (navigator) {
            globalNavigate(name, params);
          } else {
            logger.error('NavigationService: Navigator still not available after 300ms');
          }
        }, 200);
      }
    }, 100);
    return;
  }

  if (!navigator.navigate) {
    logger.warn('NavigationService: navigator.navigate not available. Name:', name);
    return;
  }

  try {
    logger.log('NavigationService: Navigating to', name, 'with params:', params);
    
    // Handle nested navigation pattern: globalNavigate('Learn', { screen: 'tutor-module' })
    if (typeof name === 'string' && params && typeof params === 'object' && params.screen) {
      // Navigate to tab first, then to screen within that stack
      navigator.navigate(name as never, {
        screen: params.screen,
        params: params.params,
      } as never);
      logger.log('NavigationService: Nested navigation successful');
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
      logger.log('NavigationService: Object navigation successful');
    } else if (typeof name === 'string') {
      // Simple string navigation - try direct navigation first
      navigator.navigate(name as never, params as never);
      logger.log('NavigationService: Direct navigation successful to', name);
    }
  } catch (error: any) {
    // Check if it's the "navigation object hasn't been initialized" error
    const errorMessage = error?.message || String(error);
    if (errorMessage.includes("navigation' object hasn't been initialized")) {
      logger.warn('NavigationService: Navigation not ready yet, will retry:', name);
      // Retry after a short delay
      setTimeout(() => {
        if (navigator && navigator.navigate) {
          try {
            if (typeof name === 'string') {
              navigator.navigate(name as never, params as never);
            }
          } catch (retryError) {
            logger.error('NavigationService: Retry also failed', retryError);
          }
        }
      }, 200);
      return;
    }
    
    logger.error('NavigationService: Navigation error', error, { name, params });
    // Try alternative navigation method if available
    if (navigator.navigate) {
      try {
        // Fallback: try just the screen name
        if (typeof name === 'string') {
          navigator.navigate(name as never, params as never);
        }
      } catch (fallbackError) {
        logger.error('NavigationService: Fallback navigation also failed', fallbackError);
      }
    }
  }
}


