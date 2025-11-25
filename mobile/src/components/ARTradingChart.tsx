import React, { useState, useEffect, useRef } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  PanGestureHandler,
  State,
  Dimensions,
  Alert,
  Vibration,
  Platform,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import * as Haptics from 'expo-haptics';
import { useVoice } from '../../contexts/VoiceContext';
import { useMutation, gql } from '@apollo/client';
import { PreExecutionRiskCheckModal } from './common/PreExecutionRiskCheckModal';

const { width: screenWidth, height: screenHeight } = Dimensions.get('window');

// GraphQL Mutations
const PLACE_ORDER = gql`
  mutation PlaceOrder($input: PlaceOrderInput!) {
    placeOrder(input: $input) {
      id
      status
      symbol
      side
      qty
    }
  }
`;

const SWITCH_TRADING_MODE = gql`
  mutation SwitchTradingMode($mode: String!) {
    switchTradingMode(mode: $mode) {
      success
      message
      currentMode
    }
  }
`;

interface TradingPick {
  symbol: string;
  side: 'LONG' | 'SHORT';
  score: number;
  features: {
    momentum_15m: number;
    rvol_10m: number;
    vwap_dist: number;
    breakout_pct: number;
    spread_bps: number;
    catalyst_score: number;
  };
  risk: {
    atr_5m: number;
    size_shares: number;
    stop: number;
    targets: number[];
    time_stop_min: number;
  };
  notes: string;
}

interface ARTradingChartProps {
  pick: TradingPick;
  onTradeExecuted: (pick: TradingPick, side: 'LONG' | 'SHORT') => void;
  onModeSwitch: (mode: 'SAFE' | 'AGGRESSIVE') => void;
}

