import React, { useState, useEffect, useRef } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  ScrollView,
  Alert,
  ActivityIndicator,
  Modal,
  TextInput,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import * as Speech from 'expo-speech';
import * as Haptics from 'expo-haptics';
import { useVoice } from '../contexts/VoiceContext';

interface VoiceCommand {
  id: string;
  type: string;
  original_text: string;
  confidence: number;
  result?: any;
  message?: string;
}

interface VoiceTradingCommandsProps {
  onCommandExecuted?: (command: VoiceCommand) => void;
  onError?: (error: string) => void;
}

const VoiceTradingCommands: React.FC<VoiceTradingCommandsProps> = ({
  onCommandExecuted,
  onError,
}) => {
  const { selectedVoice, getVoiceParameters } = useVoice();
  const [isListening, setIsListening] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const [commandHistory, setCommandHistory] = useState<VoiceCommand[]>([]);
  const [showHelp, setShowHelp] = useState(false);
  const [manualCommand, setManualCommand] = useState('');
  const [showManualInput, setShowManualInput] = useState(false);
  const [lastCommandResult, setLastCommandResult] = useState<any>(null);

  const speechTimeoutRef = useRef<NodeJS.Timeout | null>(null);

  useEffect(() => {
    return () => {
      if (speechTimeoutRef.current) {
        clearTimeout(speechTimeoutRef.current);
      }
    };
  }, []);

  const speakText = (text: string) => {
    const params = getVoiceParameters(selectedVoice.id);
    Speech.speak(text, {
      voice: selectedVoice.id,
      pitch: params.pitch,
      rate: params.rate,
    });
  };

  const processVoiceCommand = async (commandText: string) => {
    setIsProcessing(true);
    
    try {
      const response = await fetch(`${process.env.EXPO_PUBLIC_API_BASE_URL || "http://localhost:8000"}/api/voice-trading/process-command/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          text: commandText,
          voice_name: selectedVoice.name,
        }),
      });

      const data = await response.json();

      if (data.success) {
        const command: VoiceCommand = {
          id: data.command.id,
          type: data.command.type,
          original_text: data.command.original_text,
          confidence: data.command.confidence,
          result: data.result,
          message: data.message,
        };

        setCommandHistory(prev => [command, ...prev.slice(0, 9)]); // Keep last 10
        setLastCommandResult(data.result);
        
        // Speak the result
        speakText(data.message);
        
        // Haptic feedback
        Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success);
        
        onCommandExecuted?.(command);
      } else {
        const errorMessage = data.message || 'Command failed';
        speakText(errorMessage);
        
        Haptics.notificationAsync(Haptics.NotificationFeedbackType.Error);
        onError?.(errorMessage);
      }
    } catch (error) {
      const errorMessage = `Error processing command: ${error}`;
      speakText(errorMessage);
      
      Haptics.notificationAsync(Haptics.NotificationFeedbackType.Error);
      onError?.(errorMessage);
    } finally {
      setIsProcessing(false);
    }
  };

  const startListening = async () => {
    setIsListening(true);
    
    // Simulate voice recognition (in real app, use @react-native-community/voice)
    speakText(`${selectedVoice.name}: I'm listening. What would you like to do?`);
    
    // Simulate listening for 5 seconds
    speechTimeoutRef.current = setTimeout(() => {
      setIsListening(false);
      
      // Simulate different commands based on random selection
      const sampleCommands = [
        "Buy 100 shares of AAPL",
        "What's the price of TSLA",
        "Show my positions",
        "What's my account balance",
        "News for MSFT",
        "Is the market open",
        "Show my portfolio",
        "Alert me when GOOGL hits $2500"
      ];
      
      const randomCommand = sampleCommands[Math.floor(Math.random() * sampleCommands.length)];
      processVoiceCommand(randomCommand);
    }, 5000);
  };

  const stopListening = () => {
    setIsListening(false);
    if (speechTimeoutRef.current) {
      clearTimeout(speechTimeoutRef.current);
    }
    speakText(`${selectedVoice.name}: Listening stopped.`);
  };

  const executeManualCommand = () => {
    if (manualCommand.trim()) {
      processVoiceCommand(manualCommand.trim());
      setManualCommand('');
      setShowManualInput(false);
    }
  };

  const getHelpCommands = async () => {
    try {
      const response = await fetch(`${process.env.EXPO_PUBLIC_API_BASE_URL || "http://localhost:8000"}/api/voice-trading/help-commands/`);
      const data = await response.json();
      
      if (data.success) {
        setShowHelp(true);
        speakText(data.message);
      }
    } catch (error) {
      onError?.(`Error getting help: ${error}`);
    }
  };

  const getCommandIcon = (type: string) => {
    switch (type) {
      case 'TRADE': return 'trending-up';
      case 'QUOTE': return 'pricetag';
      case 'POSITION': return 'pie-chart';
      case 'ACCOUNT': return 'wallet';
      case 'NEWS': return 'newspaper';
      case 'MARKET_STATUS': return 'time';
      case 'PORTFOLIO': return 'briefcase';
      case 'ALERT': return 'notifications';
      default: return 'help-circle';
    }
  };

  const getCommandColor = (type: string) => {
    switch (type) {
      case 'TRADE': return '#4CAF50';
      case 'QUOTE': return '#2196F3';
      case 'POSITION': return '#FF9800';
      case 'ACCOUNT': return '#9C27B0';
      case 'NEWS': return '#F44336';
      case 'MARKET_STATUS': return '#607D8B';
      case 'PORTFOLIO': return '#795548';
      case 'ALERT': return '#E91E63';
      default: return '#9E9E9E';
    }
  };

  const renderCommandHistory = () => (
    <ScrollView style={styles.commandHistory} showsVerticalScrollIndicator={false}>
      <Text style={styles.historyTitle}>Recent Commands</Text>
      {commandHistory.map((command, index) => (
        <View key={command.id} style={styles.commandItem}>
          <View style={styles.commandHeader}>
            <Ionicons 
              name={getCommandIcon(command.type)} 
              size={20} 
              color={getCommandColor(command.type)} 
            />
            <Text style={styles.commandType}>{command.type}</Text>
            <Text style={styles.confidence}>
              {(command.confidence * 100).toFixed(0)}%
            </Text>
          </View>
          <Text style={styles.commandText}>"{command.original_text}"</Text>
          {command.message && (
            <Text style={styles.commandResult}>{command.message}</Text>
          )}
        </View>
      ))}
      {commandHistory.length === 0 && (
        <Text style={styles.noCommands}>No commands yet. Try saying something!</Text>
      )}
    </ScrollView>
  );

  const renderHelpModal = () => (
    <Modal visible={showHelp} animationType="slide" presentationStyle="pageSheet">
      <View style={styles.helpModal}>
        <View style={styles.helpHeader}>
          <Text style={styles.helpTitle}>Voice Commands</Text>
          <TouchableOpacity onPress={() => setShowHelp(false)}>
            <Ionicons name="close" size={24} color="#333" />
          </TouchableOpacity>
        </View>
        
        <ScrollView style={styles.helpContent}>
          <View style={styles.helpSection}>
            <Text style={styles.helpSectionTitle}>Trading Commands</Text>
            <Text style={styles.helpCommand}>• "Buy 100 shares of AAPL"</Text>
            <Text style={styles.helpCommand}>• "Sell 50 TSLA at market"</Text>
            <Text style={styles.helpCommand}>• "Place limit order for 25 MSFT at $300"</Text>
            <Text style={styles.helpCommand}>• "Buy 10 GOOGL with stop loss at $2500"</Text>
          </View>

          <View style={styles.helpSection}>
            <Text style={styles.helpSectionTitle}>Quote Commands</Text>
            <Text style={styles.helpCommand}>• "What's the price of AAPL"</Text>
            <Text style={styles.helpCommand}>• "Show me TSLA quote"</Text>
            <Text style={styles.helpCommand}>• "Current price for MSFT"</Text>
          </View>

          <View style={styles.helpSection}>
            <Text style={styles.helpSectionTitle}>Position Commands</Text>
            <Text style={styles.helpCommand}>• "Show my AAPL position"</Text>
            <Text style={styles.helpCommand}>• "What positions do I have"</Text>
            <Text style={styles.helpCommand}>• "Position status for TSLA"</Text>
          </View>

          <View style={styles.helpSection}>
            <Text style={styles.helpSectionTitle}>Account Commands</Text>
            <Text style={styles.helpCommand}>• "What's my account balance"</Text>
            <Text style={styles.helpCommand}>• "Show my buying power"</Text>
            <Text style={styles.helpCommand}>• "Account equity"</Text>
          </View>

          <View style={styles.helpSection}>
            <Text style={styles.helpSectionTitle}>News Commands</Text>
            <Text style={styles.helpCommand}>• "News for AAPL"</Text>
            <Text style={styles.helpCommand}>• "Show me TSLA headlines"</Text>
            <Text style={styles.helpCommand}>• "Latest news for MSFT"</Text>
          </View>

          <View style={styles.helpSection}>
            <Text style={styles.helpSectionTitle}>Market Commands</Text>
            <Text style={styles.helpCommand}>• "Is the market open"</Text>
            <Text style={styles.helpCommand}>• "Market status"</Text>
            <Text style={styles.helpCommand}>• "Trading hours"</Text>
          </View>

          <View style={styles.helpSection}>
            <Text style={styles.helpSectionTitle}>Portfolio Commands</Text>
            <Text style={styles.helpCommand}>• "Show my portfolio"</Text>
            <Text style={styles.helpCommand}>• "All positions"</Text>
            <Text style={styles.helpCommand}>• "Portfolio summary"</Text>
          </View>

          <View style={styles.helpSection}>
            <Text style={styles.helpSectionTitle}>Alert Commands</Text>
            <Text style={styles.helpCommand}>• "Alert me when AAPL hits $160"</Text>
            <Text style={styles.helpCommand}>• "Watch TSLA above $250"</Text>
            <Text style={styles.helpCommand}>• "Monitor MSFT below $300"</Text>
          </View>
        </ScrollView>
      </View>
    </Modal>
  );

  const renderManualInputModal = () => (
    <Modal visible={showManualInput} animationType="slide" presentationStyle="pageSheet">
      <View style={styles.manualModal}>
        <View style={styles.manualHeader}>
          <Text style={styles.manualTitle}>Manual Command</Text>
          <TouchableOpacity onPress={() => setShowManualInput(false)}>
            <Ionicons name="close" size={24} color="#333" />
          </TouchableOpacity>
        </View>
        
        <View style={styles.manualContent}>
          <Text style={styles.manualLabel}>Enter your trading command:</Text>
          <TextInput
            style={styles.manualInput}
            value={manualCommand}
            onChangeText={setManualCommand}
            placeholder="e.g., Buy 100 shares of AAPL"
            multiline
            autoFocus
          />
          
          <TouchableOpacity 
            style={[styles.executeButton, !manualCommand.trim() && styles.executeButtonDisabled]}
            onPress={executeManualCommand}
            disabled={!manualCommand.trim()}
          >
            <Text style={styles.executeButtonText}>Execute Command</Text>
          </TouchableOpacity>
        </View>
      </View>
    </Modal>
  );

  return (
    <View style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.title}>Voice Trading Commands</Text>
        <Text style={styles.voiceName}>Voice: {selectedVoice.name}</Text>
      </View>

      <View style={styles.controls}>
        <TouchableOpacity
          style={[styles.listenButton, isListening && styles.listening]}
          onPress={isListening ? stopListening : startListening}
          disabled={isProcessing}
        >
          {isListening ? (
            <ActivityIndicator color="#fff" size="small" />
          ) : (
            <Ionicons name="mic" size={24} color="#fff" />
          )}
          <Text style={styles.listenButtonText}>
            {isListening ? 'Listening...' : 'Tap to Speak'}
          </Text>
        </TouchableOpacity>

        <View style={styles.buttonRow}>
          <TouchableOpacity style={styles.actionButton} onPress={getHelpCommands}>
            <Ionicons name="help-circle" size={20} color="#007bff" />
            <Text style={styles.actionButtonText}>Help</Text>
          </TouchableOpacity>

          <TouchableOpacity 
            style={styles.actionButton} 
            onPress={() => setShowManualInput(true)}
          >
            <Ionicons name="create-outline" size={20} color="#007bff" />
            <Text style={styles.actionButtonText}>Manual</Text>
          </TouchableOpacity>
        </View>
      </View>

      {isProcessing && (
        <View style={styles.processingIndicator}>
          <ActivityIndicator size="small" color="#007bff" />
          <Text style={styles.processingText}>Processing command...</Text>
        </View>
      )}

      {lastCommandResult && (
        <View style={styles.resultContainer}>
          <Text style={styles.resultTitle}>Last Command Result:</Text>
          <Text style={styles.resultText}>
            {JSON.stringify(lastCommandResult, null, 2)}
          </Text>
        </View>
      )}

      {renderCommandHistory()}
      {renderHelpModal()}
      {renderManualInputModal()}
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f0f2f5',
  },
  header: {
    padding: 20,
    backgroundColor: '#fff',
    borderBottomWidth: 1,
    borderBottomColor: '#e0e0e0',
  },
  title: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#333',
    marginBottom: 5,
  },
  voiceName: {
    fontSize: 16,
    color: '#666',
  },
  controls: {
    padding: 20,
    backgroundColor: '#fff',
    marginBottom: 10,
  },
  listenButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: '#007bff',
    paddingVertical: 15,
    paddingHorizontal: 30,
    borderRadius: 30,
    marginBottom: 15,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.2,
    shadowRadius: 4,
    elevation: 5,
  },
  listening: {
    backgroundColor: '#ffc107',
  },
  listenButtonText: {
    color: '#fff',
    fontSize: 18,
    fontWeight: 'bold',
    marginLeft: 10,
  },
  buttonRow: {
    flexDirection: 'row',
    justifyContent: 'space-around',
  },
  actionButton: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: 10,
    paddingHorizontal: 20,
    borderRadius: 20,
    backgroundColor: '#f8f9fa',
    borderWidth: 1,
    borderColor: '#007bff',
  },
  actionButtonText: {
    color: '#007bff',
    fontSize: 16,
    fontWeight: '600',
    marginLeft: 5,
  },
  processingIndicator: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    padding: 15,
    backgroundColor: '#fff',
    marginBottom: 10,
  },
  processingText: {
    marginLeft: 10,
    fontSize: 16,
    color: '#007bff',
  },
  resultContainer: {
    backgroundColor: '#fff',
    margin: 10,
    padding: 15,
    borderRadius: 10,
    borderLeftWidth: 4,
    borderLeftColor: '#007bff',
  },
  resultTitle: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#333',
    marginBottom: 10,
  },
  resultText: {
    fontSize: 14,
    color: '#666',
    fontFamily: 'monospace',
  },
  commandHistory: {
    flex: 1,
    padding: 10,
  },
  historyTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#333',
    marginBottom: 15,
    paddingHorizontal: 10,
  },
  commandItem: {
    backgroundColor: '#fff',
    padding: 15,
    marginBottom: 10,
    borderRadius: 10,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.1,
    shadowRadius: 3,
    elevation: 3,
  },
  commandHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 8,
  },
  commandType: {
    fontSize: 14,
    fontWeight: 'bold',
    color: '#333',
    marginLeft: 8,
    flex: 1,
  },
  confidence: {
    fontSize: 12,
    color: '#666',
    backgroundColor: '#f0f0f0',
    paddingHorizontal: 8,
    paddingVertical: 2,
    borderRadius: 10,
  },
  commandText: {
    fontSize: 16,
    color: '#333',
    fontStyle: 'italic',
    marginBottom: 5,
  },
  commandResult: {
    fontSize: 14,
    color: '#666',
    backgroundColor: '#f8f9fa',
    padding: 8,
    borderRadius: 5,
  },
  noCommands: {
    textAlign: 'center',
    fontSize: 16,
    color: '#999',
    fontStyle: 'italic',
    marginTop: 50,
  },
  helpModal: {
    flex: 1,
    backgroundColor: '#fff',
  },
  helpHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: 20,
    borderBottomWidth: 1,
    borderBottomColor: '#e0e0e0',
  },
  helpTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#333',
  },
  helpContent: {
    flex: 1,
    padding: 20,
  },
  helpSection: {
    marginBottom: 25,
  },
  helpSectionTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#333',
    marginBottom: 10,
  },
  helpCommand: {
    fontSize: 16,
    color: '#666',
    marginBottom: 5,
    paddingLeft: 10,
  },
  manualModal: {
    flex: 1,
    backgroundColor: '#fff',
  },
  manualHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: 20,
    borderBottomWidth: 1,
    borderBottomColor: '#e0e0e0',
  },
  manualTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#333',
  },
  manualContent: {
    flex: 1,
    padding: 20,
  },
  manualLabel: {
    fontSize: 16,
    color: '#333',
    marginBottom: 15,
  },
  manualInput: {
    borderWidth: 1,
    borderColor: '#ddd',
    borderRadius: 10,
    padding: 15,
    fontSize: 16,
    minHeight: 100,
    textAlignVertical: 'top',
    marginBottom: 20,
  },
  executeButton: {
    backgroundColor: '#007bff',
    paddingVertical: 15,
    borderRadius: 10,
    alignItems: 'center',
  },
  executeButtonDisabled: {
    backgroundColor: '#ccc',
  },
  executeButtonText: {
    color: '#fff',
    fontSize: 18,
    fontWeight: 'bold',
  },
});

export default VoiceTradingCommands;
