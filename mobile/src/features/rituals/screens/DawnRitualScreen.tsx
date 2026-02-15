/**
 * Dawn Ritual Screen (Ritual Dawn)
 * Full-screen modal wrapper for the tactical morning check-in.
 */

import React from 'react';
import { Modal } from 'react-native';
import { DawnRitual } from '../components/DawnRitual';

interface DawnRitualScreenProps {
  visible: boolean;
  onComplete?: (result: { syncedTransactions: number; actionTaken: string }) => void;
  onClose?: () => void;
  onNavigate?: (screen: string, params?: Record<string, unknown>) => void;
}

export const DawnRitualScreen: React.FC<DawnRitualScreenProps> = ({
  visible,
  onComplete,
  onClose,
  onNavigate,
}) => {
  const handleComplete = (result: { syncedTransactions: number; actionTaken: string }) => {
    onComplete?.(result);
    onClose?.();
  };

  const handleSkip = () => {
    onClose?.();
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
        onNavigate={onNavigate}
      />
    </Modal>
  );
};
