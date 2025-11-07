/**
 * Dawn Ritual Screen
 * Full-screen experience for the daily dawn ritual
 */

import React, { useState } from 'react';
import { Modal, StyleSheet } from 'react-native';
import { DawnRitual } from '../components/DawnRitual';

interface DawnRitualScreenProps {
  visible: boolean;
  onComplete?: (transactionsSynced: number) => void;
  onClose?: () => void;
}

export const DawnRitualScreen: React.FC<DawnRitualScreenProps> = ({
  visible,
  onComplete,
  onClose,
}) => {
  const [isComplete, setIsComplete] = useState(false);

  const handleComplete = (transactionsSynced: number) => {
    setIsComplete(true);
    // Auto-close after 2 seconds
    setTimeout(() => {
      if (onComplete) {
        onComplete(transactionsSynced);
      }
      if (onClose) {
        onClose();
      }
      setIsComplete(false);
    }, 2000);
  };

  const handleSkip = () => {
    if (onClose) {
      onClose();
    }
  };

  return (
    <Modal
      visible={visible}
      animationType="fade"
      transparent={false}
      onRequestClose={handleSkip}
    >
      <DawnRitual
        visible={visible}
        onComplete={handleComplete}
        onSkip={handleSkip}
      />
    </Modal>
  );
};

