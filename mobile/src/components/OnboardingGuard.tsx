/**
 * OnboardingGuard - Shows onboarding prompt if user hasn't completed onboarding/KYC
 * Use this component on screens that require account setup
 */

import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  Modal,
  ActivityIndicator,
} from 'react-native';
import Icon from 'react-native-vector-icons/Feather';
import UserProfileService from '../features/user/services/UserProfileService';
import { useAuth } from '../contexts/AuthContext';

interface OnboardingGuardProps {
  children: React.ReactNode;
  requireKYC?: boolean; // If true, also check for KYC completion
  onNavigateToOnboarding?: () => void;
  forceShowForDemo?: boolean; // Force show modal for demo purposes
}

export default function OnboardingGuard({ 
  children, 
  requireKYC = false,
  onNavigateToOnboarding,
  forceShowForDemo = true // Default to true for demo
}: OnboardingGuardProps) {
  const { user, isAuthenticated } = useAuth();
  const [hasCompletedOnboarding, setHasCompletedOnboarding] = useState<boolean | null>(null);
  const [hasCompletedKYC, setHasCompletedKYC] = useState<boolean | null>(null);
  const [isChecking, setIsChecking] = useState(true);
  const [showPrompt, setShowPrompt] = useState(false);
  const [demoModalDismissed, setDemoModalDismissed] = useState(false);

  useEffect(() => {
    const checkOnboardingStatus = async () => {
      console.log('[OnboardingGuard] Checking status:', { isAuthenticated, hasUser: !!user, requireKYC });
      
      // If user is not authenticated, show prompt to complete account setup
      if (!isAuthenticated || !user) {
        console.log('[OnboardingGuard] User not authenticated, showing prompt');
        setHasCompletedOnboarding(false);
        setHasCompletedKYC(false);
        setIsChecking(false);
        setShowPrompt(true);
        return;
      }

      try {
        const userProfileService = UserProfileService.getInstance();
        const onboardingComplete = await userProfileService.isOnboardingCompleted();
        console.log('[OnboardingGuard] Onboarding complete:', onboardingComplete);
        
        setHasCompletedOnboarding(onboardingComplete);
        
        // TODO: Add KYC check when KYC service is available
        // For now, assume KYC is not required if onboarding is complete
        setHasCompletedKYC(onboardingComplete);
        
        // Show prompt if onboarding not completed, or if KYC required but not completed
        if (!onboardingComplete || (requireKYC && !onboardingComplete)) {
          console.log('[OnboardingGuard] Showing prompt - onboarding:', !onboardingComplete, 'KYC required:', requireKYC);
          setShowPrompt(true);
        } else {
          console.log('[OnboardingGuard] All checks passed, allowing access');
        }
      } catch (error) {
        console.error('[OnboardingGuard] Error checking onboarding status:', error);
        // On error, allow access (graceful degradation for demo)
        setHasCompletedOnboarding(true);
        setHasCompletedKYC(true);
      } finally {
        setIsChecking(false);
      }
    };

    checkOnboardingStatus();
  }, [isAuthenticated, user, requireKYC]);

  const handleCompleteOnboarding = () => {
    setShowPrompt(false);
    if (onNavigateToOnboarding) {
      onNavigateToOnboarding();
    } else {
      // If no navigation handler provided, try to navigate to login/onboarding
      // This is a fallback - ideally the parent component should provide navigation
      console.warn('OnboardingGuard: No navigation handler provided');
    }
  };

  const handleSkip = () => {
    // Allow access for demo purposes, but mark that user was prompted
    console.log('[OnboardingGuard] User clicked "Maybe Later"');
    setShowPrompt(false);
    // Also hide the demo modal if in force mode
    if (forceShowForDemo) {
      // In demo mode, we'll use a state to track if user dismissed
      // For now, just hide it
    }
  };

  // For demo mode: show button to trigger modal, or show modal if not dismissed
  if (forceShowForDemo) {
    const shouldShowModal = !demoModalDismissed;
    console.log('[OnboardingGuard] Demo mode - modal should show:', shouldShowModal);
    
    return (
      <>
        {children}
        {/* Demo: Add a floating button to show onboarding/KYC prompt */}
        {!shouldShowModal && (
          <TouchableOpacity
            style={{
              position: 'absolute',
              bottom: 20,
              right: 20,
              backgroundColor: '#007AFF',
              borderRadius: 28,
              width: 56,
              height: 56,
              justifyContent: 'center',
              alignItems: 'center',
              shadowColor: '#000',
              shadowOffset: { width: 0, height: 2 },
              shadowOpacity: 0.25,
              shadowRadius: 8,
              elevation: 8,
              zIndex: 1000,
            }}
            onPress={() => {
              console.log('[OnboardingGuard] Demo button pressed - showing modal');
              setDemoModalDismissed(false);
            }}
            accessibilityLabel="Complete Account Setup"
          >
            <Icon name="user-check" size={24} color="#FFFFFF" />
          </TouchableOpacity>
        )}
        <Modal
          visible={shouldShowModal}
          transparent={true}
          animationType="fade"
          onRequestClose={() => {
            console.log('[OnboardingGuard] Modal close requested');
            setDemoModalDismissed(true);
          }}
        >
          <View style={styles.modalOverlay}>
            <View style={styles.modalContent}>
              <View style={styles.iconContainer}>
                <Icon name="user-check" size={48} color="#007AFF" />
              </View>
              
              <Text style={styles.modalTitle}>
                {!isAuthenticated || !user
                  ? 'Create Your Account'
                  : !hasCompletedOnboarding 
                  ? 'Complete Your Profile' 
                  : 'Verify Your Identity'}
              </Text>
              
              <Text style={styles.modalMessage}>
                {!isAuthenticated || !user
                  ? 'To access trading features, please create an account and complete your profile setup. This takes less than 2 minutes.'
                  : !hasCompletedOnboarding
                  ? 'To access trading features and personalized recommendations, please complete your profile setup. This takes less than 2 minutes.'
                  : 'To access trading features, we need to verify your identity. This is a quick and secure process.'}
              </Text>

              <View style={styles.buttonContainer}>
                <TouchableOpacity
                  style={styles.skipButton}
                  onPress={() => {
                    console.log('[OnboardingGuard] Maybe Later clicked (demo mode)');
                    setDemoModalDismissed(true);
                    handleSkip();
                  }}
                >
                  <Text style={styles.skipButtonText}>Maybe Later</Text>
                </TouchableOpacity>
                
                <TouchableOpacity
                  style={styles.primaryButton}
                  onPress={handleCompleteOnboarding}
                >
                  <Text style={styles.primaryButtonText}>
                    {!isAuthenticated || !user
                      ? 'Create Account'
                      : !hasCompletedOnboarding 
                      ? 'Complete Setup' 
                      : 'Start Verification'}
                  </Text>
                </TouchableOpacity>
              </View>
            </View>
          </View>
        </Modal>
      </>
    );
  }

  if (isChecking) {
    return (
      <View style={styles.checkingContainer}>
        <ActivityIndicator size="large" color="#007AFF" />
        <Text style={styles.checkingText}>Checking account status...</Text>
      </View>
    );
  }

  // If user hasn't completed onboarding, show prompt modal
  const shouldShowPrompt = showPrompt && (!hasCompletedOnboarding || (requireKYC && !hasCompletedKYC));
  console.log('[OnboardingGuard] Render decision:', { 
    showPrompt, 
    hasCompletedOnboarding, 
    hasCompletedKYC, 
    requireKYC, 
    forceShowForDemo,
    shouldShowPrompt,
    isAuthenticated,
    hasUser: !!user
  });
  
  if (shouldShowPrompt) {
    console.log('[OnboardingGuard] Rendering modal');
    return (
      <>
        {children}
        <Modal
          visible={true}
          transparent={true}
          animationType="fade"
          onRequestClose={handleSkip}
        >
          <View style={styles.modalOverlay}>
            <View style={styles.modalContent}>
              <View style={styles.iconContainer}>
                <Icon name="user-check" size={48} color="#007AFF" />
              </View>
              
              <Text style={styles.modalTitle}>
                {!isAuthenticated || !user
                  ? 'Create Your Account'
                  : !hasCompletedOnboarding 
                  ? 'Complete Your Profile' 
                  : 'Verify Your Identity'}
              </Text>
              
              <Text style={styles.modalMessage}>
                {!isAuthenticated || !user
                  ? 'To access trading features, please create an account and complete your profile setup. This takes less than 2 minutes.'
                  : !hasCompletedOnboarding
                  ? 'To access trading features and personalized recommendations, please complete your profile setup. This takes less than 2 minutes.'
                  : 'To access trading features, we need to verify your identity. This is a quick and secure process.'}
              </Text>

              <View style={styles.buttonContainer}>
                <TouchableOpacity
                  style={styles.skipButton}
                  onPress={handleSkip}
                >
                  <Text style={styles.skipButtonText}>Maybe Later</Text>
                </TouchableOpacity>
                
                <TouchableOpacity
                  style={styles.primaryButton}
                  onPress={handleCompleteOnboarding}
                >
                  <Text style={styles.primaryButtonText}>
                    {!isAuthenticated || !user
                      ? 'Create Account'
                      : !hasCompletedOnboarding 
                      ? 'Complete Setup' 
                      : 'Start Verification'}
                  </Text>
                </TouchableOpacity>
              </View>
            </View>
          </View>
        </Modal>
      </>
    );
  }

  // User has completed onboarding (and KYC if required), show content
  return <>{children}</>;
}

