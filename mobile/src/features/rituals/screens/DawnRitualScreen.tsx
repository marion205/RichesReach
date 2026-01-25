/**
 * Dawn Ritual Screen
 * Full-screen experience for the daily dawn ritual
 */

import React, { useState, useRef, useEffect } from 'react';
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
  const closeTimeoutRef = useRef<NodeJS.Timeout | null>(null);

  // Cleanup timeout on unmount
  useEffect(() => {
    return () => {
      if (closeTimeoutRef.current) {
        clearTimeout(closeTimeoutRef.current);
        closeTimeoutRef.current = null;
      }
    };
  }, []);

  const handleComplete = (transactionsSynced: number) => {
    setIsComplete(true);
    // Auto-close after 2 seconds
    if (closeTimeoutRef.current) {
      clearTimeout(closeTimeoutRef.current);
    }
    closeTimeoutRef.current = setTimeout(() => {
      if (onComplete) {
        onComplete(transactionsSynced);
      }
      if (onClose) {
        onClose();
      }
      setIsComplete(false);
      closeTimeoutRef.current = null;
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

