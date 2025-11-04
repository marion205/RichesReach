/**
 * Chart Test Screen - Isolated testing environment for chart features
 * Access via navigation: navigateTo('chart-test')
 * Safe to test without affecting main app
 */
import React, { useState, useEffect } from 'react';
import { View, Text, StyleSheet, TouchableOpacity, Alert, ActivityIndicator, InteractionManager } from 'react-native';
import { ScrollView } from 'react-native-gesture-handler';
import { SafeAreaView } from 'react-native-safe-area-context';
import InnovativeChart from './InnovativeChart';

// Sample data for testing - with clear regime patterns
const generateSampleData = (days: number = 30) => {
  const now = Date.now();
  const dayMs = 24 * 60 * 60 * 1000;
  const series = [];
  let price = 100;
  
  // Create distinct regime patterns for testing:
  // Days 0-10: TREND UP (steady upward movement, low volatility)
  // Days 10-20: CHOP (sideways, small movements, low volatility)
  // Days 20-25: SHOCK (high volatility, large swings)
  // Days 25-30: TREND DOWN (steady downward, low volatility)
  
  for (let i = 0; i < days; i++) {
    const t = now - (days - i) * dayMs;
    
    if (i < 10) {
      // TREND UP: Steady upward movement
      price += 1.2 + (Math.random() - 0.5) * 0.3; // Low volatility, upward
    } else if (i < 20) {
      // CHOP: Sideways, small movements
      price += (Math.random() - 0.5) * 0.4; // Very low volatility, no direction
    } else if (i < 25) {
      // SHOCK: High volatility
      price += (Math.random() - 0.5) * 6; // High volatility, large swings
    } else {
      // TREND DOWN: Steady downward movement
      price -= 1.2 + (Math.random() - 0.5) * 0.3; // Low volatility, downward
    }
    
    // Ensure price stays reasonable
    price = Math.max(50, Math.min(200, price));
    
    series.push({
      t: new Date(t),
      price: Math.round(price * 100) / 100,
    });
  }
  
  return series;
};

const generateEvents = () => {
  const now = Date.now();
  return [
    {
      t: new Date(now - 15 * 24 * 60 * 60 * 1000),
      title: 'Earnings Release',
      summary: 'Q3 results exceeded expectations',
      color: '#3B82F6',
    },
    {
      t: new Date(now - 5 * 24 * 60 * 60 * 1000),
      title: 'Fed Decision',
      summary: 'Interest rates maintained',
      color: '#EF4444',
    },
  ];
};

const generateDrivers = () => {
  const now = Date.now();
  return [
    {
      t: new Date(now - 10 * 24 * 60 * 60 * 1000),
      driver: 'news' as const,
      cause: 'Positive earnings forecast',
      relevancy: 85,
    },
    {
      t: new Date(now - 8 * 24 * 60 * 60 * 1000),
      driver: 'macro' as const,
      cause: 'GDP growth exceeded expectations',
      relevancy: 70,
    },
    {
      t: new Date(now - 3 * 24 * 60 * 60 * 1000),
      driver: 'flow' as const,
      cause: 'Institutional buying surge',
      relevancy: 90,
    },
  ];
};

