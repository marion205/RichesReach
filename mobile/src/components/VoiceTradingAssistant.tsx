import React, { useState, useEffect, useCallback } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  Alert,
  Vibration,
  Platform,
} from 'react-native';
import { useMutation, useSubscription } from '@apollo/client';
import { gql } from '@apollo/client';
import * as Haptics from 'expo-haptics';
import * as Speech from 'expo-speech';
import { useVoice } from '../../contexts/VoiceContext';

// GraphQL Mutations and Subscriptions
const PARSE_VOICE_COMMAND = gql`
  mutation ParseVoiceCommand($input: VoiceCommandInput!) {
    parseVoiceCommand(input: $input) {
      success
      parsedOrder {
        symbol
        side
        quantity
        orderType
        price
        confidence
        confirmationMessage
      }
      message
      error
    }
  }
`;

const PLACE_ORDER = gql`
  mutation PlaceOrder($input: OrderInput!) {
    placeOrder(input: $input) {
      success
      order {
        id
        symbol
        side
        orderType
        quantity
        status
        limitPrice
        stopPrice
      }
      message
      error
    }
  }
`;

const QUOTE_SUBSCRIPTION = gql`
  subscription QuoteUpdate($symbol: String!) {
    quoteUpdate(symbol: $symbol) {
      symbol
      bidPrice
      askPrice
      spreadBps
      timestamp
      midPrice
    }
  }
`;

const VOICE_ALERT_SUBSCRIPTION = gql`
  subscription VoiceAlert {
    voiceAlert {
      symbol
      message
      alertType
      timestamp
    }
  }
`;

interface ParsedOrder {
  symbol: string;
  side: string;
  quantity: number;
  orderType: string;
  price?: number;
  confidence: number;
  confirmationMessage: string;
}

interface VoiceTradingState {
  isListening: boolean;
  parsedOrder: ParsedOrder | null;
  pendingConfirmation: boolean;
  liveQuotes: Record<string, any>;
  voiceAlerts: any[];
}

