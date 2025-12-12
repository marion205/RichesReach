/**
 * useServiceInitialization Hook
 * Handles initialization of app services (push notifications, price alerts, dawn ritual scheduler)
 * Extracted from App.tsx to improve testability and separation of concerns
 */

import { useEffect, useState } from 'react';
import logger from '../utils/logger';
import expoGoCompatibleNotificationService from '../features/notifications/services/ExpoGoCompatibleNotificationService';
import expoGoCompatiblePriceAlertService from '../features/stocks/services/ExpoGoCompatiblePriceAlertService';

interface UseServiceInitializationResult {
  isLoading: boolean;
}

/**
 * Hook to initialize app services
 * Services are initialized in the background (non-blocking)
 */
export function useServiceInitialization(): UseServiceInitializationResult {
  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    const initializeServices = async () => {
      // Skip blocking initialization for demo
      setIsLoading(false);
      try {
        // Authentication state is now handled by AuthContext
        // No need to check JWT service here

        // Initialize Version 2 services in background
        // Note: OfflineInsightsService status is available via the service if needed

        // Initialize push notifications in background (non-blocking)
        if (expoGoCompatibleNotificationService) {
          expoGoCompatibleNotificationService.initialize().catch(() => {
            // Silently fail - service will retry on next app open
          });
        }

        // Initialize price alert service in background (non-blocking)
        if (expoGoCompatiblePriceAlertService) {
          expoGoCompatiblePriceAlertService.initialize().catch(() => {
            // Silently fail - service will retry on next app open
          });
        }

        // Note: RAHA Notification Service is initialized in NotificationPreferencesScreen
        // when the user opens that screen (requires Apollo Client mutation)

        // Initialize Dawn Ritual scheduler
        const { dawnRitualScheduler } = await import(
          '../features/rituals/services/DawnRitualScheduler'
        );
        const preferences = await dawnRitualScheduler.getPreferences();
        if (preferences.enabled) {
          await dawnRitualScheduler.scheduleDailyRitual(preferences);
        }
      } catch (error) {
        logger.error('Error initializing services:', error);
      } finally {
        setIsLoading(false);
      }
    };

    initializeServices();
  }, []);

  return { isLoading };
}