export default function ChartTestScreen({ navigation, route }: { navigation?: any; route?: any; onClose?: () => void }) {
  const [dataDays, setDataDays] = useState(30);
  const [chartReady, setChartReady] = useState(false);
  const [chartEnabled, setChartEnabled] = useState(false); // User must explicitly enable
  const [chartData, setChartData] = useState({
    series: generateSampleData(30),
    events: generateEvents(),
    drivers: generateDrivers(),
    costBasis: 105,
    benchmarkData: generateSampleData(30).map((p, i) => ({
      t: p.t,
      price: p.price * 0.98 + Math.random() * 2,
    })),
  });

  useEffect(() => {
    // Only set chartReady if user explicitly enabled it
    if (chartEnabled) {
      // Delay chart mounting to prevent freeze
      const timer = setTimeout(() => {
        setChartReady(true);
      }, 2000); // Increased delay to 2 seconds
      return () => clearTimeout(timer);
    }
  }, [chartEnabled]);

  const regenerateData = (days: number) => {
    setDataDays(days);
    setChartData({
      series: generateSampleData(days),
      events: generateEvents(),
      drivers: generateDrivers(),
      costBasis: 105,
      benchmarkData: generateSampleData(days).map((p, i) => ({
        t: p.t,
        price: p.price * 0.98 + Math.random() * 2,
      })),
    });
  };

  return (
    <SafeAreaView style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.title}>Chart Test Screen</Text>
        <TouchableOpacity 
          onPress={() => {
            if (navigation?.goBack) {
              navigation.goBack();
            } else if (onClose) {
              onClose();
            }
          }} 
          style={styles.closeButton}
        >
          <Text style={styles.closeText}>Close</Text>
        </TouchableOpacity>
      </View>

      <ScrollView 
        style={styles.content}
        scrollEnabled={true}
        nestedScrollEnabled={true}
        // GestureHandler ScrollView allows simultaneous gestures by default
      >
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Test Controls</Text>
          <View style={styles.buttonRow}>
            <TouchableOpacity
              style={[styles.button, dataDays === 7 && styles.buttonActive]}
              onPress={() => regenerateData(7)}
            >
              <Text style={styles.buttonText}>7 Days</Text>
            </TouchableOpacity>
            <TouchableOpacity
              style={[styles.button, dataDays === 30 && styles.buttonActive]}
              onPress={() => regenerateData(30)}
            >
              <Text style={styles.buttonText}>30 Days</Text>
            </TouchableOpacity>
            <TouchableOpacity
              style={[styles.button, dataDays === 90 && styles.buttonActive]}
              onPress={() => regenerateData(90)}
            >
              <Text style={styles.buttonText}>90 Days</Text>
            </TouchableOpacity>
          </View>
        </View>

        <View style={styles.chartSection}>
          <Text style={styles.sectionTitle}>Chart Preview</Text>
          {!chartEnabled ? (
            <View style={styles.enableContainer}>
              <Text style={styles.enableText}>⚠️ Chart Disabled by Default</Text>
              <Text style={styles.enableSubtext}>
                The Skia chart component can freeze the app.{'\n'}
                Click below to enable it at your own risk.
              </Text>
              <TouchableOpacity
                style={styles.enableButton}
                onPress={() => {
                  Alert.alert(
                    'Enable Chart?',
                    'This may freeze the app. Are you sure?',
                    [
                      { text: 'Cancel', style: 'cancel' },
                      { 
                        text: 'Enable', 
                        style: 'destructive',
                        onPress: () => setChartEnabled(true)
                      },
                    ]
                  );
                }}
              >
                <Text style={styles.enableButtonText}>Enable Chart (Risky)</Text>
              </TouchableOpacity>
            </View>
          ) : !chartReady ? (
            <View style={styles.loadingContainer}>
              <ActivityIndicator size="large" color="#0F62FE" />
              <Text style={styles.loadingText}>Loading chart...</Text>
              <Text style={styles.loadingSubtext}>Delayed 2s to prevent freeze</Text>
            </View>
          ) : (
            <View style={styles.chartContainer} testID="chart-container">
              <InnovativeChart
                series={chartData.series}
                events={chartData.events}
                drivers={chartData.drivers}
                costBasis={chartData.costBasis}
                benchmarkData={chartData.benchmarkData}
                showMoneyView={false}
                height={300}
                margin={16}
              />
            </View>
          )}
        </View>

        <View style={styles.featuresSection}>
          <Text style={styles.sectionTitle}>Features to Test</Text>
          <View style={styles.featureList}>
            <Text style={styles.featureItem}>✅ Regime Bands (trend/chop/shock)</Text>
            <Text style={styles.featureSubtext}>
              • Green bands = TREND (directional movement){'\n'}
              • Yellow bands = CHOP (sideways, low volatility){'\n'}
              • Red bands = SHOCK (high volatility){'\n'}
              • Test data includes all three regimes
            </Text>
            <Text style={styles.featureItem}>✅ Confidence Glass (80%/50%)</Text>
            <Text style={styles.featureItem}>✅ Event Markers (blue/red dots)</Text>
            <Text style={styles.featureItem}>✅ Driver Lines (colored vertical)</Text>
            <Text style={styles.featureItem}>✅ Pinch to Zoom</Text>
            <Text style={styles.featureSubtext}>
              • iOS Simulator: Hold Option (⌥) + drag{'\n'}
              • Android Emulator: Extended Controls → Fingerprint{'\n'}
              • Physical device: Use two fingers
            </Text>
            <Text style={styles.featureItem}>✅ Pan/Scroll</Text>
            <Text style={styles.featureItem}>✅ Tap Events for details</Text>
            <Text style={styles.featureItem}>✅ Tap Drivers for explanations</Text>
          </View>
        </View>

        <View style={styles.warningSection}>
          <Text style={styles.warningTitle}>⚠️ Testing Notes</Text>
          <Text style={styles.warningText}>
            • Chart loads after 1s delay to prevent freeze{'\n'}
            • If app freezes, force quit and restart{'\n'}
            • Test gestures after chart fully loads{'\n'}
            • Monitor console for errors
          </Text>
        </View>
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#F8FAFC',
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: 16,
    backgroundColor: '#FFFFFF',
    borderBottomWidth: 1,
    borderBottomColor: '#E5E7EB',
  },
  title: {
    fontSize: 20,
    fontWeight: '700',
    color: '#1C1C1E',
  },
  closeButton: {
    paddingHorizontal: 16,
    paddingVertical: 8,
    backgroundColor: '#EF4444',
    borderRadius: 8,
  },
  closeText: {
    color: '#FFFFFF',
    fontWeight: '600',
  },
  content: {
    flex: 1,
  },
  section: {
    padding: 16,
    backgroundColor: '#FFFFFF',
    marginBottom: 8,
  },
  sectionTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: '#1C1C1E',
    marginBottom: 12,
  },
  buttonRow: {
    flexDirection: 'row',
    gap: 12,
  },
  button: {
    flex: 1,
    paddingVertical: 12,
    paddingHorizontal: 16,
    backgroundColor: '#F3F4F6',
    borderRadius: 8,
    alignItems: 'center',
  },
  buttonActive: {
    backgroundColor: '#0F62FE',
  },
  buttonText: {
    color: '#1C1C1E',
    fontWeight: '600',
    fontSize: 14,
  },
  chartSection: {
    padding: 16,
    backgroundColor: '#FFFFFF',
    marginBottom: 8,
  },
  loadingContainer: {
    height: 300,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: '#F9FAFB',
    borderRadius: 12,
  },
  loadingText: {
    marginTop: 12,
    fontSize: 16,
    color: '#6B7280',
    fontWeight: '600',
  },
  loadingSubtext: {
    marginTop: 4,
    fontSize: 12,
    color: '#9CA3AF',
  },
  enableContainer: {
    height: 300,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: '#FEF3C7',
    borderRadius: 12,
    padding: 24,
    borderWidth: 2,
    borderColor: '#F59E0B',
  },
  enableText: {
    fontSize: 18,
    fontWeight: '700',
    color: '#92400E',
    marginBottom: 8,
    textAlign: 'center',
  },
  enableSubtext: {
    fontSize: 14,
    color: '#78350F',
    textAlign: 'center',
    lineHeight: 20,
    marginBottom: 20,
  },
  enableButton: {
    backgroundColor: '#EF4444',
    paddingHorizontal: 24,
    paddingVertical: 12,
    borderRadius: 8,
  },
  enableButtonText: {
    color: '#FFFFFF',
    fontSize: 16,
    fontWeight: '600',
  },
  chartContainer: {
    backgroundColor: '#FFFFFF',
    borderRadius: 12,
    padding: 8, // Reduced padding to give chart more room
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 8,
    elevation: 3,
    overflow: 'hidden', // Ensure content doesn't overflow
  },
  featuresSection: {
    padding: 16,
    backgroundColor: '#FFFFFF',
    marginBottom: 8,
  },
  featureList: {
    gap: 8,
  },
  featureItem: {
    fontSize: 14,
    color: '#4B5563',
    paddingVertical: 4,
  },
  warningSection: {
    padding: 16,
    backgroundColor: '#FEF3C7',
    margin: 16,
    borderRadius: 8,
    borderLeftWidth: 4,
    borderLeftColor: '#F59E0B',
  },
  warningTitle: {
    fontSize: 16,
    fontWeight: '700',
    color: '#92400E',
    marginBottom: 8,
  },
  warningText: {
    fontSize: 13,
    color: '#78350F',
    lineHeight: 20,
  },
});