const styles = StyleSheet.create({
  checkingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: '#F8F9FA',
  },
  checkingText: {
    marginTop: 16,
    fontSize: 16,
    color: '#6B7280',
  },
  modalOverlay: {
    flex: 1,
    backgroundColor: 'rgba(0, 0, 0, 0.5)',
    justifyContent: 'center',
    alignItems: 'center',
    padding: 20,
  },
  modalContent: {
    backgroundColor: '#FFFFFF',
    borderRadius: 20,
    padding: 24,
    width: '100%',
    maxWidth: 400,
    alignItems: 'center',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.25,
    shadowRadius: 12,
    elevation: 8,
  },
  iconContainer: {
    width: 80,
    height: 80,
    borderRadius: 40,
    backgroundColor: '#EBF4FF',
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: 20,
  },
  modalTitle: {
    fontSize: 24,
    fontWeight: '700',
    color: '#1C1C1E',
    marginBottom: 12,
    textAlign: 'center',
  },
  modalMessage: {
    fontSize: 16,
    color: '#6B7280',
    textAlign: 'center',
    lineHeight: 24,
    marginBottom: 24,
  },
  buttonContainer: {
    flexDirection: 'row',
    gap: 12,
    width: '100%',
  },
  skipButton: {
    flex: 1,
    paddingVertical: 14,
    paddingHorizontal: 20,
    borderRadius: 12,
    backgroundColor: '#F3F4F6',
    alignItems: 'center',
  },
  skipButtonText: {
    fontSize: 16,
    fontWeight: '600',
    color: '#6B7280',
  },
  primaryButton: {
    flex: 1,
    paddingVertical: 14,
    paddingHorizontal: 20,
    borderRadius: 12,
    backgroundColor: '#007AFF',
    alignItems: 'center',
  },
  primaryButtonText: {
    fontSize: 16,
    fontWeight: '600',
    color: '#FFFFFF',
  },
});

