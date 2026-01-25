import { useState, useCallback } from 'react';
import { useQuery, useMutation } from '@apollo/client';
import { 
  GET_ALERT_PREFERENCES, 
  UPDATE_ALERT_PREFERENCES,
  parseAlertPreferences,
  AlertPreferences 
} from '../graphql/smartAlertsQueries';
import logger from '../utils/logger';

interface UseAlertPreferencesReturn {
  preferences: AlertPreferences | null;
  loading: boolean;
  error: string | null;
  updatePreferences: (updates: Partial<AlertPreferences>) => Promise<boolean>;
  isUpdating: boolean;
}

export const useAlertPreferences = (): UseAlertPreferencesReturn => {
  const [isUpdating, setIsUpdating] = useState(false);
  const [optimisticPreferences, setOptimisticPreferences] = useState<AlertPreferences | null>(null);

  const { data, loading, error, refetch } = useQuery(GET_ALERT_PREFERENCES, {
    fetchPolicy: 'cache-and-network',
    onCompleted: (data) => {
      const parsed = parseAlertPreferences(data.alertPreferences);
      if (parsed) {
        setOptimisticPreferences(parsed);
      }
    }
  });

  const [updatePreferencesMutation] = useMutation(UPDATE_ALERT_PREFERENCES, {
    onError: (error) => {
      logger.error('Failed to update alert preferences:', error);
      // Revert optimistic update on error
      if (data?.alertPreferences) {
        const parsed = parseAlertPreferences(data.alertPreferences);
        setOptimisticPreferences(parsed);
      }
    },
    onCompleted: (result) => {
      if (result.updateAlertPreferences?.success) {
        // Update successful, refetch to get latest data
        refetch();
      } else {
        // Revert optimistic update on failure
        if (data?.alertPreferences) {
          const parsed = parseAlertPreferences(data.alertPreferences);
          setOptimisticPreferences(parsed);
        }
      }
    }
  });

  const updatePreferences = useCallback(async (updates: Partial<AlertPreferences>): Promise<boolean> => {
    if (!optimisticPreferences) return false;

    setIsUpdating(true);

    try {
      // Optimistic update
      const newPreferences = { ...optimisticPreferences, ...updates };
      setOptimisticPreferences(newPreferences);

      // Prepare mutation input
      const input: any = {};

      if (updates.enabled_categories !== undefined) {
        input.enabled_categories = updates.enabled_categories;
      }

      if (updates.priority_threshold !== undefined) {
        input.priority_threshold = updates.priority_threshold;
      }

      if (updates.frequency !== undefined) {
        input.frequency = updates.frequency;
      }

      if (updates.delivery_method !== undefined) {
        input.delivery_method = updates.delivery_method;
      }

      if (updates.quiet_hours !== undefined) {
        input.quiet_hours = {
          enabled: updates.quiet_hours.enabled,
          start: updates.quiet_hours.start,
          end: updates.quiet_hours.end
        };
      }

      if (updates.custom_thresholds !== undefined) {
        input.custom_thresholds = {
          performance_threshold: updates.custom_thresholds.performance_threshold,
          volatility_threshold: updates.custom_thresholds.volatility_threshold,
          drawdown_threshold: updates.custom_thresholds.drawdown_threshold,
          sector_concentration_threshold: updates.custom_thresholds.sector_concentration_threshold
        };
      }

      // Execute mutation
      const result = await updatePreferencesMutation({
        variables: { input }
      });

      return result.data?.updateAlertPreferences?.success || false;

    } catch (error) {
      logger.error('Error updating preferences:', error);
      return false;
    } finally {
      setIsUpdating(false);
    }
  }, [optimisticPreferences, updatePreferencesMutation]);

  // Return optimistic preferences if available, otherwise parsed data
  const currentPreferences = optimisticPreferences || parseAlertPreferences(data?.alertPreferences);

  return {
    preferences: currentPreferences,
    loading,
    error: error?.message || null,
    updatePreferences,
    isUpdating
  };
};

// Helper hook for specific preference updates
export const useAlertThresholds = () => {
  const { preferences, updatePreferences, isUpdating } = useAlertPreferences();

  const updateThreshold = useCallback(async (
    thresholdType: keyof AlertPreferences['custom_thresholds'],
    value: number
  ) => {
    if (!preferences) return false;

    return updatePreferences({
      custom_thresholds: {
        ...preferences.custom_thresholds,
        [thresholdType]: value
      }
    });
  }, [preferences, updatePreferences]);

  const updatePerformanceThreshold = useCallback((value: number) => 
    updateThreshold('performance_threshold', value), [updateThreshold]);

  const updateVolatilityThreshold = useCallback((value: number) => 
    updateThreshold('volatility_threshold', value), [updateThreshold]);

  const updateDrawdownThreshold = useCallback((value: number) => 
    updateThreshold('drawdown_threshold', value), [updateThreshold]);

  const updateSectorConcentrationThreshold = useCallback((value: number) => 
    updateThreshold('sector_concentration_threshold', value), [updateThreshold]);

  return {
    thresholds: preferences?.custom_thresholds || null,
    updatePerformanceThreshold,
    updateVolatilityThreshold,
    updateDrawdownThreshold,
    updateSectorConcentrationThreshold,
    isUpdating
  };
};

// Helper hook for delivery preferences
export const useAlertDelivery = () => {
  const { preferences, updatePreferences, isUpdating } = useAlertPreferences();

  const updateDeliveryMethod = useCallback(async (method: AlertPreferences['delivery_method']) => {
    if (!preferences) return false;

    return updatePreferences({
      delivery_method: method
    });
  }, [preferences, updatePreferences]);

  const updateQuietHours = useCallback(async (quietHours: AlertPreferences['quiet_hours']) => {
    if (!preferences) return false;

    return updatePreferences({
      quiet_hours: quietHours
    });
  }, [preferences, updatePreferences]);

  const updateFrequency = useCallback(async (frequency: AlertPreferences['frequency']) => {
    if (!preferences) return false;

    return updatePreferences({
      frequency
    });
  }, [preferences, updatePreferences]);

  return {
    deliveryMethod: preferences?.delivery_method || 'in_app',
    quietHours: preferences?.quiet_hours || { enabled: true, start: '22:00', end: '08:00' },
    frequency: preferences?.frequency || 'daily',
    updateDeliveryMethod,
    updateQuietHours,
    updateFrequency,
    isUpdating
  };
};