const ARTradingChart: React.FC<ARTradingChartProps> = ({
  pick,
  onTradeExecuted,
  onModeSwitch,
}) => {
  const { selectedVoice, getVoiceParameters } = useVoice();
  const [placeOrderMutation] = useMutation(PLACE_ORDER);
  const [switchModeMutation] = useMutation(SWITCH_TRADING_MODE);
  
  const [isGestureActive, setIsGestureActive] = useState(false);
  const [gestureDirection, setGestureDirection] = useState<string>('');
  const [currentMode, setCurrentMode] = useState<'SAFE' | 'AGGRESSIVE'>('SAFE');
  
  const gestureRef = useRef<PanGestureHandler>(null);

  const speakText = (text: string) => {
    const params = getVoiceParameters(selectedVoice.id);
    // Use Speech.speak with voice parameters
    if (Platform.OS === 'ios') {
      // iOS speech synthesis
      const utterance = new SpeechSynthesisUtterance(text);
      utterance.voice = selectedVoice.id;
      utterance.pitch = params.pitch;
      utterance.rate = params.rate;
      speechSynthesis.speak(utterance);
    }
  };

  const [showRiskCheck, setShowRiskCheck] = useState(false);
  
  const executeTrade = async (side: 'LONG' | 'SHORT') => {
    // Show risk check before execution
    setShowRiskCheck(true);
  };
  
  const handleRiskCheckConfirm = async () => {
    setShowRiskCheck(false);
    try {
      // Haptic feedback
      await Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success);
      
      // Voice confirmation
      speakText(`${selectedVoice.name}: Executing ${pick.side} trade for ${pick.symbol}`);
      
      // Place order
      const { data } = await placeOrderMutation({
        variables: {
          input: {
            symbol: pick.symbol,
            side: pick.side,
            qty: pick.risk.size_shares,
            type: 'MARKET',
            clientNonce: `${pick.symbol}-${Date.now()}`,
          },
        },
      });
      
      if (data?.placeOrder) {
        // Success haptic
        await Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success);
        
        // Voice confirmation
        speakText(`Trade executed successfully! Order ID: ${data.placeOrder.id}`);
        
        // Callback
        onTradeExecuted(pick, pick.side);
      }
    } catch (error) {
      console.error('Trade execution failed:', error);
      
      // Error haptic
      await Haptics.notificationAsync(Haptics.NotificationFeedbackType.Error);
      
      // Voice error message
      speakText('Trade execution failed. Please try again.');
    }
  };

  const switchMode = async (mode: 'SAFE' | 'AGGRESSIVE') => {
    try {
      // Haptic feedback
      await Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Medium);
      
      // Voice confirmation
      speakText(`Switching to ${mode} mode`);
      
      // Switch mode
      const { data } = await switchModeMutation({
        variables: { mode },
      });
      
      if (data?.switchTradingMode?.success) {
        setCurrentMode(mode);
        
        // Success haptic
        await Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success);
        
        // Voice confirmation
        speakText(`${mode} mode activated`);
        
        // Callback
        onModeSwitch(mode);
      }
    } catch (error) {
      console.error('Mode switch failed:', error);
      
      // Error haptic
      await Haptics.notificationAsync(Haptics.NotificationFeedbackType.Error);
      
      // Voice error message
      speakText('Mode switch failed. Please try again.');
    }
  };

  const handleGesture = (event: any) => {
    const { translationX, translationY, state } = event.nativeEvent;
    
    if (state === State.BEGAN) {
      setIsGestureActive(true);
      await Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light);
    } else if (state === State.ACTIVE) {
      // Determine gesture direction
      if (Math.abs(translationX) > Math.abs(translationY)) {
        if (translationX > 50) {
          setGestureDirection('RIGHT');
        } else if (translationX < -50) {
          setGestureDirection('LEFT');
        }
      } else {
        if (translationY > 50) {
          setGestureDirection('DOWN');
        } else if (translationY < -50) {
          setGestureDirection('UP');
        }
      }
    } else if (state === State.END) {
      setIsGestureActive(false);
      
      // Execute action based on gesture
      if (gestureDirection === 'RIGHT') {
        // Swipe right = Long trade
        executeTrade('LONG');
      } else if (gestureDirection === 'LEFT') {
        // Swipe left = Short trade
        executeTrade('SHORT');
      } else if (gestureDirection === 'UP') {
        // Swipe up = Switch to Aggressive mode
        switchMode('AGGRESSIVE');
      } else if (gestureDirection === 'DOWN') {
        // Swipe down = Switch to Safe mode
        switchMode('SAFE');
      }
      
      setGestureDirection('');
    }
  };

  const getGestureHint = () => {
    if (gestureDirection === 'RIGHT') return '→ LONG';
    if (gestureDirection === 'LEFT') return '← SHORT';
    if (gestureDirection === 'UP') return '↑ AGGRESSIVE';
    if (gestureDirection === 'DOWN') return '↓ SAFE';
    return 'Swipe to trade';
  };

  return (
    <View style={styles.container}>
      {/* AR Chart Overlay */}
      <View style={styles.chartContainer}>
        <PanGestureHandler
          ref={gestureRef}
          onGestureEvent={handleGesture}
          onHandlerStateChange={handleGesture}
        >
          <View style={[
            styles.chartOverlay,
            isGestureActive && styles.gestureActive,
            gestureDirection === 'RIGHT' && styles.gestureRight,
            gestureDirection === 'LEFT' && styles.gestureLeft,
            gestureDirection === 'UP' && styles.gestureUp,
            gestureDirection === 'DOWN' && styles.gestureDown,
          ]}>
            {/* Chart Visualization */}
            <View style={styles.chartContent}>
              <Text style={styles.symbolText}>{pick.symbol}</Text>
              <Text style={styles.scoreText}>Score: {pick.score.toFixed(3)}</Text>
              
              {/* Feature Indicators */}
              <View style={styles.featureIndicators}>
                <View style={styles.featureItem}>
                  <Text style={styles.featureLabel}>Momentum</Text>
                  <Text style={styles.featureValue}>
                    {(pick.features.momentum_15m * 100).toFixed(1)}%
                  </Text>
                </View>
                <View style={styles.featureItem}>
                  <Text style={styles.featureLabel}>Volume</Text>
                  <Text style={styles.featureValue}>
                    {pick.features.rvol_10m.toFixed(1)}x
                  </Text>
                </View>
                <View style={styles.featureItem}>
                  <Text style={styles.featureLabel}>Catalyst</Text>
                  <Text style={styles.featureValue}>
                    {(pick.features.catalyst_score * 100).toFixed(0)}%
                  </Text>
                </View>
              </View>
              
              {/* Risk Metrics */}
              <View style={styles.riskMetrics}>
                <Text style={styles.riskLabel}>Risk: {pick.risk.atr_5m.toFixed(2)}</Text>
                <Text style={styles.riskLabel}>Size: {pick.risk.size_shares}</Text>
                <Text style={styles.riskLabel}>Stop: {(pick.risk.stop * 100).toFixed(1)}%</Text>
              </View>
            </View>
            
            {/* Gesture Hints */}
            <View style={styles.gestureHints}>
              <View style={styles.gestureHint}>
                <Ionicons name="arrow-forward" size={24} color="#4CAF50" />
                <Text style={styles.gestureText}>LONG</Text>
              </View>
              <View style={styles.gestureHint}>
                <Ionicons name="arrow-back" size={24} color="#F44336" />
                <Text style={styles.gestureText}>SHORT</Text>
              </View>
              <View style={styles.gestureHint}>
                <Ionicons name="arrow-up" size={24} color="#FF9800" />
                <Text style={styles.gestureText}>AGGRESSIVE</Text>
              </View>
              <View style={styles.gestureHint}>
                <Ionicons name="arrow-down" size={24} color="#2196F3" />
                <Text style={styles.gestureText}>SAFE</Text>
              </View>
            </View>
            
            {/* Current Mode Indicator */}
            <View style={styles.modeIndicator}>
              <Text style={styles.modeText}>
                Mode: {currentMode}
              </Text>
            </View>
            
            {/* Gesture Feedback */}
            {isGestureActive && (
              <View style={styles.gestureFeedback}>
                <Text style={styles.gestureFeedbackText}>
                  {getGestureHint()}
                </Text>
              </View>
            )}
          </View>
        </PanGestureHandler>
      </View>
      
      {/* Manual Controls */}
      <View style={styles.manualControls}>
        <TouchableOpacity
          style={[styles.controlButton, styles.longButton]}
          onPress={() => executeTrade('LONG')}
        >
          <Ionicons name="arrow-forward" size={20} color="#fff" />
          <Text style={styles.controlButtonText}>LONG</Text>
        </TouchableOpacity>
        
        <TouchableOpacity
          style={[styles.controlButton, styles.shortButton]}
          onPress={() => executeTrade('SHORT')}
        >
          <Ionicons name="arrow-back" size={20} color="#fff" />
          <Text style={styles.controlButtonText}>SHORT</Text>
        </TouchableOpacity>
        
        <TouchableOpacity
          style={[styles.controlButton, styles.modeButton]}
          onPress={() => switchMode(currentMode === 'SAFE' ? 'AGGRESSIVE' : 'SAFE')}
        >
          <Ionicons name="swap-vertical" size={20} color="#fff" />
          <Text style={styles.controlButtonText}>
            {currentMode === 'SAFE' ? 'AGGRESSIVE' : 'SAFE'}
          </Text>
        </TouchableOpacity>
      </View>
      
      {/* Pre-Execution Risk Check Modal */}
      {showRiskCheck && (
        <PreExecutionRiskCheckModal
          visible={showRiskCheck}
          onClose={() => setShowRiskCheck(false)}
          onConfirm={handleRiskCheckConfirm}
          symbol={pick.symbol}
          side={pick.side}
          quantity={pick.risk.size_shares}
          entryPrice={pick.risk.stop ? pick.risk.stop + (pick.risk.atr_5m || 1) : 0}
          stopPrice={pick.risk.stop}
          targetPrice={pick.risk.targets?.[0]}
          totalRisk={pick.risk.stop ? Math.abs((pick.risk.stop + (pick.risk.atr_5m || 1)) - pick.risk.stop) * pick.risk.size_shares : undefined}
        />
      )}
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#000',
  },
  chartContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  chartOverlay: {
    width: screenWidth * 0.9,
    height: screenHeight * 0.6,
    backgroundColor: 'rgba(0, 0, 0, 0.8)',
    borderRadius: 20,
    borderWidth: 2,
    borderColor: '#333',
    justifyContent: 'center',
    alignItems: 'center',
  },
  gestureActive: {
    borderColor: '#FFD700',
    borderWidth: 3,
  },
  gestureRight: {
    borderColor: '#4CAF50',
    backgroundColor: 'rgba(76, 175, 80, 0.1)',
  },
  gestureLeft: {
    borderColor: '#F44336',
    backgroundColor: 'rgba(244, 67, 54, 0.1)',
  },
  gestureUp: {
    borderColor: '#FF9800',
    backgroundColor: 'rgba(255, 152, 0, 0.1)',
  },
  gestureDown: {
    borderColor: '#2196F3',
    backgroundColor: 'rgba(33, 150, 243, 0.1)',
  },
  chartContent: {
    alignItems: 'center',
    padding: 20,
  },
  symbolText: {
    fontSize: 32,
    fontWeight: 'bold',
    color: '#fff',
    marginBottom: 10,
  },
  scoreText: {
    fontSize: 18,
    color: '#4CAF50',
    marginBottom: 20,
  },
  featureIndicators: {
    flexDirection: 'row',
    justifyContent: 'space-around',
    width: '100%',
    marginBottom: 20,
  },
  featureItem: {
    alignItems: 'center',
  },
  featureLabel: {
    fontSize: 12,
    color: '#888',
    marginBottom: 5,
  },
  featureValue: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#fff',
  },
  riskMetrics: {
    flexDirection: 'row',
    justifyContent: 'space-around',
    width: '100%',
  },
  riskLabel: {
    fontSize: 12,
    color: '#FF9800',
  },
  gestureHints: {
    position: 'absolute',
    top: 20,
    left: 20,
    right: 20,
    flexDirection: 'row',
    justifyContent: 'space-between',
  },
  gestureHint: {
    alignItems: 'center',
  },
  gestureText: {
    fontSize: 10,
    color: '#888',
    marginTop: 5,
  },
  modeIndicator: {
    position: 'absolute',
    top: 20,
    right: 20,
    backgroundColor: 'rgba(255, 255, 255, 0.1)',
    paddingHorizontal: 10,
    paddingVertical: 5,
    borderRadius: 15,
  },
  modeText: {
    fontSize: 12,
    color: '#fff',
    fontWeight: 'bold',
  },
  gestureFeedback: {
    position: 'absolute',
    bottom: 20,
    left: 20,
    right: 20,
    backgroundColor: 'rgba(255, 255, 255, 0.9)',
    padding: 15,
    borderRadius: 10,
    alignItems: 'center',
  },
  gestureFeedbackText: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#000',
  },
  manualControls: {
    flexDirection: 'row',
    justifyContent: 'space-around',
    paddingHorizontal: 20,
    paddingVertical: 20,
    backgroundColor: 'rgba(0, 0, 0, 0.8)',
  },
  controlButton: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 20,
    paddingVertical: 15,
    borderRadius: 25,
    minWidth: 100,
    justifyContent: 'center',
  },
  longButton: {
    backgroundColor: '#4CAF50',
  },
  shortButton: {
    backgroundColor: '#F44336',
  },
  modeButton: {
    backgroundColor: '#FF9800',
  },
  controlButtonText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: 'bold',
    marginLeft: 5,
  },
});

export default ARTradingChart;