const VoiceTradingAssistant: React.FC = () => {
  const { getSelectedVoice, speakText } = useVoice();
  const [state, setState] = useState<VoiceTradingState>({
    isListening: false,
    parsedOrder: null,
    pendingConfirmation: false,
    liveQuotes: {},
    voiceAlerts: [],
  });

  // GraphQL mutations
  const [parseVoiceCommand] = useMutation(PARSE_VOICE_COMMAND);
  const [placeOrder, { loading: placingOrder }] = useMutation(PLACE_ORDER);

  // Subscriptions for real-time updates
  useSubscription(QUOTE_SUBSCRIPTION, {
    variables: { symbol: state.parsedOrder?.symbol },
    onData: ({ data }) => {
      if (data?.data?.quoteUpdate) {
        const quote = data.data.quoteUpdate;
        setState(prev => ({
          ...prev,
          liveQuotes: {
            ...prev.liveQuotes,
            [quote.symbol]: quote,
          },
        }));
      }
    },
  });

  useSubscription(VOICE_ALERT_SUBSCRIPTION, {
    onData: ({ data }) => {
      if (data?.data?.voiceAlert) {
        const alert = data.data.voiceAlert;
        setState(prev => ({
          ...prev,
          voiceAlerts: [...prev.voiceAlerts, alert],
        }));
        
        // Speak the alert
        speakText(alert.message, { voice: getSelectedVoice() });
        
        // Haptic feedback
        triggerHapticFeedback('heavy');
      }
    },
  });

  const triggerHapticFeedback = useCallback((style: 'light' | 'medium' | 'heavy') => {
    if (Platform.OS === 'ios') {
      Haptics.impactAsync(Haptics.ImpactFeedbackStyle[style.toUpperCase()]);
    } else {
      Vibration.vibrate(100);
    }
  }, []);

  const handleVoiceCommand = useCallback(async (transcript: string) => {
    try {
      const selectedVoice = getSelectedVoice();
      
      // Parse the voice command
      const result = await parseVoiceCommand({
        variables: {
          input: {
            transcript,
            voiceName: selectedVoice,
          },
        },
      });

      if (result.data?.parseVoiceCommand?.success) {
        const parsedOrder = result.data.parseVoiceCommand.parsedOrder;
        
        setState(prev => ({
          ...prev,
          parsedOrder,
          pendingConfirmation: true,
        }));

        // Speak confirmation
        speakText(parsedOrder.confirmationMessage, { voice: selectedVoice });
        
        // Haptic feedback for successful parsing
        triggerHapticFeedback('medium');
        
      } else {
        const error = result.data?.parseVoiceCommand?.error || 'Could not parse command';
        speakText(`Sorry, I couldn't process that trade. ${error}`, { voice: selectedVoice });
        triggerHapticFeedback('light');
      }
      
    } catch (error) {
      console.error('Voice command parsing failed:', error);
      speakText('Sorry, there was an error processing your command.', { voice: getSelectedVoice() });
    }
  }, [parseVoiceCommand, getSelectedVoice, speakText, triggerHapticFeedback]);

  const confirmOrder = useCallback(async () => {
    if (!state.parsedOrder) return;

    try {
      const selectedVoice = getSelectedVoice();
      
      // Place the order
      const result = await placeOrder({
        variables: {
          input: {
            symbol: state.parsedOrder.symbol,
            side: state.parsedOrder.side,
            quantity: state.parsedOrder.quantity,
            orderType: state.parsedOrder.orderType,
            price: state.parsedOrder.price,
            clientOrderId: `${state.parsedOrder.symbol}-${Date.now()}`,
          },
        },
      });

      if (result.data?.placeOrder?.success) {
        const order = result.data.placeOrder.order;
        
        // Success feedback
        const successMessage = `Order placed successfully! ID ${order.id}. Watching with Oracle.`;
        speakText(successMessage, { voice: selectedVoice });
        
        // Strong haptic feedback for successful order
        triggerHapticFeedback('heavy');
        
        // Reset state
        setState(prev => ({
          ...prev,
          parsedOrder: null,
          pendingConfirmation: false,
        }));
        
      } else {
        const error = result.data?.placeOrder?.error || 'Order placement failed';
        speakText(`Order failed: ${error}`, { voice: selectedVoice });
        triggerHapticFeedback('light');
      }
      
    } catch (error) {
      console.error('Order placement failed:', error);
      speakText('Sorry, there was an error placing your order.', { voice: getSelectedVoice() });
    }
  }, [state.parsedOrder, placeOrder, getSelectedVoice, speakText, triggerHapticFeedback]);

  const cancelOrder = useCallback(() => {
    const selectedVoice = getSelectedVoice();
    speakText('Order cancelled.', { voice: selectedVoice });
    
    setState(prev => ({
      ...prev,
      parsedOrder: null,
      pendingConfirmation: false,
    }));
    
    triggerHapticFeedback('light');
  }, [getSelectedVoice, speakText, triggerHapticFeedback]);

  const startListening = useCallback(() => {
    setState(prev => ({ ...prev, isListening: true }));
    triggerHapticFeedback('medium');
  }, [triggerHapticFeedback]);

  const stopListening = useCallback(() => {
    setState(prev => ({ ...prev, isListening: false }));
  }, []);

  return (
    <View style={styles.container}>
      {/* Voice Trading Status */}
      <View style={styles.statusContainer}>
        <Text style={styles.statusTitle}>Voice Trading Assistant</Text>
        <Text style={styles.statusText}>
          {state.isListening ? '🎤 Listening...' : '🔇 Ready'}
        </Text>
      </View>

      {/* Live Quotes Display */}
      {state.parsedOrder && state.liveQuotes[state.parsedOrder.symbol] && (
        <View style={styles.quoteContainer}>
          <Text style={styles.quoteTitle}>Live Quote: {state.parsedOrder.symbol}</Text>
          <Text style={styles.quoteText}>
            Bid: ${state.liveQuotes[state.parsedOrder.symbol].bidPrice?.toFixed(2)}
          </Text>
          <Text style={styles.quoteText}>
            Ask: ${state.liveQuotes[state.parsedOrder.symbol].askPrice?.toFixed(2)}
          </Text>
          <Text style={styles.quoteText}>
            Spread: {state.liveQuotes[state.parsedOrder.symbol].spreadBps?.toFixed(1)} bps
          </Text>
        </View>
      )}

      {/* Parsed Order Confirmation */}
      {state.parsedOrder && (
        <View style={styles.orderContainer}>
          <Text style={styles.orderTitle}>Order Confirmation</Text>
          <Text style={styles.orderText}>
            {state.parsedOrder.side.toUpperCase()} {state.parsedOrder.quantity} {state.parsedOrder.symbol}
          </Text>
          <Text style={styles.orderText}>
            Type: {state.parsedOrder.orderType.toUpperCase()}
          </Text>
          {state.parsedOrder.price && (
            <Text style={styles.orderText}>
              Price: ${state.parsedOrder.price}
            </Text>
          )}
          <Text style={styles.confidenceText}>
            Confidence: {(state.parsedOrder.confidence * 100).toFixed(0)}%
          </Text>
        </View>
      )}

      {/* Voice Alerts */}
      {state.voiceAlerts.length > 0 && (
        <View style={styles.alertsContainer}>
          <Text style={styles.alertsTitle}>Live Alerts</Text>
          {state.voiceAlerts.slice(-3).map((alert, index) => (
            <Text key={index} style={styles.alertText}>
              {alert.message}
            </Text>
          ))}
        </View>
      )}

      {/* Action Buttons */}
      <View style={styles.buttonContainer}>
        {!state.pendingConfirmation ? (
          <TouchableOpacity
            style={[styles.button, styles.listenButton]}
            onPress={startListening}
            disabled={state.isListening}
          >
            <Text style={styles.buttonText}>
              {state.isListening ? '🎤 Listening...' : '🎤 Start Listening'}
            </Text>
          </TouchableOpacity>
        ) : (
          <>
            <TouchableOpacity
              style={[styles.button, styles.confirmButton]}
              onPress={confirmOrder}
              disabled={placingOrder}
            >
              <Text style={styles.buttonText}>
                {placingOrder ? '⏳ Placing...' : '✅ Confirm Order'}
              </Text>
            </TouchableOpacity>
            <TouchableOpacity
              style={[styles.button, styles.cancelButton]}
              onPress={cancelOrder}
            >
              <Text style={styles.buttonText}>❌ Cancel</Text>
            </TouchableOpacity>
          </>
        )}
      </View>

      {/* Instructions */}
      <View style={styles.instructionsContainer}>
        <Text style={styles.instructionsTitle}>Voice Commands:</Text>
        <Text style={styles.instructionText}>• "Buy 100 AAPL at limit $150"</Text>
        <Text style={styles.instructionText}>• "Sell 50 TSLA at market"</Text>
        <Text style={styles.instructionText}>• "Long 25 MSFT at $300"</Text>
        <Text style={styles.instructionText}>• "Short 10 NVDA stop at $200"</Text>
      </View>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    padding: 20,
    backgroundColor: '#1a1a1a',
  },
  statusContainer: {
    backgroundColor: '#2a2a2a',
    padding: 15,
    borderRadius: 10,
    marginBottom: 20,
  },
  statusTitle: {
    color: '#00ff88',
    fontSize: 18,
    fontWeight: 'bold',
    marginBottom: 5,
  },
  statusText: {
    color: '#ffffff',
    fontSize: 16,
  },
  quoteContainer: {
    backgroundColor: '#2a2a2a',
    padding: 15,
    borderRadius: 10,
    marginBottom: 20,
  },
  quoteTitle: {
    color: '#00ff88',
    fontSize: 16,
    fontWeight: 'bold',
    marginBottom: 10,
  },
  quoteText: {
    color: '#ffffff',
    fontSize: 14,
    marginBottom: 5,
  },
  orderContainer: {
    backgroundColor: '#2a2a2a',
    padding: 15,
    borderRadius: 10,
    marginBottom: 20,
  },
  orderTitle: {
    color: '#00ff88',
    fontSize: 16,
    fontWeight: 'bold',
    marginBottom: 10,
  },
  orderText: {
    color: '#ffffff',
    fontSize: 14,
    marginBottom: 5,
  },
  confidenceText: {
    color: '#ffaa00',
    fontSize: 12,
    fontStyle: 'italic',
  },
  alertsContainer: {
    backgroundColor: '#2a2a2a',
    padding: 15,
    borderRadius: 10,
    marginBottom: 20,
  },
  alertsTitle: {
    color: '#ff6b6b',
    fontSize: 16,
    fontWeight: 'bold',
    marginBottom: 10,
  },
  alertText: {
    color: '#ffffff',
    fontSize: 12,
    marginBottom: 5,
  },
  buttonContainer: {
    flexDirection: 'row',
    justifyContent: 'space-around',
    marginBottom: 20,
  },
  button: {
    padding: 15,
    borderRadius: 10,
    minWidth: 120,
    alignItems: 'center',
  },
  listenButton: {
    backgroundColor: '#00ff88',
  },
  confirmButton: {
    backgroundColor: '#00ff88',
  },
  cancelButton: {
    backgroundColor: '#ff6b6b',
  },
  buttonText: {
    color: '#000000',
    fontSize: 16,
    fontWeight: 'bold',
  },
  instructionsContainer: {
    backgroundColor: '#2a2a2a',
    padding: 15,
    borderRadius: 10,
  },
  instructionsTitle: {
    color: '#00ff88',
    fontSize: 16,
    fontWeight: 'bold',
    marginBottom: 10,
  },
  instructionText: {
    color: '#ffffff',
    fontSize: 12,
    marginBottom: 5,
  },
});

export default VoiceTradingAssistant;
